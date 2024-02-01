import app
import hub
import motor
import motor_pair
import runloop

leftMotor = hub.port.D
rightMotor = hub.port.C

# small wheels
# wheelDiameterInCM = 5.6 # cm
# wheelCircumferenceInCM = 17.5 # cm

# big wheels
wheelDiameterInCM = 8.8 # cm
wheelCircumferenceInCM = 27.6 # cm

# works
async def start():
    for countDown in range(3, 0, -1):
        hub.sound.beep(783, 200, 50)
        await hub.light_matrix.write(str(countDown))
        await runloop.sleep_ms(1000)
    hub.sound.beep(1567, 1000, 50)
    hub.light_matrix.clear();

# works
async def finish():
    app.sound.play('Applause 1')
    hub.light_matrix.show_image(hub.light_matrix.IMAGE_HAPPY)

def move( velocity, steering ):
    motor_pair.move( motor_pair.PAIR_1, steering, velocity=velocity)

# works
async def rotateToYaw( yawInDegrees, velocity ):
    currentYaw = hub.motion_sensor.tilt_angles()[0] / 10
    deltaYaw = yawInDegrees - currentYaw
    while abs( deltaYaw ) > 1:
        correction = deltaYaw / 180
        currentVelocity = adaptiveVelocity( abs( deltaYaw * 5 ), velocity )
        if( correction > 0 ):
            hub.light_matrix.show_image(hub.light_matrix.IMAGE_GO_RIGHT)
            move( currentVelocity, -100 )
        else:
            hub.light_matrix.show_image(hub.light_matrix.IMAGE_GO_LEFT)
            move( currentVelocity, 100 )
        await runloop.sleep_ms( 50 )
        currentYaw = hub.motion_sensor.tilt_angles()[0] / 10
        deltaYaw = yawInDegrees - currentYaw

    hub.light_matrix.clear()
    move( 0, 0 )

# works
async def spin( speed, time_ms ):
    move( speed, 100 )
    await runloop.sleep_ms( time_ms )
    move( 0, 0 )

# works, but is a bit slow
def adaptiveVelocity( deltaPosition, maxVelocity ):
    return int( round( max( min( deltaPosition, min( maxVelocity, 1000 ) ), 50 ) ))

# works
async def moveDistance( distanceInCM, velocity ):
    relativePosition = distanceInCM / wheelCircumferenceInCM * 360
    motor.reset_relative_position( leftMotor, 0 )
    motor.reset_relative_position( rightMotor, 0 )
    relativePositionRemaining = relativePosition
    hub.light_matrix.show_image(hub.light_matrix.IMAGE_ARROW_S)
    while( relativePositionRemaining > 0 ):
        move( adaptiveVelocity( relativePositionRemaining, velocity ), 0 )
        leftPosition = motor.relative_position( leftMotor )
        rightPosition = motor.relative_position( rightMotor )
        averagePosition = ( abs( leftPosition ) + abs( rightPosition ) ) / 2;
        relativePositionRemaining = relativePosition - averagePosition
        print(relativePositionRemaining)
        await runloop.sleep_ms( 50 )
    move( 0, 0 )
    hub.light_matrix.clear()

async def main():
    await start()
    motor_pair.pair(motor_pair.PAIR_1, leftMotor, rightMotor)
    motor.reset_relative_position( leftMotor, 0 )
    motor.reset_relative_position( rightMotor, 0 )
    hub.motion_sensor.reset_yaw( 0 )
    await rotateToYaw( 0, 500 )
    await rotateToYaw( 180, 500 )
    await rotateToYaw( 90, 500 )
    await moveDistance( 50, 1000 )
    await rotateToYaw( -90, 500 )
    await moveDistance( 50, 1000 )
    await finish()

runloop.run(main())
