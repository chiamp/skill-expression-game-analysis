import numpy as np

import torch
from torch import nn

import time

from blackjack import BlackJack
from agent import RLAgent
from win_probability_analysis import get_total_ai_win_probability


def train(config):
    """
    Train an agent to learn an optimal strategy for the BlackJack game, in the format specified in the config.
    Periodically calculate the AI agent's current learned strategy's theoretical winrate, and sample games with greedy action selection to get its empirical winrate.
    
    Args:
        config (dict): A dictionary specifying parameter configurations

    Returns:
        agent (RLAgent): An AI agent trained on the BlackJack game, in the format specified in the config
        theoretical_win_probability_history (list[ tuple(int,float) ]): A list where each element contains the episode number timestamp and the corresponding theoretical winrate of the AI agent's strategy at that time
        empirical_win_probability_history (list[ tuple(int,float) ]): A list where each element contains the episode number timestamp and the corresponding empirical winrate of the AI agent's strategy at that time
        random_empirical_win_probability (float): The empirical winrate of a random strategy
    """
    
    agent = RLAgent(config)
    game = BlackJack(config)

    theoretical_win_probability_history = [ ( 0 , get_total_ai_win_probability(agent,config) ) ] # list[ tuple( episode_num , win_probability ) ]; keep track of the theoretical win probability of the learned AI strategy
    empirical_win_probability_history = [ ( 0 , evaluate_agent(agent,config) ) ] # list[ tuple( episode_num , win_probability ) ]; keep track of the empirical win probability of the learned AI strategy
    print(f"Episode: 0\tAI strategy theoretical winrate: {theoretical_win_probability_history[0][1]}\tAI strategy empirical winrate: {empirical_win_probability_history[0][1]}")

    start_time = time.time()
    for episode_num in range( 1 , int( config['train']['num_episodes'] ) + 1 ):
        game.reset()
        current_game_features = game.get_features()

        last_observed_game_features = current_game_features # the last game_features observed by the agent, BEFORE making its final action_index
        last_action_index = None # the last action_index made by the agent, before it either busts or stays and gives the turn to the dealer

        game_over,result = game.is_game_over()
        while not game_over:

            if game.turn == 0: # player turn
                last_observed_game_features = current_game_features

                if np.random.uniform() < config['train']['exploration_factor']: action_index = np.random.choice(range(2))
                else: action_index = agent.get_argmax_action_index( current_game_features )

                game.apply_action(action_index)
                last_action_index = action_index

                game_over,result = game.is_game_over()

                # don't train the agent on the new_game_features if it stays; train it on the result of the game
                # don't train the agent on the new_game_features if it's game_over (which means the agent busts); train it on the result of the game
                if (not game_over) and (action_index == 1): # the agent hit and didn't bust
                    new_game_features = game.get_features()
                    
                    td_estimate = config['train']['discount_factor'] * agent.get_max_action_value(new_game_features) # no transition rewards
                    agent.update_weights(current_game_features,action_index,td_estimate)

                    current_game_features = new_game_features

            else: # dealer turn
                game.apply_action(1)
                game_over,result = game.is_game_over()

        td_estimate = config['train']['discount_factor'] * torch.tensor([result]).float() # no transition rewards
        agent.update_weights(last_observed_game_features,last_action_index,td_estimate) # we only care about the last game_features the agent sees
        # the game_features technically change while the dealer draws cards, but its inconsequential to the agent, since it can't affect the game anymore
        # therefore last_observed_game_features contains the game_features right before the agent stays or busts
        # in the case that the agent stays, the td_estimate will be the result of either the dealer busting or reaching the dealer_limit

        if episode_num % int(config['train']['interval']) == 0:
            theoretical_win_probability = get_total_ai_win_probability(agent,config)
            theoretical_win_probability_history.append( ( episode_num , theoretical_win_probability ) )

            empirical_win_probability = evaluate_agent(agent,config)
            empirical_win_probability_history.append( ( episode_num , empirical_win_probability ) )

            print(f"Episode: {episode_num}\tAI strategy theoretical winrate: {theoretical_win_probability}\tAI strategy empirical winrate: {empirical_win_probability}\t{time.time()-start_time} seconds")
            start_time = time.time()

    # evaluate the trained AI player agent on their empirical winrate and skill score
    ai_empirical_win_probability = evaluate_agent(agent,config) # sample games to get the AI strategy's empirical winrate
    random_empirical_win_probability = evaluate_agent(None,config) # sample games to get the random strategy's empirical winrate
    print( f'\nAI strategy empirical winrate: {ai_empirical_win_probability}\t' + \
           f'Random strategy empirical winrate: {random_empirical_win_probability}\t' + \
           f'Empirical skill score: {1 - random_empirical_win_probability/(ai_empirical_win_probability+1e-15)}' ) # add 1e-15 to the denominator for numerical stability (there's a chance the denominator is zero)

    return agent , theoretical_win_probability_history , empirical_win_probability_history , random_empirical_win_probability

def evaluate_agent(agent,config,print_game=False):
    """
    Evaluate the AI agent's strategy for the BlackJack game, in the format specified in the config.
    Sample a number of games specified in the config and use greedy action selection (unless the strategy is specifically a random strategy).
    
    Args:
        agent (RLAgent / None): The AI agent whose strategy we want to evaluate; if the input is None, the player will play a random strategy
        config (dict): A dictionary specifying parameter configurations
        print_game (bool): True if you want to print the game as it's played, False otherwise

    Returns:
        winrate (float): The winrate of using the AI agent's strategy
    """
    
    game = BlackJack(config)

    num_wins = 0
    for _ in range( int( config['evaluate']['num_episodes'] ) ):
        game.reset()

        game_over,result = game.is_game_over()
        while not game_over:
            if print_game: print(game)

            if game.turn == 0: # player turn
                if print_game: print([ float( agent(game.get_features(),i) ) for i in range(2) ])

                if type(agent) == type(None): action_index = np.random.choice(range(2)) # if we're using a random strategy, sample a random action
                else: action_index = agent.get_argmax_action_index( game.get_features() ) # otherwise, always take the greedy action_index that maximizes the RLAgent's action-value

                game.apply_action(action_index)

            else: # dealer turn
                game.apply_action(1)

            game_over,result = game.is_game_over()
        if print_game: print(game)

        num_wins += result

    return num_wins / config['evaluate']['num_episodes']
