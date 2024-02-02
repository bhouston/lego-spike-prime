import app
import builtins
import hub
import motor
import runloop
import color
import math
import platform


print( f'platform.platform = {platform.platform}');
print( f'platform.libc_ver = {platform.libc_ver}');
print( f'platform.python_compiler = {platform.python_compiler}');


leftMotor = hub.port.D
rightMotor = hub.port.C

liftMotor = hub.port.B

# small wheels
wheelDiameterInCM = 5.6 # cm
wheelCircumferenceInCM = 17.5 # cm

# big wheels
#wheelDiameterInCM = 8.8 # cm
#wheelCircumferenceInCM = 27.6 # cm

import json

# generated via ChatGPT: https://chat.openai.com/share/e15a442f-1524-4915-a3d4-5a84e2bb16f3
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

async def wait( ms ):
    await runloop.sleep_ms(ms)

def sign( number ):
    if number >= 0:
        return 1
    else:
        return -1

def getShortedRotation( currentYaw, targetYaw ):
    deltaYaw = targetYaw - currentYaw
    return removeRotations( deltaYaw )

def removeRotations( yaw ):
    while yaw > 180:
        yaw -= 360
    while yaw < -180:
        yaw += 360
    return yaw

def radToDeg( rad ):
    return rad * 180 / math.pi

def degToRad( deg ):
    return deg * math.pi / 180


def getYaw():
    return hub.motion_sensor.tilt_angles()[0] / 10

def getPitch():
    return hub.motion_sensor.tilt_angles()[1] / 10

def getRollh():
    return hub.motion_sensor.tilt_angles()[1] / 10

def clamp( value, minimum, maximum ):
    return min( max( value, minimum ), maximum )

# works, but is a bit slow
def adaptiveVelocity( deltaPosition, minVelocity=100, maxVelocity=1000 ):
    deltaPositionSign = sign( deltaPosition );
    deltaPositionAbs = abs( deltaPosition )
    return int( round( clamp( deltaPositionAbs, minVelocity, maxVelocity ) * deltaPositionSign ))

def lerp( a, b, t ):
    return a * ( 1 - t ) + b * t

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

def move( leftVelocity, rightVelocity ):
    motor.run( rightMotor, rightVelocity )
    motor.run( leftMotor, leftVelocity )

# works
async def rotateToYaw( targetYaw ):
    hub.light.color( hub.light.POWER, color.ORANGE )
    currentYaw = getYaw()
    deltaYaw = getShortedRotation( currentYaw, targetYaw )
    while abs( deltaYaw ) > 1:
        currentVelocity = adaptiveVelocity( deltaYaw * 5, 50, 1000 )
        if( currentVelocity > 0 ):
            hub.light_matrix.show_image(hub.light_matrix.IMAGE_GO_RIGHT)
        else:
            hub.light_matrix.show_image(hub.light_matrix.IMAGE_GO_LEFT)
        move( currentVelocity, currentVelocity );
        await wait( 20 )
        currentYaw = getYaw()
        deltaYaw = getShortedRotation( currentYaw, targetYaw )

    hub.light_matrix.clear()
    move( 0, 0 )

# works
async def moveDistance( distanceInCM, targetYaw ):
    hub.light.color( hub.light.POWER, color.PURPLE )
    relativePosition = distanceInCM / wheelCircumferenceInCM * 360
    motor.reset_relative_position( leftMotor, 0 )
    motor.reset_relative_position( rightMotor, 0 )
    relativePositionRemaining = relativePosition
    while( abs( relativePositionRemaining ) > 0.5 ):
        if sign( relativePositionRemaining ) == 1:
            hub.light_matrix.show_image(hub.light_matrix.IMAGE_ARROW_S)
        else:
            hub.light_matrix.show_image(hub.light_matrix.IMAGE_ARROW_N)
        currentVelocity = adaptiveVelocity( relativePositionRemaining, 25, 800 )
        currentYaw = getYaw()
        deltaYaw = getShortedRotation( currentYaw, targetYaw );
        move( int( round( -currentVelocity * ( 1 - deltaYaw * 0.02 * sign( currentVelocity ) ))), currentVelocity )
        leftPosition = -motor.relative_position( leftMotor )
        rightPosition = motor.relative_position( rightMotor )
        averagePosition = ( leftPosition + rightPosition ) / 2;
        relativePositionRemaining = relativePosition - averagePosition
        await wait( 100 )
    move( 0, 0 )
    hub.light_matrix.clear()

currentX = 0 # in cm, assuming +x is 90 yaw
currentY = 0 # in cm, assuming +y is 0 yaw

async def moveTo( targetX, targetY, targetYaw ):
    global currentX
    global currentY
    deltaX = targetX - currentX
    deltaY = currentY - targetY 
    deltaDistance = ( deltaX ** 2 + deltaY ** 2 ) ** 0.5
    deltaYaw = 90 - radToDeg( math.atan2( deltaY, deltaX ) )
    await rotateToYaw( deltaYaw )
    await moveDistance( deltaDistance, deltaYaw )

    if( targetYaw != -1 ):
        await rotateToYaw( targetYaw )

    currentX = targetX
    currentY = targetY
    hub.light_matrix.show_image(hub.light_matrix.IMAGE_GHOST)
    await wait( 1000 )
    hub.light_matrix.clear()

async def moveStraight( deltaDistance ):
    global currentX
    global currentY
    yaw = getYaw()
    await moveDistance( deltaDistance, yaw )
    # probably wrong
    currentX += deltaDistance * math.sin( yaw )
    currentY += deltaDistance * math.cos( yaw )
   
currentLiftHeight = 0

async def resetLiftDown():
    await motor.run_to_relative_position( liftMotor, -3000, 1000 )
    motor.reset_relative_position( liftMotor, 0 )

async def liftHeight( targetLiftHeight ):
    global currentLiftHeight;
    deltaHeight = targetLiftHeight - currentLiftHeight
    await motor.run_to_relative_position( liftMotor, deltaHeight, 500 )
    currentLiftHeight = targetLiftHeight

async def main():
    await start()
    await resetLiftDown()
    motor.reset_relative_position( leftMotor, 0 )
    motor.reset_relative_position( rightMotor, 0 )
    hub.motion_sensor.reset_yaw( 0 )
    hub.light.color( hub.light.POWER, color.RED )

    await moveTo( -55, -38, -1)
    await liftHeight( 2000 )

    await moveTo( -65, 32, -1)
    await liftHeight( 0 )
    await moveStraight( -30 )

    await finish()

runloop.run(main())

builtins.

