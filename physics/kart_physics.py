from panda3d.core import Vec3, Vec4
from direct.task import Task
from physics.track_detection import is_kart_on_track, get_kart_terrain

class KartPhysics:
    def __init__(self, kart):
        self.kart = kart
        self.key_map = {
            "forward": False,
            "brake": False,
            "left": False,
            "right": False
        }
        self.velocity = 0.0
        self.max_velocity = 50.0
        self.acceleration = 10.0
        self.braking_force = 25.0
        self.turn_speed = 100.0
        self.drag = 0.5  # Simple linear drag
        self.friction = 5.0  # Friction when not accelerating/braking
        
        # Terrain-specific factors
        self.current_terrain = 'road'  # Current terrain: 'road', 'sand', or 'lawn'
        self.previous_terrain = 'road'  # Track previous terrain for transitions
        self.terrain_factors = {
            'road': {
                'speed': 1.0,       # No speed reduction on road
                'acceleration': 1.0, # No acceleration reduction on road
                'friction': 1.0      # No extra friction on road
            },
            'sand': {
                'speed': 0.8,       # 20% speed reduction on sand
                'acceleration': 0.7, # 30% acceleration reduction on sand
                'friction': 1.3      # 30% more friction on sand
            },
            'lawn': {
                'speed': 0.5,       # 50% speed reduction on lawn
                'acceleration': 0.5, # 50% acceleration reduction on lawn
                'friction': 1.5      # 50% more friction on lawn
            }
        }
        # For smooth deceleration on terrain change
        self.lawn_deceleration_rate = 80.0  # units per second^2 (tune as needed)
        self.slowing_down_on_lawn = False
        
        # For display purposes
        self.terrain_colors = {
            'road': Vec4(0.3, 0.3, 0.3, 1),        # Dark gray
            'sand': Vec4(0.87, 0.77, 0.54, 1),     # Beige
            'lawn': Vec4(0.4, 0.7, 0.3, 1)         # Green
        }

    def setup_controls(self, accept_method):
        """
        Setup event handlers for kart controls
        """
        accept_method("w", self.set_key, ["forward", True])
        accept_method("w-up", self.set_key, ["forward", False])
        accept_method("s", self.set_key, ["brake", True])
        accept_method("s-up", self.set_key, ["brake", False])
        accept_method("a", self.set_key, ["left", True])
        accept_method("a-up", self.set_key, ["left", False])
        accept_method("d", self.set_key, ["right", True])
        accept_method("d-up", self.set_key, ["right", False])

    def set_key(self, key, value):
        """
        Update keymap based on key presses
        """
        self.key_map[key] = value

    def update(self, dt, track_z=0, track_curve_points=None, road_width=10.0, track_width=20.0, stripe_width=1.0):
        """
        Update kart physics based on current controls and time delta
        """
        # Skip updates if not moving the kart
        if not any(self.key_map.values()) and abs(self.velocity) < 0.1:
            self.velocity = 0
            return
            
        # Check what terrain the kart is on
        if track_curve_points:
            kart_pos = self.kart.getPos()
            self.current_terrain = get_kart_terrain(kart_pos, track_curve_points, road_width, track_width, stripe_width)
        else:
            self.current_terrain = 'road'  # Default to road if no track data provided

        # --- Smooth deceleration when entering lawn ---
        # Get max allowed velocity for current terrain
        max_velocity_factor = self.terrain_factors[self.current_terrain]['speed']
        max_allowed_velocity = self.max_velocity * max_velocity_factor
        
        if self.current_terrain == 'lawn' and self.velocity > max_allowed_velocity:
            # Apply strong deceleration until reaching max lawn speed
            self.slowing_down_on_lawn = True
        if self.slowing_down_on_lawn:
            if self.velocity > max_allowed_velocity:
                self.velocity -= self.lawn_deceleration_rate * dt
                if self.velocity < max_allowed_velocity:
                    self.velocity = max_allowed_velocity
            else:
                self.slowing_down_on_lawn = False
        
        # Track terrain transitions
        if self.current_terrain != self.previous_terrain:
            if self.current_terrain != 'lawn':
                self.slowing_down_on_lawn = False
            self.previous_terrain = self.current_terrain
        
        current_heading = self.kart.getH()

        # Get terrain-specific factors
        terrain_factors = self.terrain_factors[self.current_terrain]
        
        # Acceleration / Braking - Apply terrain-specific effects
        if self.key_map["forward"]:
            acceleration_multiplier = terrain_factors['acceleration']
            self.velocity += self.acceleration * dt * acceleration_multiplier
        elif self.key_map["brake"]:
            self.velocity -= self.braking_force * dt
        else:
            # Apply friction/drag if no acceleration/brake input
            friction_multiplier = terrain_factors['friction']
            friction_force = self.friction * dt * friction_multiplier
            drag_force = self.drag * self.velocity * dt
            if self.velocity > 0:
                self.velocity -= max(0, friction_force + drag_force)
            elif self.velocity < 0:
                # Allow braking to reverse slightly, but friction stops forward motion
                self.velocity += max(0, friction_force - drag_force)  # Drag opposes motion

        # Clamp velocity - Apply terrain-specific speed limiting
        speed_multiplier = terrain_factors['speed']
        max_velocity_adjusted = self.max_velocity * speed_multiplier
        self.velocity = max(-max_velocity_adjusted / 4, min(max_velocity_adjusted, self.velocity))  # Allow slower reverse

        # Stop if velocity is very small
        if not self.key_map["forward"] and not self.key_map["brake"] and abs(self.velocity) < 0.1:
            self.velocity = 0

        # Turning (only when moving)
        if abs(self.velocity) > 0.1:
            turn_rate = self.turn_speed * dt
            # Scale turning speed based on velocity (optional, adds realism)
            # turn_scale = min(1.0, abs(self.velocity) / (self.max_velocity * 0.3))
            # turn_rate *= turn_scale

            if self.key_map["left"]:
                current_heading += turn_rate
            if self.key_map["right"]:
                current_heading -= turn_rate

        # --- Update Kart Position and Rotation ---
        # Update Heading first
        self.kart.setH(current_heading)
        # Prevent kart from tilting visually
        self.kart.setP(0)
        self.kart.setR(0)

        # Move kart based on velocity and HORIZONTAL direction
        forward_vec = self.kart.getQuat().getForward()
        forward_vec_horizontal = Vec3(forward_vec.x, forward_vec.y, 0)  # Project onto XY plane
        if forward_vec_horizontal.lengthSquared() > 0.001:  # Avoid division by zero if vector is vertical
            forward_vec_horizontal.normalize()
            delta_pos = forward_vec_horizontal * self.velocity * dt
            new_pos = self.kart.getPos() + delta_pos
            # Ensure Z position stays correct (relative to track at Z=0)
            new_pos.setZ(track_z + 0.5)  # Track Z + half kart height
            self.kart.setPos(new_pos)

    def reset(self):
        """
        Reset kart physics values
        """
        self.velocity = 0.0
        for key in self.key_map:
            self.key_map[key] = False
