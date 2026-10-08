# mdp.py
# ------
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


import random
from abc import abstractmethod


class MarkovDecisionProcess:

    @abstractmethod
    def get_states(self):
        """
        Return a list of all states in the MDP.
        Not generally possible for large MDPs.
        """

    @abstractmethod
    def get_start_state(self):
        """
        Return the start state of the MDP.
        """

    @abstractmethod
    def get_possible_actions(self, state):
        """
        Return list of possible actions from 'state'.
        """

    @abstractmethod
    def get_transition_states_and_probs(self, state, action):
        """
        Returns list of (next_state, prob) pairs
        representing the states reachable
        from 'state' by taking 'action' along
        with their transition probabilities.

        Note that in Q-Learning and reinforcment
        learning in general, we do not know these
        probabilities nor do we directly model them.
        """

    @abstractmethod
    def get_reward(self, state, action, next_state):
        """
        Get the reward for the state, action, next_state transition.

        Not available in reinforcement learning.
        """

    @abstractmethod
    def is_terminal(self, state):
        """
        Returns true if the current state is a terminal state.  By convention,
        a terminal state has zero future rewards.  Sometimes the terminal state(s)
        may have no possible actions.  It is also common to think of the terminal
        state as having a self-loop action 'pass' with zero reward; the formulations
        are equivalent.
        """
