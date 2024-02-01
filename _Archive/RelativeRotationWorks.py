import app
import hub
import motor
import motor_pair
import runloop
import color

leftMotor = hub.port.D
rightMotor = hub.port.C

# small wheels
wheelDiameterInCM = 5.6 # cm
wheelCircumferenceInCM = 17.5 # cm

# big wheels
#wheelDiameterInCM = 8.8 # cm
#wheelCircumferenceInCM = 27.6 # cm

async def wait( ms ):
    await runloop.sleep_ms(ms)

def sign( number ):
    if number >= 0:
        return 1
    else:
        return -1

# works
async def start():
    hub.light.color( hub.light.POWER, color.WHITE )
    for countDown in range(3, 0, -1):
        hub.sound.beep(783, 200, 50)
        await hub.light_matrix.write(str(countDown))
        await wait(1000)
    hub.light_matrix.show_image(hub.light_matrix.IMAGE_HAPPY)
    await hub.sound.beep(1567, 1000, 50)
    hub.light_matrix.clear();

# works
async def finish():
    app.sound.play('Applause 1')
    hub.light_matrix.show_image(hub.light_matrix.IMAGE_HAPPY)
    hub.light.color( hub.light.POWER, color.GREEN )
    await hub.sound.beep(1567, 500, 50)
    await hub.sound.beep(783, 500, 50)

def move( velocity, steering ):
    motor_pair.move( motor_pair.PAIR_1, steering, velocity=velocity)

def getShortedRotation( currentYaw, targetYaw ):
    deltaYaw = targetYaw - currentYaw
    return removeRotations( deltaYaw )

def removeRotations( yaw ):
    while yaw > 180:
        yaw -= 360
    while yaw < -180:
        yaw += 360
    return yaw

def getYaw():
    return hub.motion_sensor.tilt_angles()[0] / 10

def getPitch():
    return hub.motion_sensor.tilt_angles()[1] / 10

def getRollh():
    return hub.motion_sensor.tilt_angles()[1] / 10

# works
async def rotateToYaw( targetYaw, velocity ):
    hub.light.color( hub.light.POWER, color.ORANGE )
    currentYaw = getYaw()
    deltaYaw = getShortedRotation( currentYaw, targetYaw )
    while abs( deltaYaw ) > 1:
        currentVelocity = adaptiveVelocity( abs( deltaYaw * 5 ), velocity, 50 )
        if( deltaYaw > 0 ):
            hub.light_matrix.show_image(hub.light_matrix.IMAGE_GO_RIGHT)
            move( currentVelocity, -100 )
        else:
            hub.light_matrix.show_image(hub.light_matrix.IMAGE_GO_LEFT)
            move( currentVelocity, 100 )
        currentYaw = getYaw()
        deltaYaw = getShortedRotation( currentYaw, targetYaw )
    hub.light_matrix.clear()
    move( 0, 0 )

# works
async def spin( speed, time_ms ):
    move( speed, 100 )
    await wait( time_ms )
    move( 0, 0 )

# works, but is a bit slow
def adaptiveVelocity( deltaPosition, maxVelocity=1000, minVelocity=100 ):
    return int( round( max( min( deltaPosition, min( maxVelocity, 1000 ) ), minVelocity ) ))

# works
async def moveDistance( distanceInCM, velocity ):
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
        move( adaptiveVelocity( abs( relativePositionRemaining ), velocity, 25 ) * sign( relativePositionRemaining ), 0 )
        leftPosition = -motor.relative_position( leftMotor )
        rightPosition = motor.relative_position( rightMotor )
        averagePosition = ( leftPosition + rightPosition ) / 2;
        relativePositionRemaining = relativePosition - averagePosition
    move( 0, 0 )
    hub.light_matrix.clear()

async def main():
    await start()
    motor_pair.pair(motor_pair.PAIR_1, leftMotor, rightMotor)
    motor.reset_relative_position( leftMotor, 0 )
    motor.reset_relative_position( rightMotor, 0 )
    hub.motion_sensor.reset_yaw( 0 )
    hub.light.color( hub.light.POWER, color.RED )

    for i in range(0,4): 
        await hub.light_matrix.write(str(i))
        await wait(1000)
        await rotateToYaw( i*90, 1000 )
        #await wait( 250 )
        await moveDistance( 50, 1000 )
        await rotateToYaw( i*90, 1000 )
        #await wait( 250 )
        await moveDistance( -25, 1000 )
        await rotateToYaw( i*90, 1000 )
        #await wait( 250 )

    await rotateToYaw( 0, 1000 )
    await finish()

runloop.run(main())
