from panda3d.core import Vec3

# Camera state
transition_time = 2.0  # Initial transition duration in seconds
follow_smoothness = 4.0  # Higher values = smoother camera (but more lag)
is_transitioning = False
transition_progress = 0.0
initial_position = None
initial_hpr = None
initial_look_at = None
target_position = None
target_hpr = None

# Camera smoothing state
current_camera_pos = None
current_look_at_pos = None
current_hpr = None

def setup_camera_transition(camera, kart):
    """
    Sets up a smooth camera transition from the current position to the gameplay camera position
    """
    global is_transitioning, transition_progress, initial_position, initial_hpr
    global current_camera_pos, current_look_at_pos, initial_look_at
    global target_position, target_hpr
    
    # Store the current camera position and orientation
    initial_position = camera.getPos()
    initial_hpr = camera.getHpr()
    initial_look_at = kart.getPos() + Vec3(0, 0, 2)

    # Calculate the TARGET position and HPR for the final follow-cam view
    cam_offset = Vec3(0, -15, 7)
    rotated_offset = kart.getQuat().xform(cam_offset)
    target_position = kart.getPos() + rotated_offset
    target_look_at_point = kart.getPos() + Vec3(0, 0, 2)
    
    # Temporarily move camera to target pos to calculate target HPR
    current_pos = camera.getPos()
    current_hpr = camera.getHpr()
    camera.setPos(target_position)
    camera.lookAt(target_look_at_point, Vec3.up())
    target_hpr = camera.getHpr()
    camera.setPos(current_pos)
    camera.setHpr(current_hpr)
    
    # Initialize smoothing variables with current position/lookAt
    current_camera_pos = initial_position
    
    # Reset transition state
    is_transitioning = True
    transition_progress = 0.0
    
    # Return the function to check if transition is complete
    return lambda: not is_transitioning

def update_camera(camera, kart, dt=None):
    """
    Updates the camera position to follow the kart with smooth transitions
    during both initial transition and regular gameplay
    """
    global is_transitioning, transition_progress, current_camera_pos, current_look_at_pos, current_hpr
    
    # If dt is None, we can't do smooth interpolation
    if dt is None:
        dt = 1.0/60.0  # Assume 60 FPS if no dt provided
    
    # Get target follow-cam position
    cam_offset = Vec3(0, -15, 7)  # Offset behind and above
    rotated_offset = kart.getQuat().xform(cam_offset)
    target_cam_pos = kart.getPos() + rotated_offset
    
    # Get target look-at position (slightly above kart's center)
    target_look_at = kart.getPos() + Vec3(0, 0, 2)
    
    # Initialize camera position smoothing if needed
    if current_camera_pos is None:
        current_camera_pos = camera.getPos()
    if current_look_at_pos is None:
        current_look_at_pos = target_look_at
    
    # If we're in the initial transition
    if is_transitioning:
        # Update transition progress
        transition_progress += dt / transition_time
        
        # Clamp progress between 0 and 1
        if transition_progress >= 1.0:
            transition_progress = 1.0
            is_transitioning = False
            current_camera_pos = target_position
            current_hpr = target_hpr
            current_look_at_pos = target_look_at
        else:
            current_camera_pos = initial_position + (target_position - initial_position) * transition_progress
            current_hpr = initial_hpr + (target_hpr - initial_hpr) * transition_progress
        
        camera.setPos(current_camera_pos)
        camera.setHpr(current_hpr)

    else:
        # Smooth camera follow during normal gameplay
        lerp_factor = min(1.0, dt * follow_smoothness)
        
        current_camera_pos = current_camera_pos + (target_cam_pos - current_camera_pos) * lerp_factor
        current_look_at_pos = current_look_at_pos + (target_look_at - current_look_at_pos) * lerp_factor
        
        camera.setPos(current_camera_pos)
        camera.lookAt(current_look_at_pos, Vec3.up())
