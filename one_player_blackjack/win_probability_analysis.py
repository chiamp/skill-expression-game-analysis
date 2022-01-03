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
    Get the theoretical probability of winning if you play an optimal strategy and a random strategy, according to the game format specified in config.
    This function iterates through all possible initial states and calculates the probability of winning from that state onward (factoring in the probability of starting in each initial state), using an optimal and random strategy.
    
    Args:
        config (dict): A dictionary specifying parameter configurations

    Returns:
        total_optimal_win_probability , total_random_win_probability (float,float): A tuple containing the probability of winning if you play an optimal strategy and a random strategy
    """
    
    initial_states = get_all_initial_states(config)

    # record keeps track of return values of recursive calls of the get_theoretical_win_probability() function, so we can re-use values for game_states we've calculated already
    record = {} # dict{ game_state_representation_tuple: tuple( optimal_win_probability , random_win_probability ) }

    total_optimal_win_probability = 0
    total_random_win_probability = 0

    for game_state,probability in initial_states:
        optimal_win_probability , random_win_probability = get_theoretical_win_probability(game_state,record)
        
        total_optimal_win_probability += probability * optimal_win_probability
        total_random_win_probability += probability * random_win_probability

    return total_optimal_win_probability , total_random_win_probability

def get_theoretical_win_probability(game_state,record):
    """
    Get the theoretical probability of winning if you start from game_state and play an optimal strategy and a random strategy onward.
    
    Args:
        game_state (BlackJack): The current game instance
        record (dict): A dictionary, dict{ game_state_representation : tuple(probabilities) }, that keeps track of results made by recursive calls of this function (so that we can re-use its results in future function calls)

    Returns:
        total_optimal_win_probability , total_random_win_probability (float,float): A tuple containing the probability of winning if you play an optimal strategy and a random strategy
    """
    
    game_state_representation = get_game_state_representation(game_state)
    if game_state_representation in record: return record[game_state_representation]
    
    game_over,result = game_state.is_game_over()
    if game_over: return result,result # optimal_win_probability and random_win_probability are trivially identical for the terminal state

    total_optimal_win_probability = 0 # the probability of winning if you play an optimal strategy
    total_random_win_probability = 0 # the probability of winning if you play a random strategy
    
    if game_state.turn == 1: # dealer turn

        for card in np.unique(game_state.deck): # have the dealer hit every possible unique card in the current game_state's deck
            dealer_hit_game_state = game_state.copy()
            card_draw_prob = draw_prob(dealer_hit_game_state,card) # the probability of drawing this card from the current game_state's deck

            dealer_hit_game_state.dealer_hand.append(card)
            dealer_hit_game_state.deck.remove(card)

            # probability values should be identical, as you have no control over how the dealer plays, regardless if you're playing an optimal or random strategy
            optimal_win_probability , random_win_probability = get_theoretical_win_probability(dealer_hit_game_state,record)

            total_optimal_win_probability += card_draw_prob * optimal_win_probability
            total_random_win_probability += card_draw_prob * random_win_probability

    else: # player turn

        # player stay
        player_stay_game_state = game_state.copy()
        player_stay_game_state.turn += 1

        # probability values should be identical, as you have no control over how the dealer plays, regardless if you're playing an optimal or random strategy
        # no transition probabilities need to be added, since you're not adding a new card to your hand
        stay_optimal_win_probability , stay_random_win_probability = get_theoretical_win_probability(player_stay_game_state,record)
        
        # player hit
        hit_optimal_win_probability = 0 # the expected probability of winning if we hit, and then play an optimal strategy
        hit_random_win_probability = 0 # the expected probability of winning if we hit, and then play a random strategy
        # both probability values account for the chance of drawing each unique card remaining in the current game_state's deck
        for card in np.unique(game_state.deck): # have the player hit every possible unique card in the current game_state's deck
            player_hit_game_state = game_state.copy()
            card_draw_prob = draw_prob(player_hit_game_state,card)

            player_hit_game_state.player_hand.append(card)
            player_hit_game_state.deck.remove(card)

            # probability values can be different, as optimal_win_probability will only contain the probability of choosing the optimal action,
            # whereas random_win_probability will contain an expected probability of winning if we randomly sample an action uniformly in the next player_hit_game_state
            optimal_win_probability , random_win_probability = get_theoretical_win_probability(player_hit_game_state,record)

            hit_optimal_win_probability += card_draw_prob * optimal_win_probability
            hit_random_win_probability += card_draw_prob * random_win_probability

        # the optimal strategy would always pick the same action that gives the highest percentage probability of winning
        total_optimal_win_probability += max( stay_optimal_win_probability , hit_optimal_win_probability )

        # a random strategy would do either action 50% of the time
        total_random_win_probability += 0.5 * stay_random_win_probability + 0.5 * hit_random_win_probability 

    record[game_state_representation] = ( total_optimal_win_probability , total_random_win_probability ) # store result in record, so we don't have to redo this work
    return total_optimal_win_probability , total_random_win_probability
            
##################################################################################################################################################################################################################

def get_total_ai_win_probability(agent,config):
    """
    Get the theoretical probability of winning if you play the AI agent's strategy, according to the game format specified in config.
    This function iterates through all possible initial states and calculates the probability of winning from that state onward (factoring in the probability of starting in each initial state), using the AI agent's strategy.
    
    Args:
        agent (RLAgent): The AI agent whose strategy we are calculating
        config (dict): A dictionary specifying parameter configurations

    Returns:
        total_ai_win_probability (float): The probability of winning if you play the AI agent's strategy
    """
    
    initial_states = get_all_initial_states(config)

    # record keeps track of return values of recursive calls of the get_win_probability() function, so we can re-use values for game_states we've calculated already
    record = {} # dict{ game_state_representation_tuple: tuple( optimal_win_probability , random_win_probability ) }

    total_ai_win_probability = 0
    
    for game_state,probability in initial_states:
        total_ai_win_probability += probability * get_ai_win_probability(agent,game_state,record)

    return total_ai_win_probability

def get_ai_win_probability(agent,game_state,record):
    """
    Get the theoretical probability of winning if you start from game_state and play the AI agent's strategy onward.
    
    Args:
        agent (RLAgent): The AI agent whose strategy we are calculating
        game_state (BlackJack): The current game instance
        record (dict): A dictionary, dict{ game_state_representation : tuple(probabilities) }, that keeps track of results made by recursive calls of this function (so that we can re-use its results in future function calls)

    Returns:
        total_ai_win_probability (float): The probability of winning if you play the AI agent's strategy
    """
    
    game_state_representation = get_game_state_representation(game_state)
    if game_state_representation in record: return record[game_state_representation]
    
    game_over,result = game_state.is_game_over()
    if game_over: return result # return whether the AI agent won or not

    total_ai_win_probability = 0 # the probability of winning if you play an optimal strategy
    
    if game_state.turn == 1: # dealer turn

        for card in np.unique(game_state.deck): # have the dealer hit every possible unique card in the current game_state's deck
            dealer_hit_game_state = game_state.copy()
            card_draw_prob = draw_prob(dealer_hit_game_state,card) # the probability of drawing this card from the current game_state's deck

            dealer_hit_game_state.dealer_hand.append(card)
            dealer_hit_game_state.deck.remove(card)

            # multiply by probability of winning the dealer_hit_game_state by the probability of drawing the card that would lead to that game_state
            total_ai_win_probability += card_draw_prob * get_ai_win_probability(agent,dealer_hit_game_state,record)

    else: # player turn

        action_index = agent.get_argmax_action_index( game_state.get_features() )
        
        if action_index == 0: # player stays

            player_stay_game_state = game_state.copy()
            player_stay_game_state.turn += 1
            # no transition probabilities need to be added, since you're not adding a new card to your hand
            total_ai_win_probability += get_ai_win_probability(agent,player_stay_game_state,record)
            
        else: # player hits
            
            for card in np.unique(game_state.deck): # have the player hit every possible unique card in the current game_state's deck
                player_hit_game_state = game_state.copy()
                card_draw_prob = draw_prob(player_hit_game_state,card)

                player_hit_game_state.player_hand.append(card)
                player_hit_game_state.deck.remove(card)

                total_ai_win_probability += card_draw_prob * get_ai_win_probability(agent,player_hit_game_state,record)

    record[game_state_representation] = total_ai_win_probability # store result in record, so we don't have to redo this work
    return total_ai_win_probability
