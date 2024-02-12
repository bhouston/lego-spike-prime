import math
import app
import hub
import motor
import runloop
import color
import math
import json
import time

motorPorts = [ hub.port.A, hub.port.B ]
motorDirections = [ -1, 1 ]


# small wheels
#wheelDiameter = 5.6 * 0.01 # cm
#wheelCircumference = 17.5 * 0.01 # cm

# big wheels
wheelDiameter = 8.8 * 0.01 # meters
wheelCircumference = 27.6 * 0.01 # meters
wheelBase = 12.5 * 0.01 # meters
turnCircumference = wheelBase * math.pi

correctHertz = 1000
correctPeriod = 1 / correctHertz


def clamp( value: float, minimum: float, maximum: float ):
    assert minimum <= maximum

    return min( max( value, minimum ), maximum )

async def wait( seconds: float ):
    assert seconds > 0

    await runloop.sleep_ms( int( seconds * 1000 ) )

def getLargeMotorPwmForVelocity( velocity: float ):
    assert velocity >= 0

    # solved via: https://docs.google.com/spreadsheets/d/1fMy7IWmIwwSYXO3f4HmrwL1FzmLGRcA1NbI71U6MwQ8/edit#gid=549077105
    return ( velocity + 12.12025332 ) / 0.01207307271

def motorsSetDirection( directionName: str ):
    if( directionName == "forward" ):
        motorDirections[ 0 ] = -1
        motorDirections[ 1 ] = 1

    elif( directionName == "backward" ):
        motorDirections[ 0 ] = 1
        motorDirections[ 1 ] = -1

    elif( directionName == "left" ):
        motorDirections[ 0 ] = 1
        motorDirections[ 1 ] = 1

    elif( directionName == "right"):
        motorDirections[ 0 ] = -1
        motorDirections[ 1 ] = -1

    else:
        raise Exception( "Unsupported directionName: " + directionName )

def motorSetVelocity( motorIndex: int, velocity: float ):
    #print( "motorIndex", motorIndex, "velocity", velocity)
    #assert motorIndex == 0 or motorIndex == 1
    #assert velocity >= 0

    port = motorPorts[ motorIndex ]
    direction = motorDirections[ motorIndex ]
    motor.set_duty_cycle( port, int( getLargeMotorPwmForVelocity( velocity ) * direction ) )

def motorGetPosition( motorIndex: int ):
    assert motorIndex == 0 or motorIndex == 1

    port = motorPorts[ motorIndex ]
    direction = motorDirections[ motorIndex ]
    return motor.relative_position( port ) * direction

def motorResetPosition( motorIndex: int, position: float ):
    assert motorIndex == 0 or motorIndex == 1

    motorPort = motorPorts[ motorIndex ]
    direction = motorDirections[ motorIndex ]
    motor.reset_relative_position( motorPort, int( position * direction ) )

# Based on: https://chat.openai.com/share/a2abb404-0bb0-44d3-9e05-e43122645c8a

# S-curve profile, returns the current velocity
def sProfileInstantaneousVelocity(x: float, d: float, a: float, v: float, msv: float):
    assert d >= 0
    assert a >= 0
    assert v >= 0
    assert msv >= 0

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

        if x < da:# Acceleration phase
            return max( msv, (2 * a * x) ** 0.5 )
        elif x < da + dc:# Constant velocity phase
            return v
        else:# Deceleration phase
            return max( (2 * a * (d - x)), 0 ) ** 0.5


# TODO:
# - Read from the gyro and use this to also correct the rotation
async def move( totalRotations: float, directionName: str = "forward", velocity: float = 500, acceleration: float = 100):
    assert totalRotations >= 0

    motorsSetDirection( directionName )
    motorResetPosition( 0, 0 )
    motorResetPosition( 1, 0 )

    remainingRotations = totalRotations
    deltaVelocity = 0

    while( remainingRotations > 0 ):
        instantaneousVelocity = sProfileInstantaneousVelocity( clamp( totalRotations - remainingRotations, 0, totalRotations ), totalRotations, acceleration, velocity, 10 )
        
        motorSetVelocity( 0, clamp( instantaneousVelocity + deltaVelocity * 0.5, 0, 10000 ) )
        motorSetVelocity( 1, clamp( instantaneousVelocity - deltaVelocity * 0.5, 0, 10000 ) )

        await wait( correctPeriod )

        leftMotorRotations = motorGetPosition( 0 )
        rightMotorRotations = motorGetPosition( 1 )

        deltaVelocity = ( rightMotorRotations - leftMotorRotations )

        remainingRotations = clamp( totalRotations - ( rightMotorRotations + leftMotorRotations ) / 2, 0, totalRotations )

    motorSetVelocity( 0, 0 )
    motorSetVelocity( 1, 0 )

async def moveForward( distance: float ):
    await move( distance / wheelCircumference * 360, "forward", 25, 50 )

async def moveBackward( distance: float ):
    await move( distance / wheelCircumference * 360, "backward", 25, 50 )

async def turnLeft( degrees: float = 90 ):
    distance = turnCircumference * degrees / 360
    await move( distance / wheelCircumference * 360, "left", 25, 50 )

async def turnRight( degrees: float = 90 ):
    distance = turnCircumference * degrees / 360 * 0.5
    await move( distance / wheelCircumference * 360, "right", 25, 50 )


async def main():

    # sequence of moves to make a square, end up exactly where one started
    await moveForward( 0.5 )
    await wait( 1 )
    await turnRight( 90 )
    await wait( 1 )
    await moveForward( 0.5 )
    await wait( 1 )
    await turnLeft( 90 )
    await wait( 1 )
    await moveBackward( 0.5 )
    await wait( 1 )
    await turnLeft( 90 )
    await wait( 1 )
    await moveForward( 0.5 )
    await wait( 1 )
    await turnRight( 90 )

async def rotationTest():
    for degrees in range(0,12):
        await turnLeft( 90 )
        await wait( 1 )

runloop.run( rotationTest() )