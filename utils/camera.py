from panda3d.core import Vec3

# Camera state
transition_time = 2.0  # Initial transition duration in seconds
follow_smoothness = 4.0  # Higher values = smoother camera (but more lag)
is_transitioning = False
transition_progress = 0.0
initial_position = None
initial_hpr = None

# Camera smoothing state
current_camera_pos = None
current_look_at_pos = None

def setup_camera_transition(camera, kart):
    """
    Sets up a smooth camera transition from the current position to the gameplay camera position
    """
    global is_transitioning, transition_progress, initial_position, initial_hpr
    global current_camera_pos, current_look_at_pos
    
    # Store the current camera position and orientation
    initial_position = camera.getPos()
    initial_hpr = camera.getHpr()
    
    # Initialize smoothing variables with current position
    current_camera_pos = initial_position
    current_look_at_pos = kart.getPos() + Vec3(0, 0, 2)
    
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
    global is_transitioning, transition_progress, current_camera_pos, current_look_at_pos
    
    # If dt is None, we can't do smooth interpolation
    if dt is None:
        dt = 1.0/60.0  # Assume 60 FPS if no dt provided
    
    # Get target follow-cam position
    cam_offset = Vec3(0, -15, 7)  # Offset behind and above
    # Rotate the offset by the kart's rotation to keep it behind the kart
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
        
        # Interpolate between initial and target positions
        current_camera_pos = initial_position + (target_cam_pos - initial_position) * transition_progress
        current_look_at_pos = target_look_at  # Look directly at the kart during transition
    else:
        # Smooth camera follow during normal gameplay
        # Calculate the interpolation factor based on delta time and smoothness
        # Lower lerp_factor = smoother but laggy camera, higher = more responsive but jittery
        lerp_factor = min(1.0, dt * follow_smoothness)
        
        # Interpolate camera position
        current_camera_pos = current_camera_pos + (target_cam_pos - current_camera_pos) * lerp_factor
        
        # Smoothly update look-at position
        current_look_at_pos = current_look_at_pos + (target_look_at - current_look_at_pos) * lerp_factor
    
    # Set the camera position and orientation
    camera.setPos(current_camera_pos)
    camera.lookAt(current_look_at_pos)
