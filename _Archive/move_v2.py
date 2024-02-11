import math
import app
import hub
import motor
import runloop
import color
import math
import json

from enum import Enum

leftMotor = hub.port.A
rightMotor = hub.port.B

# small wheels
#wheelDiameterInCM = 5.6 # cm
#wheelCircumferenceInCM = 17.5 # cm

# big wheels
wheelDiameterInCM = 8.8 # cm
wheelCircumferenceInCM = 27.6 # cm

correctHertz = 20
correctPeriodInMS = 1000 / correctHertz


def clamp( value, minimum, maximum ):
    return min( max( value, minimum ), maximum )

async def wait( ms ):
    await runloop.sleep_ms(ms)

# solved via: https://docs.google.com/spreadsheets/d/1fMy7IWmIwwSYXO3f4HmrwL1FzmLGRcA1NbI71U6MwQ8/edit#gid=549077105
def getLargeMotorPwmForVelocity( velocity ):
    return ( velocity + 12.12025332 ) / 0.01207307271


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


# TODO: 
# - Try to ensure both wheels are have the same number of rotations, otherwise apply a correction factor
# - Read from the gyro and use this to also correct the rotation
async def moveForward( distanceInCM ):
    hub.light.color( hub.light.POWER, color.PURPLE )

    leftRightCorrection = 1

    totalRotations = distanceInCM / wheelCircumferenceInCM * 360
    remainingRotations = totalRotations
    
    while( remainingRotations > 0 ):
        
        instantaneousVelocity = sProfileInstantaneousVelocity(
                totalRotations - remainingRotations, totalRotations,
                100, 1000, 50 )

        motor.run( rightMotor, instantaneousVelocity )
        motor.run( leftMotor, instantaneousVelocity )
        await wait( int( correctPeriodInMS ) )

        leftMotorRotations = motor.relative_position( leftMotor / leftRightCorrection )
        rightMotorRotations = motor.relative_position( rightMotor * leftRightCorrection )

        leftRightCorrection = clamp( leftMotorRotations / rightMotorRotations, 0.9, 1 / 0.9 ) # we could look at the remaining time and look to make it up in a certain amount of time?
        remainingRotations = totalRotations - ( rightMotorRotations + rightMotorRotations ) / 2

    motor.run( rightMotor, 0 )
    motor.run( leftMotor, 0 )

    hub.light_matrix.clear()

    # instantaneousVelocity = sProfileInstantaneousVelocity( currentDistanceViaInstantaneous, totalDistance, maxAcceleration, maxVelocity, minStartVelocity )

async def main():
    await moveForward( 100 )
    await moveForward( 100 )
    await moveForward( 100 )

runloop.run( main() )