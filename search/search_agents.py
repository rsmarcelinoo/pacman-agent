# search_agents.py
# ---------------
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


"""
This file contains all of the agents that can be selected to control Pacman.  To
select an agent, use the '-p' option when running pacman.py.  Arguments can be
passed to your agent using '-a'.  For example, to load a SearchAgent that uses
depth first search (dfs), run the following command:

> python pacman.py -p SearchAgent -a fn=depth_first_search

Commands to invoke other search strategies can be found in the project
description.

Please only change the parts of the file you are asked to.  Look for the lines
that say

"*** YOUR CODE HERE ***"

The parts you fill in start about 3/4 of the way down.  Follow the project
description for details.

Good luck and happy searching!
"""

from itertools import chain, combinations
from game import Directions
from game import Agent
from game import Actions
from game import Grid
import util
import time
import search

class GoWestAgent(Agent):
    """An agent that goes West until it can't."""

    def get_action(self, state):
        """The agent receives a GameState (defined in pacman.py)."""
        if Directions.WEST in state.get_legal_pacman_actions():
            return Directions.WEST
        else:
            return Directions.STOP

#######################################################
# This portion is written for you, but will only work #
#       after you fill in parts of search.py          #
#######################################################

class SearchAgent(Agent):
    """
    This very general search agent finds a path using a supplied search
    algorithm for a supplied search problem, then returns actions to follow that
    path.

    As a default, this agent runs DFS on a PositionSearchProblem to find
    location (1,1)

    Options for fn include:
      depth_first_search or dfs
      breadth_first_search or bfs


    Note: You should NOT change any code in SearchAgent
    """

    def __init__(self, fn='depth_first_search', prob='PositionSearchProblem', heuristic='null_heuristic'):
        # Warning: some advanced Python magic is employed below to find the right functions and problems

        # Get the search function from the name and heuristic
        super().__init__()
        if fn not in dir(search):
            raise AttributeError(fn + ' is not a search function in search.py.')
        func = getattr(search, fn)
        if 'heuristic' not in func.__code__.co_varnames:
            print('[SearchAgent] using function ' + fn)
            self.searchFunction = func
        else:
            if heuristic in globals().keys():
                heur = globals()[heuristic]
            elif heuristic in dir(search):
                heur = getattr(search, heuristic)
            else:
                raise AttributeError(heuristic + ' is not a function in search_agents.py or search.py.')
            print('[SearchAgent] using function %s and heuristic %s' % (fn, heuristic))
            # Note: this bit of Python trickery combines the search algorithm and the heuristic
            self.searchFunction = lambda x: func(x, heuristic=heur)

        # Get the search problem type from the name
        if prob not in globals().keys() or not prob.endswith('Problem'):
            raise AttributeError(prob + ' is not a search problem type in SearchAgents.py.')
        self.searchType = globals()[prob]
        print('[SearchAgent] using problem type ' + prob)

    def register_initial_state(self, state):
        """
        This is the first time that the agent sees the layout of the game
        board. Here, we choose a path to the goal. In this phase, the agent
        should compute the path to the goal and store it in a local variable.
        All of the work is done in this method!

        state: a GameState obj (pacman.py)
        """
        if self.searchFunction is None: raise Exception("No search function provided for SearchAgent")
        start_time = time.time()
        problem = self.searchType(state) # Makes a new search problem
        self.actions  = self.searchFunction(problem) # Find a path
        total_cost = problem.get_cost_of_actions(self.actions)
        print('Path found with total cost of %d in %.1f seconds' % (total_cost, time.time() - start_time))
        if '_expanded' in dir(problem): print('Search nodes expanded: %d' % problem._expanded)

    def get_action(self, state):
        """
        Returns the next action in the path chosen earlier (in
        register_initial_state).  Return Directions.STOP if there is no further
        action to take.

        state: a GameState obj (pacman.py)
        """
        if 'action_index' not in dir(self): self.action_index = 0
        i = self.action_index
        self.action_index += 1
        if i < len(self.actions):
            return self.actions[i]
        else:
            return Directions.STOP

class PositionSearchProblem(search.SearchProblem):
    """
    A search problem defines the state space, start state, goal test, successor
    function and cost function.  This search problem can be used to find paths
    to a particular point on the pacman board.

    The state space consists of (x,y) positions in a pacman game.

    Note: this search problem is fully specified; you should NOT change it.
    """

    def __init__(self, game_state, cost_fn = lambda x: 1, goal=(1, 1), start=None, warn=True, visualize=True):
        """
        Stores the start and goal.

        game_state: A GameState obj (pacman.py)
        cost_fn: A function from a search state (tuple) to a non-negative number
        goal: A position in the game_state
        """
        self.walls = game_state.get_walls()
        self.startState = game_state.get_pacman_position()
        if start is not None: self.startState = start
        self.goal = goal
        self.cost_fn = cost_fn
        self.visualize = visualize
        if warn and (game_state.get_num_food() != 1 or not game_state.has_food(*goal)):
            print('Warning: this does not look like a regular search maze')

        # For display purposes
        self._visited, self._visited_list, self._expanded = {}, [], 0 # DO NOT CHANGE

    def get_start_state(self):
        return self.startState

    def is_goal_state(self, state):
        is_goal = state == self.goal

        # For display purposes only
        if is_goal and self.visualize:
            self._visited_list.append(state)
            import __main__
            if '_display' in dir(__main__):
                if 'draw_expanded_cells' in dir(__main__._display): #@UndefinedVariable
                    __main__._display.draw_expanded_cells(self._visited_list) #@UndefinedVariable

        return is_goal

    def get_successors(self, state):
        """
        Returns successor states, the actions they require, and a cost of 1.

         As noted in search.py:
             For a given state, this should return a list of triples,
         (successor, action, stepCost), where 'successor' is a
         successor to the current state, 'action' is the action
         required to get there, and 'stepCost' is the incremental
         cost of expanding to that successor
        """

        successors = []
        for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
            x,y = state
            dx, dy = Actions.direction_to_vector(action)
            next_x, next_y = int(x + dx), int(y + dy)
            if not self.walls[next_x][next_y]:
                next_state = (next_x, next_y)
                cost = self.cost_fn(next_state)
                successors.append( ( next_state, action, cost) )

        # Bookkeeping for display purposes
        self._expanded += 1 # DO NOT CHANGE
        if state not in self._visited:
            self._visited[state] = True
            self._visited_list.append(state)

        return successors

    def get_cost_of_actions(self, actions):
        """
        Returns the cost of a particular sequence of actions. If those actions
        include an illegal move, return 999999.
        """
        if actions is None: return 999999
        x,y= self.get_start_state()
        cost = 0
        for action in actions:
            # Check figure out the next state and see whether its' legal
            dx, dy = Actions.direction_to_vector(action)
            x, y = int(x + dx), int(y + dy)
            if self.walls[x][y]: return 999999
            cost += self.cost_fn((x, y))
        return cost

class StayEastSearchAgent(SearchAgent):
    """
    An agent for position search with a cost function that penalizes being in
    positions on the West side of the board.

    The cost function for stepping into a position (x,y) is 1/2^x.
    """
    def __init__(self):
        super().__init__()
        self.searchFunction = search.uniform_cost_search
        cost_fn = lambda pos: .5 ** pos[0]
        self.searchType = lambda state: PositionSearchProblem(state, cost_fn, (1, 1), None, False)

class StayWestSearchAgent(SearchAgent):
    """
    An agent for position search with a cost function that penalizes being in
    positions on the East side of the board.

    The cost function for stepping into a position (x,y) is 2^x.
    """
    def __init__(self):
        super().__init__()
        self.searchFunction = search.uniform_cost_search
        cost_fn = lambda pos: 2 ** pos[0]
        self.searchType = lambda state: PositionSearchProblem(state, cost_fn)

def manhattan_heuristic(position, problem, info={}):
    """The Manhattan distance heuristic for a PositionSearchProblem"""
    xy1 = position
    xy2 = problem.goal
    return abs(xy1[0] - xy2[0]) + abs(xy1[1] - xy2[1])

def euclidean_heuristic(position, problem, info={}):
    """The Euclidean distance heuristic for a PositionSearchProblem"""
    xy1 = position
    xy2 = problem.goal
    return ( (xy1[0] - xy2[0]) ** 2 + (xy1[1] - xy2[1]) ** 2 ) ** 0.5

#####################################################
# This portion is incomplete.  Time to write code!  #
#####################################################

class CornersProblem(search.SearchProblem):
    """
    This search problem finds paths through all four corners of a layout.

    You must select a suitable state space and successor function
    """

    def __init__(self, starting_game_state, corners=None):
        """
        Stores the walls, pacman's starting position and corners.
        """
        self.walls = starting_game_state.get_walls()
        self.startingPosition = starting_game_state.get_pacman_position()
        top, right = self.walls.height-2, self.walls.width-2
        self.corners = ((1,1), (1,top), (right, 1), (right, top))
        if corners is not None: self.corners = corners
        for corner in self.corners:
            if not starting_game_state.has_food(*corner):
                print('Warning: no food in corner ' + str(corner))
        self._expanded = 0 # DO NOT CHANGE; Number of search nodes expanded
        # Please add any code here which you would like to use
        # in initializing the problem
        "*** YOUR CODE HERE ***"

    def get_start_state(self):
        """
        Returns the start state (in your state space, not the full Pacman state
        space)
        """
        "*** YOUR CODE HERE ***"
        util.raise_not_defined()

    def is_goal_state(self, state):
        """
        Returns whether this search state is a goal state of the problem.
        """
        "*** YOUR CODE HERE ***"
        util.raise_not_defined()

    def get_successors(self, state):
        """
        Returns successor states, the actions they require, and a cost of 1.

         As noted in search.py:
            For a given state, this should return a list of triples, (successor,
            action, step_cost), where 'successor' is a successor to the current
            state, 'action' is the action required to get there, and 'step_cost'
            is the incremental cost of expanding to that successor
        """
        successors = []
        for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
            # Add a successor state to the successor list if the action is legal
            # Here's a code snippet for figuring out whether a new position hits a wall:
            #   current_position = state[0]
            #   x,y = current_position
            #   dx, dy = Actions.direction_to_vector(action)
            #   next_x, next_y = int(x + dx), int(y + dy)
            #   hits_wall = self.walls[next_x][next_y]

            "*** YOUR CODE HERE ***"

        self._expanded += 1 # DO NOT CHANGE
        return successors

    def get_cost_of_actions(self, actions):
        """
        Returns the cost of a particular sequence of actions.  If those actions
        include an illegal move, return 999999.  This is implemented for you.
        """
        if actions is None: return 999999
        x,y= self.startingPosition
        for action in actions:
            dx, dy = Actions.direction_to_vector(action)
            x, y = int(x + dx), int(y + dy)
            if self.walls[x][y]: return 999999
        return len(actions)

# Defined by us
def nearest_corner(position, pending_corners):
    min_dist = 999999
    nearest_corner = None
    for corner in pending_corners:
        dist = util.manhattan_distance(position, corner)
        if dist < min_dist:
            min_dist = dist
            nearest_corner = corner

    pending_corners.remove(nearest_corner)
    return min_dist, nearest_corner


def corners_heuristic(state, problem):
    """
    A heuristic for the CornersProblem that you defined.

      state:   The current search state
               (a data structure you chose in your search problem)
               In our case ((x,y), remainingCornerns)

      problem: The CornersProblem instance for this layout.

    This function should always return a number that is a lower bound on the
    shortest path from the state to a goal of the problem; i.e.  it should be
    admissible (as well as consistent).
    """
    corners = problem.corners # These are the corner coordinates
    walls = problem.walls # These are the walls of the maze, as a Grid (game.py)

    "*** YOUR CODE HERE ***"
    return 0 # Default to trivial solution

class AStarCornersAgent(SearchAgent):
    """A SearchAgent for FoodSearchProblem using A* and your food_heuristic"""
    def __init__(self):
        super().__init__()
        self.searchFunction = lambda prob: search.a_star_search(prob, corners_heuristic)
        self.searchType = CornersProblem

class FoodSearchProblem:
    """
    A search problem associated with finding the a path that collects all of the
    food (dots) in a Pacman game.

    A search state in this problem is a tuple ( pacman_position, foodGrid ) where
      pacman_position: a tuple (x,y) of integers specifying Pacman's position
      foodGrid:       a Grid (see game.py) of either True or False, specifying remaining food
    """
    def __init__(self, starting_game_state):
        self.start = (starting_game_state.get_pacman_position(), starting_game_state.get_food())
        self.walls = starting_game_state.get_walls()
        self.starting_game_state = starting_game_state
        self._expanded = 0 # DO NOT CHANGE
        self.heuristic_info = {} # A dictionary for the heuristic to store information

    def get_start_state(self):
        return self.start

    def is_goal_state(self, state):
        return state[1].count() == 0

    def get_successors(self, state):
        """Returns successor states, the actions they require, and a cost of 1."""
        successors = []
        self._expanded += 1 # DO NOT CHANGE
        for direction in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
            x,y = state[0]
            dx, dy = Actions.direction_to_vector(direction)
            next_x, next_y = int(x + dx), int(y + dy)
            if not self.walls[next_x][next_y]:
                next_food = state[1].copy()
                next_food[next_x][next_y] = False
                successors.append( ( ((next_x, next_y), next_food), direction, 1) )
        return successors

    def get_cost_of_actions(self, actions):
        """Returns the cost of a particular sequence of actions.  If those actions
        include an illegal move, return 999999"""
        x,y= self.get_start_state()[0]
        cost = 0
        for action in actions:
            # figure out the next state and see whether it's legal
            dx, dy = Actions.direction_to_vector(action)
            x, y = int(x + dx), int(y + dy)
            if self.walls[x][y]:
                return 999999
            cost += 1
        return cost

class AStarFoodSearchAgent(SearchAgent):
    """A SearchAgent for FoodSearchProblem using A* and your food_heuristic"""
    def __init__(self):
        super().__init__()
        self.searchFunction = lambda prob: search.a_star_search(prob, food_heuristic)
        self.searchType = FoodSearchProblem

# Defined by us
class CustomGameState:
    def __init__(self, position, walls, food=None):
        self.__position = position
        self.__walls = walls
        self.__food = food
    
    def get_pacman_position(self): return self.__position
    def get_walls(self): return self.__walls
    def get_food(self): return self.__food
    def has_food(self, x, y):
        if self.__food is None: return False
        return self.__food[x][y]

# Defined by us. Finds the bottom-left-most food dot, the
# top-left-most food dot, the bottom-right-most food dot and
# the top-right-most food dot of a given grid. Each corner
# search only considers points of its own quadrant.
def find_corners(grid: Grid):
    points = grid.as_list()
    bottom_left = bottom_right = top_left = top_right = None
    dist_bl = dist_br = dist_tl = dist_tr = grid.width*grid.height

    for p in points:
        x, y = p
        if x < grid.width/2 and y < grid.height/2:
            dist = x**2 + y**2
            if dist < dist_bl:
                dist_bl = dist
                bottom_left = p
        elif y < grid.height/2:
            dist = (grid.width-1-x)**2 + y**2
            if dist < dist_br:
                dist_br = dist
                bottom_right = p
        elif x < grid.width/ 2:
            dist = x**2 + (grid.height-1-y)**2
            if dist < dist_tl:
                dist_tl = dist
                top_left = p
        else:
            dist = (grid.width-1-x)**2 + (grid.height-1-y)**2
            if dist < dist_tr:
                dist_tr = dist
                top_right = p

    corners = (bottom_left, top_left, bottom_right, top_right)
    return tuple(c for c in corners if c is not None)

# Defined by us. Given a list of points, returns a tuple containing all
# the possible subsets. For example, given points 1, 2 and 3, it
# would return {{1,2,3}, {1,2}, {1,3}, {2,3}, {1}, {2}, {3}, {}}
def power_set(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def food_heuristic(state, problem):
    """
    Your heuristic for the FoodSearchProblem goes here.

    This heuristic must be consistent to ensure correctness.  First, try to come
    up with an admissible heuristic; almost all admissible heuristics will be
    consistent as well.

    If using A* ever finds a solution that is worse uniform cost search finds,
    your heuristic is *not* consistent, and probably not admissible!  On the
    other hand, inadmissible or inconsistent heuristics may find optimal
    solutions, so be careful.

    The state is a tuple ( pacman_position, food_grid ) where food_grid is a Grid
    (see game.py) of either True or False. You can call food_grid.as_list() to get
    a list of food coordinates instead.

    If you want access to info like walls, capsules, etc., you can query the
    problem.  For example, problem.walls gives you a Grid of where the walls
    are.

    If you want to *store* information to be reused in other calls to the
    heuristic, there is a dictionary called problem.heuristic_info that you can
    use. For example, if you only want to count the walls once and store that
    value, try: problem.heuristic_info['wallCount'] = problem.walls.count()
    Subsequent calls to this heuristic can access
    problem.heuristic_info['wallCount']
    """
    position, food_grid = state
    "*** YOUR CODE HERE ***"
    return 0


def simplified_corners_heuristic(state, problem):
    """
    A heuristic for the CornersProblem that you defined.

      state:   The current search state
               (a data structure you chose in your search problem)
               In our case ((x,y), remainingCorners)

      problem: The CornersProblem instance for this layout.

    This function should always return a number that is a lower bound on the
    shortest path from the state to a goal of the problem; i.e.  it should be
    admissible (as well as consistent).
    """
    
    # position = state[0]
    # pending_corners = list(state[1])
    # dist = 0
    # if pending_corners: dist, position = nearest_corner(position, pending_corners)
    # return max(0, dist + len(state[1]) - 1)
    return len(state[1])


class ClosestDotSearchAgent(SearchAgent):
    """Search for all food using a sequence of searches"""
    def register_initial_state(self, state):
        self.actions = []
        current_state = state
        while current_state.get_food().count() > 0:
            next_path_segment = self.find_path_to_closest_dot(current_state) # The missing piece
            self.actions += next_path_segment
            for action in next_path_segment:
                legal = current_state.get_legal_actions()
                if action not in legal:
                    t = (str(action), str(current_state))
                    raise Exception('find_path_to_closest_dot returned an illegal move: %s!\n%s' % t)
                current_state = current_state.generate_successor(0, action)
        self.action_index = 0
        print('Path found with cost %d.' % len(self.actions))

    def find_path_to_closest_dot(self, game_state):
        """
        Returns a path (a list of actions) to the closest dot, starting from
        game_state.
        """
        # Here are some useful elements of the startState
        start_position = game_state.get_pacman_position()
        food = game_state.get_food()
        walls = game_state.get_walls()
        problem = AnyFoodSearchProblem(game_state)

        "*** YOUR CODE HERE ***"
        util.raise_not_defined()

class AnyFoodSearchProblem(PositionSearchProblem):
    """
    A search problem for finding a path to any food.

    This search problem is just like the PositionSearchProblem, but has a
    different goal test, which you need to fill in below.  The state space and
    successor function do not need to be changed.

    The class definition above, AnyFoodSearchProblem(PositionSearchProblem),
    inherits the methods of the PositionSearchProblem.

    You can use this search problem to help you fill in the find_path_to_closest_dot
    method.
    """

    def __init__(self, game_state):
        """Stores information from the game_state.  You don't need to change this."""
        # Store the food for later reference
        super().__init__(game_state)
        self.food = game_state.get_food()

        # Store info for the PositionSearchProblem (no need to change this)
        self.walls = game_state.get_walls()
        self.startState = game_state.get_pacman_position()
        self.cost_fn = lambda x: 1
        self._visited, self._visited_list, self._expanded = {}, [], 0 # DO NOT CHANGE

    def is_goal_state(self, state):
        """
        The state is Pacman's position. Fill this in with a goal test that will
        complete the problem definition.
        """
        x,y = state

        "*** YOUR CODE HERE ***"
        util.raise_not_defined()

def maze_distance(point1, point2, game_state):
    """
    Returns the maze distance between any two points, using the search functions
    you have already built. The game_state can be any game state -- Pacman's
    position in that state is ignored.

    Example usage: maze_distance( (2,4), (5,6), game_state)

    This might be a useful helper function for your ApproximateSearchAgent.
    """
    x1, y1 = point1
    x2, y2 = point2
    walls = game_state.get_walls()
    assert not walls[x1][y1], 'point1 is a wall: ' + str(point1)
    assert not walls[x2][y2], 'point2 is a wall: ' + str(point2)
    prob = PositionSearchProblem(game_state, start=point1, goal=point2, warn=False, visualize=False)
    # return len(search.bfs(prob))
    return len(search.astar(problem=prob, heuristic=manhattan_heuristic))
