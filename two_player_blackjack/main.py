import numpy as np

import torch
from torch import nn

import matplotlib.pyplot as plt

from train import train
from win_probability_analysis import get_total_theoretical_win_probability


def run(config):
    """
    Calculate the theoretical probability of the player winning the BlackJack game according to the game format specified in config, for the following situations:
        - the player plays an optimal strategy and the dealer plays an optimal strategy (opod)
        - the player plays an optimal strategy and the dealer plays a random strategy (oprd)
        - the player plays a random strategy and the dealer plays an optimal strategy (rpod)
    Train an AI player agent and an AI dealer agent to learn optimal strategies for the BlackJack game according to the game format specified in the config, for the following situations:
        - the player plays the AI player agent strategy and the dealer plays the AI dealer agent strategy (apad)
        - the player plays the AI player agent strategy and the dealer plays a random strategy (aprd)
        - the player plays a random strategy and the dealer plays the AI dealer agent strategy (rpad)
    Plot a graph showing how the agents' learned strategies' theoretical and empirical winrates change over time, while comparing it to the theoretical winrates of the optimal and random strategies.
    
    Args:
        config (dict): A dictionary specifying parameter configurations

    Returns: None
    """
    
    np.random.seed(config['seed'])
    torch.manual_seed(config['seed'])

    # calculate the theoretical probability of the player winning, in the following situations:
        # - the player plays an optimal strategy and the dealer plays an optimal strategy (opod)
        # - the player plays an optimal strategy and the dealer plays a random strategy (oprd)
        # - the player plays a random strategy and the dealer plays an optimal strategy (rpod)
        # - the player plays a random strategy and the dealer plays a random strategy (rprd)
    opod_win_probability,oprd_win_probability,rpod_win_probability,rprd_win_probability = get_total_theoretical_win_probability(config)

    # train an AI player_agent and AI dealer_agent to learn optimal strategies in the following situations:
        # - the player plays the AI player agent strategy and the dealer plays the AI dealer agent strategy (apad)
        # - the player plays the AI player agent strategy and the dealer plays a random strategy (aprd)
        # - the player plays a random strategy and the dealer plays the AI dealer agent strategy (rpad)
    strategy_matchups , \
    apad_theoretical_win_probability_history , aprd_theoretical_win_probability_history , rpad_theoretical_win_probability_history , \
    apad_empirical_win_probability_history , aprd_empirical_win_probability_history , rpad_empirical_win_probability_history = train(config)

    # print the theoretical probabilities of the player and dealer winning in the situations described above
    # print the player role and dealer role's theoretical skill scores
    print( f'\nPlayer theoretical winrate (opod): {opod_win_probability}\t' + \
           f'Player theoretical winrate (rpod): {rpod_win_probability}\t' + \
           f'Player theoretical skill score: {1 - rpod_win_probability/(opod_win_probability+1e-15)}' ) # add 1e-15 to the denominator for numerical stability (in case opod_win_probability is 0)
    print( f'Dealer theoretical winrate (opod): {1-opod_win_probability}\t' + \
           f'Dealer theoretical winrate (oprd): {1-oprd_win_probability}\t' + \
           f'Dealer theoretical skill score {1 - (1-oprd_win_probability)/(1-opod_win_probability+1e-15)}\n' ) # add 1e-15 to the denominator for numerical stability (in case 1-opod_win_probability is 0)
    
    episode_list , apad_win_theoretical_probability_list = tuple( zip(*apad_theoretical_win_probability_history) )
    _ , apad_win_empirical_probability_list = tuple( zip(*apad_empirical_win_probability_history) )
    _ , aprd_win_theoretical_probability_list = tuple( zip(*aprd_theoretical_win_probability_history) )
    _ , aprd_win_empirical_probability_list = tuple( zip(*aprd_empirical_win_probability_history) )
    _ , rpad_win_theoretical_probability_list = tuple( zip(*rpad_theoretical_win_probability_history) )
    _ , rpad_win_empirical_probability_list = tuple( zip(*rpad_empirical_win_probability_history) )

    # plot the player's theoretical winrate when using the optimal strategy and random strategy against the dealer's optimal strategy
    # plot the player_agent's theoretical and empirical winrates when using the AI player_agent's strategy and the random strategy against the AI dealer_agent's strategy
    plt.plot( episode_list , [ opod_win_probability for _ in range( len(episode_list) ) ] ,
              linestyle='--' , color='green' , label='Player theoretical winrate (opod)' )
    plt.plot( episode_list , [ rpod_win_probability for _ in range( len(episode_list) ) ] ,
              linestyle='--' , color='red' , label='Player theoretical winrate (rpod)' )
    plt.plot( episode_list , apad_win_theoretical_probability_list , color='blue' , label='Player theoretical winrate (apad)' )
    plt.plot( episode_list , apad_win_empirical_probability_list , color='orange' , label='Player empirical winrate (apad)' )
    plt.plot( episode_list , rpad_win_theoretical_probability_list , color='purple' , label='Player theoretical winrate (rpad)' )
    plt.plot( episode_list , rpad_win_empirical_probability_list , color='pink' , label='Player empirical winrate (rpad)' )

    plt.legend(loc='upper right')
    plt.title('Player winrate over time')
    plt.xlabel('Episode number')
    plt.ylabel('Player winrate')
    plt.ylim([0,1])
    
    plt.show()
    plt.clf()

    # plot the dealer's theoretical winrate when using the optimal strategy, the dealer-hits-until-6 strategy and random strategy against the player's optimal strategy
    # plot the dealer_agent's theoretical and empirical winrates when using the AI dealer_agent's strategy and the random strategy against the AI player_agent's strategy
    # flip the probabilities so that they're in the perspective of the dealer winning
    plt.plot( episode_list , [ 1-opod_win_probability for _ in range( len(episode_list) ) ] ,
              linestyle='--' , color='green' , label='Dealer theoretical winrate (opod)' )
    plt.plot( episode_list , [ 1-oprd_win_probability for _ in range( len(episode_list) ) ] ,
              linestyle='--' , color='red' , label='Dealer theoretical winrate (oprd)' )
    plt.plot( episode_list , [ 1-0.42380952380952375 for _ in range( len(episode_list) ) ] , # 0.42380952380952375 is the theoretical winrate of the player if it plays optimally against the dealer-hits-until-6 strategy (derived from our study of one-player blackjack)
              linestyle='--' , color='brown' , label='Dealer theoretical winrate (dealer_limit=6)' ) # therefore the theoretical winrate of the dealer against this optimal player is 1-0.42380952380952375
    plt.plot( episode_list , [ 1-probability for probability in apad_win_theoretical_probability_list ] , color='blue' , label='Dealer theoretical winrate (apad)' )
    plt.plot( episode_list , [ 1-probability for probability in apad_win_empirical_probability_list ] , color='orange' , label='Dealer empirical winrate (apad)' )
    plt.plot( episode_list , [ 1-probability for probability in aprd_win_theoretical_probability_list ] , color='purple' , label='Dealer theoretical winrate (aprd)' )
    plt.plot( episode_list , [ 1-probability for probability in aprd_win_empirical_probability_list ] , color='pink' , label='Dealer empirical winrate (aprd)' )

    plt.legend(loc='upper right')
    plt.title('Dealer winrate over time')
    plt.xlabel('Episode number')
    plt.ylabel('Dealer winrate')
    plt.ylim([0,1])
    
    plt.show()
    plt.clf()

if __name__ == '__main__':
    config = { 'game': { 'deck': [1,2,3,4]*2, # the deck composition
                         'blackjack_num': 8 }, # the maximum sum any hand can have; any higher and it busts
               'model': { 'hidden_units': [1024,1024,1024], # number of hidden units for each hidden layer respectively
                          'activation_function': nn.ReLU(),
                          'learning_rate': 1e-3 },
               'train': { 'num_episodes': 9000, # number of episodes to train the agent
                          'discount_factor': 1, # used to calculate the td_estimate when updating the AI agent model's weights
                          'exploration_factor': 0.1, # the percentage chance of choosing a random move, rather than following the AI agent's policy when training
                          'interval': 50}, # every interval episodes, print an update and calculate the AI agents' current learned strategies theoretically and empirically
               'evaluate': { 'num_episodes': 1e4 }, # number of games to sample, when evaluating the winrate of the AI agents' current learned strategies
               'seed': 1
               }

    run(config)
