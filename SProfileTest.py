# S-curve profile, returns the current velocity
def sProfileVelocity_Internal(x, d, a, v):
    # Calculate distance covered during acceleration (or deceleration)
    da = v**2 / (2 * a)
    
    # Total distance for acceleration and deceleration phases
    total_acc_dec_distance = 2 * da
    
    # Check if the total distance is greater than the path distance
    if total_acc_dec_distance >= d:
        # The robot never reaches full velocity, adjust calculations
        # Find the peak velocity it can reach before decelerating
        vmax = (a * d) ** 0.5
        if x <= d / 2:
            # Acceleration phase
            return (2 * a * x) ** 0.5
        else:
            # Deceleration phase
            return (2 * a * (d - x)) ** 0.5
    else:
        # If the robot reaches its maximum velocity
        dc = d - total_acc_dec_distance
        
        if x < da:  # Acceleration phase
            return (2 * a * x) ** 0.5
        elif x < da + dc:  # Constant velocity phase
            return v
        else:  # Deceleration phase
            return (2 * a * (d - x)) ** 0.5

def sProfileVelocity( currentDistance, totalDistance, maxAcceleration, maxVelocity, minVelocity):
    return max( minVelocity, sProfileVelocity_Internal( currentDistance, totalDistance, maxAcceleration, maxVelocity ))


totalDistance = 1000
currentDistance = 0
minVelocity = 10
maxVelocity = 100
maxAcceleration = 50

timeStep = 0.01
time = 0
while( currentDistance < totalDistance ):
    currentVelocity = sProfileVelocity( currentDistance, totalDistance,maxAcceleration, maxVelocity, minVelocity )
    currentDistance += currentVelocity * timeStep
    time += timeStep
    print( time, ',', currentDistance, ',', currentVelocity )


