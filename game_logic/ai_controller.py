from panda3d.core import Vec3, LPoint3f
import random
import time
from config import LAPS_TO_FINISH, get_ai_speed_modifier, get_ai_turn_factor, get_ai_path_deviation, DIFFICULTY

class AIController:
    def __init__(self, app, kart_data, track_points):
        """
        Initializes the AI Controller for a single kart.
        - app: Reference to the main application.
        - kart_data: The dictionary containing the AI kart's 'node' and other properties.
        - track_points: A list of LPoint3f representing the centerline of the track.
        """
        # Reset the random seed to ensure a new random offset each time
        random.seed(time.time())
        
        self.app = app
        self.kart_node = kart_data['node']
        self.track_points = track_points
        self.current_target_index = 0
        
        # Generate unique characteristics for this AI kart based on difficulty
        # Easy: Lower skill and aggression, higher variation
        # Regular: Balanced traits
        # Hard: Higher skill and aggression, more consistent
        if DIFFICULTY == "easy":
            self.personality = {
                'aggression': random.uniform(0.6, 0.9),   # Less aggressive
                'skill': random.uniform(0.6, 0.8),        # Lower skill
                'consistency': random.uniform(0.5, 0.8)    # More random behavior
            }
        elif DIFFICULTY == "hard":
            self.personality = {
                'aggression': random.uniform(1.2, 1.6),   # More aggressive
                'skill': random.uniform(1.1, 1.4),        # Higher skill
                'consistency': random.uniform(0.95, 1.3)    # More consistent
            }
        else:  # regular
            self.personality = {
                'aggression': random.uniform(0.8, 1.2),   # Balanced aggression
                'skill': random.uniform(0.8, 1.1),        # Balanced skill
                'consistency': random.uniform(0.7, 1.0)    # Moderate consistency
            }
        
        # Use same max speed as player (50.0) with difficulty modifier and personality
        self.max_speed = 55.0 * self.personality['aggression']
        self.target_speed = self.max_speed * get_ai_speed_modifier()
        
        # Current actual speed (starts at 0 and accelerates)
        self.current_speed = 0.0
        
        # Acceleration and deceleration rates with personality influence
        self.acceleration = 15.0 * self.personality['skill']
        self.braking = 25.0 * self.personality['skill']
        
        # Get the difficulty-based path deviation range and apply personality
        base_deviation = get_ai_path_deviation()
        # Higher skill means less deviation from optimal racing line
        self.max_path_deviation = base_deviation * (2.0 - self.personality['skill'])
        
        # Dynamic path offset that changes over time
        self.path_offset = 0.0
        self.target_path_offset = random.uniform(-self.max_path_deviation, self.max_path_deviation)
        self.offset_change_time = time.time()
        # More consistent karts change their racing line less frequently
        self.offset_duration = random.uniform(2.0, 4.0) * self.personality['consistency']
        
        # Add some randomness to target switching distance based on skill
        self.target_switch_distance = random.uniform(1.8, 2.5) * (2.0 - self.personality['skill'])
        
        # Get the difficulty-based turn speed reduction factor
        self.turn_speed_reduction = get_ai_turn_factor() * (2.0 - self.personality['skill'])
        
        # Mistake handling - probability and recovery based on difficulty and skill
        self.is_making_mistake = False
        self.mistake_recovery_time = 0
        self.mistake_duration = 0
        self.last_mistake_time = time.time()
        # More skilled karts (and harder difficulty) have longer cooldowns between mistakes
        self.mistake_cooldown = random.uniform(5.0, 15.0) * self.personality['skill']
        
        self.kart_data = kart_data

        if not self.track_points:
            print("Warning: AIController initialized with no track points.")
            self.current_target_point = LPoint3f(0,0,0) # Default target
        else:
            self.current_target_point = self._get_offset_target_point(self.track_points[self.current_target_index])

    def _get_offset_target_point(self, target_center_point):
        """
        Calculates the actual target point for the kart, including its dynamic path offset.
        """
        # Simplified: find direction to next point to estimate 'right' vector
        if self.current_target_index + 1 < len(self.track_points):
            next_point = self.track_points[self.current_target_index + 1]
            direction = (next_point - target_center_point).normalized()
            track_right_dir = direction.cross(Vec3.up())
            if track_right_dir.length_squared() < 0.001:
                track_right_dir = Vec3(1,0,0)
        else:
            track_right_dir = Vec3(1,0,0)

        # Update dynamic path offset
        current_time = time.time()
        if current_time - self.offset_change_time > self.offset_duration:
            self.offset_change_time = current_time
            self.offset_duration = random.uniform(2.0, 4.0)
            self.target_path_offset = random.uniform(-self.max_path_deviation, self.max_path_deviation)
        
        # Smoothly interpolate to target offset
        offset_progress = (current_time - self.offset_change_time) / self.offset_duration
        self.path_offset = (1 - offset_progress) * self.path_offset + offset_progress * self.target_path_offset
        
        # Apply the dynamic offset
        offset_vector = track_right_dir * self.path_offset
        
        # Add small Z variation for more natural movement
        z_variation = random.uniform(-0.1, 0.1) * self.personality['consistency']
        offset_vector.addZ(z_variation)
        
        return target_center_point + offset_vector

    def _check_for_mistake(self):
        """
        Determines if the AI should make a mistake based on their skill level
        """
        if self.is_making_mistake:
            current_time = time.time()
            if current_time - self.mistake_recovery_time > self.mistake_duration:
                self.is_making_mistake = False
                self.last_mistake_time = current_time
            return True
        
        # Higher skill means fewer mistakes
        mistake_probability = (1.0 - self.personality['skill']) * 0.01
        current_time = time.time()
        
        if (current_time - self.last_mistake_time > self.mistake_cooldown and 
            random.random() < mistake_probability):
            self.is_making_mistake = True
            self.mistake_recovery_time = current_time
            self.mistake_duration = random.uniform(0.5, 2.0) * (2.0 - self.personality['skill'])
            # Generate a new mistake pattern
            self.mistake_offset = random.uniform(-2.0, 2.0)
            self.mistake_speed_factor = random.uniform(0.3, 0.7)
            return True
        
        return False

    def update(self, dt):
        """
        Updates the AI kart's state.
        - dt: Delta time since the last frame.
        """
        if not self.track_points:
            return

        kart_pos = self.kart_node.getPos()
        distance_to_target = (self.current_target_point - kart_pos).length()

        # Check if target is reached using the randomized distance threshold
        if distance_to_target < self.target_switch_distance:
            self.current_target_index += 1
            if self.current_target_index >= len(self.track_points):
                self.current_target_index = 0 
                self.kart_data['current_lap'] += 1
                if self.kart_data['current_lap'] >= LAPS_TO_FINISH and self.kart_data['finish_time'] is None:
                    if hasattr(self.app, 'run_timer') and self.app.run_timer and hasattr(self.app, 'timer_elapsed'):
                        self.kart_data['finish_time'] = self.app.timer_elapsed
                    else:
                        self.kart_data['finish_time'] = -1

            # Update target point with offset
            self.current_target_point = self._get_offset_target_point(self.track_points[self.current_target_index])

        # Move towards the target point
        direction_to_target = (self.current_target_point - kart_pos).normalized()
        
        # --- Calculate target speed based on turns, difficulty, and personality ---
        target_speed = self.target_speed * self.personality['consistency']
        
        # Check for mistakes
        if self._check_for_mistake():
            # Apply mistake effects
            target_speed *= self.mistake_speed_factor
            direction_to_target += Vec3(
                random.uniform(-0.2, 0.2),
                random.uniform(-0.2, 0.2),
                0
            ) * (2.0 - self.personality['skill'])
            direction_to_target.normalize()
        
        # Look ahead to adjust speed for turns
        if self.current_target_index + 1 < len(self.track_points):
            next_target_center_point = self.track_points[self.current_target_index + 1]
            
            vec_current_segment = (self.current_target_point - kart_pos).normalized()
            vec_next_segment = (next_target_center_point - self.current_target_point).normalized()
            
            if vec_current_segment.length_squared() > 0.001 and vec_next_segment.length_squared() > 0.001:
                dot_product = vec_current_segment.dot(vec_next_segment)
                turn_sharpness_factor = (1.0 + dot_product) / 2.0
                
                # Apply personality-based turn handling
                turn_reduction = self.turn_speed_reduction * (2.0 - self.personality['skill'])
                target_speed *= (1.0 - turn_reduction * (1.0 - turn_sharpness_factor**2))
                
                # On straightaways, allow AI to reach full speed based on personality
                if turn_sharpness_factor > 0.95:
                    straightaway_boost = 1.0 + (self.personality['aggression'] - 1.0) * 0.2
                    target_speed = min(target_speed * straightaway_boost, 
                                     self.max_speed * get_ai_speed_modifier())
                
                # Add slight randomness to the minimum speed
                min_speed_factor = 0.3 + random.uniform(-0.05, 0.05) * self.personality['consistency']
                target_speed = max(target_speed, self.target_speed * min_speed_factor)

        # Apply slight random speed variation based on consistency
        speed_variation = 1.0 + random.uniform(-0.05, 0.05) * self.personality['consistency']
        target_speed *= speed_variation
        
        # --- Apply acceleration/deceleration to gradually approach target speed ---
        if self.current_speed < target_speed:
            accel_factor = 1.0 + random.uniform(-0.1, 0.1) * self.personality['consistency']
            self.current_speed += self.acceleration * accel_factor * dt
            self.current_speed = min(self.current_speed, target_speed)
        elif self.current_speed > target_speed:
            if 'turn_sharpness_factor' in locals() and turn_sharpness_factor < 0.6:
                self.current_speed -= self.braking * dt
            else:
                self.current_speed -= self.acceleration * dt
            self.current_speed = max(self.current_speed, target_speed)
        
        # Use current_speed for movement
        movement = direction_to_target * self.current_speed * dt
        
        new_pos = kart_pos + movement
        self.kart_node.setPos(new_pos)

        # Make the kart look towards its direction of movement with slight randomness
        look_target = self.current_target_point
        
        # Add small random offset to look direction for more natural turning
        if (look_target - new_pos).length_squared() > 0.01:
            small_offset = Vec3(
                random.uniform(-0.2, 0.2),
                random.uniform(-0.2, 0.2),
                0
            ) * self.personality['consistency']
            self.kart_node.lookAt(look_target + small_offset)
        
        # Update AI kart progress
        self.kart_data['lap_progress'] = self.current_target_index / float(len(self.track_points))

    def handle_barrier_collision(self):
        """
        Handles collision between an AI kart and a barrier
        Adjusts kart behavior after collision
        """
        # Reduce speed more drastically for lower skill karts
        self.current_speed = 0
        
        # Force a temporary "mistake" state after collision
        self.is_making_mistake = True
        self.mistake_recovery_time = time.time()
        self.mistake_duration = random.uniform(0.5, 1.5) * (2.0 - self.personality['skill'])
        
        # Change direction slightly to avoid getting stuck
        target_point_index = self.current_target_index
        if target_point_index > 0:
            target_point_index -= 1
        self.current_target_point = self._get_offset_target_point(self.track_points[target_point_index])

    def handle_kart_collision(self, collision_direction, is_frontal=False, is_rear=False, is_side=False):
        """
        Handles collisions between karts, adjusting AI behavior to avoid getting stuck
        
        Args:
            collision_direction: Vector of direction of the collision
            is_frontal: If the collision was frontal (AI hit another kart)
            is_rear: If the collision was from behind (AI was hit)
            is_side: If the collision was from the side
        """
        # Adjust speed based on collision type and personality
        if is_frontal:
            # Reduce speed more for less skilled karts
            self.current_speed *= 0.6 * self.personality['skill']
            
            # Generate evasive maneuver
            kart_pos = self.kart_data['node'].getPos()
            kart_forward = self.kart_data['node'].getQuat().getForward()
            
            # Create a deviation vector based on personality
            lateral_vector = kart_forward.cross(Vec3(0, 0, 1))
            lateral_vector.normalize()
            
            # More aggressive karts might try to push through
            if self.personality['aggression'] > 1.1:
                deviation_strength = 1.0
            else:
                deviation_strength = 2.0 + random.random() * self.personality['consistency']
            
            # Choose direction based on personality for consistency
            if hash(str(self.personality)) % 2 == 0:
                lateral_vector *= -1
            
            target_point_index = min(self.current_target_index + 1, len(self.track_points) - 1)
            base_target = self._get_offset_target_point(self.track_points[target_point_index])
            
            # Apply personality-based evasive maneuver
            self.current_target_point = base_target + lateral_vector * deviation_strength
            
        elif is_rear:
            # If hit from behind, try to speed up to avoid further collision
            self.current_speed *= 0.9
            self.current_speed += 2.0 * self.personality['aggression']
            
        elif is_side:
            # For side collisions, adjust speed and direction based on personality
            self.current_speed *= 0.8 * self.personality['skill']
            
            kart_pos = self.kart_data['node'].getPos()
            kart_forward = self.kart_data['node'].getQuat().getForward()
            
            # Create an evasive direction based on collision normal and personality
            perp_vector = Vec3(-collision_direction.y, collision_direction.x, 0)
            perp_vector.normalize()
            
            # More skilled karts recover better
            recovery_factor = 0.3 + (0.4 * self.personality['skill'])
            deviation_vector = (kart_forward * (1.0 - recovery_factor)) + (perp_vector * recovery_factor)
            deviation_vector.normalize()
            
            # Search for a better target point based on personality
            search_index = self.current_target_index
            best_dot = -1
            best_index = search_index
            
            # More skilled karts look further ahead
            look_ahead = int(3 + (2 * self.personality['skill']))
            
            for i in range(look_ahead):
                check_index = (self.current_target_index + i) % len(self.track_points)
                check_point = self.track_points[check_index]
                check_dir = check_point - kart_pos
                check_dir.normalize()
                
                dot = check_dir.dot(deviation_vector)
                if dot > best_dot:
                    best_dot = dot
                    best_index = check_index
            
            # Update target based on best found point
            if best_index != self.current_target_index:
                self.current_target_index = best_index
                self.current_target_point = self._get_offset_target_point(self.track_points[best_index]) 