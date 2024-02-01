How to move relative to the last move.
Current yaw.  Turn it into zero.
Thus any new yaw is taken relative to that yaw.
Then convert the result into -180 to 180.


Take existing yaw and new yaw.

Subtract the two.

it could be +360, -360.
Convert it into a -180 to + 180 value.

def getShortedRotation( currentYaw, targetYaw ):
   deltaYaw = targetYaw - currentYaw
   return removeRotations( deltaYaw )

def removeRotations( yaw ):
   while yaw > 180:
      yaw -= 360
   while yaw < -180:
      yaw += 360
   return yaw


