from panda3d.core import Vec3
from direct.task import Task

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

    def update(self, dt, track_z=0):
        """
        Update kart physics based on current controls and time delta
        """
        # Skip updates if not moving the kart
        if not any(self.key_map.values()) and abs(self.velocity) < 0.1:
            self.velocity = 0
            return

        current_heading = self.kart.getH()

        # Acceleration / Braking
        if self.key_map["forward"]:
            self.velocity += self.acceleration * dt
        elif self.key_map["brake"]:
            self.velocity -= self.braking_force * dt
        else:
            # Apply friction/drag if no acceleration/brake input
            friction_force = self.friction * dt
            drag_force = self.drag * self.velocity * dt
            if self.velocity > 0:
                self.velocity -= max(0, friction_force + drag_force)
            elif self.velocity < 0:
                # Allow braking to reverse slightly, but friction stops forward motion
                self.velocity += max(0, friction_force - drag_force)  # Drag opposes motion

        # Clamp velocity
        self.velocity = max(-self.max_velocity / 4, min(self.max_velocity, self.velocity))  # Allow slower reverse

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
