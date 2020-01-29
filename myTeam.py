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
  A base class for our agents to inherit
  """

  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    actions = gameState.getLegalActions(self.index)
    values = [self.evaluate(gameState, a) for a in actions]
    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    foodLeft = len(self.getFood(gameState).asList())

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
  A reflex agent that seeks food. The goal of the offensive agent is to go out
  and initially get food as quick as possible. It looks specifically at getting
  the closet possible food, that being the food right across the center line. It
  then tries to get one other piece of food if it can and then it will return those
  home. Once we are winning, the offensive agent now will play defense and guard
  the lane that is further from the other two. For example, on Red Team, the top
  lane is significantly further away from the middle and bottom lanes. So the
  defensive agent is guarding that bottom one and the offensive agent should
  guard that top lane. If we already got food, we can guess that one of the
  opposing team's agents is also on our side and so if we just guard the exit
  then that other team's agent will eventually have to come towards us. Once an
  enemy comes toward us, then we will go after them. If at any point we start to
  lose, the offensive agent will also try to go get more food.
  """
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    foodList = self.getFood(successor).asList()
    features['successorScore'] = -len(foodList)

    agents = self.getOpponents(gameState)
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    enemiesPo = [successor.getAgentPosition(i) for i in self.getOpponents(successor)]
    enemiesPo = [a for a in enemiesPo if a != None]

    # set team specific coordinates to go to. The guard points are where the
    # offensive agent should go between and the middle_food variable is the
    # location of the food pellet in the middle.
    if self.red:
      topGuardPoint = (12, 14)
      bottomGuardPoint = (12, 7)
      middle_food = (14, 9)
    else:
      topGuardPoint = (19, 7)
      bottomGuardPoint = (19, 1)
      middle_food = (17, 6)

    # get my current position. This variable is used often to determine where to go
    myPos = successor.getAgentState(self.index).getPosition()

    # If the obersvation history is greater than 10, start to record the move
    # history so that we can use it later when the offensive agent starts to
    # play defense.

    # If the food in the middle is still there, go for that above all else. Once
    # we either eat it and return it or eat it and then die and the food respawns,
    # we focus on something else.
    if middle_food in foodList:
      minDistance = self.getMazeDistance(myPos, middle_food)
      features['distanceToFood'] = minDistance
    else:
      # This should always be True, but better safe than sorry
      if len(foodList) > 0:

        # The first thing we want to do is check if we are winning. If we know
        # that we are winning, we want to play defense and guard the lane that
        # is by itself (the defensive agent should be guarding the other two lanes)
        if self.getScore(successor) >= 1:
          moveHistory = [self.observationHistory[-1*i].getAgentState(self.index).getPosition() for i in range(1,10)]

          # For the sake of derivates and determing the change in direction,
          # we look to the move most recently did and then the move we did
          # four turns ago.
          one_move_ago = moveHistory[1][1] - moveHistory[0][1]
          four_moves_ago = moveHistory[4][1] - moveHistory[3][1]

          # Computes distance to invaders we can see
          enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
          invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
          features['numInvaders'] = len(invaders)

          # if there are invaders, we should go attack them.
          if len(invaders) > 0:
            dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
            features['invaderDistance'] = 1000/min(dists)

          # When stopped and was moving down, now go up
          if one_move_ago == 0 and four_moves_ago > 0:
            guardArea = self.getMazeDistance(myPos, topGuardPoint)

            # there seemed to be an issue when using getMazeDistance() that if
            # we were on top of the point we were trying to get to then it would
            # return 0 and that caused some issues. So we decided to just guard
            # against that and make guardArea 1 if it was 0.
            features['guardArea'] = guardArea

            # now that we are in guard mode, attack if they come to our side
            if len(invaders) > 0:
              dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
              features['invaderDistance'] = min(dists)

          # When stopped and was moving up, now go down
          elif one_move_ago == 0 and four_moves_ago < 0:
            guardArea = self.getMazeDistance(myPos, bottomGuardPoint)

            # same issue as before with guardArea
            features['guardArea'] = guardArea

            # again, attack if people are on our side.
            if len(invaders) > 0:
              dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
              features['invaderDistance'] = min(dists)

        # make sure that if we are carrying two or more food pellets, return home
        # to collect those points.
        elif gameState.getAgentState(self.index).numCarrying >= 2:
          myPos = successor.getAgentState(self.index).getPosition()
          minDistance = self.getMazeDistance(myPos, topGuardPoint)
          features['confirmFood'] = minDistance

        # if we are not winning and we are not carrying food, we need to do many things
        else:

          # first we want to see roughly where the enemies are. If they are close
          # to where we are trying to go, we should flee. So even if the middle
          # food is there, we should still try to avoid others.
          if enemiesPo:
            minDistEn = min([self.getMazeDistance(myPos, invader) for invader in enemiesPo])
            features['fleeEnemy'] = minDistEn

          # If we are in the clear, go get the food!
          myPos = successor.getAgentState(self.index).getPosition()
          minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
          features['distanceToFood'] = minDistance

    return features

  def getWeights(self, gameState, action):
    return {
      'successorScore': 100,
      'distanceToFood': -1,
      'fleeEnemy': -5,
      'confirmFood': -100,
      'guardArea': -1,
      'numInvaders': -500,
      'invaderDistance': -500
    }

class DefensiveReflexAgent(ReflexCaptureAgent):
  """
  A defensive agent that will start the game protecting the capsule.
  If the capsule gets eaten, will try to defend our side from enemy ghosts.
  """

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    # Assigns variable myState to our agents state
    myState = successor.getAgentState(self.index)

    # Assigns variable myPos to our current position
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
      # TODO: This bad boy is commented out, not sure why or if we should just remove it?
      #features['reverse'] = -1
    else:
      foodList = self.getFoodYouAreDefending(successor).asList()
      dist = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['byFood'] = dist

      # At the start, will rush to the capsule and try to defend. If capsule
      # gets eaten, the agent does its very best to attack the enemy ghosts
      capsules = self.getCapsulesYouAreDefending(successor)
      if len(capsules) > 0:
          features['byCapsule'] = min([self.getMazeDistance(myPos, capsule) for capsule in capsules])
      else:
          features['numInvaders'] = len(invaders)
      team = [successor.getAgentState(i) for i in self.getTeam(successor) if i != self.index]
      defenders = [a for a in team if not a.isPacman and a.getPosition() != None]
      if len(defenders) > 0:
          ally_dist = min([self.getMazeDistance(myPos, ally.getPosition()) for ally in defenders])
          # TODO: lololol where did we get this stupidly small decimal and why are we dividing it by 1
          # to get a bigger value?? could just multiply ally_dist by something big, but that's just me *insert winky face*
          features['byAlly'] = 1.0/(ally_dist+.000000001)

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    return {
        'numInvaders': -1000,
        'onDefense': 5000,
        'invaderDistance': -1000,
        'stop': -100,
        'reverse': -2,
        'byCapsule': -2
      }
