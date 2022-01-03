import numpy as np

import torch
from torch import nn
from torch.optim import Adam


class RLAgent(nn.Module):
    """
    An implementation of a classic Q-action_value model.
    Given a state and action index, predicts the action-value; i.e. the expected discounted return the agent will receive if we follow our current policy till termination.
    """
    
    def __init__(self,config):
        """
        Constructor method for the RLAgent class.
        
        Args:
            config (dict): A dictionary specifying parameter configurations
            
        Attributes:
            layers (list[ torch.nn.Linear , torch.nn.ReLU , ... , ]): A list of layers in the neural network
            optimizer (torch.optim.Adam): Adam optimizer used for updating network weights
            loss_function (nn.BCELoss): Binary cross entropy loss function used as the objective function
        """
        
        super(RLAgent,self).__init__()
        
        assert len(config['model']['hidden_units']) >= 1

        # input layer; [ action_space ] + [ normalized_dealer_sum , normalized_player_sum ] + [ probability_of_drawing_card_0 , ... , probability_of_drawing_card_n ]
        layers = [ nn.Linear( 2 + 2 + np.unique( config['game']['deck'] ).size , config['model']['hidden_units'][0] ) , config['model']['activation_function'] ]
        for i in range( len( config['model']['hidden_units'][:-1] ) ): layers.extend( [ nn.Linear( config['model']['hidden_units'][i] , config['model']['hidden_units'][i+1] ) , config['model']['activation_function'] ] ) # hidden layers
        layers.extend( [ nn.Linear( config['model']['hidden_units'][-1] , 1 ) , nn.Sigmoid() ] ) # final hidden layer to output layer; outputs a single scalar value representing the action-value
        self.layers = nn.Sequential(*layers)
        
        self.optimizer = Adam(self.parameters(),lr=config['model']['learning_rate'])
        self.loss_function = nn.BCELoss()
    def forward(self,state,action_index):
        """
        Forward propagation method. Given a state and action_index, return the predicted Q-action_value.
        
        Args:
            state (numpy.ndarray): A numpy array representation of the state
            action_index (int): Represents an action (0 = stay, 1 = hit)

        Returns:
            action_value (torch.Tensor): The predicted Q-action_value (dtype float), as a one-dimensional vector of size 1
        """

        return self.layers( torch.cat( ( torch.flatten( torch.tensor(state).float() ) ,
                                         torch.tensor( [ 1 if i==action_index else 0 for i in range(2) ] ).float() )
                                       )
                            ) # concatenate flattened state and action vector and feed it into self.layers
    def __call__(self,state,action_index): return self.forward(state,action_index)
    def get_argmax_action_index(self,state):
        """
        Get the action index that maximizes the action-value for the input state.
        
        Args:
            state (numpy.ndarray): A numpy array representation of the state

        Returns:
            maximizing_action_index (int): The action index that maximizes the action-value of the input state
        """
        
        return int( self.layers( torch.tensor( np.array( [ np.append(state,[1,0]) ,
                                                           np.append(state,[0,1]) ] ) ).float() ).argmax() )
    def get_max_action_value(self,state):
        """
        Get the maximum action-value for the input state.
        
        Args:
            state (numpy.ndarray): A numpy array representation of the state

        Returns:
            maximum_action_value (torch.Tensor): The maximum action value for the input state (dtype float), as a one-dimensional vector of size 1
        """
        
        # this maximum value will be used to calculate the td_estimate, which will be used to update the RL agent model's weights,
        # so detach this value from the computational graph
        return self.layers( torch.tensor( np.array( [ np.append(state,[1,0]) ,
                                                      np.append(state,[0,1]) ] ) ).float() ).max().detach().reshape(1) # convert scalar to 1D vector of size 1
    def update_weights(self,state,action_index,td_estimate):
        """
        Given the state, action_index and td_estimate (calculated using bootstrapping), update the parameters of this model.
        
        Args:
            state (numpy.ndarray):  A numpy array representation of the state
            action_index (int): Represents an action (0 = stay, 1 = hit)
            td_estimate (torch.Tensor): The "ground truth" value calculated from bootstrapping, using the Bellman equation

        Returns: None
        """
        
        pred = self.forward(state,action_index) # output neuron is a prediction on the expected discounted return, if we were to follow the policy defined by this model until termination
        
        self.optimizer.zero_grad() # zero gradients
        self.loss_function( pred , td_estimate ).backward() # compute gradients
        self.optimizer.step() # apply gradient to model
