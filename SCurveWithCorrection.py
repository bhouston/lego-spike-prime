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

def rotationSpeedToLargeMotorPWM( rotationSpeed: float ):
    assert rotationSpeed >= 0

    # solved via: https://docs.google.com/spreadsheets/d/1fMy7IWmIwwSYXO3f4HmrwL1FzmLGRcA1NbI71U6MwQ8/edit#gid=549077105
    return ( rotationSpeed * 360 + 12.12025332 ) / 0.01207307271

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

def motorSetRotationSpeed( motorIndex: int, rotationSpeed: float ):
    assert motorIndex == 0 or motorIndex == 1
    assert rotationSpeed >= 0

    port = motorPorts[ motorIndex ]
    direction = motorDirections[ motorIndex ]
    motor.set_duty_cycle( port, int( rotationSpeedToLargeMotorPWM( rotationSpeed ) * direction ) )

def motorGetRotations( motorIndex: int ):
    assert motorIndex == 0 or motorIndex == 1

    port = motorPorts[ motorIndex ]
    direction = motorDirections[ motorIndex ]
    return motor.relative_position( port ) * direction / 360

def motorResetRotations( motorIndex: int, position: float ):
    assert motorIndex == 0 or motorIndex == 1

    motorPort = motorPorts[ motorIndex ]
    direction = motorDirections[ motorIndex ]
    motor.reset_relative_position( motorPort, int( position * direction * 360 ) )

# Based on: https://chat.openai.com/share/a2abb404-0bb0-44d3-9e05-e43122645c8a

# S-curve profile, returns the current velocity
def getSProfileSpeed(x: float, d: float, v: float, a: float, msv: float):
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
async def moveGeneric( rotations: float, directionName: str = "forward", speed: float = 1, acceleration: float = 1, minSpeed: float = 0.1 ):
    assert rotations >= 0

    motorsSetDirection( directionName )
    motorResetRotations( 0, 0 )
    motorResetRotations( 1, 0 )

    remainingRotations = rotations
    deltaRotations = 0

    while( remainingRotations > 0 ):
        rotationSpeed = getSProfileSpeed( clamp( rotations - remainingRotations, 0, rotations ), rotations, speed, acceleration, minSpeed )
        
        motorSetRotationSpeed( 0, clamp( rotationSpeed + deltaRotations * 0.5, 0, 10000 ) )
        motorSetRotationSpeed( 1, clamp( rotationSpeed - deltaRotations * 0.5, 0, 10000 ) )

        await wait( correctPeriod )

        leftMotorRotations = motorGetRotations( 0 )
        rightMotorRotations = motorGetRotations( 1 )

        deltaRotations = ( rightMotorRotations - leftMotorRotations )

        remainingRotations = clamp( rotations - ( rightMotorRotations + leftMotorRotations ) / 2, 0, rotations )

    motorSetRotationSpeed( 0, 0 )
    motorSetRotationSpeed( 1, 0 )

async def moveStraight( distance: float, directionName: str ):
    await moveGeneric( distance / wheelCircumference, directionName )

async def forward( distance: float ):
    await moveStraight( distance, "forward" )

async def backward( distance: float ):
    await moveStraight( distance, "backward" )

async def turn( degrees: float, directionName: str ):
    distance = ( degrees / 360 ) * turnCircumference
    await moveGeneric( distance / wheelCircumference, directionName )

async def turnLeft( degrees: float = 90 ):
    await turn( degrees, "left" )

async def turnRight( degrees: float = 90 ):
    await turn( degrees, "right" )


async def main():

    # sequence of moves to make a square, end up exactly where one started
    await forward( 0.5 )
    await wait( 1 )
    await turnRight( 90 )
    await wait( 1 )
    await forward( 0.5 )
    await wait( 1 )
    await turnLeft( 90 )
    await wait( 1 )
    await backward( 0.5 )
    await wait( 1 )
    await turnLeft( 90 )
    await wait( 1 )
    await forward( 0.5 )
    await wait( 1 )
    await turnRight( 90 )

async def rotationTest():
    for degrees in range(0,12):
        await turnLeft( 90 )
        await wait( 1 )

runloop.run( rotationTest() )