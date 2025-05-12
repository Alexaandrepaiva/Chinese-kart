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

# Define constants for third-person camera
THIRD_PERSON_LOOK_AT_HEIGHT_OFFSET = 1.5 # Look at kart's center + this Z offset

def get_third_person_target_look_at(kart_node_path):
    """Helper to get the consistent third-person look-at point (kart center + offset)."""
    return kart_node_path.getPos() + Vec3(0,0,THIRD_PERSON_LOOK_AT_HEIGHT_OFFSET)

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
    global current_camera_pos, initial_look_at # Removed current_look_at_pos from globals here, it's more dynamic
    global target_position, target_hpr
    
    # Store the current camera position and orientation
    initial_position = camera.getPos()
    initial_hpr = camera.getHpr()
    # initial_look_at is for conceptual context, not directly driving HPR interpolation target here.
    if view_mode == 1:
        initial_look_at = kart.getPos() + kart.getQuat().getForward() * 50
    else: # view_mode == 3
        initial_look_at = get_third_person_target_look_at(kart)

    # Calculate the TARGET camera position based on view mode
    if view_mode == 1:  # First-person view
        cam_offset = Vec3(0, 3.0, 1.36)  # Position at the front face of the kart, at driver eye level
        rotated_offset = kart.getQuat().xform(cam_offset)
        target_position = kart.getPos() + rotated_offset
    else:  # Third-person view (default)
        cam_offset = Vec3(0, -15, 7)  # Position behind and above kart
        rotated_offset = kart.getQuat().xform(cam_offset)
        target_position = kart.getPos() + rotated_offset
    
    # Define the point the camera should look at for HPR calculation
    if view_mode == 1:
        target_look_at_point_for_hpr = kart.getPos() + kart.getQuat().getForward() * 50 # Match 1st person target_look_at
    else: # view_mode == 3 (Third-person)
        target_look_at_point_for_hpr = get_third_person_target_look_at(kart)

    # Temporarily move camera to target pos to calculate target HPR
    current_pos_snapshot = camera.getPos()
    current_hpr_snapshot = camera.getHpr()
    camera.setPos(target_position)
    camera.lookAt(target_look_at_point_for_hpr, Vec3.up()) # Use the consistent look_at point
    target_hpr = camera.getHpr()
    camera.setPos(current_pos_snapshot)
    camera.setHpr(current_hpr_snapshot)
    
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
    global initial_position, initial_hpr, target_position, target_hpr # target_position & target_hpr are set by setup functions
    
    # If dt is None, we can't do smooth interpolation
    if dt is None:
        dt = 1.0/60.0  # Assume 60 FPS if no dt provided
    
    # Get target camera position based on view mode
    if view_mode == 1:  # First-person view
        cam_offset = Vec3(0, 3.0, 1.36)  # Position at the front face of the kart, at driver eye level
        rotated_offset = kart.getQuat().xform(cam_offset)
        target_cam_pos = kart.getPos() + rotated_offset
    else:  # Third-person view (default)
        cam_offset = Vec3(0, -15, 7)  # Position behind and above kart
        rotated_offset = kart.getQuat().xform(cam_offset)
        target_cam_pos = kart.getPos() + rotated_offset
    
    # Get target look-at position
    if view_mode == 1:  # First-person view
        forward_vec = kart.getQuat().getForward() * 50
        target_look_at = kart.getPos() + forward_vec + Vec3(0,0,0)
    else:  # Third-person view (view_mode == 3)
        target_look_at = get_third_person_target_look_at(kart) # Use the corrected helper
    
    # Initialize camera state variables if they are None (first run)
    if current_camera_pos is None:
        current_camera_pos = camera.getPos()
    if current_look_at_pos is None:
        current_look_at_pos = target_look_at
    
    # If we're starting a view switch transition, capture the current position as the initial position
    if is_transitioning and is_view_switching and transition_progress == 0.0: # Starting a new player-triggered view switch
        initial_position = camera.getPos()
        initial_hpr = camera.getHpr()
        
        # Calculate the new target_position for this specific view switch transition
        # (target_cam_pos is the instantaneous ideal position, target_position is the fixed end point for this transition)
        if view_mode == 1:
            cam_offset_switch = Vec3(0, 3.0, 1.36)
            target_position = kart.getPos() + kart.getQuat().xform(cam_offset_switch) # Update global target_position for this switch
        else: # view_mode == 3
            cam_offset_switch = Vec3(0, -15, 7)
            target_position = kart.getPos() + kart.getQuat().xform(cam_offset_switch) # Update global target_position for this switch
        
        # Calculate target_hpr for this new view switch transition
        # Store current cam state to restore after temp move for HPR calc
        temp_cam_pos = camera.getPos()
        temp_cam_hpr = camera.getHpr()
        camera.setPos(target_position) # Temp move to the destination of this switch
        
        # Use the consistent look-at logic for calculating HPR for the switch
        if view_mode == 1:
            look_at_for_switch_hpr = kart.getPos() + kart.getQuat().getForward() * 50
        else: # view_mode == 3
            look_at_for_switch_hpr = get_third_person_target_look_at(kart)
        camera.lookAt(look_at_for_switch_hpr, Vec3.up())
        
        target_hpr = camera.getHpr() # Update global target_hpr for this switch
        
        camera.setPos(temp_cam_pos) # Restore camera
        camera.setHpr(temp_cam_hpr)
        
        transition_progress = 0.001 # Start progress slightly to avoid re-triggering this block

    # If we're in transition (either initial or view switch)
    if is_transitioning:
        current_transition_time = view_switch_time if is_view_switching else transition_time
        transition_progress += dt / current_transition_time

        if transition_progress >= 1.0:
            transition_progress = 1.0
            
            was_initial_game_transition = not is_view_switching # Check type before resetting is_view_switching

            is_transitioning = False
            is_view_switching = False # Always reset this flag after any transition ends

            # Set final position based on the transition's target_position 
            # (calculated at the start of setup_camera_transition or view switch setup)
            camera.setPos(target_position) 

            if was_initial_game_transition:
                # For the initial game transition, explicitly orient the camera using lookAt.
                # target_look_at is calculated at the start of this update_camera call based on current view_mode and kart state.
                camera.lookAt(target_look_at, Vec3.up())
            else:
                # For view switches (e.g., player pressing 1 or 3), 
                # setting HPR from the pre-calculated target_hpr is generally preferred for smooth results.
                camera.setHpr(target_hpr)

            # Update internal state variables from the camera's actual state after positioning/orienting.
            current_camera_pos = camera.getPos()
            current_hpr = camera.getHpr()
            current_look_at_pos = target_look_at # target_look_at is up-to-date for current frame

        else:
            # Interpolation logic for ongoing transition
            t = transition_progress
            # Use smooth step for view switching, linear for initial game transition
            progress_factor = t * t * (3 - 2 * t) if is_view_switching else t 

            current_camera_pos = initial_position + (target_position - initial_position) * progress_factor
            # Ensure target_hpr and initial_hpr are valid before interpolating
            if initial_hpr is not None and target_hpr is not None:
                 current_hpr = initial_hpr + (target_hpr - initial_hpr) * progress_factor
            else:
                 # Fallback or error if HPRs are not set (should not happen with current logic)
                 current_hpr = camera.getHpr() # Maintain current HPR if targets are missing
            
            camera.setPos(current_camera_pos)
            camera.setHpr(current_hpr)
    else:
        # Smooth camera follow during normal gameplay
        lerp_factor = min(1.0, dt * follow_smoothness)
        
        current_camera_pos = current_camera_pos + (target_cam_pos - current_camera_pos) * lerp_factor
        current_look_at_pos = current_look_at_pos + (target_look_at - current_look_at_pos) * lerp_factor
        
        camera.setPos(current_camera_pos)
        camera.lookAt(current_look_at_pos, Vec3.up())
