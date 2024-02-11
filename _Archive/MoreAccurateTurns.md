# More Accurate Movement


Currently I am running into issues where my robot overshoots the target endpoint and then needs to backup and then it overshoots and then it goes forward and overshoots.

I also have to deal with motors who do not move unless they overcome some type of friction, thus 
I have a floor on the motor strength I can use.

In many ways, I want to have the robot do a bunch of tests, and figure out the expected slowdown curve so that I can hit the exact designed position.

I guess one can just backup and then start to move forward at a certain speed and then start a deceleration at a certain distance from the end.

After each run, it should tell me how much it overshoot for that deceleration curve.

- The suggested approach is to:
  - Use an S-curve acceleration/deceleration curve that is also gyro corrected using PID.


From ChatGPT:

Implementing an S-curve velocity profile for precise robot movement involves several steps. The S-curve strategy smoothly ramps up acceleration to the maximum, maintains a constant acceleration until it's time to decelerate, then smoothly ramps down acceleration. This results in a motion profile that starts and ends gently but accelerates to and decelerates from a maximum velocity efficiently.

Given the interface to your motor and the specified function signature, I will write a Python function that adheres to these requirements. The function will use the S-curve profile to achieve precise control over the motor's movement.

Here's a high-level approach before diving into the code:

Initialization: Reset the motor's relative position to ensure we're starting from a known state.
Acceleration Phase: Gradually increase the motor's rotational velocity, following an S-curve profile until the maximum velocity is reached.
Constant Velocity Phase: Maintain the maximum velocity for the duration needed to approach the target position, taking into account the distance needed for deceleration.
Deceleration Phase: Gradually decrease the motor's rotational velocity, again following an S-curve, until the motor comes to a stop at the exact target position.
This approach requires calculating the distance (in degrees) for each phase based on the maximum velocity and maximum acceleration, and then applying the correct motor velocity at each step.

The following Python code is a conceptual implementation. It assumes you have a way to call resetMotorRelativePosition, setMotorRotationalVelocity, and getMotorRelativePosition within your robotics framework. The actual motion control logic, particularly for the S-curve acceleration and deceleration, will need to be adjusted based on your robot's performance characteristics.

```py
import time

def moveExact(relativeRotationalPosition, maximumVelocity, maxAcceleration):
    # Reset the motor's position to 0
    resetMotorRelativePosition(0)
    
    # Calculate the total distance to move
    totalDistance = relativeRotationalPosition
    
    # Calculate the distance for each phase (acceleration, constant, deceleration)
    # For simplicity, let's assume equal distance for acceleration and deceleration phases
    # This will need adjustment based on actual robot performance
    accelDistance = (maximumVelocity ** 2) / (4 * maxAcceleration)
    if 2 * accelDistance > totalDistance:
        # If we don't have enough distance to accelerate and decelerate, adjust the plan
        accelDistance = totalDistance / 2
        maximumVelocity = (2 * maxAcceleration * accelDistance) ** 0.5
    
    constantDistance = totalDistance - 2 * accelDistance
    
    # Acceleration phase
    currentVelocity = 0
    while getMotorRelativePosition() < accelDistance:
        currentVelocity += maxAcceleration * timeStep() # Increase velocity smoothly
        currentVelocity = min(currentVelocity, maximumVelocity) # Cap at max velocity
        setMotorRotationalVelocity(currentVelocity)
        time.sleep(timeStep())
    
    # Constant velocity phase
    while getMotorRelativePosition() < (accelDistance + constantDistance):
        setMotorRotationalVelocity(maximumVelocity)
        time.sleep(timeStep())
    
    # Deceleration phase
    while getMotorRelativePosition() < totalDistance:
        currentVelocity -= maxAcceleration * timeStep() # Decrease velocity smoothly
        currentVelocity = max(currentVelocity, 0) # Ensure velocity doesn't go negative
        setMotorRotationalVelocity(currentVelocity)
        time.sleep(timeStep())
    
    # Ensure the motor is stopped at the end
    setMotorRotationalVelocity(0)

def timeStep():
    # Returns the time step to use for acceleration/deceleration calculations
    # Adjust this based on how frequently you can update the motor's velocity
    return 0.01  # Example: 10ms time step
```

Note: This code is a basic conceptual framework. Real-world implementation will require fine-tuning based on the specifics of your robot, such as the responsiveness of the motor control system, the precision of timing functions, and the dynamics of the robot's movement. Testing and iterative adjustments will be essential to dial in the exact behavior needed to achieve precise movements with an S-curve profile.

Correcting for drift using a gyroscope involves adjusting the velocities of individual motors based on the deviation detected by the gyroscope, ensuring the robot moves straight. This correction is typically applied in a control loop, where the gyroscope's yaw (rotation around the vertical axis) is monitored continuously during movement. The feedback from the gyroscope is used to make real-time adjustments to the motor speeds. Here are some standard and effective methods for gyroscope correction:

## Proportional Control
The most straightforward approach is proportional control, where the correction applied is directly proportional to the error detected. This method is based on the simple principle: "the bigger the error, the bigger the correction."

```py
Kp = 0.1  # Proportional gain. This value needs to be tuned for your robot.

# Assume we're inside a loop that's moving the robot forward
yaw_error = getYaw()  # Get current yaw error
correction = Kp * yaw_error

left_motor_speed = desired_speed - correction
right_motor_speed = desired_speed + correction

setMotorRotationalVelocity(left_motor_id, left_motor_speed)
setMotorRotationalVelocity(right_motor_id, right_motor_speed)
```

## PID Control

For more precise control, a PID (Proportional-Integral-Derivative) controller can be used. This approach considers not only the current error (Proportional) but also the accumulation of past errors (Integral) and the rate at which the error is changing (Derivative). PID control is more complex but can provide smoother and more accurate corrections.

```py
Kp = 0.1  # Proportional gain
Ki = 0.01  # Integral gain
Kd = 0.05  # Derivative gain

integral_error = 0
previous_error = 0

# Inside the control loop
yaw_error = getYaw()
integral_error += yaw_error  # Accumulate the error
derivative_error = yaw_error - previous_error  # Change in error

correction = Kp * yaw_error + Ki * integral_error + Kd * derivative_error

left_motor_speed = desired_speed - correction
right_motor_speed = desired_speed + correction

setMotorRotationalVelocity(left_motor_id, left_motor_speed)
setMotorRotationalVelocity(right_motor_id, right_motor_speed)

previous_error = yaw_error  # Update this for the next iteration
```

Adjusting Parameters

Kp (Proportional Gain): Controls how large the correction is for a given yaw error. If set too high, the robot may oscillate. If too low, the robot may not correct enough.
Ki (Integral Gain): Helps eliminate residual steady-state error. Too high, and it can lead to overshooting and instability.
Kd (Derivative Gain): Predicts future error and can dampen the response. Helps improve stability and reduce overshoot.

Tuning Tips

Start with Ki and Kd at 0, and adjust Kp until you get a decent response that corrects the robot back to straight movement without too much oscillation.
Introduce Ki slowly to eliminate any residual steady-state error.
Introduce Kd if the system oscillates or to further smooth out the response.
Implementing gyroscopic correction requires tuning these parameters to match the dynamics of your specific robot, including its weight, wheel traction, and the characteristics of the surface it's moving on. Testing and iterative tuning are key to finding the optimal settings for smooth and straight movement.


## Simplification

It is likely best to have a function that given a mode, gives you the current velocity.

getVelocity( mode, totalDistance, remainingDistance, maxVelocity, maxAcceleration )
