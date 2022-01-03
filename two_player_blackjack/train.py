import numpy as np

import torch
from torch import nn

import time

from blackjack import BlackJack
from agent import RLAgent
from win_probability_analysis import get_total_ai_win_probability


def train(config):
    """
    Train an AI player agent and an AI dealer agent to learn optimal strategies for the BlackJack game, in the format specified in the config.
    Periodically calculate the player's theoretical winrate and empirical winrate (via sampling games with greedy action selection), according to the following situations:
        - the player plays the AI player agent strategy and the dealer plays the AI dealer agent strategy (apad)
        - the player plays the AI player agent strategy and the dealer plays a random strategy (aprd)
        - the player plays a random strategy and the dealer plays the AI dealer agent strategy (rpad)
    
    Args:
        config (dict): A dictionary specifying parameter configurations

    Returns:
        strategy_matchups (list[ tuple(RLAgent / None , RLAgent / None) ]): A list of tuples, where each tuple is a strategy matchup, containing trained RLAgent classes (representing AI strategy) or None objects (representing random strategy)
        
        apad_theoretical_win_probability_history (list[ tuple(int,float) ]): A list where each element contains the episode number timestamp and the corresponding theoretical winrate for the player in the (apad) situation
        aprd_theoretical_win_probability_history (list[ tuple(int,float) ]): A list where each element contains the episode number timestamp and the corresponding theoretical winrate for the player in the (aprd) situation
        rpad_theoretical_win_probability_history (list[ tuple(int,float) ]): A list where each element contains the episode number timestamp and the corresponding theoretical winrate for the player in the (rpad) situation

        apad_empirical_win_probability_history (list[ tuple(int,float) ]): A list where each element contains the episode number timestamp and the corresponding empirical winrate for the player in the (apad) situation
        aprd_empirical_win_probability_history (list[ tuple(int,float) ]): A list where each element contains the episode number timestamp and the corresponding empirical winrate for the player in the (aprd) situation
        rpad_empirical_win_probability_history (list[ tuple(int,float) ]): A list where each element contains the episode number timestamp and the corresponding empirical winrate for the player in the (rpad) situation
    """
    
    # strategy_matchups: apad , aprd , rpad
    strategy_matchups = [ ( RLAgent(config) , RLAgent(config) ) , ( RLAgent(config) , None ) , ( None , RLAgent(config) ) ]
    
    game = BlackJack(config)

    # we need to call get_total_ai_win_probability() 3 times, to get the winrates for each of the 3 individual strategy_matchups
    # this is because the AI strategy trained for the player against the AI strategy of a dealer, would be different than the AI strategy trained for the player against a random strategy of a dealer (and vice versa)
    # since the get_total_ai_win_probability() requires strategy arguments for both player and dealer (even if we want to just evaluate the random strategy of one of the player/dealer),
        # we add the same strategy as a placeholder (since the winrate that we're interested in won't be affected)
        # e.g. for the (aprd) situation, we add the player_agent we're interested in evaluating against the random dealer, and then we add that player_agent again as the dealer argument
        # the strategy denoted by the dealer argument doesn't affect the (aprd) winrate, as that is calculated with a random strategy
        # the same can be applied for the (rpad) situation
    apad_theoretical_win_probability,aprd_theoretical_win_probability,rpad_theoretical_win_probability = get_total_ai_win_probability(strategy_matchups[0][0],strategy_matchups[0][1],config)
    apad_theoretical_win_probability_history = [ ( 0 , apad_theoretical_win_probability ) ] # list[ tuple( episode_num , win_probability ) ]; keep track of the theoretical win probability for the player for this strategy_matchup
    apad_theoretical_win_probability,aprd_theoretical_win_probability,rpad_theoretical_win_probability = get_total_ai_win_probability(strategy_matchups[1][0],strategy_matchups[1][0],config)
    aprd_theoretical_win_probability_history = [ ( 0 , aprd_theoretical_win_probability ) ]
    apad_theoretical_win_probability,aprd_theoretical_win_probability,rpad_theoretical_win_probability = get_total_ai_win_probability(strategy_matchups[2][1],strategy_matchups[2][1],config)
    rpad_theoretical_win_probability_history = [ ( 0 , rpad_theoretical_win_probability ) ]

    apad_empirical_win_probability_history = [ ( 0 , evaluate_agents(strategy_matchups[0][0],strategy_matchups[0][1],config) ) ]  # list[ tuple( episode_num , win_probability ) ]; keep track of the empirical win probability for the player for this strategy_matchup
    aprd_empirical_win_probability_history = [ ( 0 , evaluate_agents(strategy_matchups[1][0],strategy_matchups[1][1],config) ) ]
    rpad_empirical_win_probability_history = [ ( 0 , evaluate_agents(strategy_matchups[2][0],strategy_matchups[2][1],config) ) ]
    
    print( f'Episode: 0\n' + \
           f'AI player vs AI dealer theoretical winrate: {apad_theoretical_win_probability_history[-1][1]}\tAI player vs AI dealer empirical winrate: {apad_empirical_win_probability_history[-1][1]}\t\n' + \
           f'AI player vs random dealer theoretical winrate: {aprd_theoretical_win_probability_history[-1][1]}\tAI player vs random dealer empirical winrate: {aprd_empirical_win_probability_history[-1][1]}\t\n' + \
           f'Random player vs AI dealer theoretical winrate: {rpad_theoretical_win_probability_history[-1][1]}\tRandom player vs AI dealer empirical winrate: {rpad_empirical_win_probability_history[-1][1]}\t\n' )
    
    start_time = time.time()
    for episode_num in range( 1 , int( config['train']['num_episodes'] ) + 1 ):

        for player_agent,dealer_agent in strategy_matchups: # train for each strategy_matchup
            
            game.reset()
            current_game_features = game.get_features()

            last_observed_game_features = current_game_features # the last game_features observed by the player_agent, BEFORE making its final action_index
            last_action_index = None # the last action_index made by the player_agent, before it either busts or stays and gives the turn to the dealer_agent

            game_over,result = game.is_game_over()
            while not game_over:

                if game.turn == 0: # player turn
                    last_observed_game_features = current_game_features

                    # sample random actions if the player is using a random strategy for the current strategy_matchup
                    # or sample random actions config['train']['exploration_factor'] of the time if the player is using the AI player_agent strategy
                    if ( type(player_agent) == type(None) ) or ( np.random.uniform() < config['train']['exploration_factor'] ): action_index = np.random.choice(range(2))
                    else: action_index = player_agent.get_argmax_action_index( current_game_features )

                    game.apply_action(action_index)
                    last_action_index = action_index

                    game_over,result = game.is_game_over()

                    # don't train the player_agent on the new_game_features if it stays; train it on the result of the game
                    # don't train the player_agent on the new_game_features if it's game_over (which means the player_agent busts); train it on the result of the game
                    if (not game_over) and (action_index == 1): # the player_agent hit and didn't bust
                        new_game_features = game.get_features()

                        if type(player_agent) != type(None): # train player_agent if we're not using a random strategy for the player
                            td_estimate = config['train']['discount_factor'] * player_agent.get_max_action_value(new_game_features) # no transition rewards
                            player_agent.update_weights(current_game_features,action_index,td_estimate)

                        current_game_features = new_game_features

                else: # dealer turn

                    # sample random actions if the dealer is using a random strategy for the current strategy_matchup
                    # or sample random actions config['train']['exploration_factor'] of the time if the dealer is using the AI dealer_agent strategy
                    if ( type(dealer_agent) == type(None) ) or ( np.random.uniform() < config['train']['exploration_factor'] ): action_index = np.random.choice(range(2))
                    else: action_index = dealer_agent.get_argmax_action_index( current_game_features )

                    game.apply_action(action_index)

                    game_over,result = game.is_game_over()
                        
                    if not game_over:
                        new_game_features = game.get_features()

                        if type(dealer_agent) != type(None): # train dealer_agent if we're not using a random strategy for the dealer
                            td_estimate = config['train']['discount_factor'] * dealer_agent.get_max_action_value(new_game_features)
                            dealer_agent.update_weights(current_game_features,action_index,td_estimate)

                        current_game_features = new_game_features

            if type(dealer_agent) != type(None): # train dealer_agent if we're not using a random strategy for the dealer
                # have the dealer_agent predict the probability of the dealer winning; therefore flip the result so that it's in the perspective of the dealer
                td_estimate = config['train']['discount_factor'] * torch.tensor( [ (result+1)%2 ] ).float()
                dealer_agent.update_weights(current_game_features,action_index,td_estimate)

            if type(player_agent) != type(None): # train player_agent if we're not using a random strategy for the player
                td_estimate = config['train']['discount_factor'] * torch.tensor([result]).float()
                player_agent.update_weights(last_observed_game_features,last_action_index,td_estimate) # we only care about the last game_features the agent sees
                # the game_features technically change while the dealer draws cards, but its inconsequential to the agent, since it can't affect the game anymore
                # therefore last_observed_game_features contains the game_features right before the agent stays or busts
                # in the case that the agent stays, the td_estimate will be the result of either the dealer staying or busting

        if episode_num % int(config['train']['interval']) == 0:
            # we need to call get_total_ai_win_probability() 3 times, to get the winrates for each of the 3 individual strategy_matchups
            # this is because the AI strategy trained for the player against the AI strategy of a dealer, would be different than the AI strategy trained for the player against a random strategy of a dealer (and vice versa)
            # since the get_total_ai_win_probability() requires strategy arguments for both player and dealer (even if we want to just evaluate the random strategy of one of the player/dealer),
                # we add the same strategy as a placeholder (since the winrate that we're interested in won't be affected)
                # e.g. for the (aprd) situation, we add the player_agent we're interested in evaluating against the random dealer, and then we add that player_agent again as the dealer argument
                # the strategy denoted by the dealer argument doesn't affect the (aprd) winrate, as that is calculated with a random strategy
                # the same can be applied for the (rpad) situation
            apad_theoretical_win_probability,aprd_theoretical_win_probability,rpad_theoretical_win_probability = get_total_ai_win_probability(strategy_matchups[0][0],strategy_matchups[0][1],config)
            apad_theoretical_win_probability_history.append( ( episode_num , apad_theoretical_win_probability ) )
            apad_theoretical_win_probability,aprd_theoretical_win_probability,rpad_theoretical_win_probability = get_total_ai_win_probability(strategy_matchups[1][0],strategy_matchups[1][0],config)
            aprd_theoretical_win_probability_history.append( ( episode_num , aprd_theoretical_win_probability ) )
            apad_theoretical_win_probability,aprd_theoretical_win_probability,rpad_theoretical_win_probability = get_total_ai_win_probability(strategy_matchups[2][1],strategy_matchups[2][1],config)
            rpad_theoretical_win_probability_history.append( ( episode_num , rpad_theoretical_win_probability ) )

            apad_empirical_win_probability_history.append( ( episode_num , evaluate_agents(strategy_matchups[0][0],strategy_matchups[0][1],config) ) )
            aprd_empirical_win_probability_history.append( ( episode_num , evaluate_agents(strategy_matchups[1][0],strategy_matchups[1][1],config) ) )
            rpad_empirical_win_probability_history.append( ( episode_num , evaluate_agents(strategy_matchups[2][0],strategy_matchups[2][1],config) ) )
            
            print( f'Episode: {episode_num}\t\n' + \
                   f'AI player vs AI dealer theoretical winrate: {apad_theoretical_win_probability_history[-1][1]}\tAI player vs AI dealer empirical winrate: {apad_empirical_win_probability_history[-1][1]}\t\n' + \
                   f'AI player vs random dealer theoretical winrate: {aprd_theoretical_win_probability_history[-1][1]}\tAI player vs random dealer empirical winrate: {aprd_empirical_win_probability_history[-1][1]}\t\n' + \
                   f'Random player vs AI dealer theoretical winrate: {rpad_theoretical_win_probability_history[-1][1]}\tRandom player vs AI dealer empirical winrate: {rpad_empirical_win_probability_history[-1][1]}\t\n' + \
                   f'{time.time()-start_time} seconds\n' )
            start_time = time.time()

    # evaluate the trained AI player and dealer agents on their empirical winrate and skill scores
    apad_win_probability = evaluate_agents(strategy_matchups[0][0],strategy_matchups[0][1],config)
    aprd_win_probability = evaluate_agents(strategy_matchups[1][0],strategy_matchups[1][1],config)
    rpad_win_probability = evaluate_agents(strategy_matchups[2][0],strategy_matchups[2][1],config)
    print( f'\nPlayer empirical winrate (apad): {apad_win_probability}\t' + \
           f'Player empirical winrate (rpad): {rpad_win_probability}\t' + \
           f'Player empirical skill score: {1 - rpad_win_probability/(apad_win_probability+1e-15)}' ) # add 1e-15 to the denominator for numerical stability (there's a chance the denominator is zero early)
    print( f'Dealer empirical winrate (apad): {1-apad_win_probability}\t' + \
           f'Dealer empirical winrate (aprd): {1-aprd_win_probability}\t' + \
           f'Dealer empirical skill score {1 - (1-aprd_win_probability)/(1-apad_win_probability+1e-15)}\n' ) # add 1e-15 to the denominator for numerical stability (there's a chance the denominator is zero)

    return strategy_matchups , \
           apad_theoretical_win_probability_history , aprd_theoretical_win_probability_history , rpad_theoretical_win_probability_history , \
           apad_empirical_win_probability_history , aprd_empirical_win_probability_history , rpad_empirical_win_probability_history

def evaluate_agents(player_agent,dealer_agent,config):
    """
    Evaluate the player_agent's strategy and the dealer_agent's strategy for the BlackJack game, in the format specified in the config.
    Sample a number of games specified in the config and use greedy action selection (unless the strategy is specifically a random strategy).
    
    Args:
        player_agent (RLAgent / None): The AI player agent whose strategy we want to evaluate; if the input is None, the player will play a random strategy
        dealer_agent (RLAgent / None): The AI dealer agent whose strategy we want to evaluate; if the input is None, the dealer will play a random strategy
        config (dict): A dictionary specifying parameter configurations

    Returns:
        winrate (float): The winrate of the player, when using the player_agent's strategy against the dealer_agent's strategy
    """
    
    game = BlackJack(config)
    
    num_wins = 0
    for _ in range( int( config['evaluate']['num_episodes'] ) ):
        game.reset()

        game_over,result = game.is_game_over()
        while not game_over:

            if game.turn == 0: # player turn
                if type(player_agent) == type(None): action_index = np.random.choice(range(2)) # if we're using a random strategy, sample a random action
                else: action_index = player_agent.get_argmax_action_index( game.get_features() ) # otherwise, always take the greedy action_index that maximizes the player_agent's action-value

            else: # dealer turn
                if type(dealer_agent) == type(None): action_index = np.random.choice(range(2)) # if we're using a random strategy, sample a random action
                else: action_index = dealer_agent.get_argmax_action_index( game.get_features() ) # otherwise, always take the greedy action_index that maximizes the dealer_agent's action-value

            game.apply_action(action_index)
            game_over,result = game.is_game_over()

        num_wins += result

    return num_wins / config['evaluate']['num_episodes']
