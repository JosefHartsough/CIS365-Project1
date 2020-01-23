# baselineTeam.py
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


# baselineTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html
from __future__ import print_function
from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveReflexAgent', second = 'DefensiveReflexAgent'):
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

##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """

  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

  # def getCapsules(self, gameState):
  #   if self.red:
  #     return gameState.getBlueCapsules()
  #   else:
  #     return gameState.getRedCapsules()

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    actions = gameState.getLegalActions(self.index)
    print("legal actions", actions)
    remaining = gameState.getCapsules()

    capPos = self.getCapsules(gameState)
    # print("this is the location of the capsule!!!!!!!!", str(capPos))
    # print("this is the number of remaining capsule#########", str(remaining))
    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # if self.index == 1:
    #   print(values, file=sys.stderr)
      # print(self.getPreviousObservation(), file=sys.stderr)

    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]
    # if self.index == 1:
    #   print(bestActions, file=sys.stderr)

    foodLeft = len(self.getFood(gameState).asList())

    if foodLeft <= 2 or gameState.getAgentState(self.index).numCarrying > 5:
      bestDist = 9999
      for action in actions:
        if len(remaining) == 2:
          capsule = self.getCapsules(gameState)
          dist = self.getMazeDistance(self.start,capsule)
          print("self start", self.start)
        else:
          successor = self.getSuccessor(gameState, action)
          pos2 = successor.getAgentPosition(self.index)
          dist = self.getMazeDistance(self.start,pos2)
          print("self start", self.start)
          if dist < bestDist:
            bestAction = action
            bestDist = dist
      return bestAction

    return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """

    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)

    # if self.index == 1:
    #   print(str(features) + str(weights), file=sys.stderr)
      # print(gameState.getAgentState(self.index)) # Print out a text representation of the world.

    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)

    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}

class OffensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    foodList = self.getFood(successor).asList()
    features['successorScore'] = -len(foodList)#self.getScore(successor)

    # print("foodList", foodList)

    #if(len(self.observationHistory) > 2):
      #lastPos = self.observationHistory[-2].getAgentPosition(self.index)
      #if(lastPos != [14,9]):

    agents = self.getOpponents(gameState)
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    print("enemies ", str(enemies))
    print("self start", self.start)
    # for a in agents:
      #enemyPos = gameState.getAgentPosition(a)

      #here I am trying to look through the previous positions of the enemy agent and check if the average
      #distance between the middle point and the last moves of the enemy and set it a new feature. But i havent finished it yet...
      # if len(self.observationHistory) > 15:
      #   moveHistory = [self.observationHistory[-1*i].getAgentState(self.index).getPosition() for i in range(2,10)]
      #   d = [self.getMazeDistance(enemyPos, (15,8)) for enemyPos in moveHistory]
      #   avg = sum(d) / len(d)
      #   print("avg distance", str(avg))
      #   features['avoidTheMiddle'] = avg

    #this is the part where it goes straight to the middle food and then moves on.
    middle_food = (14, 9) if not self.red else (17, 6)
    print("score: ", self.getScore(successor))
    myPos = successor.getAgentState(self.index).getPosition()
    print("myPos", myPos)
    if len(self.observationHistory) > 10:
      moveHistory = [self.observationHistory[-1*i].getAgentState(self.index).getPosition() for i in range(1,10)]
      print("moveHistory", moveHistory)

    if middle_food in foodList:
      myPos = successor.getAgentState(self.index).getPosition()
      minDistance = self.getMazeDistance(myPos, middle_food)
      features['distanceToFood'] = minDistance
    else:
      if len(foodList) > 0: # This should always be True,  but better safe than sorry
        if self.getScore(successor) >= 4:
          myPos = successor.getAgentState(self.index).getPosition()
          topGuardPoint = (12, 14)
          bottomGuardPoint = (12, 7)
          # distanceToTop = self.distancer.getDistance(myPos, topGuardPoint)
          # print("distance", distanceToTop)
          moveHistory = [self.observationHistory[-1*i].getAgentState(self.index).getPosition() for i in range(1,10)]
          print("moveHistory", moveHistory)
          print("moveHistory[0]", moveHistory[0])
          print("moveHistory[0][1]", moveHistory[0][1])
          print("moveHistory[6][1]", moveHistory[6][1])
          print("moveHistory[6][1] - moveHistory[0][1]", moveHistory[6][1] - moveHistory[0][1])
          first_recent = moveHistory[1][1] - moveHistory[0][1]
          second_recent = moveHistory[2][1] - moveHistory[1][1]
          third_recent = moveHistory[3][1] - moveHistory[2][1]
          four_recent = moveHistory[4][1] - moveHistory[3][1]
          if first_recent == 0 and four_recent > 0:
            guardArea = self.getMazeDistance(myPos, topGuardPoint)
            features['guardArea'] = guardArea
          elif first_recent == 0 and four_recent < 0:
            guardArea = self.getMazeDistance(myPos, bottomGuardPoint)
            features['guardArea'] = guardArea
        elif gameState.getAgentState(self.index).numCarrying >= 4:
          myPos = successor.getAgentState(self.index).getPosition()
          minDistance = self.getMazeDistance(myPos, self.start)
          features['confirmFood'] = minDistance
        else:
          myPos = successor.getAgentState(self.index).getPosition()
          minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
          features['distanceToFood'] = minDistance

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  # def isOppGuardingMiddle(self, gameState):
  #   agents = self.getOpponents(gameState)
  #   for a in agents:
  #     #enemyPos = gameState.getAgentPosition(a)
  #     if len(a.observationHistory) > 15):
  #       moveHistory = [a.observationHistory[-1*i].getAgentState(a.index).getPosition() for i in range(2,10)]
  #       d = [self.getMazeDistance(enemyPos, (15,8)) for enemyPos in moveHistory]
  #       avg = sum(d) / len(d)
  #       print("this is the average for the number of distance from the centre position", str(avg))
  #       features['avoidTheMiddle'] = avg

  def getWeights(self, gameState, action):
    return {
    'successorScore': 100,
    'distanceToFood': -10,
    'fleeEnemy': -2.0,
    # 'stop': -100,
    'reverse':-5,
    # 'avoidTheMiddle': 100,
    'confirmFood': -10,
    'guardArea': -10
    }

class DefensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    # Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    # Computes distance to invaders we can see
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)
      features['reverse'] = -1
    else:
      foodList = self.getFoodYouAreDefending(successor).asList()
      dist = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['byFood'] = dist
      capsules = self.getCapsulesYouAreDefending(successor)
      if len(capsules) > 0:
          features['byCapsule'] = min([self.getMazeDistance(myPos, capsule) for capsule in capsules])
      team = [successor.getAgentState(i) for i in self.getTeam(successor) if i != self.index]
      defenders = [a for a in team if not a.isPacman and a.getPosition() != None]
      if len(defenders) > 0:
          ally_dist = min([self.getMazeDistance(myPos, ally.getPosition()) for ally in defenders])
          features['byAlly'] = 1.0/(ally_dist+.000000001)


    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    return {
      'numInvaders': -1000,
      'onDefense': 100,
      'invaderDistance': -10,
      'stop': -100,
      'reverse': -2
      }
