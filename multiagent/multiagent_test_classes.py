# multiagent_test_classes.py
# ------------------------
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


# A minimax tree which interfaces like game_state
#     state.get_num_agents()
#     state.is_win()
#     state.is_lose()
#     state.generate_successor(agent_index, action)
#     state.get_score()
#           used by multi_agents.score_evaluation_function, which is the default
#
import test_classes
import json

from collections import defaultdict
from pprint import PrettyPrinter
pp = PrettyPrinter()

from game import Agent
from pacman import GameState
from ghost_agents import RandomGhost, DirectionalGhost
import random
import math
import traceback
import sys
import os
import layout
import pacman
import autograder
# import grading

VERBOSE = False


class MultiagentTreeState(object):
    def __init__(self, problem, state):
        self.problem = problem
        self.state = state

    def generate_successor(self, agent_index, action):
        if VERBOSE:
            print("generate_successor(%s, %s, %s) -> %s" % (self.state, agent_index,
                                                            action, self.problem.state_to_successor_map[self.state][action]))
        successor = self.problem.state_to_successor_map[self.state][action]
        self.problem.generated_states.add(successor)
        return MultiagentTreeState(self.problem, successor)

    def get_score(self):
        if VERBOSE:
            print("get_score(%s) -> %s" % (self.state, self.problem.evaluation[self.state]))
        if self.state not in self.problem.evaluation:
            raise Exception('get_score() called on non-terminal state or before maximum depth achieved.')
        return float(self.problem.evaluation[self.state])

    def get_legal_actions(self, agent_index=0):
        if VERBOSE:
            print("get_legal_actions(%s) -> %s" % (self.state, self.problem.state_to_actions[self.state]))
        # if len(self.problem.state_to_actions[self.state]) == 0:
        #    print "WARNING: get_legal_actions called on leaf state %s" % (self.state,)
        return list(self.problem.state_to_actions[self.state])

    def is_win(self):
        if VERBOSE:
            print("is_win(%s) -> %s" % (self.state, self.state in self.problem.win_states))
        return self.state in self.problem.win_states

    def is_lose(self):
        if VERBOSE:
            print("is_lose(%s) -> %s" % (self.state, self.state in self.problem.lose_states))
        return self.state in self.problem.lose_states

    def get_num_agents(self):
        if VERBOSE:
            print("get_num_agents(%s) -> %s" % (self.state, self.problem.num_agents))
        return self.problem.num_agents


class MultiagentTreeProblem(object):
    def __init__(self, num_agents, start_state, win_states, lose_states, successors, evaluation):
        self.start_state = MultiagentTreeState(self, start_state)

        self.num_agents = num_agents
        self.win_states = win_states
        self.lose_states = lose_states
        self.evaluation = evaluation
        self.successors = successors

        self.reset()

        self.state_to_successor_map = defaultdict(dict)
        self.state_to_actions = defaultdict(list)
        for state, action, next_state in successors:
            self.state_to_actions[state].append(action)
            self.state_to_successor_map[state][action] = next_state

    def reset(self):
        self.generated_states = set([self.start_state.state])


def parse_tree_problem(test_dict):
    num_agents = int(test_dict["num_agents"])
    start_state = test_dict["start_state"]
    win_states = set(test_dict["win_states"].split(" "))
    lose_states = set(test_dict["lose_states"].split(" "))
    successors = []

    evaluation = {}
    for line in test_dict["evaluation"].split('\n'):
        tokens = line.split()
        if len(tokens) == 2:
            state, value = tokens
            evaluation[state] = float(value)
        else:
            raise Exception("[parseTree] Bad evaluation line: |%s|" % (line,))

    for line in test_dict["successors"].split('\n'):
        tokens = line.split()
        if len(tokens) == 3:
            state, action, next_state = tokens
            successors.append((state, action, next_state))
        else:
            raise Exception("[parseTree] Bad successor line: |%s|" % (line,))

    return MultiagentTreeProblem(num_agents, start_state, win_states, lose_states, successors, evaluation)


def run(lay, lay_name, pac, ghosts, disp, n_games=1, name='games'):
    """
    Runs a few games and outputs their statistics.
    """
    start_time = time.time()
    print('*** Running %s on' % name, lay_name, '%d time(s).' % n_games)
    games = pacman.run_games(lay, pac, ghosts, disp, n_games, False, catch_exceptions=True, timeout=120)
    print('*** Finished running %s on' % name, lay_name, 'after %d seconds.' % (time.time() - start_time))
    stats = {'time': time.time() - start_time,
             'wins': [g.state.is_win() for g in games].count(True),
             'games': games,
             'scores': [g.state.get_score() for g in games],
             'timeouts': [g.agent_timeout for g in games].count(True),
             'crashes': [g.agent_crashed for g in games].count(True)}
    print('*** Won %d out of %d games. Average score: %f ***' %
          (stats['wins'], len(games), sum(stats['scores']) * 1.0 / len(games)))
    return stats


class GradingAgent(Agent):
    def __init__(self, seed, student_agent, optimal_actions, alt_depth_actions, partial_ply_bug_actions):
        # save student agent and actions of refernce agents
        super().__init__()
        self.studentAgent = student_agent
        self.optimal_actions = optimal_actions
        self.alt_depth_actions = alt_depth_actions
        self.partial_ply_bug_actions = partial_ply_bug_actions
        # create fields for storing specific wrong actions
        self.suboptimal_moves = []
        self.wrong_states_explored = -1
        # boolean vectors represent types of implementation the student could have
        self.actions_consistent_with_optimal = [True for _ in range(len(optimal_actions[0]))]
        self.actions_consistent_with_alternative_depth = [True for _ in range(len(alt_depth_actions[0]))]
        self.actions_consistent_with_partial_ply_bug = [True for _ in range(len(partial_ply_bug_actions[0]))]
        # keep track of elapsed moves
        self.step_count = 0
        self.seed = seed

    def register_initial_state(self, state):
        if 'register_initial_state' in dir(self.studentAgent):
            self.studentAgent.register_initial_state(state)
        random.seed(self.seed)

    def get_action(self, state):
        GameState.get_and_reset_explored()
        student_action = (self.studentAgent.get_action(state),
                         len(GameState.get_and_reset_explored()))
        optimal_actions = self.optimal_actions[self.step_count]
        alt_depth_actions = self.alt_depth_actions[self.step_count]
        partial_ply_bug_actions = self.partial_ply_bug_actions[self.step_count]
        student_optimal_action = False
        cur_right_states_explored = False
        for i in range(len(optimal_actions)):
            if student_action[0] in optimal_actions[i][0]:
                student_optimal_action = True
            else:
                self.actions_consistent_with_optimal[i] = False
            if student_action[1] == int(optimal_actions[i][1]):
                cur_right_states_explored = True
        if not cur_right_states_explored and self.wrong_states_explored < 0:
            self.wrong_states_explored = 1
        for i in range(len(alt_depth_actions)):
            if student_action[0] not in alt_depth_actions[i]:
                self.actions_consistent_with_alternative_depth[i] = False
        for i in range(len(partial_ply_bug_actions)):
            if student_action[0] not in partial_ply_bug_actions[i]:
                self.actions_consistent_with_partial_ply_bug[i] = False
        if not student_optimal_action:
            self.suboptimal_moves.append(
                (state, student_action[0], optimal_actions[0][0][0]))
        self.step_count += 1
        random.seed(self.seed + self.step_count)
        return optimal_actions[0][0][0]

    def get_suboptimal_moves(self):
        return self.suboptimal_moves

    def get_wrong_states_explored(self):
        return self.wrong_states_explored

    def check_failure(self):
        """
        Return +n if have n suboptimal moves.
        Return -1 if have only off by one depth moves.
        Return 0 otherwise.
        """
        if self.wrong_states_explored > 0:
            return -3
        if self.actions_consistent_with_optimal.count(True) > 0:
            return 0
        elif self.actions_consistent_with_partial_ply_bug.count(True) > 0:
            return -2
        elif self.actions_consistent_with_alternative_depth.count(True) > 0:
            return -1
        else:
            return len(self.suboptimal_moves)


class PolyAgent(Agent):
    def __init__(self, seed, multi_agents, our_pac_options, depth):
        # prepare our pacman agents
        super().__init__()
        solution_agents, alternative_depth_agents, partial_ply_bug_agents = self.construct_our_pacs(
            multi_agents, our_pac_options)
        for p in solution_agents:
            p.depth = depth
        for p in partial_ply_bug_agents:
            p.depth = depth
        for p in alternative_depth_agents[:2]:
            p.depth = max(1, depth - 1)
        for p in alternative_depth_agents[2:]:
            p.depth = depth + 1
        self.solution_agents = solution_agents
        self.alternative_depth_agents = alternative_depth_agents
        self.partial_ply_bug_agents = partial_ply_bug_agents
        # prepare fields for storing the results
        self.optimal_action_lists = []
        self.alternative_depth_lists = []
        self.partial_ply_bug_lists = []
        self.seed = seed
        self.step_count = 0

    def select(self, list_idxs, indices):
        """
        Return a sublist of elements given by indices in list.
        """
        return [list_idxs[i] for i in indices]

    def construct_our_pacs(self, multi_agents, keyword_dict):
        pacs_without_stop = [multi_agents.StaffMultiAgentSearchAgent(**keyword_dict) for _ in range(3)]
        keyword_dict['keep_stop'] = 'True'
        pacs_with_stop = [multi_agents.StaffMultiAgentSearchAgent(**keyword_dict) for _ in range(3)]
        keyword_dict['use_partial_ply_bug'] = 'True'
        partial_ply_bug_pacs = [multi_agents.StaffMultiAgentSearchAgent(**keyword_dict)]  #FIXME: unknown Agent
        keyword_dict['keep_stop'] = 'False'
        partial_ply_bug_pacs = partial_ply_bug_pacs + \
            [multi_agents.StaffMultiAgentSearchAgent(**keyword_dict)]
        for pac in pacs_with_stop + pacs_without_stop + partial_ply_bug_pacs:
            pac.verbose = False
        our_pac = [pacs_with_stop[0], pacs_without_stop[0]]
        alternative_depth_pacs = self.select(
            pacs_with_stop + pacs_without_stop, [1, 4, 2, 5])
        return our_pac, alternative_depth_pacs, partial_ply_bug_pacs

    def register_initial_state(self, state):
        for agent in self.solution_agents + self.alternative_depth_agents:
            if 'register_initial_state' in dir(agent):
                agent.register_initial_state(state)
        random.seed(self.seed)

    def get_action(self, state):
        # survey agents
        GameState.get_and_reset_explored()
        optimal_action_lists = []
        for agent in self.solution_agents:
            optimal_action_lists.append((agent.getBestPacmanActions(
                state)[0], len(GameState.get_and_reset_explored())))
        alternative_depth_lists = [agent.getBestPacmanActions(
            state)[0] for agent in self.alternative_depth_agents]
        partial_ply_bug_lists = [agent.getBestPacmanActions(
            state)[0] for agent in self.partial_ply_bug_agents]
        # record responses
        self.optimal_action_lists.append(optimal_action_lists)
        self.alternative_depth_lists.append(alternative_depth_lists)
        self.partial_ply_bug_lists.append(partial_ply_bug_lists)
        self.step_count += 1
        random.seed(self.seed + self.step_count)
        return optimal_action_lists[0][0][0]

    def get_traces(self):
        # return traces from individual agents
        return self.optimal_action_lists, self.alternative_depth_lists, self.partial_ply_bug_lists


class PacmanGameTreeTest(test_classes.TestCase):

    def __init__(self, question, test_dict):
        super(PacmanGameTreeTest, self).__init__(question, test_dict)
        self.seed = int(self.test_dict['seed'])
        self.alg = self.test_dict['alg']
        self.layout_text = self.test_dict['layout']
        self.layout_name = self.test_dict['layout_name']
        self.depth = int(self.test_dict['depth'])
        self.max_points = int(self.test_dict['max_points'])

    def execute(self, grades, module_dict, solution_dict):
        # load student code and staff code solutions
        multi_agents = module_dict['multi_agents']
        student_agent = getattr(multi_agents, self.alg)(depth=self.depth)
        all_actions = [json.loads(x)
                      for x in solution_dict['optimal_actions'].split('\n')]
        alt_depth_actions = [json.loads(
            x) for x in solution_dict['alt_depth_actions'].split('\n')]
        partial_ply_bug_actions = [json.loads(
            x) for x in solution_dict['partial_ply_bug_actions'].split('\n')]
        # set up game state and play a game
        random.seed(self.seed)
        lay = layout.Layout([l.strip() for l in self.layout_text.split('\n')])
        pac = GradingAgent(self.seed, student_agent, all_actions,
                           alt_depth_actions, partial_ply_bug_actions)
        # check return codes and assign grades
        disp = self.question.get_display()
        stats = run(lay, self.layout_name, pac, [DirectionalGhost(
            i + 1) for i in range(2)], disp, name=self.alg)
        if stats['timeouts'] > 0:
            self.add_message('Agent timed out on smallClassic.  No credit')
            return self.test_fail(grades)
        if stats['crashes'] > 0:
            self.add_message('Agent crashed on smallClassic.  No credit')
            return self.test_fail(grades)
        code = pac.check_failure()
        if code == 0:
            return self.test_pass(grades)
        elif code == -3:
            if pac.get_wrong_states_explored() >= 0:
                self.add_message('Bug: Wrong number of states expanded.')
                return self.test_fail(grades)
            else:
                return self.test_pass(grades)
        elif code == -2:
            self.add_message('Bug: Partial Ply Bug')
            return self.test_fail(grades)
        elif code == -1:
            self.add_message('Bug: Search depth off by 1')
            return self.test_fail(grades)
        elif code > 0:
            moves = pac.get_suboptimal_moves()
            state, student_move, opt_move = random.choice(moves)
            self.add_message('Bug: Suboptimal moves')
            self.add_message('State:%s\nStudent Move:%s\nOptimal Move:%s' % (
                state, student_move, opt_move))
            return self.test_fail(grades)

    def write_list(self, handle, name, list_lines):
        handle.write('%s: """\n' % name)
        for l in list_lines:
            handle.write('%s\n' % json.dumps(l))
        handle.write('"""\n')

    def write_solution(self, module_dict, file_path):
        # load module, set seed, create ghosts and macman, run game
        multi_agents = module_dict['multi_agents']
        random.seed(self.seed)
        lay = layout.Layout([l.strip() for l in self.layout_text.split('\n')])
        if self.alg == 'ExpectimaxAgent':
            our_pac_options = {'expectimax': 'True'}
        elif self.alg == 'AlphaBetaAgent':
            our_pac_options = {'alphabeta': 'True'}
        else:
            our_pac_options = {}
        pac = PolyAgent(self.seed, multi_agents, our_pac_options, self.depth)
        disp = self.question.get_display()
        run(lay, self.layout_name, pac, [DirectionalGhost(
            i + 1) for i in range(2)], disp, name=self.alg)
        (optimal_actions, alt_depth_actions, partial_ply_bug_actions) = pac.get_traces()
        # recover traces and record to file
        handle = open(file_path, 'w')
        self.write_list(handle, 'optimal_actions', optimal_actions)
        self.write_list(handle, 'alt_depth_actions', alt_depth_actions)
        self.write_list(handle, 'partial_ply_bug_actions', partial_ply_bug_actions)
        handle.close()


class GraphGameTreeTest(test_classes.TestCase):

    def __init__(self, question, test_dict):
        super(GraphGameTreeTest, self).__init__(question, test_dict)
        self.problem = parse_tree_problem(test_dict)
        self.alg = self.test_dict['alg']
        self.diagram = self.test_dict['diagram'].split('\n')
        self.depth = int(self.test_dict['depth'])

    def solve_problem(self, multi_agents):
        self.problem.reset()
        student_agent = getattr(multi_agents, self.alg)(depth=self.depth)
        action = student_agent.get_action(self.problem.start_state)
        generated = self.problem.generated_states
        return action, " ".join([str(s) for s in sorted(generated)])

    def add_diagram(self):
        self.add_message('Tree:')
        for line in self.diagram:
            self.add_message(line)

    def execute(self, grades, module_dict, solution_dict):
        multi_agents = module_dict['multi_agents']
        gold_action = solution_dict['action']
        gold_generated = solution_dict['generated']
        action, generated = self.solve_problem(multi_agents)

        fail = False
        if action != gold_action:
            self.add_message('Incorrect move for depth=%s' % (self.depth,))
            self.add_message(
                '    Student move: %s\n    Optimal move: %s' % (action, gold_action))
            fail = True

        if generated != gold_generated:
            self.add_message(
                'Incorrect generated nodes for depth=%s' % (self.depth,))
            self.add_message('    Student generated nodes: %s\n    Correct generated nodes: %s' % (
                generated, gold_generated))
            fail = True

        if fail:
            self.add_diagram()
            return self.test_fail(grades)
        else:
            return self.test_pass(grades)

    def write_solution(self, module_dict, file_path):
        multi_agents = module_dict['multi_agents']
        action, generated = self.solve_problem(multi_agents)
        with open(file_path, 'w') as handle:
            handle.write('# This is the solution file for %s.\n' % self.path)
            handle.write('action: "%s"\n' % (action,))
            handle.write('generated: "%s"\n' % (generated,))
        return True


import time
from util import TimeoutFunction


class EvalAgentTest(test_classes.TestCase):

    def __init__(self, question, test_dict):
        super(EvalAgentTest, self).__init__(question, test_dict)
        self.layout_name = test_dict['layout_name']
        self.agent_name = test_dict['agent_name']
        self.ghosts = eval(test_dict['ghosts'])
        self.max_time = int(test_dict['max_time'])
        self.seed = int(test_dict['random_seed'])
        self.num_games = int(test_dict['num_games'])

        self.score_minimum = int(
            test_dict['score_minimum']) if 'score_minimum' in test_dict else None
        self.non_timeout_minimum = int(
            test_dict['non_timeout_minimum']) if 'non_timeout_minimum' in test_dict else None
        self.wins_minimum = int(
            test_dict['wins_minimum']) if 'wins_minimum' in test_dict else None

        self.score_thresholds = [int(s) for s in test_dict.get(
            'score_thresholds', '').split()]
        self.non_timeout_thresholds = [int(s) for s in test_dict.get(
            'non_timeout_thresholds', '').split()]
        self.wins_thresholds = [int(s) for s in test_dict.get(
            'wins_thresholds', '').split()]

        self.max_points = sum([len(t) for t in [
                             self.score_thresholds, self.non_timeout_thresholds, self.wins_thresholds]])
        self.agent_args = test_dict.get('agent_args', '')

    def execute(self, grades, module_dict, solution_dict):
        start_time = time.time()

        agent_type = getattr(module_dict['multi_agents'], self.agent_name)
        agent_opts = pacman.parse_agent_args(self.agent_args) if self.agent_args != '' else {}
        agent = agent_type(**agent_opts)

        lay = layout.get_layout(self.layout_name, 3)

        disp = self.question.get_display()

        random.seed(self.seed)
        games = pacman.run_games(lay, agent, self.ghosts, disp, self.num_games,
                                 False, catch_exceptions=True, timeout=self.max_time)
        total_time = time.time() - start_time

        stats = {'time': total_time, 'wins': [g.state.is_win() for g in games].count(True),
                 'games': games, 'scores': [g.state.get_score() for g in games],
                 'timeouts': [g.agent_timeout for g in games].count(True), 'crashes': [g.agent_crashed for g in games].count(True)}

        average_score = sum(stats['scores']) / float(len(stats['scores']))
        non_timeouts = self.num_games - stats['timeouts']
        wins = stats['wins']

        def grade_threshold(value, minimum, thresholds, name):
            points = 0
            passed = (minimum is None) or (value >= minimum)
            if passed:
                for t in thresholds:
                    if value >= t:
                        points += 1
            return passed, points, value, minimum, thresholds, name

        results = [grade_threshold(average_score, self.score_minimum, self.score_thresholds, "average score"),
                   grade_threshold(non_timeouts, self.non_timeout_minimum,
                                   self.non_timeout_thresholds, "games not timed out"),
                   grade_threshold(wins, self.wins_minimum, self.wins_thresholds, "wins")]

        total_points = 0
        for passed, points, value, minimum, thresholds, name in results:
            if (minimum is None) and (len(thresholds) == 0):
                continue

            # print passed, points, value, minimum, thresholds, name
            total_points += points
            if not passed:
                assert points == 0
                self.add_message("%s %s (fail: below minimum value %s)" % (value, name, minimum))
            else:
                self.add_message("%s %s (%s of %s points)" % (value, name, points, len(thresholds)))

            if minimum is not None:
                self.add_message("    Grading scheme:")
                self.add_message("     < %s:  fail" % (minimum,))
                if len(thresholds) == 0 or minimum != thresholds[0]:
                    self.add_message("    >= %s:  0 points" % (minimum,))
                for idx, threshold in enumerate(thresholds):
                    self.add_message("    >= %s:  %s points" %
                                     (threshold, idx+1))
            elif len(thresholds) > 0:
                self.add_message("    Grading scheme:")
                self.add_message("     < %s:  0 points" % (thresholds[0],))
                for idx, threshold in enumerate(thresholds):
                    self.add_message("    >= %s:  %s points" %
                                     (threshold, idx+1))

        if any([not passed for passed, _, _, _, _, _ in results]):
            total_points = 0

        return self.test_partial(grades, total_points, self.max_points)

    def write_solution(self, module_dict, file_path):
        handle = open(file_path, 'w')
        handle.write('# This is the solution file for %s.\n' % self.path)
        handle.write('# File intentionally blank.\n')
        handle.close()
        return True
