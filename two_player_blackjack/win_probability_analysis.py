import numpy as np

from itertools import permutations

from blackjack import BlackJack


def draw_prob(game,card):
    """
    Get the probability of drawing the card from the deck of the game.
    
    Args:
        game (BlackJack): The current game instance
        card (int): The card we are interested in getting the probability for

    Returns:
        card_probability (float): The probability of drawing the card from the deck
    """
    
    return game.deck.count(card) / len(game.deck)

def get_game_state_representation(game_state):
    """
    Get a game state representation of game_state. This is not the same as the game state representation used by the RLAgent models.
    This game state representation will be used as a key for a dictionary that stores return values from recursive calls in the get_theoretical_win_probability() and get_ai_win_probability() functions.
    
    Args:
        game_state (BlackJack): The current game instance

    Returns:
        game_state_representation (tuple(int,int,list[int],int)): The game state representation consisting of tuple( sum_dealer_cards , sum_player_cards , tuple( sorted_deck_of_game_state ) , game_turn )
    """
    
    return ( sum(game_state.dealer_hand) , sum(game_state.player_hand) , tuple( sorted(game_state.deck) ) , game_state.turn )

##################################################################################################################################################################################################################

def get_all_initial_states(config):
    """
    Get all possible initial states and the corresponding probability of starting in that initial state for the game format specified in the config.
    
    Args:
        config (dict): A dictionary specifying parameter configurations

    Returns:
        initial_states_list (list[ tuple(BlackJack,float) ]): A list of BlackJack game instances set at all possible initial states and the probabilities of those initial states occurring
    """
    
    game = BlackJack(config)
    game.reset()
    
    initial_state_probabilities = {} # dict { state_tuple: count }; where state_tuple is a tuple( dealer_card , lower_value_player_card , higher_value_player_card ) }

    initial_state_permutations = tuple( permutations(game.deck_copy,r=3) )
    for dealer_card,player_card1,player_card2 in initial_state_permutations:
        initial_state = tuple( [dealer_card] + sorted( ( player_card1 , player_card2 ) ) )
        if initial_state not in initial_state_probabilities: initial_state_probabilities[initial_state] = 0
        initial_state_probabilities[initial_state] += 1

    num_initial_states = len(initial_state_permutations)
    for initial_state in initial_state_probabilities: initial_state_probabilities[initial_state] /= num_initial_states

    # create a hard-copy game instance with all cards in deck
    game_hard_copy = game.copy()
    game_hard_copy.reset()
    game_hard_copy.deck.append( game_hard_copy.dealer_hand.pop() )
    for _ in range(2): game_hard_copy.deck.append( game_hard_copy.player_hand.pop() )

    initial_states = [] # list[ tuple( game , probability ) , ... , ]; where game is an instantiation of an initial state and probability is its corresponding probability
    for initial_state in initial_state_probabilities:
        dealer_card,player_card1,player_card2 = initial_state
        
        new_game = game_hard_copy.copy()
        new_game.dealer_hand = [dealer_card]
        new_game.player_hand = [player_card1,player_card2]

        for card in initial_state: new_game.deck.remove(card)

        initial_states.append( ( new_game , initial_state_probabilities[initial_state] ) )

    return initial_states

##################################################################################################################################################################################################################

def get_total_theoretical_win_probability(config):
    """
    Get the theoretical probability of the player winning according to the game format specified in config, for the following situations:
        - the player plays an optimal strategy and the dealer plays an optimal strategy
        - the player plays an optimal strategy and the dealer plays a random strategy
        - the player plays a random strategy and the dealer plays an optimal strategy
        - the player plays a random strategy and the dealer plays a random strategy
    This function iterates through all possible initial states and calculates the probability of the player winning from that state onward (factoring in the probability of starting in each initial state), for each of the situations described above.
    
    Args:
        config (dict): A dictionary specifying parameter configurations

    Returns:
        total_optimal_player_vs_optimal_dealer_win_probability (float): The probability of the player winning if the player plays an optimal strategy and the dealer plays an optimal strategy
        total_optimal_player_vs_random_dealer_win_probability (float): The probability of the player winning if the player plays an optimal strategy and the dealer plays a random strategy
        total_random_player_vs_optimal_dealer_win_probability (float): The probability of the player winning if the player plays a random strategy and the dealer plays an optimal strategy
        total_random_player_vs_random_dealer_win_probability (float): The probability of the player winning if the player plays a random strategy and the dealer plays a random strategy
    """
    
    initial_states = get_all_initial_states(config)

    # record keeps track of return values of recursive calls of the get_theoretical_win_probability() function, so we can re-use values for game_states we've calculated already
    record = {} # dict{ game_state_representation_tuple: tuple( optimal_win_probability , random_win_probability ) }

    total_optimal_player_vs_optimal_dealer_win_probability = 0 # the probability of the player winning if the player plays an optimal strategy and the dealer plays an optimal strategy
    total_optimal_player_vs_random_dealer_win_probability = 0 # the probability of the player winning if the player plays an optimal strategy and the dealer plays a random strategy
    total_random_player_vs_optimal_dealer_win_probability = 0 # the probability of the player winning if the player plays a random strategy and the dealer plays an optimal strategy
    total_random_player_vs_random_dealer_win_probability = 0 # the probability of the player winning if the player plays a random strategy and the dealer plays a random strategy

    for game_state,probability in initial_states:
        opod_win_probability,oprd_win_probability,rpod_win_probability,rprd_win_probability = get_theoretical_win_probability(game_state,record)
        
        total_optimal_player_vs_optimal_dealer_win_probability += probability * opod_win_probability
        total_optimal_player_vs_random_dealer_win_probability += probability * oprd_win_probability
        total_random_player_vs_optimal_dealer_win_probability += probability * rpod_win_probability
        total_random_player_vs_random_dealer_win_probability += probability * rprd_win_probability

    return ( total_optimal_player_vs_optimal_dealer_win_probability ,
             total_optimal_player_vs_random_dealer_win_probability ,
             total_random_player_vs_optimal_dealer_win_probability ,
             total_random_player_vs_random_dealer_win_probability )

def get_theoretical_win_probability(game_state,record):
    """
    Get the theoretical probability of the player winning if you start from game_state and the following strategies are played onward:
        - the player plays an optimal strategy and the dealer plays an optimal strategy
        - the player plays an optimal strategy and the dealer plays a random strategy
        - the player plays a random strategy and the dealer plays an optimal strategy
        - the player plays a random strategy and the dealer plays a random strategy
    
    Args:
        game_state (BlackJack): The current game instance
        record (dict): A dictionary, dict{ game_state_representation : tuple(probabilities) }, that keeps track of results made by recursive calls of this function (so that we can re-use its results in future function calls)

    Returns:
        total_optimal_player_vs_optimal_dealer_win_probability (float): The probability of the player winning if the player plays an optimal strategy and the dealer plays an optimal strategy
        total_optimal_player_vs_random_dealer_win_probability (float): The probability of the player winning if the player plays an optimal strategy and the dealer plays a random strategy
        total_random_player_vs_optimal_dealer_win_probability (float): The probability of the player winning if the player plays a random strategy and the dealer plays an optimal strategy
        total_random_player_vs_random_dealer_win_probability (float): The probability of the player winning if the player plays a random strategy and the dealer plays a random strategy
    """
    
    game_state_representation = get_game_state_representation(game_state)
    if game_state_representation in record: return record[game_state_representation]
    
    game_over,result = game_state.is_game_over() # results are all in the perspective of the player (1 = player wins, 0 = player loses)
    if game_over: return result,result,result,result # win probabilities are trivially identical for the terminal state, regardless of what strategies were used

    total_optimal_player_vs_optimal_dealer_win_probability = 0 # the probability of the player winning if the player plays an optimal strategy and the dealer plays an optimal strategy
    total_optimal_player_vs_random_dealer_win_probability = 0 # the probability of the player winning if the player plays an optimal strategy and the dealer plays a random strategy
    total_random_player_vs_optimal_dealer_win_probability = 0 # the probability of the player winning if the player plays a random strategy and the dealer plays an optimal strategy
    total_random_player_vs_random_dealer_win_probability = 0 # the probability of the player winning if the player plays a random strategy and the dealer plays a random strategy
    
    if game_state.turn == 1: # dealer turn

        # dealer stay
        dealer_stay_game_state = game_state.copy()
        dealer_stay_game_state.turn += 1

        # opod = optimal player vs optimal dealer , oprd = optimal player vs random dealer , rpod = random player vs optimal dealer , rprd = random player vs random dealer
        # stay_opod_win_probability and stay_rpod_win_probability should be identical, and
        # stay_oprd_win_probability and stay_rprd_win_probability should be identical,
            # since the dealer strategy is identical, and the player has no control of the outcome of the game once it's the dealer's turn
        # no transition probabilities need to be added, since you're not adding a new card to your hand
        stay_opod_win_probability,stay_oprd_win_probability,stay_rpod_win_probability,stay_rprd_win_probability = get_theoretical_win_probability(dealer_stay_game_state,record)
        
        # dealer hit
        # the expected probability of winning if the dealer hits, and then plays an optimal (od) or random (rd) strategy
        hit_opod_win_probability,hit_oprd_win_probability,hit_rpod_win_probability,hit_rprd_win_probability = 0,0,0,0
        # factor in transition probabilities for drawing each unique card remaining in the current game_state's deck
        for card in np.unique(game_state.deck): # have the dealer hit every possible unique card in the current game_state's deck
            dealer_hit_game_state = game_state.copy()
            card_draw_prob = draw_prob(dealer_hit_game_state,card)

            dealer_hit_game_state.dealer_hand.append(card)
            dealer_hit_game_state.deck.remove(card)

            # opod_win_probability and rpod_win_probability should be identical, and
            # oprd_win_probability and rprd_win_probability should be identical,
                # since the dealer strategy is identical, and the player has no control of the outcome of the game once it's the dealer's turn
            opod_win_probability,oprd_win_probability,rpod_win_probability,rprd_win_probability = get_theoretical_win_probability(dealer_hit_game_state,record)
            
            hit_opod_win_probability += card_draw_prob * opod_win_probability
            hit_oprd_win_probability += card_draw_prob * oprd_win_probability
            hit_rpod_win_probability += card_draw_prob * rpod_win_probability
            hit_rprd_win_probability += card_draw_prob * rprd_win_probability

        # the optimal strategy for the dealer would be to always pick the same action that gives the lowest percentage probability of the player winning
        total_optimal_player_vs_optimal_dealer_win_probability += min( stay_opod_win_probability , hit_opod_win_probability )
        total_random_player_vs_optimal_dealer_win_probability += min( stay_rpod_win_probability , hit_rpod_win_probability )

        # a random strategy for the dealer would do either action 50% of the time
        total_optimal_player_vs_random_dealer_win_probability += 0.5 * stay_oprd_win_probability + 0.5 * hit_oprd_win_probability
        total_random_player_vs_random_dealer_win_probability += 0.5 * stay_rprd_win_probability + 0.5 * hit_rprd_win_probability

    else: # player turn

        # player stay
        player_stay_game_state = game_state.copy()
        player_stay_game_state.turn += 1

        # opod = optimal player vs optimal dealer , oprd = optimal player vs random dealer , rpod = random player vs optimal dealer , rprd = random player vs random dealer
        # no transition probabilities need to be added, since you're not adding a new card to your hand
        stay_opod_win_probability,stay_oprd_win_probability,stay_rpod_win_probability,stay_rprd_win_probability = get_theoretical_win_probability(player_stay_game_state,record)
        
        # player hit
        # the expected probability of winning if the player hits, and then:
            # - the player plays an optimal strategy and the dealer plays an optimal strategy (opod)
            # - the player plays an optimal strategy and the dealer plays a random strategy (oprd)
            # - the player plays a random strategy and the dealer plays an optimal strategy (rpod)
            # - the player plays a random strategy and the dealer plays a random strategy (rprd)
        hit_opod_win_probability,hit_oprd_win_probability,hit_rpod_win_probability,hit_rprd_win_probability = 0,0,0,0
        # factor in transition probabilities for drawing each unique card remaining in the current game_state's deck
        for card in np.unique(game_state.deck): # have the player hit every possible unique card in the current game_state's deck
            player_hit_game_state = game_state.copy()
            card_draw_prob = draw_prob(player_hit_game_state,card)

            player_hit_game_state.player_hand.append(card)
            player_hit_game_state.deck.remove(card)

            opod_win_probability,oprd_win_probability,rpod_win_probability,rprd_win_probability = get_theoretical_win_probability(player_hit_game_state,record)
            
            hit_opod_win_probability += card_draw_prob * opod_win_probability
            hit_oprd_win_probability += card_draw_prob * oprd_win_probability
            hit_rpod_win_probability += card_draw_prob * rpod_win_probability
            hit_rprd_win_probability += card_draw_prob * rprd_win_probability

        # the optimal strategy for the player would be to always pick the same action that gives the highest percentage probability of the player winning
        total_optimal_player_vs_optimal_dealer_win_probability += max( stay_opod_win_probability , hit_opod_win_probability )
        total_optimal_player_vs_random_dealer_win_probability += max( stay_oprd_win_probability , hit_oprd_win_probability )

        # a random strategy for the player would do either action 50% of the time
        total_random_player_vs_optimal_dealer_win_probability += 0.5 * stay_rpod_win_probability + 0.5 * hit_rpod_win_probability
        total_random_player_vs_random_dealer_win_probability += 0.5 * stay_rprd_win_probability + 0.5 * hit_rprd_win_probability

    record[game_state_representation] = ( total_optimal_player_vs_optimal_dealer_win_probability ,
                                          total_optimal_player_vs_random_dealer_win_probability ,
                                          total_random_player_vs_optimal_dealer_win_probability ,
                                          total_random_player_vs_random_dealer_win_probability ) # store result in record, so we don't have to redo this work
    
    return ( total_optimal_player_vs_optimal_dealer_win_probability ,
             total_optimal_player_vs_random_dealer_win_probability ,
             total_random_player_vs_optimal_dealer_win_probability ,
             total_random_player_vs_random_dealer_win_probability )
            
##################################################################################################################################################################################################################

def get_total_ai_win_probability(player_agent,dealer_agent,config):
    """
    Get the theoretical probability of the player winning according to the game format specified in config, for the following situations:
        - the player plays the AI player agent strategy and the dealer plays the AI dealer agent strategy
        - the player plays the AI player agent strategy and the dealer plays a random strategy
        - the player plays a random strategy and the dealer plays the AI dealer agent strategy
    This function iterates through all possible initial states and calculates the probability of the player winning from that state onward (factoring in the probability of starting in each initial state), for each of the situations described above.
    
    Args:
        player_agent (RLAgent): The AI player agent, of which we derive the AI player agent strategy from its Q-function
        dealer_agent (RLAgent): The AI dealer agent, of which we derive the AI dealer agent strategy from its Q-function
        config (dict): A dictionary specifying parameter configurations

    Returns:
        total_ai_player_agent_vs_ai_dealer_agent_win_probability (float): The probability of the player winning if the player plays the AI player agent strategy and the dealer plays the AI dealer agent strategy
        total_ai_player_agent_vs_random_dealer_win_probability (float): The probability of the player winning if the player plays the AI player agent strategy and the dealer plays a random strategy
        total_random_player_vs_ai_dealer_agent_win_probability (float): The probability of the player winning if the player plays a random strategy and the dealer plays the AI dealer agent strategy
    """
    
    initial_states = get_all_initial_states(config)

    # record keeps track of return values of recursive calls of the get_ai_win_probability() function, so we can re-use values for game_states we've calculated already
    record = {} # dict{ game_state_representation_tuple: tuple( optimal_win_probability , random_win_probability ) }
    
    total_ai_player_agent_vs_ai_dealer_agent_win_probability = 0 # the probability of the player winning if the player plays the AI player agent strategy and the dealer plays the AI dealer agent strategy
    total_ai_player_agent_vs_random_dealer_win_probability = 0 # the probability of the player winning if the player plays the AI player agent strategy and the dealer plays a random strategy
    total_random_player_vs_ai_dealer_agent_win_probability = 0 # the probability of the player winning if the player plays a random strategy and the dealer plays the AI dealer agent strategy
    
    for game_state,probability in initial_states:
        apad_win_probability,aprd_win_probability,rpad_win_probability = get_ai_win_probability(player_agent,dealer_agent,game_state,record)

        total_ai_player_agent_vs_ai_dealer_agent_win_probability += probability * apad_win_probability
        total_ai_player_agent_vs_random_dealer_win_probability += probability * aprd_win_probability
        total_random_player_vs_ai_dealer_agent_win_probability += probability * rpad_win_probability

    return ( total_ai_player_agent_vs_ai_dealer_agent_win_probability ,
             total_ai_player_agent_vs_random_dealer_win_probability ,
             total_random_player_vs_ai_dealer_agent_win_probability )

def get_ai_win_probability(player_agent,dealer_agent,game_state,record):
    """
    Get the theoretical probability of the player winning if you start from game_state and the following strategies are played onward:
        - the player plays the AI player agent strategy and the dealer plays the AI dealer agent strategy
        - the player plays the AI player agent strategy and the dealer plays a random strategy
        - the player plays a random strategy and the dealer plays the AI dealer agent strategy
    
    Args:
        player_agent (RLAgent): The AI player agent, of which we derive the AI player agent strategy from its Q-function
        dealer_agent (RLAgent): The AI dealer agent, of which we derive the AI dealer agent strategy from its Q-function
        game_state (BlackJack): The current game instance
        record (dict): A dictionary, dict{ game_state_representation : tuple(probabilities) }, that keeps track of results made by recursive calls of this function (so that we can re-use its results in future function calls)

    Returns:
        total_ai_player_agent_vs_ai_dealer_agent_win_probability (float): The probability of the player winning if the player plays the AI player agent strategy and the dealer plays the AI dealer agent strategy
        total_ai_player_agent_vs_random_dealer_win_probability (float): The probability of the player winning if the player plays the AI player agent strategy and the dealer plays a random strategy
        total_random_player_vs_ai_dealer_agent_win_probability (float): The probability of the player winning if the player plays a random strategy and the dealer plays the AI dealer agent strategy
    """

    game_state_representation = get_game_state_representation(game_state)
    if game_state_representation in record: return record[game_state_representation]
    
    game_over,result = game_state.is_game_over() # results are all in the perspective of the player (1 = player wins, 0 = player loses)
    if game_over: return result,result,result # win probabilities are trivially identical for the terminal state, regardless of what strategies were used

    total_ai_player_agent_vs_ai_dealer_agent_win_probability = 0 # the probability of the player winning if the player plays the AI player agent strategy and the dealer plays the AI dealer agent strategy
    total_ai_player_agent_vs_random_dealer_win_probability = 0 # the probability of the player winning if the player plays the AI player agent strategy and the dealer plays a random strategy
    total_random_player_vs_ai_dealer_agent_win_probability = 0 # the probability of the player winning if the player plays a random strategy and the dealer plays the AI dealer agent strategy

    if game_state.turn == 1: # dealer turn

        action_index = dealer_agent.get_argmax_action_index( game_state.get_features() )
        
        # dealer stay
        dealer_stay_game_state = game_state.copy()
        dealer_stay_game_state.turn += 1

        # apad = AI player agent vs AI dealer agent , aprd = AI player agent vs random dealer , rpad = random player vs AI dealer agent
        # no transition probabilities need to be added, since you're not adding a new card to your hand
        # all probability values should be identical since as soon as the dealer stays, the game is over and the result cannot change
        stay_apad_win_probability,stay_aprd_win_probability,stay_rpad_win_probability = get_ai_win_probability(player_agent,dealer_agent,dealer_stay_game_state,record)

        # dealer hit
        # the expected probability of the player winning if the dealer hits, and then:
            # - the player plays the AI player agent strategy and the dealer plays the AI dealer agent strategy (apad)
            # - the player plays the AI player agent and the dealer plays a random strategy (aprd)
            # - the player plays a random strategy and the dealer plays the AI dealer agent strategy (rpad)
        # NOTE: the probability values of apad and rpad should be identical, since the dealer implements the same strategy and the player cannot influence the game at this point
        hit_apad_win_probability,hit_aprd_win_probability,hit_rpad_win_probability = 0,0,0
        # factor in transition probabilities for drawing each unique card remaining in the current game_state's deck
        for card in np.unique(game_state.deck): # have the dealer hit every possible unique card in the current game_state's deck
            dealer_hit_game_state = game_state.copy()
            card_draw_prob = draw_prob(dealer_hit_game_state,card)

            dealer_hit_game_state.dealer_hand.append(card)
            dealer_hit_game_state.deck.remove(card)

            apad_win_probability,aprd_win_probability,rpad_win_probability = get_ai_win_probability(player_agent,dealer_agent,dealer_hit_game_state,record)
            
            hit_apad_win_probability += card_draw_prob * apad_win_probability
            hit_aprd_win_probability += card_draw_prob * aprd_win_probability
            hit_rpad_win_probability += card_draw_prob * rpad_win_probability

        # update AI dealer agent's probabilities with only the probability of the action it chose
        if action_index == 0: # AI dealer agent stay
            total_ai_player_agent_vs_ai_dealer_agent_win_probability += stay_apad_win_probability
            total_random_player_vs_ai_dealer_agent_win_probability += stay_rpad_win_probability
        else: # AI dealer agent hit
            total_ai_player_agent_vs_ai_dealer_agent_win_probability += hit_apad_win_probability
            total_random_player_vs_ai_dealer_agent_win_probability += hit_rpad_win_probability

        # a random strategy for the dealer would do either action 50% of the time
        total_ai_player_agent_vs_random_dealer_win_probability += 0.5 * stay_aprd_win_probability + 0.5 * hit_aprd_win_probability

    else: # player turn

        action_index = player_agent.get_argmax_action_index( game_state.get_features() )
        
        # player stay
        player_stay_game_state = game_state.copy()
        player_stay_game_state.turn += 1

        # apad = AI player agent vs AI dealer agent , aprd = AI player agent vs random dealer , rpad = random player vs AI dealer agent
        # no transition probabilities need to be added, since you're not adding a new card to your hand
        stay_apad_win_probability,stay_aprd_win_probability,stay_rpad_win_probability = get_ai_win_probability(player_agent,dealer_agent,player_stay_game_state,record)

        # player hit
        # the expected probability of the player winning if the player hits, and then:
            # - the player plays the AI player agent strategy and the dealer plays the AI dealer agent strategy (apad)
            # - the player plays the AI player agent and the dealer plays a random strategy (aprd)
            # - the player plays a random strategy and the dealer plays the AI dealer agent strategy (rpad)
        hit_apad_win_probability,hit_aprd_win_probability,hit_rpad_win_probability = 0,0,0
        # factor in transition probabilities for drawing each unique card remaining in the current game_state's deck
        for card in np.unique(game_state.deck): # have the player hit every possible unique card in the current game_state's deck
            player_hit_game_state = game_state.copy()
            card_draw_prob = draw_prob(player_hit_game_state,card)

            player_hit_game_state.player_hand.append(card)
            player_hit_game_state.deck.remove(card)

            apad_win_probability,aprd_win_probability,rpad_win_probability = get_ai_win_probability(player_agent,dealer_agent,player_hit_game_state,record)
            
            hit_apad_win_probability += card_draw_prob * apad_win_probability
            hit_aprd_win_probability += card_draw_prob * aprd_win_probability
            hit_rpad_win_probability += card_draw_prob * rpad_win_probability

        # update AI player agent's probabilities with only the probability of the action it chose
        if action_index == 0: # AI player agent stay
            total_ai_player_agent_vs_ai_dealer_agent_win_probability += stay_apad_win_probability
            total_ai_player_agent_vs_random_dealer_win_probability += stay_aprd_win_probability
        else: # AI player agent hit
            total_ai_player_agent_vs_ai_dealer_agent_win_probability += hit_apad_win_probability
            total_ai_player_agent_vs_random_dealer_win_probability += hit_aprd_win_probability

        # a random strategy for the player would do either action 50% of the time
        total_random_player_vs_ai_dealer_agent_win_probability += 0.5 * stay_rpad_win_probability + 0.5 * hit_rpad_win_probability

    record[game_state_representation] = ( total_ai_player_agent_vs_ai_dealer_agent_win_probability ,
                                          total_ai_player_agent_vs_random_dealer_win_probability ,
                                          total_random_player_vs_ai_dealer_agent_win_probability ) # store result in record, so we don't have to redo this work
    
    return ( total_ai_player_agent_vs_ai_dealer_agent_win_probability ,
             total_ai_player_agent_vs_random_dealer_win_probability ,
             total_random_player_vs_ai_dealer_agent_win_probability )
