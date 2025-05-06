from panda3d.core import Vec3

# Camera state
transition_time = 2.0  # Initial transition duration in seconds
view_switch_time = 0.5  # Faster transition for view switching (in seconds)
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

# Camera view mode (1 = first-person, 3 = third-person)
view_mode = 3  # Default to third-person view
is_view_switching = False  # Flag to distinguish between initial game transition and view switching

def get_view_mode():
    """
    Returns the current camera view mode (1 for first-person, 3 for third-person)
    """
    global view_mode
    return view_mode

def set_view_mode(mode):
    """
    Sets the camera view mode (1 for first-person, 3 for third-person)
    """
    global view_mode, is_transitioning, is_view_switching, transition_progress
    
    # Only allow view changes if we're not in the middle of the initial transition
    # (during initial transition, is_transitioning is True but we don't want to
    # allow more view changes until it completes)
    if is_transitioning and not is_view_switching and transition_progress < 0.5:
        print("Cannot change view during initial camera transition")
        return False
        
    if mode in [1, 3] and mode != view_mode:
        view_mode = mode
        # Start a smooth transition to the new view
        is_transitioning = True
        is_view_switching = True  # This is a view switch, not the initial transition
        transition_progress = 0.0
        print(f"Camera view changed to {'first-person' if mode == 1 else 'third-person'} view")
        return True
    return False

def setup_camera_transition(camera, kart):
    """
    Sets up a smooth camera transition from the current position to the gameplay camera position
    """
    global is_transitioning, is_view_switching, transition_progress, initial_position, initial_hpr
    global current_camera_pos, current_look_at_pos, initial_look_at
    global target_position, target_hpr
    
    # Store the current camera position and orientation
    initial_position = camera.getPos()
    initial_hpr = camera.getHpr()
    initial_look_at = kart.getPos() + Vec3(0, 0, 2)

    # Calculate the TARGET position and HPR based on view mode
    if view_mode == 1:  # First-person view
        cam_offset = Vec3(1, 2.0, 1.5)  # Position at the front face of the kart, at driver eye level
        rotated_offset = kart.getQuat().xform(cam_offset)
        target_position = kart.getPos() + rotated_offset
    else:  # Third-person view (default)
        cam_offset = Vec3(0, -15, 7)  # Position behind and above kart
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
    is_view_switching = False  # This is the initial game transition, not a view switch
    transition_progress = 0.0
    
    # Return the function to check if transition is complete
    return lambda: not is_transitioning

def update_camera(camera, kart, dt=None):
    """
    Updates the camera position to follow the kart with smooth transitions
    during both initial transition and regular gameplay
    """
    global is_transitioning, is_view_switching, transition_progress, current_camera_pos, current_look_at_pos, current_hpr, view_mode
    global initial_position, initial_hpr, target_position, target_hpr
    
    # If dt is None, we can't do smooth interpolation
    if dt is None:
        dt = 1.0/60.0  # Assume 60 FPS if no dt provided
    
    # Get target camera position based on view mode
    if view_mode == 1:  # First-person view
        cam_offset = Vec3(1, 2.0, 1.5)  # Position at the front face of the kart, at driver eye level
        rotated_offset = kart.getQuat().xform(cam_offset)
        target_cam_pos = kart.getPos() + rotated_offset
    else:  # Third-person view (default)
        cam_offset = Vec3(0, -15, 7)  # Position behind and above kart
        rotated_offset = kart.getQuat().xform(cam_offset)
        target_cam_pos = kart.getPos() + rotated_offset
    
    # Get target look-at position (slightly above kart's center for third-person,
    # or in front of the kart for first-person)
    if view_mode == 1:  # First-person view
        # Look ahead of the kart
        forward_vec = kart.getQuat().getForward() * 50  # Look 50 units ahead
        target_look_at = kart.getPos() + forward_vec + Vec3(0, 0, 0)
    else:  # Third-person view
        target_look_at = kart.getPos() + Vec3(0, 0, 2)
    
    # Initialize camera position smoothing if needed
    if current_camera_pos is None:
        current_camera_pos = camera.getPos()
    if current_look_at_pos is None:
        current_look_at_pos = target_look_at
    
    # If we're starting a view switch transition, capture the current position as the initial position
    if is_transitioning and is_view_switching and transition_progress == 0.0:
        initial_position = camera.getPos()
        initial_hpr = camera.getHpr()
        
        # Calculate the new target position for the camera transition
        if view_mode == 1:  # First-person view
            cam_offset = Vec3(1, 2.0, 1.5)
            rotated_offset = kart.getQuat().xform(cam_offset)
            target_position = kart.getPos() + rotated_offset
        else:  # Third-person view
            cam_offset = Vec3(0, -15, 7)
            rotated_offset = kart.getQuat().xform(cam_offset)
            target_position = kart.getPos() + rotated_offset
        
        # Calculate target HPR
        current_pos = camera.getPos()
        current_hpr = camera.getHpr()
        camera.setPos(target_position)
        
        if view_mode == 1:  # First-person view
            # Look ahead of the kart for first-person
            forward_vec = kart.getQuat().getForward() * 50
            camera.lookAt(kart.getPos() + forward_vec + Vec3(0, 0, 0), Vec3.up())
        else:  # Third-person view
            camera.lookAt(kart.getPos() + Vec3(0, 0, 2), Vec3.up())
            
        target_hpr = camera.getHpr()
        camera.setPos(current_pos)
        camera.setHpr(current_hpr)
        
        # Set the first frame progress to slightly above 0 to avoid recalculating
        transition_progress = 0.01
    
    # If we're in transition (either initial or view switch)
    if is_transitioning:
        # Select appropriate transition speed based on whether this is a view switch or initial transition
        current_transition_time = view_switch_time if is_view_switching else transition_time
        
        # Update transition progress
        transition_progress += dt / current_transition_time
        
        # Clamp progress between 0 and 1
        if transition_progress >= 1.0:
            transition_progress = 1.0
            is_transitioning = False
            is_view_switching = False
            current_camera_pos = target_position
            current_hpr = target_hpr
            current_look_at_pos = target_look_at
        else:
            # Smooth the transition with an ease-in-out function for view switching
            if is_view_switching:
                # Use smooth step function: 3t² - 2t³ for smoother transition
                t = transition_progress
                smooth_t = t * t * (3 - 2 * t)
                current_camera_pos = initial_position + (target_position - initial_position) * smooth_t
                current_hpr = initial_hpr + (target_hpr - initial_hpr) * smooth_t
            else:
                # Linear interpolation for initial game transition
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
