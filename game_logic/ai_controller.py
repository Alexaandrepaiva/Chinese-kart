from panda3d.core import Vec3, LPoint3f
import random
from config import LAPS_TO_FINISH  # Import the lap constant from config

class AIController:
    def __init__(self, app, kart_data, track_points):
        """
        Initializes the AI Controller for a single kart.
        - app: Reference to the main application.
        - kart_data: The dictionary containing the AI kart's 'node' and other properties.
        - track_points: A list of LPoint3f representing the centerline of the track.
        """
        self.app = app
        self.kart_node = kart_data['node']
        self.track_points = track_points
        self.current_target_index = 0
        self.speed = random.uniform(25.0, 40.0) # Increased speed range for AI karts for better challenge
        self.path_offset = random.uniform(-0.5, 0.5) # Slight offset from the center line for variation
        self.kart_data = kart_data # Store kart_data to update progress

        if not self.track_points:
            print("Warning: AIController initialized with no track points.")
            self.current_target_point = LPoint3f(0,0,0) # Default target
        else:
            self.current_target_point = self._get_offset_target_point(self.track_points[self.current_target_index])

    def _get_offset_target_point(self, target_center_point):
        """
        Calculates the actual target point for the kart, including its random path offset.
        This requires knowing the track's orientation to apply the offset correctly (e.g., to the side).
        For simplicity, we'll initially apply a simple offset, which might not always be perfectly perpendicular.
        A more robust solution would calculate the perpendicular vector at that point on the track.
        """
        # Simplified: find direction to next point to estimate 'right' vector
        if self.current_target_index + 1 < len(self.track_points):
            next_point = self.track_points[self.current_target_index + 1]
            direction = (next_point - target_center_point).normalized()
            # Assuming Z is up, a simple cross product can give a 'right' vector
            # This is a simplification; for a non-flat track, this is more complex.
            track_right_dir = direction.cross(Vec3.up())
            if track_right_dir.length_squared() < 0.001: # If direction is vertical
                track_right_dir = Vec3(1,0,0) # Default if direction is up/down
        else: # At the end of the track
            track_right_dir = Vec3(1,0,0) # Default if no next point

        offset_vector = track_right_dir * self.path_offset
        return target_center_point + offset_vector


    def update(self, dt):
        """
        Updates the AI kart's state.
        - dt: Delta time since the last frame.
        """
        if not self.track_points:
            return

        kart_pos = self.kart_node.getPos()
        distance_to_target = (self.current_target_point - kart_pos).length()

        # Check if target is reached
        if distance_to_target < 2.0: # Threshold to switch target
            self.current_target_index += 1
            if self.current_target_index >= len(self.track_points):
                # Lap completed for this AI
                self.current_target_index = 0 
                self.kart_data['current_lap'] += 1
                # Record finish time if this is the first time completing the required lap(s)
                if self.kart_data['current_lap'] >= LAPS_TO_FINISH and self.kart_data['finish_time'] is None:
                    # Use the official race timer if available and running
                    if hasattr(self.app, 'run_timer') and self.app.run_timer and hasattr(self.app, 'timer_elapsed'):
                        self.kart_data['finish_time'] = self.app.timer_elapsed
                    else:
                        # Fallback if official timer isn't suitable (e.g., player hasn't moved)
                        # This case needs careful consideration for fairness.
                        # For now, mark as finished but without a comparable time if player hasn't started timer.
                        self.kart_data['finish_time'] = -1 # Indicates finished but timing might be off

                # print(f"AI {self.kart_node.getName()} completed lap {self.kart_data['current_lap']}")
            
            # Update target point with offset
            self.current_target_point = self._get_offset_target_point(self.track_points[self.current_target_index])


        # Move towards the target point
        direction_to_target = (self.current_target_point - kart_pos).normalized()
        
        # --- Speed adjustment based on turns ---
        current_speed = self.speed # Base speed for this AI
        # Look ahead to the next segment to adjust speed for turns
        if self.current_target_index + 1 < len(self.track_points):
            next_target_center_point = self.track_points[self.current_target_index + 1]
            # No need to apply offset to this lookahead point, just for general direction
            
            vec_current_segment = (self.current_target_point - kart_pos).normalized()
            vec_next_segment = (next_target_center_point - self.current_target_point).normalized()
            
            if vec_current_segment.length_squared() > 0.001 and vec_next_segment.length_squared() > 0.001:
                # Dot product gives cosine of angle; smaller value means sharper turn
                dot_product = vec_current_segment.dot(vec_next_segment)
                turn_sharpness_factor = (1.0 + dot_product) / 2.0 # Normalize to 0 (sharp turn) - 1 (straight)
                
                # Reduce speed more for sharper turns (lower turn_sharpness_factor)
                # Example: factor 0.5 (90 degree turn) might reduce speed by 40%
                # factor 1.0 (straight) reduces speed by 0%
                speed_reduction_on_turn = 0.6 # Max percentage of speed to reduce on sharpest turns
                current_speed *= (1.0 - speed_reduction_on_turn * (1.0 - turn_sharpness_factor**2)) # Squared for more effect
                current_speed = max(current_speed, self.speed * 0.3) # Don't slow down too much

        movement = direction_to_target * current_speed * dt
        
        new_pos = kart_pos + movement
        self.kart_node.setPos(new_pos)

        # Make the kart look towards its direction of movement or the next target
        # For smoother turning, look slightly ahead or at the target
        if (self.current_target_point - new_pos).length_squared() > 0.01:
             self.kart_node.lookAt(self.current_target_point)
        
        # Simple collision avoidance (placeholder)
        # This would require checking for obstacles or other karts and adjusting path
        # For now, karts might pass through each other or simple obstacles

        # Update AI kart progress (e.g., based on closest track point or segments passed)
        # This is a simplified progress update. A more robust one would consider track segments.
        self.kart_data['lap_progress'] = self.current_target_index / float(len(self.track_points)) 