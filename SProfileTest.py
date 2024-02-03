import math
from enum import Enum

def clamp( value, minimum, maximum ):
    return min( max( value, minimum ), maximum )

# Based on: https://chat.openai.com/share/a2abb404-0bb0-44d3-9e05-e43122645c8a

# S-curve profile, returns the current velocity
def sProfileVelocity_Internal(x, d, a, v, msv):
    # Calculate distance covered during acceleration (or deceleration)
    da = v**2 / (2 * a)
    
    # Total distance for acceleration and deceleration phases
    total_acc_dec_distance = 2 * da
    
    # Check if the total distance is greater than the path distance
    if total_acc_dec_distance >= d:
        # The robot never reaches full velocity, adjust calculations
        if x <= d / 2:
            # Acceleration phase
            return max( msv, (2 * a * x) ** 0.5 )
        else:
            # Deceleration phase
            return (2 * a * (d - x)) ** 0.5
    else:
        # If the robot reaches its maximum velocity
        dc = d - total_acc_dec_distance
        
        if x < da:  # Acceleration phase
            return max( msv, (2 * a * x) ** 0.5 )
        elif x < da + dc:  # Constant velocity phase
            return v
        else:  # Deceleration phase
            return (2 * a * (d - x)) ** 0.5

def sProfileVelocity( currentDistance, totalDistance, maxAcceleration, maxVelocity, minStartVelocity):
    return sProfileVelocity_Internal( currentDistance, totalDistance, maxAcceleration, maxVelocity, minStartVelocity )

def constantVelocity( currentDistance, totalDistance, maxAcceleration, maxVelocity, minStartVelocity):
    return maxVelocity

def adaptiveVelocity( currentDistance, totalDistance, maxAcceleration, maxVelocity, minStartVelocity):
    deltaPosition = totalDistance - currentDistance
    deltaPositionSign = math.sign( deltaPosition )
    deltaPositionAbs = abs( deltaPosition )
    return int( round( clamp( deltaPositionAbs, minVelocity, maxVelocity ) * deltaPositionSign ))

class VelocityMode(Enum):
    SProfile = 1
    Adaptive = 2
    Constant = 3

def getVelocity( mode, currentDistance, totalDistance, maxAcceleration, maxVelocity, minStartVelocity):
    if mode == VelocityMode.SProfile:
        return sProfileVelocity( currentDistance, totalDistance, maxAcceleration, maxVelocity, minStartVelocity )
    
    if mode == VelocityMode.Adaptive:
        return adaptiveVelocity( currentDistance, totalDistance, maxAcceleration, maxVelocity, minStartVelocity )

    if mode == VelocityMode.Constant:    
        return constantVelocity( currentDistance, totalDistance, maxAcceleration, maxVelocity, minStartVelocity )

    # throw error
    return 0

totalDistance = 1000
currentDistance = 0
minStartVelocity = 10
maxVelocity = 100
maxAcceleration = 800

timeStep = 0.01
time = 0
while( currentDistance < totalDistance ):
    currentVelocity = sProfileVelocity( currentDistance, totalDistance,maxAcceleration, maxVelocity, minStartVelocity )
    # adjust velocity to hit target in given timeStep if at the end
    if currentDistance + currentVelocity * timeStep > totalDistance:
        currentVelocity = (totalDistance - currentDistance) / timeStep
    currentDistance += currentVelocity * timeStep
    time += timeStep
    print( time, ',', currentDistance, ',', currentVelocity )



