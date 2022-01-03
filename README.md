# Analyzing Skill vs Chance in Games
This is a repo where I describe a method to measure the amount of skill expression games have.

## Table of Contents
* [Motivation](#motivation)
* [Defining Skill](#defining-skill)
* [Algorithms and Experiments](#algorithms-and-experiments)
* [Results](#results)
* [Caveats](#caveats)
* [Future Work](#future-work)
* [File Descriptions](#file-descriptions)
* [Additional Resources](#additional-resources)

## Motivation
A friend of mine is a board game designer and was describing a thesis he had to me: 

***Games that incorporate random chance elements can allow less-skilled players to occasionally beat better-skilled players. There exists an optimal balance between the win rates of the less-skilled players and the better-skilled players, that make a game popular.***

As a consequence, games that never allow less-skilled players to beat better-skilled players, would make casual players less inclined to play those games. On the other hand, games that allow less-skilled players to beat better-skilled players too often would give the impression to the players that their choice of actions have little to no effect on the outcome of the game; i.e. the game gives players little to no **agency**.

5 days ago, my friend was pondering whether there was an objective way of quantifying this win rate balance (i.e. the chance a less-skilled player beating a better-skilled player) for board games. If such a method existed, then one can calculate this measurement across many board games and see whether there is a trend in terms of how popular the game is compared to what the win rate balance is like. And if such a trend exists, then that could help in designing future board games that will be popular in general.

Personally I'm a big fan of games in general, and so I found the problem very interesting and started brainstorming some ideas. After a few days of coding and a few sleepless nights, I formulated a possible solution for calculating this win rate balance measurement.

## Defining Skill
The distinction between less-skilled players and better-skilled players is the win rate. Better-skilled players are expected to win more often than less-skilled players. 

To get a measure of how much skill matters in a game (i.e. how much does skill affect the win rate in a game), we need to take a look at both ends of the skill spectrum: players with maximum skill and players with no skill. 

A player with maximum skill will always pick the optimal action that maximizes its chance of winning the game; such a player therefore plays an **optimal strategy** and is deemed an **optimal player**.

A player with no skill is a little bit harder to define. In this project, I define a player with no skill as a player that implements a **random strategy** (i.e. the player always picks random actions) and is thus deemed a **random player**.

By comparing the win rates of a player with maximum skill (an optimal player ) and a player with no skill (a random player), we can measure the maximum effect that skill has in affecting the win rate in a particular game.

## Skill Score
Let's first start with single-player games as an example (e.g. blackjack, solitaire, free cell etc.).

Suppose an optimal player plays a single-player game and ends up with a 60% win rate, averaged over trillions of games. Now suppose a random player plays the same single-player game where it only pick random actions and ends up with a 20% win rate. I would then argue that since a random player has no skill, then any wins that it was able to achieve must've therefore been due to chance effects from the game itself. 

Therefore in this specific example, we see that random chance in a game can account for up to a third of the win rate of the optimal strategy. On the flip side, we can say that the remaining two-thirds of the optimal win rate can be attributed to skill. I call this two-thirds value, the **skill score**:

<img src="https://render.githubusercontent.com/render/math?math=s = 1 - \frac{w_r}{w_o}">

where <img src="https://render.githubusercontent.com/render/math?math=s"> is the skill score, <img src="https://render.githubusercontent.com/render/math?math=w_r"> is the win rate of the random strategy and <img src="https://render.githubusercontent.com/render/math?math=w_o"> is the win rate of the optimal strategy.

In this example, we can see that skill has some influence on the outcome of the game, but part of the outcome is also influenced by random chance.

Now imagine that instead of 20%, the random player achieves a 60% win rate as well. Then in this case, we can see that random chance can account for the total win rate of the optimal strategy. In other words, we can say that none of the games won by the optimal strategy can be attributed to skill. In this example, we can see that the outcome of the game is influenced solely by random chance, and skill has no influence on the outcome of the game. Therefore the skill score is 0.

Finally, if the random player achieves a 0% win rate, then we can conclude that random chance accounts for none of the win rate of the optimal strategy. And therefore, the total optimal win rate can be attributed solely to skill. In this example, we can see that the outcome of the game is influenced solely by skill, and random chance has no influence on the outcome of the game. Therefore the skill score is 1.

The skill score is a measurement from 0 to 1 that tells you how much skill affects the outcome of the game. A skill score of 0 means that the outcome of the game is determined purely by random chance, whereas a skill score of 1 means that the outcome of the game is determined purely by skill. A number in-between means that the outcome of the game is determined by a combination of skill and random chance.

Comparing the skill scores of different games will give us an idea of which games favour skill more or less. If the win rate of a player with no skill (i.e. a player using the random strategy) becomes further and further away from the win rate of a player with maximum skill (i.e. a player using the optimal strategy), then intuitively the game favours skill more; i.e. a higher skill score. If the win rate of a player with no skill becomes closer and closer to the win rate of a player with maximum skill, then intuitively the game favours skill less; i.e. a lower skill score.

An example of a game with a skill score of 0 is guessing a coin flip; the win rate of the random strategy is 50%, which is also the win rate of the optimal strategy.

Note: the win rate of an optimal player will always be at least equal to the win rate of the random player (in the case where the win rates are equal, that would imply that the optimal strategy for the game is the random strategy)

<img src="https://render.githubusercontent.com/render/math?math=">




---

![Alt text](one_player_blackjack/player_winrate.png)

---

![Alt text](two_player_blackjack/player_winrate.png)

![Alt text](two_player_blackjack/dealer_winrate.png)

---


<img src="https://render.githubusercontent.com/render/math?math=">

## Algorithms and Experiments

## Results

## Caveats

## Future Work

## File Descriptions
* `one_player_blackjack / two_player_blackjack`: there are identical files in the `one_player_blackjack` and `two_player_blackjack` directory. Their functions are primarily the same except applied to the one-player blackjack game and the two-player blackjack game respectively:
	* `blackjack.py` holds the BlackJack class, that facilitates the blackjack game
	* `agent.py` holds the RLAgent class, that learns an optimal strategy using reinforcement learning
	* `win_probability_analysis.py` holds functions that calculate the theoretical win rates using optimal, random and AI strategies
	* `train.py` holds the training function to train AI agents to learn an optimal strategy
	* `main.py` runs the entire training procedure for the AI agents and compares the win rates of their learned strategies with the theoretical win rates of the optimal and random strategies
	* `results.txt` contains the results of the AI strategy win rates and the theoretical win rates of the optimal and random strategies
* `requirements.txt` holds all required dependencies, which can be installed by typing `pip install -r requirements.txt` in the command line
* `ideas.txt` holds my (slightly unorganized) ideas that I've brainstormed throughout working on this project, in roughly the order that I came up with them; there are many ideas in there that I explored hypothetically but never implemented

For this project, I'm using Python 3.7.11.

## Additional Resources
* [A paper detailing an alternative approach to measuring skill in games](https://www.uni-trier.de/fileadmin/fb4/prof/BWL/FIN/Veranstaltungen/duersch--Skill_and_chance_2018-03-07.pdf)