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
import random
import time
import util
import sys
from game import Directions, Actions
import game
from util import nearestPoint


def createTeam(firstIndex, secondIndex, isRed,
               first='DefensiveReflexAgent', second='DefensiveReflexAgent'):
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


class BaseAgent(CaptureAgent):
    """
    A defense agent that stays in the middle of the map and tries to guard
    against attackers. If an attacker is on our side, will attempt to try 
    and catch opponent. 
    """

    def getSuccessor(self, gameState, action):
            successor = gameState.generateSuccessor(self.index, action)
            pos = successor.getAgentState(self.index).getPosition()
            if pos != nearestPoint(pos):

                return successor.generateSuccessor(self.index, action)
            else:
                return successor

    def evaluate(self, gameState, action):
        features = self.evaluateAttackParameters(gameState, action)
        weights = self.getCostOfAttackParameter(gameState, action)
        return features * weights

    def evaluateAttackParameters(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)
        return features

    def getCostOfAttackParameter(self, gameState, action):
        return {'successorScore': 1.0}


class DefensiveReflexAgent(BaseAgent):
    def __init__(self, index):
        CaptureAgent.__init__(self, index)
        self.target = None
        self.previousFood = []
        self.counter = 0

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.setPatrolPoint(gameState)

    def setPatrolPoint(self, gameState):
        '''
        Look for center of the maze for patrolling
        '''
        x = (gameState.data.layout.width - 2) // 2
        if not self.red:
            x += 1
        self.patrolPoints = []
        for i in range(1, gameState.data.layout.height - 1):
            if not gameState.hasWall(x, i):
                self.patrolPoints.append((x, i))

        for i in range(len(self.patrolPoints)):
            if len(self.patrolPoints) > 2:
                self.patrolPoints.remove(self.patrolPoints[0])
                self.patrolPoints.remove(self.patrolPoints[-1])
            else:
                break

    def getNextDefensiveMove(self, gameState):

        agentActions = []
        actions = gameState.getLegalActions(self.index)

        rev_dir = Directions.REVERSE[gameState.getAgentState(
            self.index).configuration.direction]
        actions.remove(Directions.STOP)

        for i in range(0, len(actions)-1):
            if rev_dir == actions[i]:
                actions.remove(rev_dir)

        for i in range(len(actions)):
            a = actions[i]
            new_state = gameState.generateSuccessor(self.index, a)
            if not new_state.getAgentState(self.index).isPacman:
                agentActions.append(a)

        if len(agentActions) == 0:
            self.counter = 0
        else:
            self.counter = self.counter + 1
        if self.counter > 4 or self.counter == 0:
            agentActions.append(rev_dir)

        return agentActions

    def chooseAction(self, gameState):

        position = gameState.getAgentPosition(self.index)
        if position == self.target:
            self.target = None
        invaders = []
        nearestInvader = []
        minDistance = float("inf")

        # Look for enemy position in our home
        opponentsPositions = self.getOpponents(gameState)
        i = 0
        while i != len(opponentsPositions):
            opponentPos = opponentsPositions[i]
            opponent = gameState.getAgentState(opponentPos)
            if opponent.isPacman and opponent.getPosition() != None:
                opponentPos = opponent.getPosition()
                invaders.append(opponentPos)
            i = i + 1

        # if enemy is found chase it and kill it
        if len(invaders) > 0:
            for oppPosition in invaders:
                dist = self.getMazeDistance(oppPosition, position)
                if dist < minDistance:
                    minDistance = dist
                    nearestInvader.append(oppPosition)
            self.target = nearestInvader[-1]

        # if enemy has eaten some food, then remove it from targets
        else:
            if len(self.previousFood) > 0:
                if len(self.getFoodYouAreDefending(gameState).asList()) < len(self.previousFood):
                    yummy = set(self.previousFood) - \
                        set(self.getFoodYouAreDefending(gameState).asList())
                    self.target = yummy.pop()

        self.previousFood = self.getFoodYouAreDefending(gameState).asList()

        if self.target == None:
            if len(self.getFoodYouAreDefending(gameState).asList()) <= 4:
                highPriorityFood = self.getFoodYouAreDefending(
                    gameState).asList() + self.getCapsulesYouAreDefending(gameState)
                self.target = random.choice(highPriorityFood)
            else:
                self.target = random.choice(self.patrolPoints)
        candAct = self.getNextDefensiveMove(gameState)
        awsomeMoves = []
        fvalues = []

        i = 0

        # find the best move
        while i < len(candAct):
            a = candAct[i]
            nextState = gameState.generateSuccessor(self.index, a)
            newpos = nextState.getAgentPosition(self.index)
            awsomeMoves.append(a)
            fvalues.append(self.getMazeDistance(newpos, self.target))
            i = i + 1

        best = min(fvalues)
        bestActions = [a for a, v in zip(awsomeMoves, fvalues) if v == best]
        bestAction = random.choice(bestActions)
        return bestAction
