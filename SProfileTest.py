import math
from enum import Enum

def clamp( value, minimum, maximum ):
    return min( max( value, minimum ), maximum )

# Based on: https://chat.openai.com/share/a2abb404-0bb0-44d3-9e05-e43122645c8a

# S-curve profile, returns the current velocity
def sProfileInstantaneousVelocity(x, d, a, v, msv):
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
            return max( (2 * a * (d - x)), 0 ) ** 0.5
    else:
        # If the robot reaches its maximum velocity
        dc = d - total_acc_dec_distance
        
        if x < da:  # Acceleration phase
            return max( msv, (2 * a * x) ** 0.5 )
        elif x < da + dc:  # Constant velocity phase
            return v
        else:  # Deceleration phase
            return max( (2 * a * (d - x)), 0 ) ** 0.5

def sProfileAverageVelocity(x, d, a, v, ts):
    def phase_velocity(position):
        # Calculate distance covered during acceleration (or deceleration)
        da = v**2 / (2 * a)
        total_acc_dec_distance = 2 * da
        if total_acc_dec_distance >= d:
            vmax = (a * d) ** 0.5
            if position <= d / 2:
                return (2 * a * position) ** 0.5, 'acc'
            else:
                return max((2 * a * (d - position)), 0) ** 0.5, 'dec'
        else:
            dc = d - total_acc_dec_distance
            if position < da:
                return (2 * a * position) ** 0.5, 'acc'
            elif position < da + dc:
                return v, 'const'
            else:
                return max( (2 * a * (d - position)), 0) ** 0.5, 'dec'

    # Calculate the velocity at the starting position
    initial_velocity, phase = phase_velocity(x)
    
    # Estimate the distance traveled during the time step
    if phase == 'acc' or phase == 'dec':
        # Calculate acceleration or deceleration effect
        delta_x = initial_velocity * ts + 0.5 * a * ts**2 if phase == 'acc' else initial_velocity * ts - 0.5 * a * ts**2
    else:
        delta_x = initial_velocity * ts

    # Adjust delta_x to not exceed total distance
    delta_x = min(delta_x, d - x)
    
    # Calculate the velocity at the end of the time step
    final_velocity, _ = phase_velocity(x + delta_x)
    
    # Compute the average velocity
    average_velocity = (initial_velocity + final_velocity) / 2
    
    return average_velocity

totalDistance = 1000
currentDistanceViaInstantaneous = 0
currentDistanceViaAverage = 0
minStartVelocity = 5
maxVelocity = 500
maxAcceleration = 800

timeStep = 0.01
time = 0
while( currentDistanceViaInstantaneous <= totalDistance * 1.01 or currentDistanceViaAverage <= totalDistance * 1.01):
    instantaneousVelocity = sProfileInstantaneousVelocity( currentDistanceViaInstantaneous, totalDistance,maxAcceleration, maxVelocity, minStartVelocity )
    averageVelocity = sProfileAverageVelocity( currentDistanceViaAverage, totalDistance, maxAcceleration, maxVelocity, timeStep )
    
    instantaneousVelocity = min( instantaneousVelocity, ( totalDistance - currentDistanceViaInstantaneous ) / timeStep )
    averageVelocity = min( averageVelocity, ( totalDistance - currentDistanceViaAverage ) / timeStep )
    
    print( time, ',', currentDistanceViaInstantaneous, ',', instantaneousVelocity, ',', currentDistanceViaAverage, ',', averageVelocity )

    currentDistanceViaInstantaneous += instantaneousVelocity * timeStep
    currentDistanceViaAverage += averageVelocity * timeStep
    time += timeStep



