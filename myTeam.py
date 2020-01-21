# multiAgents.py
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

from __future__ import print_function
from captureAgents import CaptureAgent
import distanceCalculator
import random , time, util, sys
from game import Directions, Actions
import game
from util import nearestPoint


def createTeam(firstIndex, secondIndex, isRed,
               first='DefenseAgent', second='DefenseAgent'):
    """
    This function should return a list of two agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.  isRed is True if the red team is being created, and
    will be False if the blue team is being created.

    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments ("first" and "second" are
    such arguments in the case of this function), which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


class DefenseAgent(CaptureAgent):
    """
    A defense agent that takes score maximizing actions. The fetures and weights given prioritizes
    defensive actions first.
    """

    def registerInitialState(self, gameState):
        """
        This method handles the initial setup  of team and agent. Also gets details from the game such as
        oppenents, food we need, and the food we are defending.
        """

        CaptureAgent.registerInitialState(self, gameState)
        self.myAgents = CaptureAgent.getTeam(self, gameState)
        self.enemyAgents = CaptureAgent.getOpponents(self, gameState)
        self.myFoods = CaptureAgent.getFood(self, gameState).asList()                       #A list of the food we need
        self.opFoods = CaptureAgent.getFoodYouAreDefending(self, gameState).asList()        #List of food that is ours(defending)

    def getSuccessor(self, gameState, action):
        """
        Finds the next successor which is a grid position (location tuple)
        """
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
            # Only half a grid position was covered
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    # Returns a counter of features for the state
    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)

        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()

        # Computes whether we're on defense (1) or offense (0)
        features['onDefense'] = 1
        if myState.isPacman: features['onDefense'] = 0

        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        features['numInvaders'] = len(invaders)
        if len(invaders) > 0:
            dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
            features['invaderDistance'] = min(dists)

        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1

        return features

    # Returns a dictionary of features for the state
    def getWeights(self, gameState, action):
        return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2}

    # Computes a linear combination of features and feature weights
    def evaluate(self, gameState, action):
        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights

    # Choose the best action for the current agent to take
    def chooseAction(self, gameState):
        agentPos = gameState.getAgentPosition(self.index)
        actions = gameState.getLegalActions(self.index)

        # Distances between agent and foods
        distToFood = []
        for food in self.myFoods:
            distToFood.append(self.distancer.getDistance(agentPos, food))

        # Distances between agent and opponents
        distToEnemyAgents = []
        for opponent in self.enemyAgents:
            opponentPosition = gameState.getAgentPosition(opponent)
            if opponentPosition != None:
                distToEnemyAgents.append(self.distancer.getDistance(agentPos, opponentPosition))

        # Get the best action based on values
        values = [self.evaluate(gameState, a) for a in actions]
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]
        return random.choice(bestActions)


#Still working on this
#class offensiveAgent(CaptureAgent):
