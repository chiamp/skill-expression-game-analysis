import numpy as np

import torch
from torch import nn

import matplotlib.pyplot as plt

from train import train
from win_probability_analysis import get_total_theoretical_win_probability


def run(config):
    """
    Calculate the theoretical probability of winning the BlackJack game if you play an optimal strategy and a random strategy, according to the game format specified in config.
    Train an AI agent to learn an optimal strategy for the BlackJack game, in the format specified in the config.
    Plot a graph showing how the AI agent's learned strategy's theoretical and empirical winrate changes over time, while comparing it to the theoretical winrate of the optimal and random strategy.
    Plot the empircal winrate of the random strategy as well.
    
    Args:
        config (dict): A dictionary specifying parameter configurations

    Returns: None
    """
    
    np.random.seed(config['seed'])
    torch.manual_seed(config['seed'])

    # calculate theoretical probability of winning, using an optimal and random strategy
    optimal_win_probability , random_win_probability = get_total_theoretical_win_probability(config)

    # train an AI agent to learn an optimal strategy
    agent , ai_theoretical_win_probability_history , ai_empirical_win_probability_history , random_empirical_win_probability = train(config)
    episode_list , ai_win_theoretical_probability_list = tuple( zip(*ai_theoretical_win_probability_history) )
    _ , ai_win_empirical_probability_list = tuple( zip(*ai_empirical_win_probability_history) )

    # print the theoretical probabilities of the player winning using an optimal strategy and random strategy
    # print the player role's theoretical skill score
    print( f'\nOptimal strategy theoretical winrate: {optimal_win_probability}\t' + \
           f'Random strategy theoretical winrate: {random_win_probability}\t' + \
           f'Theoretical skill score: {1 - random_win_probability/(optimal_win_probability+1e-15)}\n') # add 1e-15 to the denominator for numerical stability (in case the optimal_win_probability is 0)

    # plot the theoretical winrates of the optimal and random strategy
    # plot the theoretical and empirical winrates of the AI strategy over time
    plt.plot( episode_list , [ optimal_win_probability for _ in range( len(episode_list) ) ] ,
              linestyle='--' , color='green' , label='Player theoretical winrate (optimal strategy)' )
    plt.plot( episode_list , [ random_win_probability for _ in range( len(episode_list) ) ] ,
              linestyle='--' , color='red' , label='Player theoretical winrate (random strategy)' )
    plt.plot( episode_list , ai_win_theoretical_probability_list , color='blue' , label='Player theoretical winrate (AI strategy)' )
    plt.plot( episode_list , ai_win_empirical_probability_list , color='orange' , label='Player empirical winrate (AI strategy)' )
    plt.plot( episode_list , [ random_empirical_win_probability for _ in range( len(episode_list) ) ] ,
              color='pink' , label='Player empirical winrate (random strategy)' )

    plt.legend(loc='upper right')
    plt.title('Player winrate over time')
    plt.xlabel('Episode number')
    plt.ylabel('Player Winrate')
    plt.ylim([0,1])
    
    plt.show()
    plt.clf()

if __name__ == '__main__':
    config = { 'game': { 'deck': [1,2,3,4]*2, # the deck composition
                         'blackjack_num': 8, # the maximum sum any hand can have; any higher and it busts
                         'dealer_limit': 6 }, # the dealer must hit until the sum of their hand reaches or exceeds this number
               'model': { 'hidden_units': [1024,1024,1024], # number of hidden units for each hidden layer respectively
                          'activation_function': nn.ReLU(),
                          'learning_rate': 1e-3 },
               'train': { 'num_episodes': 5000, # number of episodes to train the agent
                          'discount_factor': 1, # used to calculate the td_estimate when updating the AI agent model's weights
                          'exploration_factor': 0.1, # the percentage chance of choosing a random move, rather than following the AI agent's policy when training
                          'interval': 50}, # every interval episodes, print an update and calculate the AI agent's current learned strategy theoretically and empirically
               'evaluate': { 'num_episodes': 1e4 }, # number of games to sample, when evaluating the winrate of the AI agent's current learned strategy
               'seed': 1
               }

    run(config)
