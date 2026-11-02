# multi_agents.py
# --------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from util import manhattan_distance
from game import Directions, Actions
from pacman import GhostRules, GameState
import random, util
from game import Agent

class ReflexAgent(Agent):
    """
    A reflex agent chooses an action at each choice point by examining
    its alternatives via a state evaluation function.

    The code below is provided as a guide.  You are welcome to change
    it in any way you see fit, so long as you don't touch our method
    headers.
    """


    def get_action(self, game_state):
        """
        You do not need to change this method, but you're welcome to.

        get_action chooses among the best options according to the evaluation function.

        Just like in the previous project, get_action takes a GameState and returns
        some Directions.X for some X in the set {NORTH, SOUTH, WEST, EAST, STOP}
        """
        # Collect legal moves and successor states
        legal_moves = game_state.get_legal_actions()

        # Choose one of the best actions
        scores = [self.evaluation_function(game_state, action) for action in legal_moves]
        best_score = max(scores)
        best_indices = [index for index in range(len(scores)) if scores[index] == best_score]
        chosen_index = random.choice(best_indices) # Pick randomly among the best

        "Add more of your code here if you want to"

        return legal_moves[chosen_index]

    def evaluation_function(self, current_game_state: GameState, action):
        """
        Design a better evaluation function here.

        The evaluation function takes in the current and proposed successor
        GameStates (pacman.py) and returns a number, where higher numbers are better.

        The code below extracts some useful information from the state, like the
        remaining food (new_food) and Pacman position after moving (new_pos).
        new_scared_times holds the number of moves that each ghost will remain
        scared because of Pacman having eaten a power pellet.

        Print out these variables to see what you're getting, then combine them
        to create a masterful evaluation function.
        """
        # Useful information you can extract from a GameState (pacman.py)
        successor_game_state = current_game_state.generate_pacman_successor(action)
        new_pos = successor_game_state.get_pacman_position()
        new_food = successor_game_state.get_food()
        new_ghost_states = successor_game_state.get_ghost_states()
        new_scared_times = [ghostState.scared_timer for ghostState in new_ghost_states]
        
        "*** YOUR CODE HERE ***"

        score = successor_game_state.get_score()

        # power pellets
        capsules = current_game_state.get_capsules()
        if capsules:
            nearest_capsule = min(manhattan_distance(new_pos, c) for c in capsules)
            score += 2.0 / (nearest_capsule + 1)
        if new_pos in capsules:
            score += 50

        #food
        food_list = new_food.as_list()
        if food_list:
            nearest_food = min(manhattan_distance(new_pos, f) for f in food_list)
            score += 1/(1.5*nearest_food + 1) #avoid division by 0

        #ghosts
        for ghost, scared in zip(new_ghost_states, new_scared_times):
            d = manhattan_distance(new_pos, ghost.get_position())
            if d > 10:
                continue
            if scared > d:
                # ghost stays scared long enough to reach it: chase
                score += 30.0 / (d + 1)
            else:
                # active, or about to un-scare before Pacman gets there: avoid
                if d <= 1:
                    return float('-inf')
                score -= 2.0 / d

        if action == Directions.STOP:
            score -= 10

        return score

def score_evaluation_function(current_game_state):
    """
    This default evaluation function just returns the score of the state.
    The score is the same one displayed in the Pacman GUI.

    This evaluation function is meant for use with adversarial search agents
    (not reflex agents).
    """
    return current_game_state.get_score()

class MultiAgentSearchAgent(Agent):
    """
    This class provides some common elements to all of your
    multi-agent searchers.  Any methods defined here will be available
    to the MinimaxPacmanAgent, AlphaBetaPacmanAgent & ExpectimaxPacmanAgent.

    You *do not* need to make any changes here, but you can if you want to
    add functionality to all your adversarial search agents.  Please do not
    remove anything, however.

    Note: this is an abstract class: one that should not be instantiated.  It's
    only partially specified, and designed to be extended.  Agent (game.py)
    is another abstract class.
    """

    def __init__(self, eval_fn='score_evaluation_function', depth='2'):
        super().__init__()
        self.index = 0 # Pacman is always agent index 0
        self.evaluation_function = util.lookup(eval_fn, globals())
        self.depth = int(depth) 

class MinimaxAgent(MultiAgentSearchAgent):
    """
    Your minimax agent (question 2)
    """

    def get_action(self, game_state):
        """
        Returns the minimax action from the current game_state using self.depth
        and self.evaluation_function.

        Here are some method calls that might be useful when implementing minimax.

        game_state.get_legal_actions(agent_index):
        Returns a list of legal actions for an agent
        agent_index=0 means Pacman, ghosts are >= 1

        game_state.generate_successor(agent_index, action):
        Returns the successor game state after an agent takes an action

        game_state.get_num_agents():
        Returns the total number of agents in the game

        game_state.is_win():
        Returns whether or not the game state is a winning state

        game_state.is_lose():
        Returns whether or not the game state is a losing state
        """
        "*** YOUR CODE HERE ***"
        num_agents = game_state.get_num_agents()

        def minimax(state, agent_index, depth):
            """
            Returns the minimax value of `state` when it is `agent_index`'s turn.
            `depth` counts how many full plies are already completed; one ply is
            a move by Pacman followed by one move from every ghost.
            """
            # Terminal test: game over, or we reached the depth limit.
            # In both cases we score the state with the evaluation function.
            if state.is_win() or state.is_lose() or depth == self.depth:
                return self.evaluation_function(state)

            # Work out whose turn comes next. After the last ghost moves we
            # wrap back to Pacman (index 0) and one more ply is complete.
            next_agent = (agent_index + 1) % num_agents
            next_depth = depth + 1 if next_agent == 0 else depth

            values = [minimax(state.generate_successor(agent_index, action), next_agent, next_depth)
                      for action in state.get_legal_actions(agent_index)]

            # Pacman (agent 0) is the MAX player; every ghost is a MIN player.
            return max(values) if agent_index == 0 else min(values)

        # At the root Pacman picks the action whose successor has the highest
        # minimax value. The first ghost (index 1) moves next, still in ply 0.
        best_action = None
        best_value = float('-inf')
        for action in game_state.get_legal_actions(0):
            value = minimax(game_state.generate_successor(0, action), 1 % num_agents,
                            1 if num_agents == 1 else 0)
            if value > best_value:
                best_value, best_action = value, action
        return best_action


class AlphaBetaAgent(MultiAgentSearchAgent):
    """
    Your minimax agent with alpha-beta pruning (question 3)
    """

    def get_action(self, game_state):
        """
        Returns the minimax action using self.depth and self.evaluation_function
        """
        "*** YOUR CODE HERE ***"
        num_agents = game_state.get_num_agents()

        def alpha_beta(state, agent_index, depth, alpha, beta):
            """
            Minimax value of `state` with alpha-beta pruning.
            alpha = best value MAX (Pacman) can already guarantee on the path to the root.
            beta  = best value MIN (ghosts) can already guarantee on the path to the root.
            Successors are generated lazily, one at a time, so that pruned
            branches are never expanded.
            """
            # Same terminal test as in minimax.
            if state.is_win() or state.is_lose() or depth == self.depth:
                return self.evaluation_function(state)

            next_agent = (agent_index + 1) % num_agents
            next_depth = depth + 1 if next_agent == 0 else depth

            if agent_index == 0:
                # MAX node (Pacman)
                value = float('-inf')
                for action in state.get_legal_actions(agent_index):
                    successor = state.generate_successor(agent_index, action)
                    value = max(value, alpha_beta(successor, next_agent, next_depth, alpha, beta))
                    # A MIN ancestor already has an option worth beta, so it will
                    # never let the game reach this node: stop exploring.
                    # Strict '>' so we do not prune on equality.
                    if value > beta:
                        return value
                    alpha = max(alpha, value)
                return value
            else:
                # MIN node (a ghost)
                value = float('inf')
                for action in state.get_legal_actions(agent_index):
                    successor = state.generate_successor(agent_index, action)
                    value = min(value, alpha_beta(successor, next_agent, next_depth, alpha, beta))
                    # A MAX ancestor already has an option worth alpha, so it
                    # will avoid this node: stop exploring.
                    if value < alpha:
                        return value
                    beta = min(beta, value)
                return value

        # The root is a MAX node; we do it here so we can remember the action
        # (not only the value). alpha is updated after every child so that the
        # later root children benefit from pruning too.
        alpha, beta = float('-inf'), float('inf')
        best_action = None
        best_value = float('-inf')
        for action in game_state.get_legal_actions(0):
            value = alpha_beta(game_state.generate_successor(0, action), 1 % num_agents,
                               1 if num_agents == 1 else 0, alpha, beta)
            if value > best_value:
                best_value, best_action = value, action
            alpha = max(alpha, best_value)
        return best_action


class ExpectimaxAgent(MultiAgentSearchAgent):
    """
      Your expectimax agent (question 4)
    """

    def get_action(self, game_state):
        """
        Returns the expectimax action using self.depth and self.evaluation_function

        All ghosts should be modeled as choosing uniformly at random from their
        legal moves.
        """
        "*** YOUR CODE HERE ***"
        util.raise_not_defined()

def better_evaluation_function(current_game_state):
    """
    Your extreme ghost-hunting, pellet-nabbing, food-gobbling, unstoppable
    evaluation function (question 5).

    DESCRIPTION: <write something here so we know what you did>
    """
    "*** YOUR CODE HERE ***"
    util.raise_not_defined()
    


# Abbreviation
better = better_evaluation_function
