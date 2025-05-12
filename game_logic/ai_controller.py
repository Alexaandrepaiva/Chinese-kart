from panda3d.core import Vec3, LPoint3f
import random
import time
from config import LAPS_TO_FINISH, get_ai_speed_modifier, get_ai_turn_factor, get_ai_path_deviation

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
        
        # Use same max speed as player (50.0) with difficulty modifier
        # This allows AI karts to reach 180 km/h just like the player
        self.max_speed = 49.0
        self.target_speed = self.max_speed * get_ai_speed_modifier()
        
        # Current actual speed (starts at 0 and accelerates)
        self.current_speed = 0.0
        
        # Acceleration and deceleration rates (units per second²)
        self.acceleration = 10.0  # Same as player kart
        self.braking = 20.0       # Faster deceleration when needed
        
        # Get the difficulty-based path deviation range
        max_deviation = get_ai_path_deviation()
        # Randomize the path offset within the allowed deviation range
        self.path_offset = random.uniform(-max_deviation, max_deviation)
        # Add some randomness to target switching distance
        self.target_switch_distance = random.uniform(1.8, 2.5)
        
        # Get the difficulty-based turn speed reduction factor
        self.turn_speed_reduction = get_ai_turn_factor()
        
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

        # Apply the random offset
        offset_vector = track_right_dir * self.path_offset
        
        # Add small Z variation for more natural movement
        z_variation = random.uniform(-0.1, 0.1)
        offset_vector.addZ(z_variation)
        
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

        # Check if target is reached using the randomized distance threshold
        if distance_to_target < self.target_switch_distance:
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

            # Update target point with offset
            self.current_target_point = self._get_offset_target_point(self.track_points[self.current_target_index])


        # Move towards the target point
        direction_to_target = (self.current_target_point - kart_pos).normalized()
        
        # --- Calculate target speed based on turns and difficulty ---
        target_speed = self.target_speed
        
        # Look ahead to the next segment to adjust speed for turns
        if self.current_target_index + 1 < len(self.track_points):
            next_target_center_point = self.track_points[self.current_target_index + 1]
            
            vec_current_segment = (self.current_target_point - kart_pos).normalized()
            vec_next_segment = (next_target_center_point - self.current_target_point).normalized()
            
            if vec_current_segment.length_squared() > 0.001 and vec_next_segment.length_squared() > 0.001:
                # Dot product gives cosine of angle; smaller value means sharper turn
                dot_product = vec_current_segment.dot(vec_next_segment)
                turn_sharpness_factor = (1.0 + dot_product) / 2.0 # Normalize to 0 (sharp turn) - 1 (straight)
                
                # Apply difficulty-based speed reduction on turns
                # self.turn_speed_reduction is higher on easy difficulty (more slowing down)
                target_speed *= (1.0 - self.turn_speed_reduction * (1.0 - turn_sharpness_factor**2))
                
                # On straightaways, allow AI to reach full max speed when turn_sharpness_factor is close to 1
                if turn_sharpness_factor > 0.95:
                    target_speed = min(target_speed * 1.1, self.max_speed * get_ai_speed_modifier())
                
                # Add slight randomness to the minimum speed to create more varied behavior
                min_speed_factor = 0.3 + random.uniform(-0.05, 0.05)
                target_speed = max(target_speed, self.target_speed * min_speed_factor)

        # Apply slight random speed variation for more natural movement
        speed_variation = 1.0 + random.uniform(-0.05, 0.05)
        target_speed *= speed_variation
        
        # --- Apply acceleration/deceleration to gradually approach target speed ---
        # If current speed is less than target speed, accelerate
        if self.current_speed < target_speed:
            # Apply acceleration with some randomness to make each AI slightly different
            accel_factor = 1.0 + random.uniform(-0.1, 0.1)
            self.current_speed += self.acceleration * accel_factor * dt
            # Cap at target speed
            self.current_speed = min(self.current_speed, target_speed)
        # If current speed is greater than target speed, decelerate
        elif self.current_speed > target_speed:
            # Brake harder when approaching sharp turns
            if 'turn_sharpness_factor' in locals() and turn_sharpness_factor < 0.6:
                # Sharp turn ahead, brake harder
                self.current_speed -= self.braking * dt
            else:
                # Normal deceleration
                self.current_speed -= self.acceleration * dt
            # Don't slow down below target speed
            self.current_speed = max(self.current_speed, target_speed)
        
        # Use current_speed (which respects acceleration limits) for movement
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
            )
            self.kart_node.lookAt(look_target + small_offset)
        
        # Update AI kart progress
        self.kart_data['lap_progress'] = self.current_target_index / float(len(self.track_points)) 

    def handle_barrier_collision(self):
        """
        Trata a colisão entre um kart AI e uma barreira
        Ajusta o comportamento do kart após a colisão
        """
        # Reduzir velocidade
        self.current_speed = 0
        
        # Mudar direção levemente para evitar ficar preso
        target_point_index = self.current_target_index
        if target_point_index > 0:
            target_point_index -= 1
        self.current_target_point = self._get_offset_target_point(self.track_points[target_point_index])

    def handle_kart_collision(self, collision_direction, is_frontal=False, is_rear=False, is_side=False):
        """
        Trata a colisão entre karts, ajustando o comportamento do AI para evitar ficar preso
        
        Args:
            collision_direction: Vetor de direção da colisão
            is_frontal: Se a colisão foi frontal (AI bateu na traseira de outro kart)
            is_rear: Se a colisão foi traseira (AI foi atingido por trás)
            is_side: Se a colisão foi lateral
        """
        # Ajustar velocidade baseado no tipo de colisão
        if is_frontal:
            # Se bateu em outro kart pela traseira, reduzir velocidade significativamente
            self.current_speed *= 0.6
            
            # Tentar desviar lateralmente
            kart_pos = self.kart_data['node'].getPos()
            kart_forward = self.kart_data['node'].getQuat().getForward()
            
            # Gerar um vetor de desvio lateral
            lateral_vector = kart_forward.cross(Vec3(0, 0, 1))
            lateral_vector.normalize()
            
            # Escolher aleatoriamente entre esquerda e direita
            if random.random() < 0.5:
                lateral_vector *= -1
            
            # Modificar o ponto alvo para desviar
            deviation_strength = 2.0 + random.random() * 1.0  # Desvio de 2-3 unidades
            target_point_index = min(self.current_target_index + 1, len(self.track_points) - 1)
            base_target = self._get_offset_target_point(self.track_points[target_point_index])
            
            # Aplicar desvio lateral para contornar
            self.current_target_point = base_target + lateral_vector * deviation_strength
            
        elif is_rear:
            # Se foi atingido por trás, não reduzir tanto a velocidade
            self.current_speed *= 0.9
            
            # Tentar acelerar um pouco para se afastar
            self.current_speed += 2.0
            
        elif is_side:
            # Em colisão lateral, reduzir menos a velocidade
            self.current_speed *= 0.8
            
            # Criar uma direção de desvio baseada na normal da colisão
            kart_pos = self.kart_data['node'].getPos()
            kart_forward = self.kart_data['node'].getQuat().getForward()
            
            # Para colisões laterais, tentar continuar na direção do movimento
            # mas com um leve ajuste para se afastar do ponto de colisão
            perp_vector = Vec3(-collision_direction.y, collision_direction.x, 0)
            perp_vector.normalize()
            
            # Mesclar a direção frontal com uma componente lateral para contornar o obstáculo
            deviation_vector = (kart_forward * 0.7) + (perp_vector * 0.3)
            deviation_vector.normalize()
            
            # Procurar o próximo ponto do track que esteja na direção geral do movimento
            search_index = self.current_target_index
            best_dot = -1
            best_index = search_index
            
            # Buscar um ponto na pista que seja mais adequado para a nova direção
            for i in range(5):  # Verificar até 5 pontos à frente
                check_index = (self.current_target_index + i) % len(self.track_points)
                check_point = self.track_points[check_index]
                check_dir = check_point - kart_pos
                check_dir.normalize()
                
                dot = check_dir.dot(deviation_vector)
                if dot > best_dot:
                    best_dot = dot
                    best_index = check_index
            
            # Avançar para o melhor ponto encontrado
            if best_index != self.current_target_index:
                self.current_target_index = best_index
                self.current_target_point = self._get_offset_target_point(self.track_points[best_index])
        
        # Fallback para colisões não classificadas
        else:
            # Comportamento padrão quando o tipo de colisão não é claro
            self.current_speed *= 0.7
            
            # Gerar um pequeno desvio aleatório
            perp_vector = Vec3(-collision_direction.y, collision_direction.x, 0)
            perp_vector.normalize()
            
            # Escolher aleatoriamente entre esquerda e direita
            if random.random() < 0.5:
                perp_vector *= -1
            
            # Aplicar um desvio moderado
            deviation_amount = random.uniform(1.5, 2.5)
            target_point_index = self.current_target_index
            base_target = self._get_offset_target_point(self.track_points[target_point_index])
            self.current_target_point = base_target + perp_vector * deviation_amount 