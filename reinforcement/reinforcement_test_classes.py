# reinforcement_test_classes.py
# ---------------------------
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


import test_classes
import random, math, traceback, sys, os
import layout, text_display, pacman, gridworld
import time
from util import Counter, TimeoutFunction, FixedRandom, Experiences
from collections import defaultdict
from pprint import PrettyPrinter
from hashlib import sha1
from functools import reduce
pp = PrettyPrinter()
VERBOSE = False

import gridworld

LIVING_REWARD = -0.1
NOISE = 0.2

class ValueIterationTest(test_classes.TestCase):

    def __init__(self, question, test_dict):
        super(ValueIterationTest, self).__init__(question, test_dict)
        self.discount = float(test_dict['discount'])
        self.grid = gridworld.Gridworld(parse_grid(test_dict['grid']))
        iterations = int(test_dict['value_iterations'])
        if 'noise' in test_dict: self.grid.set_noise(float(test_dict['noise']))
        if 'living_reward' in test_dict: self.grid.set_living_reward(float(test_dict['living_reward']))
        max_pre_iterations = 10
        self.nums_iterations_for_display = list(range(min(iterations, max_pre_iterations)))
        self.test_out_file = test_dict['test_out_file']
        if max_pre_iterations < iterations:
            self.nums_iterations_for_display.append(iterations)

    def write_failure_file(self, string):
        with open(self.test_out_file, 'w') as handle:
            handle.write(string)

    def remove_failure_file_if_exists(self):
        if os.path.exists(self.test_out_file):
            os.remove(self.test_out_file)

    def execute(self, grades, module_dict, solution_dict):
        failure_output_file_string = ''
        failure_output_std_string = ''
        for n in self.nums_iterations_for_display:
            check_policy = (n == self.nums_iterations_for_display[-1])
            test_pass, std_out_string, file_out_string = self.execute_n_iterations(grades, module_dict, solution_dict, n, check_policy)
            failure_output_std_string += std_out_string
            failure_output_file_string += file_out_string
            if not test_pass:
                self.add_message(failure_output_std_string)
                self.add_message('For more details to help you debug, see test output file %s\n\n' % self.test_out_file)
                self.write_failure_file(failure_output_file_string)
                return self.test_fail(grades)
        self.remove_failure_file_if_exists()
        return self.test_pass(grades)

    def execute_n_iterations(self, grades, module_dict, solution_dict, n, check_policy):
        test_pass = True
        values_pretty, q_values_pretty, actions, policy_pretty = self.run_agent(module_dict, n)
        std_out_string = ''
        file_out_string = ''
        values_key = "values_k_%d" % n
        if self.compare_pretty_values(values_pretty, solution_dict[values_key]):
            file_out_string += "Values at iteration %d are correct.\n" % n
            file_out_string += "   Student/correct solution:\n %s\n" % self.pretty_value_solution_string(values_key, values_pretty)
        else:
            test_pass = False
            out_string = "Values at iteration %d are NOT correct.\n" % n
            out_string += "   Student solution:\n %s\n" % self.pretty_value_solution_string(values_key, values_pretty)
            out_string += "   Correct solution:\n %s\n" % self.pretty_value_solution_string(values_key, solution_dict[values_key])
            std_out_string += out_string
            file_out_string += out_string
        for action in actions:
            q_values_key = 'q_values_k_%d_action_%s' % (n, action)
            q_values = q_values_pretty[action]
            if self.compare_pretty_values(q_values, solution_dict[q_values_key]):
                file_out_string += "Q-Values at iteration %d for action %s are correct.\n" % (n, action)
                file_out_string += "   Student/correct solution:\n %s\n" % self.pretty_value_solution_string(q_values_key, q_values)
            else:
                test_pass = False
                out_string = "Q-Values at iteration %d for action %s are NOT correct.\n" % (n, action)
                out_string += "   Student solution:\n %s\n" % self.pretty_value_solution_string(q_values_key, q_values)
                out_string += "   Correct solution:\n %s\n" % self.pretty_value_solution_string(q_values_key, solution_dict[q_values_key])
                std_out_string += out_string
                file_out_string += out_string
        if check_policy:
            if not self.compare_pretty_values(policy_pretty, solution_dict['policy']):
                test_pass = False
                out_string = "Policy is NOT correct.\n"
                out_string += "   Student solution:\n %s\n" % self.pretty_value_solution_string('policy', policy_pretty)
                out_string += "   Correct solution:\n %s\n" % self.pretty_value_solution_string('policy', solution_dict['policy'])
                std_out_string += out_string
                file_out_string += out_string
        return test_pass, std_out_string, file_out_string

    def write_solution(self, module_dict, file_path):
        with open(file_path, 'w') as handle:
            policy_pretty = ''
            actions = []
            for n in self.nums_iterations_for_display:
                values_pretty, q_values_pretty, actions, policy_pretty = self.run_agent(module_dict, n)
                handle.write(self.pretty_value_solution_string('values_k_%d' % n, values_pretty))
                for action in actions:
                    handle.write(self.pretty_value_solution_string('q_values_k_%d_action_%s' % (n, action), q_values_pretty[action]))
            handle.write(self.pretty_value_solution_string('policy', policy_pretty))
            handle.write(self.pretty_value_solution_string('actions', '\n'.join(actions) + '\n'))
        return True

    def run_agent(self, module_dict, num_iterations):
        agent = module_dict['value_iteration_agents'].ValueIterationAgent(self.grid, discount=self.discount, iterations=num_iterations)
        states = self.grid.get_states()
        actions = list(reduce(lambda a, b: set(a).union(b), [self.grid.get_possible_actions(state) for state in states]))
        values = {}
        q_values = {}
        policy = {}
        for state in states:
            values[state] = agent.get_value(state)
            policy[state] = agent.compute_action_from_values(state)
            possible_actions = self.grid.get_possible_actions(state)
            for action in actions:
                if action not in q_values:
                    q_values[action] = {}
                if action in possible_actions:
                    q_values[action][state] = agent.compute_q_value_from_values(state, action)
                else:
                    q_values[action][state] = None
        values_pretty = self.pretty_values(values)
        policy_pretty = self.pretty_policy(policy)
        q_values_pretty = {}
        for action in actions:
            q_values_pretty[action] = self.pretty_values(q_values[action])
        return values_pretty, q_values_pretty, actions, policy_pretty

    def pretty_print(self, elements, format_string):
        pretty = ''
        states = self.grid.get_states()
        for y_bar in range(self.grid.grid.height):
            y = self.grid.grid.height-1-y_bar
            row = []
            for x in range(self.grid.grid.width):
                if (x, y) in states:
                    value = elements[(x, y)]
                    if value is None:
                        row.append('   illegal')
                    else:
                        row.append(format_string.format(elements[(x, y)]))
                else:
                    row.append('_' * 10)
            pretty += '        %s\n' % ("   ".join(row), )
        pretty += '\n'
        return pretty

    def pretty_values(self, values):
        return self.pretty_print(values, '{0:10.4f}')

    def pretty_policy(self, policy):
        return self.pretty_print(policy, '{0:10s}')

    def pretty_value_solution_string(self, name, pretty):
        return '%s: """\n%s\n"""\n\n' % (name, pretty.rstrip())

    def compare_pretty_values(self, a_pretty, b_pretty, tolerance=0.01):
        a_list = self.parse_pretty_values(a_pretty)
        b_list = self.parse_pretty_values(b_pretty)
        if len(a_list) != len(b_list):
            return False
        for a, b in zip(a_list, b_list):
            try:
                a_num = float(a)
                b_num = float(b)
                # error = abs((a_num - b_num) / ((a_num + b_num) / 2.0))
                error = abs(a_num - b_num)
                if error > tolerance:
                    return False
            except ValueError:
                if a.strip() != b.strip():
                    return False
        return True

    def parse_pretty_values(self, pretty):
        values = pretty.split()
        return values


class AsynchronousValueIterationTest(ValueIterationTest):
    def run_agent(self, module_dict, num_iterations):
        agent = module_dict['value_iteration_agents'].AsynchronousValueIterationAgent(self.grid, discount=self.discount, iterations=num_iterations)
        states = self.grid.get_states()
        actions = list(reduce(lambda a, b: set(a).union(b), [self.grid.get_possible_actions(state) for state in states]))
        values = {}
        q_values = {}
        policy = {}
        for state in states:
            values[state] = agent.get_value(state)
            policy[state] = agent.compute_action_from_values(state)
            possible_actions = self.grid.get_possible_actions(state)
            for action in actions:
                if action not in q_values:
                    q_values[action] = {}
                if action in possible_actions:
                    q_values[action][state] = agent.compute_q_value_from_values(state, action)
                else:
                    q_values[action][state] = None
        values_pretty = self.pretty_values(values)
        policy_pretty = self.pretty_policy(policy)
        q_values_pretty = {}
        for action in actions:
            q_values_pretty[action] = self.pretty_values(q_values[action])
        return values_pretty, q_values_pretty, actions, policy_pretty

class PrioritizedSweepingValueIterationTest(ValueIterationTest):
    def run_agent(self, module_dict, num_iterations):
        agent = module_dict['value_iteration_agents'].PrioritizedSweepingValueIterationAgent(self.grid, discount=self.discount, iterations=num_iterations)
        states = self.grid.get_states()
        actions = list(reduce(lambda a, b: set(a).union(b), [self.grid.get_possible_actions(state) for state in states]))
        values = {}
        q_values = {}
        policy = {}
        for state in states:
            values[state] = agent.get_value(state)
            policy[state] = agent.compute_action_from_values(state)
            possible_actions = self.grid.get_possible_actions(state)
            for action in actions:
                if action not in q_values:
                    q_values[action] = {}
                if action in possible_actions:
                    q_values[action][state] = agent.compute_q_value_from_values(state, action)
                else:
                    q_values[action][state] = None
        values_pretty = self.pretty_values(values)
        policy_pretty = self.pretty_policy(policy)
        q_values_pretty = {}
        for action in actions:
            q_values_pretty[action] = self.pretty_values(q_values[action])
        return values_pretty, q_values_pretty, actions, policy_pretty

class ApproximateQLearningTest(test_classes.TestCase):
    def __init__(self, question, test_dict):
        super(ApproximateQLearningTest, self).__init__(question, test_dict)
        self.discount = float(test_dict['discount'])
        self.grid = gridworld.Gridworld(parse_grid(test_dict['grid']))
        if 'noise' in test_dict: self.grid.set_noise(float(test_dict['noise']))
        if 'living_reward' in test_dict: self.grid.set_living_reward(float(test_dict['living_reward']))
        self.grid = gridworld.Gridworld(parse_grid(test_dict['grid']))
        self.env = gridworld.GridworldEnvironment(self.grid)
        self.epsilon = float(test_dict['epsilon'])
        self.learning_rate = float(test_dict['learning_rate'])
        self.extractor = 'IdentityExtractor'
        if 'extractor' in test_dict:
            self.extractor = test_dict['extractor']
        self.opts = {'action_fn': self.env.get_possible_actions, 'epsilon': self.epsilon, 'gamma': self.discount, 'alpha': self.learning_rate}
        num_experiences = int(test_dict['num_experiences'])
        max_pre_experiences = 10
        self.nums_experiences_for_display = list(range(min(num_experiences, max_pre_experiences)))
        self.testOutFile = test_dict['test_out_file']
        if sys.platform == 'win32':
            _, question_name, test_name = test_dict['test_out_file'].split('\\')
        else:
            _, question_name, test_name = test_dict['test_out_file'].split('/')
        self.experiences = Experiences(test_name.split('.')[0])
        if max_pre_experiences < num_experiences:
            self.nums_experiences_for_display.append(num_experiences)

    def write_failure_file(self, string):
        with open(self.testOutFile, 'w') as handle:
            handle.write(string)

    def remove_failure_file_if_exists(self):
        if os.path.exists(self.testOutFile):
            os.remove(self.testOutFile)

    def execute(self, grades, module_dict, solution_dict):
        failure_output_file_string = ''
        failure_output_std_string = ''
        for n in self.nums_experiences_for_display:
            test_pass, std_out_string, file_out_string = self.execute_n_experiences(grades, module_dict, solution_dict, n)
            failure_output_std_string += std_out_string
            failure_output_file_string += file_out_string
            if not test_pass:
                self.add_message(failure_output_std_string)
                self.add_message('For more details to help you debug, see test output file %s\n\n' % self.testOutFile)
                self.write_failure_file(failure_output_file_string)
                return self.test_fail(grades)
        self.remove_failure_file_if_exists()
        return self.test_pass(grades)

    def execute_n_experiences(self, grades, module_dict, solution_dict, n):
        test_pass = True
        q_values_pretty, weights, actions, last_experience = self.run_agent(module_dict, n)
        std_out_string = ''
        file_out_string = "==================== Iteration %d ====================\n" % n
        if last_experience is not None:
            file_out_string += "Agent observed the transition (startState = %s, action = %s, endState = %s, reward = %f)\n\n" % last_experience
        weights_key = 'weights_k_%d' % n
        if weights == eval(solution_dict[weights_key]):
            file_out_string += "Weights at iteration %d are correct." % n
            file_out_string += "   Student/correct solution:\n\n%s\n\n" % pp.pformat(weights)
        for action in actions:
            q_values_key = 'q_values_k_%d_action_%s' % (n, action)
            q_values = q_values_pretty[action]
            if self.compare_pretty_values(q_values, solution_dict[q_values_key]):
                file_out_string += "Q-Values at iteration %d for action '%s' are correct." % (n, action)
                file_out_string += "   Student/correct solution:\n\t%s" % self.pretty_value_solution_string(q_values_key, q_values)
            else:
                test_pass = False
                out_string = "Q-Values at iteration %d for action '%s' are NOT correct." % (n, action)
                out_string += "   Student solution:\n\t%s" % self.pretty_value_solution_string(q_values_key, q_values)
                out_string += "   Correct solution:\n\t%s" % self.pretty_value_solution_string(q_values_key, solution_dict[q_values_key])
                std_out_string += out_string
                file_out_string += out_string
        return test_pass, std_out_string, file_out_string

    def write_solution(self, module_dict, file_path):
        with open(file_path, 'w') as handle:
            for n in self.nums_experiences_for_display:
                q_values_pretty, weights, actions, _ = self.run_agent(module_dict, n)
                handle.write(self.pretty_value_solution_string('weights_k_%d' % n, pp.pformat(weights)))
                for action in actions:
                    handle.write(self.pretty_value_solution_string('q_values_k_%d_action_%s' % (n, action), q_values_pretty[action]))
        return True

    def run_agent(self, module_dict, num_experiences):
        agent = module_dict['q_learning_agents'].ApproximateQAgent(extractor=self.extractor, **self.opts)
        states = [state for state in self.grid.get_states() if len(self.grid.get_possible_actions(state)) > 0]
        states.sort()
        last_experience = None
        for i in range(num_experiences):
            last_experience = self.experiences.get_experience()
            agent.update(*last_experience)
        actions = list(reduce(lambda a, b: set(a).union(b), [self.grid.get_possible_actions(state) for state in states]))
        q_values = {}
        weights = agent.get_weights()
        for state in states:
            possible_actions = self.grid.get_possible_actions(state)
            for action in actions:
                if action not in q_values:
                    q_values[action] = {}
                if action in possible_actions:
                    q_values[action][state] = agent.get_q_value(state, action)
                else:
                    q_values[action][state] = None
        q_values_pretty = {}
        for action in actions:
            q_values_pretty[action] = self.pretty_values(q_values[action])
        return q_values_pretty, weights, actions, last_experience

    def pretty_print(self, elements, format_string):
        pretty = ''
        states = self.grid.get_states()
        for ybar in range(self.grid.grid.height):
            y = self.grid.grid.height-1-ybar
            row = []
            for x in range(self.grid.grid.width):
                if (x, y) in states:
                    value = elements[(x, y)]
                    if value is None:
                        row.append('   illegal')
                    else:
                        row.append(format_string.format(elements[(x, y)]))
                else:
                    row.append('_' * 10)
            pretty += '        %s\n' % ("   ".join(row), )
        pretty += '\n'
        return pretty

    def pretty_values(self, values):
        return self.pretty_print(values, '{0:10.4f}')

    def pretty_policy(self, policy):
        return self.pretty_print(policy, '{0:10s}')

    def pretty_value_solution_string(self, name, pretty):
        return '%s: """\n%s\n"""\n\n' % (name, pretty.rstrip())

    def compare_pretty_values(self, a_pretty, b_pretty, tolerance=0.01):
        a_list = self.parse_pretty_values(a_pretty)
        b_list = self.parse_pretty_values(b_pretty)
        if len(a_list) != len(b_list):
            return False
        for a, b in zip(a_list, b_list):
            try:
                a_num = float(a)
                b_num = float(b)
                # error = abs((a_num - b_num) / ((a_num + b_num) / 2.0))
                error = abs(a_num - b_num)
                if error > tolerance:
                    return False
            except ValueError:
                if a.strip() != b.strip():
                    return False
        return True

    def parse_pretty_values(self, pretty):
        values = pretty.split()
        return values


class QLearningTest(test_classes.TestCase):

    def __init__(self, question, test_dict):
        super(QLearningTest, self).__init__(question, test_dict)
        self.discount = float(test_dict['discount'])
        self.grid = gridworld.Gridworld(parse_grid(test_dict['grid']))
        if 'noise' in test_dict: self.grid.set_noise(float(test_dict['noise']))
        if 'living_reward' in test_dict: self.grid.set_living_reward(float(test_dict['living_reward']))
        self.grid = gridworld.Gridworld(parse_grid(test_dict['grid']))
        self.env = gridworld.GridworldEnvironment(self.grid)
        self.epsilon = float(test_dict['epsilon'])
        self.learning_rate = float(test_dict['learning_rate'])
        self.opts = {'action_fn': self.env.get_possible_actions, 'epsilon': self.epsilon, 'gamma': self.discount, 'alpha': self.learning_rate}
        num_experiences = int(test_dict['num_experiences'])
        max_pre_experiences = 10
        self.nums_experiences_for_display = list(range(min(num_experiences, max_pre_experiences)))
        self.test_out_file = test_dict['test_out_file']
        if sys.platform == 'win32':
            _, question_name, test_name = test_dict['test_out_file'].split('\\')
        else:
            _, question_name, test_name = test_dict['test_out_file'].split('/')
        self.experiences = Experiences(test_name.split('.')[0])
        if max_pre_experiences < num_experiences:
            self.nums_experiences_for_display.append(num_experiences)

    def write_failure_file(self, string):
        with open(self.test_out_file, 'w') as handle:
            handle.write(string)

    def remove_failure_file_if_exists(self):
        if os.path.exists(self.test_out_file):
            os.remove(self.test_out_file)

    def execute(self, grades, module_dict, solution_dict):
        failure_output_file_string = ''
        failure_output_std_string = ''
        for n in self.nums_experiences_for_display:
            check_values_and_policy = (n == self.nums_experiences_for_display[-1])
            test_pass, std_out_string, file_out_string = self.execute_n_experiences(grades, module_dict, solution_dict, n, check_values_and_policy)
            failure_output_std_string += std_out_string
            failure_output_file_string += file_out_string
            if not test_pass:
                self.add_message(failure_output_std_string)
                self.add_message('For more details to help you debug, see test output file %s\n\n' % self.test_out_file)
                self.write_failure_file(failure_output_file_string)
                return self.test_fail(grades)
        self.remove_failure_file_if_exists()
        return self.test_pass(grades)

    def execute_n_experiences(self, grades, module_dict, solution_dict, n, check_values_and_policy):
        test_pass = True
        values_pretty, q_values_pretty, actions, policy_pretty, last_experience = self.run_agent(module_dict, n)
        std_out_string = ''
        # file_out_string = "==================== Iteration %d ====================\n" % n
        file_out_string = ''
        if last_experience is not None:
            # file_out_string += "Agent observed the transition (startState = %s, action = %s, endState = %s, reward = %f)\n\n\n" % last_experience
            pass
        for action in actions:
            q_values_key = 'q_values_k_%d_action_%s' % (n, action)
            q_values = q_values_pretty[action]

            if self.compare_pretty_values(q_values, solution_dict[q_values_key]):
                # file_out_string += "Q-Values at iteration %d for action '%s' are correct." % (n, action)
                # file_out_string += "   Student/correct solution:\n\t%s" % self.pretty_value_solution_string(q_values_key, q_values)
                pass
            else:
                test_pass = False
                out_string = "Q-Values at iteration %d for action '%s' are NOT correct." % (n, action)
                out_string += "   Student solution:\n\t%s" % self.pretty_value_solution_string(q_values_key, q_values)
                out_string += "   Correct solution:\n\t%s" % self.pretty_value_solution_string(q_values_key, solution_dict[q_values_key])
                std_out_string += out_string
                file_out_string += out_string
        if check_values_and_policy:
            if not self.compare_pretty_values(values_pretty, solution_dict['values']):
                test_pass = False
                out_string = "Values are NOT correct."
                out_string += "   Student solution:\n\t%s" % self.pretty_value_solution_string('values', values_pretty)
                out_string += "   Correct solution:\n\t%s" % self.pretty_value_solution_string('values', solution_dict['values'])
                std_out_string += out_string
                file_out_string += out_string
            if not self.compare_pretty_values(policy_pretty, solution_dict['policy']):
                test_pass = False
                out_string = "Policy is NOT correct."
                out_string += "   Student solution:\n\t%s" % self.pretty_value_solution_string('policy', policy_pretty)
                out_string += "   Correct solution:\n\t%s" % self.pretty_value_solution_string('policy', solution_dict['policy'])
                std_out_string += out_string
                file_out_string += out_string
        return test_pass, std_out_string, file_out_string

    def write_solution(self, module_dict, file_path):
        with open(file_path, 'w') as handle:
            values_pretty = ''
            policy_pretty = ''
            for n in self.nums_experiences_for_display:
                values_pretty, q_values_pretty, actions, policy_pretty, _ = self.run_agent(module_dict, n)
                for action in actions:
                    handle.write(self.pretty_value_solution_string('q_values_k_%d_action_%s' % (n, action), q_values_pretty[action]))
            handle.write(self.pretty_value_solution_string('values', values_pretty))
            handle.write(self.pretty_value_solution_string('policy', policy_pretty))
        return True

    def run_agent(self, module_dict, num_experiences):
        agent = module_dict['q_learning_agents'].QLearningAgent(**self.opts)
        states = [state for state in self.grid.get_states() if len(self.grid.get_possible_actions(state)) > 0]
        states.sort()
        last_experience = None
        for i in range(num_experiences):
            last_experience = self.experiences.get_experience()
            agent.update(*last_experience)
        actions = list(reduce(lambda a, b: set(a).union(b), [self.grid.get_possible_actions(state) for state in states]))
        values = {}
        q_values = {}
        policy = {}
        for state in states:
            values[state] = agent.compute_value_from_q_values(state)
            policy[state] = agent.compute_action_from_q_values(state)
            possible_actions = self.grid.get_possible_actions(state)
            for action in actions:
                if action not in q_values:
                    q_values[action] = {}
                if action in possible_actions:
                    q_values[action][state] = agent.get_q_value(state, action)
                else:
                    q_values[action][state] = None
        values_pretty = self.pretty_values(values)
        policy_pretty = self.pretty_policy(policy)
        q_values_pretty = {}
        for action in actions:
            q_values_pretty[action] = self.pretty_values(q_values[action])
        return values_pretty, q_values_pretty, actions, policy_pretty, last_experience

    def pretty_print(self, elements, format_string):
        pretty = ''
        states = self.grid.get_states()
        for y_bar in range(self.grid.grid.height):
            y = self.grid.grid.height-1-y_bar
            row = []
            for x in range(self.grid.grid.width):
                if (x, y) in states:
                    value = elements[(x, y)]
                    if value is None:
                        row.append('   illegal')
                    else:
                        row.append(format_string.format(elements[(x, y)]))
                else:
                    row.append('_' * 10)
            pretty += '        %s\n' % ("   ".join(row), )
        pretty += '\n'
        return pretty

    def pretty_values(self, values):
        return self.pretty_print(values, '{0:10.4f}')

    def pretty_policy(self, policy):
        return self.pretty_print(policy, '{0:10s}')

    def pretty_value_solution_string(self, name, pretty):
        return '%s: """\n%s\n"""\n\n' % (name, pretty.rstrip())

    def compare_pretty_values(self, a_pretty, b_pretty, tolerance=0.01):
        a_list = self.parse_pretty_values(a_pretty)
        b_list = self.parse_pretty_values(b_pretty)
        if len(a_list) != len(b_list):
            return False
        for a, b in zip(a_list, b_list):
            try:
                a_num = float(a)
                b_num = float(b)
                # error = abs((a_num - b_num) / ((a_num + b_num) / 2.0))
                error = abs(a_num - b_num)
                if error > tolerance:
                    return False
            except ValueError:
                if a.strip() != b.strip():
                    return False
        return True

    def parse_pretty_values(self, pretty):
        values = pretty.split()
        return values


class EpsilonGreedyTest(test_classes.TestCase):

    def __init__(self, question, test_dict):
        super(EpsilonGreedyTest, self).__init__(question, test_dict)
        self.discount = float(test_dict['discount'])
        self.grid = gridworld.Gridworld(parse_grid(test_dict['grid']))
        if 'noise' in test_dict: self.grid.set_noise(float(test_dict['noise']))
        if 'living_reward' in test_dict: self.grid.set_living_reward(float(test_dict['living_reward']))

        self.grid = gridworld.Gridworld(parse_grid(test_dict['grid']))
        self.env = gridworld.GridworldEnvironment(self.grid)
        self.epsilon = float(test_dict['epsilon'])
        self.learning_rate = float(test_dict['learning_rate'])
        self.num_experiences = int(test_dict['num_experiences'])
        self.num_iterations = int(test_dict['iterations'])
        self.opts = {'action_fn': self.env.get_possible_actions, 'epsilon': self.epsilon, 'gamma': self.discount, 'alpha': self.learning_rate}
        if sys.platform == 'win32':
            _, question_name, test_name = test_dict['test_out_file'].split('\\')
        else:
            _, question_name, test_name = test_dict['test_out_file'].split('/')
        self.experiences = Experiences(test_name.split('.')[0])

    def execute(self, grades, module_dict, solution_dict):
        if self.test_epsilon_greedy(module_dict):
            return self.test_pass(grades)
        else:
            return self.test_fail(grades)

    def write_solution(self, module_dict, file_path):
        with open(file_path, 'w') as handle:
            handle.write('# This is the solution file for %s.\n' % self.path)
            handle.write('# File intentionally blank.\n')
        return True

    def run_agent(self, module_dict):
        agent = module_dict['q_learning_agents'].QLearningAgent(**self.opts)
        states = [state for state in self.grid.get_states() if len(self.grid.get_possible_actions(state)) > 0]
        states.sort()
        for i in range(self.num_experiences):
            last_experience = self.experiences.get_experience()
            agent.update(*last_experience)
        return agent

    def test_epsilon_greedy(self, module_dict, tolerance=0.025):
        agent = self.run_agent(module_dict)
        for state in self.grid.get_states():
            num_legal_actions = len(agent.get_legal_actions(state))
            if num_legal_actions <= 1:
                continue
            num_greedy_choices = 0
            optimal_action = agent.compute_action_from_q_values(state)
            for iteration in range(self.num_iterations):
                # assume that their compute_action_from_q_values implementation is correct (q4 tests this)
                if agent.get_action(state) == optimal_action:
                    num_greedy_choices += 1
            # e = epsilon, g = # greedy actions, n = num_iterations, k = num_legal_actions
            # g = n * [(1-e) + e/k] -> e = (n - g) / (n - n/k)
            empirical_epsilon_numerator = self.num_iterations - num_greedy_choices
            empirical_epsilon_denominator = self.num_iterations - self.num_iterations / float(num_legal_actions)
            empirical_epsilon = empirical_epsilon_numerator / empirical_epsilon_denominator
            error = abs(empirical_epsilon - self.epsilon)
            if error > tolerance:
                self.add_message("Epsilon-greedy action selection is not correct.")
                self.add_message("Actual epsilon = %f; student empirical epsilon = %f; error = %f > tolerance = %f" % (self.epsilon, empirical_epsilon, error, tolerance))
                return False
        return True


### q8
class Question8Test(test_classes.TestCase):

    def __init__(self, question, test_dict):
        super(Question8Test, self).__init__(question, test_dict)

    def execute(self, grades, module_dict, solution_dict):
        student_solution = module_dict['analysis'].question8()
        student_solution = str(student_solution).strip().lower()
        hashed_solution = sha1(student_solution.encode('utf-8')).hexdigest()
        if hashed_solution == '46729c96bb1e4081fdc81a8ff74b3e5db8fba415':
            return self.test_pass(grades)
        else:
            self.add_message("Solution is not correct.")
            self.add_message("   Student solution: %s" % (student_solution,))
            return self.test_fail(grades)

    def write_solution(self, module_dict, file_path):
        handle = open(file_path, 'w')
        handle.write('# This is the solution file for %s.\n' % self.path)
        handle.write('# File intentionally blank.\n')
        handle.close()
        return True


### q7/q8
### =====
## Average wins of a pacman agent

class EvalAgentTest(test_classes.TestCase):

    def __init__(self, question, test_dict):
        super(EvalAgentTest, self).__init__(question, test_dict)
        self.pacman_params = test_dict['pacman_params']

        self.score_minimum = int(test_dict['score_minimum']) if 'score_minimum' in test_dict else None
        self.non_timeout_minimum = int(test_dict['non_timeout_minimum']) if 'non_timeout_minimum' in test_dict else None
        self.wins_minimum = int(test_dict['wins_minimum']) if 'wins_minimum' in test_dict else None

        self.score_thresholds = [int(s) for s in test_dict.get('score_thresholds', '').split()]
        self.non_timeout_thresholds = [int(s) for s in test_dict.get('non_timeout_thresholds', '').split()]
        self.wins_thresholds = [int(s) for s in test_dict.get('wins_thresholds', '').split()]

        self.max_points = sum([len(t) for t in [self.score_thresholds, self.non_timeout_thresholds, self.wins_thresholds]])


    def execute(self, grades, module_dict, solution_dict):
        self.add_message('Grading agent using command:  python pacman.py %s' % (self.pacman_params,))

        start_time = time.time()
        games = pacman.run_games(** pacman.read_command(self.pacman_params.split(' ')))
        total_time = time.time() - start_time
        num_games = len(games)

        stats = {'time': total_time, 'wins': [g.state.is_win() for g in games].count(True),
                 'games': games, 'scores': [g.state.get_score() for g in games],
                 'timeouts': [g.agent_timeout for g in games].count(True), 'crashes': [g.agent_crashed for g in games].count(True)}

        average_score = sum(stats['scores']) / float(len(stats['scores']))
        non_timeouts = num_games - stats['timeouts']
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
                   grade_threshold(non_timeouts, self.non_timeout_minimum, self.non_timeout_thresholds, "games not timed out"),
                   grade_threshold(wins, self.wins_minimum, self.wins_thresholds, "wins")]

        total_points = 0
        for passed, points, value, minimum, thresholds, name in results:
            if (minimum is None) and (len(thresholds)==0):
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
                if len(thresholds)==0 or minimum != thresholds[0]:
                    self.add_message("    >= %s:  0 points" % (minimum,))
                for idx, threshold in enumerate(thresholds):
                    self.add_message("    >= %s:  %s points" % (threshold, idx + 1))
            elif len(thresholds) > 0:
                self.add_message("    Grading scheme:")
                self.add_message("     < %s:  0 points" % (thresholds[0],))
                for idx, threshold in enumerate(thresholds):
                    self.add_message("    >= %s:  %s points" % (threshold, idx + 1))

        if any([not passed for passed, _, _, _, _, _ in results]):
            total_points = 0

        return self.test_partial(grades, total_points, self.max_points)

    def write_solution(self, module_dict, file_path):
        with open(file_path, 'w') as handle:
            handle.write('# This is the solution file for %s.\n' % self.path)
            handle.write('# File intentionally blank.\n')
        return True




### q2/q3
### =====
## For each parameter setting, compute the optimal policy, see if it satisfies some properties

def follow_path(policy, start, num_steps=100):
    state = start
    path = []
    for i in range(num_steps):
        if state not in policy:
            break
        action = policy[state]
        path.append("(%s,%s)" % state)
        if action == 'north': next_state = state[0],state[1]+1
        if action == 'south': next_state = state[0],state[1]-1
        if action == 'east': next_state = state[0]+1,state[1]
        if action == 'west': next_state = state[0]-1,state[1]
        if (action == 'exit') or (action is None):
            path.append('TERMINAL_STATE')
            break
        state = next_state

    return path

def parse_grid(string):
    grid = [[entry.strip() for entry in line.split()] for line in string.split('\n')]
    for row in grid:
        for x, col in enumerate(row):
            try:
                col = int(col)
            except:
                pass
            if col == "_":
                col = ' '
            row[x] = col
    return gridworld.make_grid(grid)


def compute_policy(module_dict, grid, discount):
    value_iterator = module_dict['value_iteration_agents'].ValueIterationAgent(grid, discount=discount)
    policy = {}
    for state in grid.get_states():
        policy[state] = value_iterator.compute_action_from_values(state)
    return policy



class GridPolicyTest(test_classes.TestCase):

    def __init__(self, question, test_dict):
        super(GridPolicyTest, self).__init__(question, test_dict)

        # Function in module in analysis that returns (discount, noise)
        self.parameter_fn = test_dict['parameter_fn']
        self.question2 = test_dict.get('question2', 'false').lower() == 'true'

        # GridWorld specification
        #    _ is empty space
        #    numbers are terminal states with that value
        #    # is a wall
        #    S is a start state
        #
        self.grid_text = test_dict['grid']
        self.grid = gridworld.Gridworld(parse_grid(test_dict['grid']))
        self.grid_name = test_dict['grid_name']

        # Policy specification
        #    _                  policy choice not checked
        #    N, E, S, W policy action must be north, east, south, west
        #
        self.policy = parse_grid(test_dict['policy'])

        # State the most probable path must visit
        #    (x,y) for a particular location; (0,0) is bottom left
        #    terminal for the terminal state
        self.path_visits = test_dict.get('path_visits', None)

        # State the most probable path must not visit
        #    (x,y) for a particular location; (0,0) is bottom left
        #    terminal for the terminal state
        self.path_not_visits = test_dict.get('path_not_visits', None)


    def execute(self, grades, module_dict, solution_dict):
        if not hasattr(module_dict['analysis'], self.parameter_fn):
            self.add_message('Method not implemented: analysis.%s' % (self.parameter_fn,))
            return self.test_fail(grades)

        result = getattr(module_dict['analysis'], self.parameter_fn)()

        if type(result) == str and result.lower()[0:3] == "not":
            self.add_message('Actually, it is possible!')
            return self.test_fail(grades)

        if self.question2:
            living_reward = None
            try:
                discount, noise = result
                discount = float(discount)
                noise = float(noise)
            except:
                self.add_message('Did not return a (discount, noise) pair; instead analysis.%s returned: %s' % (self.parameter_fn, result))
                return self.test_fail(grades)
            if discount != 0.9 and noise != 0.2:
                self.add_message('Must change either the discount or the noise, not both. Returned (discount, noise) = %s' % (result,))
                return self.test_fail(grades)
        else:
            try:
                discount, noise, living_reward = result
                discount = float(discount)
                noise = float(noise)
                living_reward = float(living_reward)
            except:
                self.add_message('Did not return a (discount, noise, living reward) triple; instead analysis.%s returned: %s' % (self.parameter_fn, result))
                return self.test_fail(grades)

        self.grid.set_noise(noise)
        if living_reward is not None:
            self.grid.set_living_reward(living_reward)

        start = self.grid.get_start_state()
        policy = compute_policy(module_dict, self.grid, discount)

        ## check policy
        action_map = {'N': 'north', 'E': 'east', 'S': 'south', 'W': 'west', 'X': 'exit'}
        width, height = self.policy.width, self.policy.height
        policy_passed = True
        for x in range(width):
            for y in range(height):
                if self.policy[x][y] in action_map and policy[(x,y)] != action_map[self.policy[x][y]]:
                    differ_point = (x,y)
                    policy_passed = False

        if not policy_passed:
            self.add_message('Policy not correct.')
            self.add_message('    Student policy at %s: %s' % (differ_point, policy[differ_point]))
            self.add_message('    Correct policy at %s: %s' % (differ_point, action_map[self.policy[differ_point[0]][differ_point[1]]]))
            self.add_message('    Student policy:')
            self.print_policy(policy, False)
            self.add_message("        Legend:  N,S,E,W at states which move north etc, X at states which exit,")
            self.add_message("                 . at states where the policy is not defined (e.g. walls)")
            self.add_message('    Correct policy specification:')
            self.print_policy(self.policy, True)
            self.add_message("        Legend:  N,S,E,W for states in which the student policy must move north etc,")
            self.add_message("                 _ for states where it doesn't matter what the student policy does.")
            self.print_gridworld()
            return self.test_fail(grades)

        ## check path
        path = follow_path(policy, self.grid.get_start_state())

        if (self.path_visits is not None) and (self.path_visits not in path):
            self.add_message('Policy does not visit state %s when moving without noise.' % (self.path_visits,))
            self.add_message('    States visited: %s' % (path,))
            self.add_message('    Student policy:')
            self.print_policy(policy, False)
            self.add_message("        Legend:  N,S,E,W at states which move north etc, X at states which exit,")
            self.add_message("                 . at states where policy not defined")
            self.print_gridworld()
            return self.test_fail(grades)

        if (self.path_not_visits is not None) and (self.path_not_visits in path):
            self.add_message('Policy visits state %s when moving without noise.' % (self.path_not_visits,))
            self.add_message('    States visited: %s' % (path,))
            self.add_message('    Student policy:')
            self.print_policy(policy, False)
            self.add_message("        Legend:  N,S,E,W at states which move north etc, X at states which exit,")
            self.add_message("                 . at states where policy not defined")
            self.print_gridworld()
            return self.test_fail(grades)

        return self.test_pass(grades)

    def print_gridworld(self):
        self.add_message('    Gridworld:')
        for line in self.grid_text.split('\n'):
            self.add_message('     ' + line)
        self.add_message('        Legend: # wall, _ empty, S start, numbers terminal states with that reward.')

    def print_policy(self, policy, policy_type_is_grid):
        if policy_type_is_grid:
            legend = {'N': 'N', 'E': 'E', 'S': 'S', 'W': 'W', ' ': '_', 'X': 'X', '.': '.'}
        else:
            legend = {'north': 'N', 'east': 'E', 'south': 'S', 'west': 'W', 'exit': 'X', '.': '.', ' ': '_'}

        for y_bar in range(self.grid.grid.height):
            y = self.grid.grid.height-1-y_bar
            if policy_type_is_grid:
                self.add_message("        %s" % ("    ".join([legend[policy[x][y]] for x in range(self.grid.grid.width)]),))
            else:
                self.add_message("        %s" % ("    ".join([legend[policy.get((x, y), '.')] for x in range(self.grid.grid.width)]),))
        # for state in sorted(self.grid.get_states()):
        #     if state != 'TERMINAL_STATE':
        #         self.add_message('      (%s,%s) %s' % (state[0], state[1], policy[state]))


    def write_solution(self, module_dict, file_path):
        with open(file_path, 'w') as handle:
            handle.write('# This is the solution file for %s.\n' % self.path)
            handle.write('# File intentionally blank.\n')
        return True

