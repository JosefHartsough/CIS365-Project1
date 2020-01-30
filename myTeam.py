from __future__ import print_function
from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint


################################################################################
# This verion of myTeam.py was created by Jarod Collier, Josef Hartsough,
# and Jemima Turnbull.
# Date: 1/30/2020
################################################################################

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
  A base class for our agents to inherit. Most of the code here in the
  ReflexCaptureAgent class is from the generic baselineTeam.py file. We determined
  we didn't mind the template code and rather looked to change the behavior for
  each of the offensive and defensive agents that inherit this class.
  """

  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a). As mentioned in the class'
    description, we left this code largely how the default template left it and
    then decided to change how it is implemented in each of the subclasses.
    """

    actions = gameState.getLegalActions(self.index)
    values = [self.evaluate(gameState, a) for a in actions]
    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    foodLeft = len(self.getFood(gameState).asList())

    return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple). This
    method also should be close to what the default getSuccessor method is in the
    baselineTeam.py file.
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

  def agentIsOnDefense(self, defense):
    """
    This method is to simply set an instance variable to keep track of whether
    we are on defense or not. At first, I wanted to create a constructor, but it
    seems some weird things happen with the special way that these classes are
    created. So I opted to just make a setter function that this class will call
    when you want to change the boolean of whether we are on defense or not.
    """
    self.on_defense = defense

  def getFeatures(self, gameState, action):
    """
    Determine the proper features of the offensive agent. Largely, we want to
    get the closest food in the middle first and just confirm the two food that
    are right there. Once we can confirm those food and we are winning, then
    the features change to allow it to play defense
    """

    # Largely for bookkeaping purposes since the method is created right above here,
    # we first off set the defensive instance variable to false because we want
    # the offensive agent to go get food right away.
    self.agentIsOnDefense(False)

    # These next three blocks of variables are from the template as they pretty much
    # just set up the variables that we may need later on when determining where
    # we would like our bots to go.
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    foodList = self.getFood(successor).asList()
    features['successorScore'] = -len(foodList)

    # As the offensive agent, we naturally want to know where the enemies are.
    # The goal of obtaining these positions is largely to make it so that the
    # offensive agent can flee if he needs to when he is attacking and then also
    # so that he can play defense if we are winning.
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
        # Also, if the obersvation history is greater than 10, start to record the move
        # history so that we can use it later when the offensive agent starts to
        # play defense. We shouldn't hit this block of code before 10 moves, but
        # it is still safe to account for the history actually being there before
        # we try to access it.
        if self.getScore(successor) > 1 and len(self.observationHistory) > 10:

          # Now that we have scored, we want to tell the offensive agent to play
          # defense and so we call the setter to change the weights around.
          self.agentIsOnDefense(True)

          # start keeping track of the history of the moves so we can determine
          # where to go next.
          moveHistory = [self.observationHistory[-1*i].getAgentState(self.index).getPosition() for i in range(1,10)]

          # features['onDefense'] = 1
          # if myState.isPacman: features['onDefense'] = 0

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
            features['invaderDistance'] = min(dists)

          # if we are too far away from the bottomGuardPoint, then we should just
          # head there first. Of course, we want to continually check if there
          # are invaders. If there are, that takes priority and we go get them.
          # Otherwise, we want to get close to the guard points so then we can
          # start patrolling.
          if self.getMazeDistance(myPos, bottomGuardPoint) > 8:
            guardArea = self.getMazeDistance(myPos, bottomGuardPoint)
            features['guardArea'] = guardArea

            # now that we are in guard mode, attack if they come to our side
            if len(invaders) > 0:
              dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
              features['invaderDistance'] = min(dists)
          # When stopped and was moving down, now go up
          elif one_move_ago == 0 and four_moves_ago > 0:
            guardArea = self.getMazeDistance(myPos, topGuardPoint)
            features['guardArea'] = guardArea

            # now that we are in guard mode, attack if they come to our side
            if len(invaders) > 0:
              dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
              features['invaderDistance'] = min(dists)

          # When stopped and was moving up, now go down
          elif one_move_ago == 0 and four_moves_ago < 0:
            guardArea = self.getMazeDistance(myPos, bottomGuardPoint)
            features['guardArea'] = guardArea

            # again, attack if people are on our side.
            if len(invaders) > 0:
              dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
              features['invaderDistance'] = min(dists)

        # make sure that if we are carrying two or more food pellets, return home
        # to collect those points.
        elif gameState.getAgentState(self.index).numCarrying >= 2:
          myPos = successor.getAgentState(self.index).getPosition()
          minDistance = self.getMazeDistance(myPos, bottomGuardPoint)
          features['confirmFood'] = minDistance

        # if we are not winning and we are not carrying food, we need to do attack
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
    """
    Particularly with this offensive agent, we want to explicitly distinguish
    what it should do based on the state of the game. If we are attacking and
    trying to get food, then we most definitely should weight actions accordingly.
    If we are playing defense because we are winning, then we should ensure that
    the agent will attack the opposing players properly.
    """
    # if the offensive agent is on defense, we should drastically change the
    # weights so that he eats people up. Specifically, we remove the distanceToFood
    # and confirmFood keys and replace them with onDefense, invaderDistance, and
    # numInvaders to make him defend our area.
    if self.on_defense:
      return {
        'successorScore': 100,
        'guardArea': -1000,
        'onDefense': 5000,
        'invaderDistance': -10,
        'numInvaders': -1000,
      }
    # This branch is for when we are on offense and thus want to make sure the only
    # thing he is thinking about is the distance to the food and if there happen
    # to be enemies that he needs to flee. Once he has food, he needs to confirm it
    # and then his state will change to defensive and the weights above will be used.
    else:
      return {
        'successorScore': 100,
        'distanceToFood': -1,
        'fleeEnemy': 10,
        'confirmFood': -1,
      }

class DefensiveReflexAgent(ReflexCaptureAgent):
  """
  A defensive agent that will start the game protecting the capsule.
  If the capsule gets eaten, will try to defend our side from enemy ghosts.
  """

  def getFeatures(self, gameState, action):

    # set up the basic variables needed for the features to work in this game
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

    # if there are invaders, then we should find the minimum distance to them
    # and go attack them.
    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)
    # if there are not attackers, we can find the food we are meant to defend
    # and just go defend it. This functionality largely gets replaced by us
    # wanting to guard the capsule most of the time.
    else:
      foodList = self.getFoodYouAreDefending(successor).asList()
      dist = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['byFood'] = dist

      # At the start, will rush to the capsule and try to defend. If capsule
      # gets eaten, the agent does its very best to attack the enemy ghosts
      capsules = self.getCapsulesYouAreDefending(successor)
      if len(capsules) > 0:
          features['byCapsule'] = min([self.getMazeDistance(myPos, capsule) for capsule in capsules])
          if len(self.observationHistory) > 10:
            moveHistory = [self.observationHistory[-1*i].getAgentState(self.index).getPosition() for i in range(1,10)]

      # if the capsule has been eaten, we should guard ceratin areas based on our color
      else:

        # We should guard the two lanes that are closer to each other and let
        # the offensive agent guard the lane that is further away once we are
        # winning. If we are red, that means we want to guard the lower two lanes.
        if self.red:
          topGuardPoint = (12, 6)
          bottomGuardPoint = (7, 1)
        else:
          topGuardPoint = (26, 13)
          bottomGuardPoint = (19, 9)

        # Before we even look at move history or anything else, we want to be sure
        # that we are attacking invaders if there are any.
        features['numInvaders'] = len(invaders)

        # I imagine it would be impossible to eat the capsule in under 10 moves,
        # but the trend in this AI code is that it's better to be safe than sorry.
        # Hence, we get this if statement to make sure there is adequate history length.
        if len(self.observationHistory) > 10:
          moveHistory = [self.observationHistory[-1*i].getAgentState(self.index).getPosition() for i in range(1,10)]

          # For the sake of derivatives and determing the change in direction,
          # we look to the move most recently performed and then the move we did
          # four turns ago. In the offensive agent we are comparing y values for
          # simplicity, here we are going to compare there x values as the defensive
          # agent should be moving more left and right than up and down around
          # the two lanes.
          one_move_ago = moveHistory[1][0] - moveHistory[0][0]
          four_moves_ago = moveHistory[4][0] - moveHistory[3][0]

          # if we are too far away from the bottomGuardPoint, then we should just
          # head there first. We want to get close to the guard points so then we can
          # start patrolling.
          if self.getMazeDistance(myPos, bottomGuardPoint) > 8:
            guardArea = self.getMazeDistance(myPos, bottomGuardPoint)
            features['guardArea'] = guardArea

          # When stopped and was moving right, now go left
          elif one_move_ago == 0 and four_moves_ago > 0:
            guardArea = self.getMazeDistance(myPos, bottomGuardPoint)
            features['guardArea'] = guardArea

          # When stopped and was moving left, now go right
          elif one_move_ago == 0 and four_moves_ago < 0:
            guardArea = self.getMazeDistance(myPos, topGuardPoint)
            features['guardArea'] = guardArea

    # We want to make sure that if the best action is to stop or to go in the
    # opposite direction that we assign a feature to that. This is a similar
    # behavior that baselineTeam does and we don't mind keeping it in here.
    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
    return {
        'numInvaders': -1000,
        'onDefense': 5000,
        'invaderDistance': -100,
        'stop': -100,
        'reverse': -2,
        'byCapsule': -10,
        'guardArea': -1
      }
