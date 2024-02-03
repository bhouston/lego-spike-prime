
import app
import hub
import motor
import runloop
import color
import math
import json


leftMotor = hub.port.A
rightMotor = hub.port.B

liftMotor = hub.port.E

# small wheels
#wheelDiameterInCM = 5.6 # cm
#wheelCircumferenceInCM = 17.5 # cm

# big wheels
wheelDiameterInCM = 8.8 # cm
wheelCircumferenceInCM = 27.6 # cm


def log(item):
    # Check if the item is a string or a number (int or float)
    if isinstance(item, (str, int, float)):
        print(item)
    # Check if the item is an object that can be serialized to JSON
    elif isinstance(item, (dict, list)):
        print(json.dumps(item))
    else:
        # If the item is neither, print an error message
        print("Error: Unsupported type for logging.")

def sign( number ):
    if number >= 0:
        return 1
    else:
        return -1

async def wait( ms ):
    await runloop.sleep_ms(ms)

def removeRotations( yaw ):
    while yaw > 180:
        yaw -= 360
    while yaw < -180:
        yaw += 360
    return yaw

def getShortedRotation( currentYaw, targetYaw ):
    deltaYaw = targetYaw - currentYaw
    return removeRotations( deltaYaw )

def radToDeg( rad ):
    return rad * 180 / math.pi

def degToRad( deg ):
    return deg * math.pi / 180

# S-curve profile, returns the current velocity
def SProfile( currentDistance, totalDistance, minVelocity, maxVelocity, maxAcceleration ):
    assert( currentDistance >= 0 )
    #assert( totalDistance >= currentDistance )
    assert( maxVelocity > 0 )
    assert( maxVelocity > minVelocity )
    assert( minVelocity >= 0)
    assert( maxAcceleration > 0)

    remainingDistance = totalDistance - currentDistance

    # max transition distance
    maxTransitionDistance = totalDistance / 2

    # calculate the accel and deceleration distances
    transitionDistance = min( maxTransitionDistance, maxVelocity * maxVelocity / ( 2 * maxAcceleration ) )

    # we are in the acceleration phase
    if( currentDistance <= transitionDistance ):
        # we are in the acceleration phase
        return max(minVelocity, maxAcceleration * currentDistance )

    if( remainingDistance <= transitionDistance ):
        # we are in the deceleration phase
        return max(minVelocity, maxAcceleration * remainingDistance)

    # we are in the constant velocity phase (which if it exists, is between the acceleration and deceleration phases)
    return maxVelocity

def getYaw():
    return hub.motion_sensor.tilt_angles()[0] / 10

# works
async def moveStraight( distanceInCM, yaw ):
    hub.light.color( hub.light.POWER, color.PURPLE )

    totalRotationsInDegrees = distanceInCM / wheelCircumferenceInCM * 360
    motor.reset_relative_position( leftMotor, 0 )
    motor.reset_relative_position( rightMotor, 0 )

    remainingRotationsInDegrees = totalRotationsInDegrees
    currentRotationInDegrees = 0
    frequency = 20
    periodInMS = 1000 / frequency
    currentLeftRotationsInDegrees = 0
    currentRightRotationsInDegrees = 0
    i = 0
    while( remainingRotationsInDegrees > 0 ):
        if sign( remainingRotationsInDegrees ) == 1:
            hub.light_matrix.show_image(hub.light_matrix.IMAGE_ARROW_S)
        else:
            hub.light_matrix.show_image(hub.light_matrix.IMAGE_ARROW_N)

        currentVelocity = SProfile( currentRotationInDegrees, totalRotationsInDegrees, 10, 500, 100 )
        app.linegraph.plot( 0, i, currentVelocity );

        #motor.run( rightMotor, currentVelocity )
        #motor.run( leftMotor, currentVelocity )
        await wait( int( periodInMS ) )

        currentLeftRotationsInDegrees += currentVelocity * periodInMS / 1000 # -motor.relative_position( leftMotor )
        currentRightRotationsInDegrees += currentVelocity * periodInMS / 1000 # motor.relative_position( rightMotor )

        currentRotationInDegrees = ( currentLeftRotationsInDegrees + currentRightRotationsInDegrees ) / 2
        remainingRotationsInDegrees = totalRotationsInDegrees - currentRotationInDegrees
        app.linegraph.plot( 1, i, currentRotationInDegrees );
        app.linegraph.plot( 2, i, remainingRotationsInDegrees );
        app.linegraph.plot( 3, i, totalRotationsInDegrees );

        i += 1

    motor.run( rightMotor, 0 )
    motor.run( leftMotor, 0 )

    hub.light_matrix.clear()

# works
async def start():
    hub.light.color( hub.light.POWER, color.WHITE )
    for countDown in range(3, 0, -1):
        hub.sound.beep(783, 200, 50)
        await hub.light_matrix.write(str(countDown))
        await wait(1000)
    hub.light_matrix.show_image(hub.light_matrix.IMAGE_HAPPY)
    await hub.sound.beep(1567, 1000, 50)
    hub.light_matrix.clear()

# works
async def finish():
    app.sound.play('Applause 1')
    hub.light_matrix.show_image(hub.light_matrix.IMAGE_HAPPY)
    hub.light.color( hub.light.POWER, color.GREEN )
    await hub.sound.beep(1567, 500, 50)
    await hub.sound.beep(783, 500, 50)

async def liftDown():
    motor.reset_relative_position( liftMotor, 0 )
    await motor.run_to_relative_position( liftMotor, -1000, 1000 )

async def liftUp():
    motor.reset_relative_position( liftMotor, 0 )
    await motor.run_to_relative_position( liftMotor, 1000, 1000 )


async def main():
    app.linegraph.clear_all()
    app.linegraph.show( False )
    await start()
    await liftUp()
    await liftUp()
    #await moveStraight( 100, 0 )
    #motor.run( leftMotor, 2000 );
    #motor.run( rightMotor, -2000 );
    #await wait( 250 );
    #motor.run( leftMotor, -2000 );
    #motor.run( rightMotor, 2000 );
    #await wait( 500 );
    #motor.run( leftMotor, 0 );
    #motor.run( rightMotor, 0 );
    #await wait( 1000 );
    #await liftUp()
    #await finish()
    await liftDown()
    await liftDown()

runloop.run( main() )