from copy import deepcopy

import numpy as np


class BlackJack:
    """
    An implementation of a simpler version of blackjack. The player is dealt 2 cards face-up and the dealer is dealt 1 card face-up.
    The player goes first and hits until they stay or bust. Then the dealer hits until they stay or bust.
    Aces (represented by the int 1) are only worth 1 and not 11. Ties are won by the dealer.
    """
    
    def __init__(self,config):
        """
        Constructor method for the BlackJack class.
        
        Args:
            config (dict): A dictionary specifying parameter configurations
            
        Attributes:
            deck_copy (list[int]): A hard-copy list of the deck of cards for the game format specified in the config parameter
            blackjack_num (int): The highest possible sum a hand can have. Any number higher than this, that player or dealer busts

            deck (list[int]): A list containing the cards in the deck for the current game
            dealer_hand (list[int]): A list containing the cards for the dealer's hand
            player_hand (list[int]): A list containing the cards for the player's hand

            turn (int): Denotes the current turn (0 = player turn, 1 = dealer turn)
        """
        
        self.deck_copy = config['game']['deck'].copy()
        self.blackjack_num = config['game']['blackjack_num']

        self.deck = None
        self.dealer_hand = None
        self.player_hand = None

        self.turn = None # 0 = player turn, 1 = dealer turn
    def reset(self):
        """
        Reset BlackJack environment: Repopulate the deck with a copy of self.deck_copy, shuffle the deck, deal cards to the player and dealer, and reset the turn counter to 0.
        
        Args: None

        Returns: None
        """
        
        self.deck = self.deck_copy.copy()
        np.random.shuffle(self.deck)

        self.dealer_hand = [ self.deck.pop() ]
        self.player_hand = [ self.deck.pop() for _ in range(2) ]

        self.turn = 0
    def deal(self):
        """
        Deal the top card (represented by the last element) of self.deck to the player (if self.turn == 0) or to the dealer (if self.turn == 1).
        
        Args: None

        Returns: None
        """
        
        if self.turn == 0: self.player_hand.append( self.deck.pop() )
        else: self.dealer_hand.append( self.deck.pop() )
    def apply_action(self,action_index): # 0 = stay, 1 = hit
        """
        Apply the action_index to the BlackJack environment (where action_index == 0 is stay and action_index == 1 is hit).
        
        Args:
            action_index (int): Represents an action (0 = stay, 1 = hit)

        Returns: None
        """
        
        if action_index == 1: self.deal()
        else: self.turn += 1
    def is_game_over(self):
        """
        Check if the game is over, according to the following conditions:
            - the player busts
            - the dealer busts
            - the dealer stays
        
        Args: None

        Returns:
             game_over,result (tuple(bool,float)): bool is True if game is over, float is 1 if player wins, 0 if player loses or ties
        """
        
        if (self.turn == 0) and sum(self.player_hand) > self.blackjack_num: return (True,0.) # player busts

        elif (self.turn == 1) and sum(self.dealer_hand) > self.blackjack_num: return (True,1.) # dealer busts

        elif (self.turn == 2): # dealer stays
            if sum(self.player_hand) > sum(self.dealer_hand): return (True,1.) # player hand is larger than dealer hand
            elif sum(self.player_hand) < sum(self.dealer_hand): return (True,0.) # player hand is smaller than dealer hand
            else: return (True,0.) # tie; *NOTE*: dealer wins if it's a tie!

        return (False,None)

    def get_features(self):
        """
        Get the numpy array representation of the current game state. This method will be used for RLAgent models.
        Features format: [ normalized_dealer_sum , normalized_player_sum ] + [ probability_of_drawing_card_0 , ... , probability_of_drawing_card_n ].
        
        Args: None

        Returns:
            state (numpy.ndarray): A numpy array representation of the state
        """

        # no need to include a feature for game turn as both the player and dealer act independently of each other;
        # i.e., when the player acts, the dealer cannot respond to any actions until the player passes the turn over, at which point the player cannot act for the rest of the round
        # both the player and the dealer can look at the same game features and extract meaningful information to determine what the best action for them to take is
        return np.array( [ sum(self.dealer_hand) / self.blackjack_num , sum(self.player_hand) / self.blackjack_num ] + \
                         [ self.deck.count(card) / len(self.deck) for card in np.unique(self.deck_copy) ] )
    
    def copy(self):
        """
        Return a deep copy of this game instance. This method will be used when calculating the theoretical winrates of the game using the functions found in win_probability_analysis.py.
        
        Args: None

        Returns:
            game_copy (BlackJack): A deep copy of the current game instance
        """

        return deepcopy(self)
    def play_test(self):
        """
        Play test the game using input commands: 0 = stay , 1 = hit.
        
        Args: None

        Returns: None
        """
        
        while True:
            self.reset()

            game_over,result = self.is_game_over()
            while not game_over:
                print(self)

                if self.turn == 0: # player turn
                    action_index = int( input('Player hit or stay: ') )
                    self.apply_action(action_index)

                else: # dealer turn
                    action_index = int( input('Dealer hit or stay: ') )
                    self.apply_action(action_index)
                
                game_over,result = self.is_game_over()
            print(self)
            
            print(f'Game over! Result: {result}')
                    
    def __str__(self):
        """
        Return a human-readable string representation of the current game.
        
        Args: None

        Returns:
            string_representation (str): The string representation of the current game
        """
        
        return f'\nDeck: {self.deck}\nDealer hand: {self.dealer_hand}\nPlayer hand: {self.player_hand}\nTurn: {self.turn}\n'
    def __repr__(self): return str(self)
