import math
from panda3d.core import Vec3
import config

class ProgressTracker:
    def __init__(self, kart, track_curve_points):
        self.kart = kart
        self.trackCurvePoints = track_curve_points
        self.kart_progress = 0.0
        self.max_progress_reached = 0.0
        self.lap_completed = False
        self.has_left_start_line = False  # Flag for leaving the start area after race start
        self.current_lap = 0  # Track the number of laps completed

    def reset(self):
        self.kart_progress = 0.0
        self.max_progress_reached = 0.0
        self.lap_completed = False
        self.has_left_start_line = False
        self.current_lap = 0

    def _point_segment_distance_sq(self, p, a, b):
        """Calculate the squared distance from point p to line segment (a, b)."""
        l2 = (b - a).lengthSquared()
        if l2 == 0.0:
            return (p - a).lengthSquared()
        t = (p - a).dot(b - a) / l2
        t = max(0, min(1, t))
        vector_ab = Vec3(b - a)
        scalar_t = float(t)
        scaled_vector = vector_ab * scalar_t
        projection = a + scaled_vector
        return (p - projection).lengthSquared()

    def calculate_kart_progress(self):
        """Calculates the kart's progress along the track spline (0.0 to 1.0)."""
        kart_pos = self.kart.getPos()
        min_dist_sq = float('inf')
        closest_segment_index = -1
        num_segments = len(self.trackCurvePoints) - 1

        if num_segments < 1:
            return 0.0

        for i in range(num_segments):
            p1 = self.trackCurvePoints[i]
            p2 = self.trackCurvePoints[i+1]
            dist_sq = self._point_segment_distance_sq(kart_pos, p1, p2)
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest_segment_index = i

        if closest_segment_index == -1:
             return self.kart_progress # Keep last progress if error

        progress = float(closest_segment_index) / num_segments
        return progress

    def update(self):
        previous_progress = self.kart_progress
        self.kart_progress = self.calculate_kart_progress()
        
        # Detect direction and progress changes
        progress_change = self.kart_progress - previous_progress
        
        # Handle wrap-around at start/finish line
        if previous_progress > 0.9 and self.kart_progress < 0.1:
            # Moving forward across the start/finish line (end to start)
            progress_change = (1.0 - previous_progress) + self.kart_progress
        elif previous_progress < 0.1 and self.kart_progress > 0.9:
            # Moving backward across the start/finish line (start to end)
            progress_change = -(previous_progress + (1.0 - self.kart_progress))
        
        # Going forward on the track (correct direction)
        going_forward = progress_change > 0
        
        # Track maximum progress reached during this lap attempt
        # Only update when moving in the correct direction
        if going_forward:
            self.max_progress_reached = max(self.max_progress_reached, self.kart_progress)
        
        # Lap completion logic: crossing finish line after going around most of the track
        crossed_finish_line = previous_progress > 0.9 and self.kart_progress < 0.1 and going_forward
        left_start_area = self.kart_progress > 0.1
        
        if not self.has_left_start_line:
            # Wait until the kart has left the start area
            if left_start_area:
                self.has_left_start_line = True
            return False
        
        # Only count the lap if:
        # 1. Crossed finish line going forward
        # 2. Has gone through most of the track (at least 90% progress)
        # 3. Has left the start area
        if crossed_finish_line and self.max_progress_reached > 0.9 and self.has_left_start_line:
            # Increment lap counter on each crossing of the finish line
            self.current_lap += 1  # Increment lap counter
            # Reset max progress for next lap
            self.max_progress_reached = 0.0
            return True  # Lap completed this frame
        
        # Reset lap_completed flag when far enough away from start/finish line
        # to prepare for the next lap
        if self.kart_progress > 0.1 and self.kart_progress < 0.9:
            self.lap_completed = False
        
        return False  # Lap not completed this frame
    
    def has_completed_required_laps(self, required_laps):
        """
        Checks if the player has completed the required number of laps
        
        Args:
            required_laps: Number of laps required to finish the race
            
        Returns:
            bool: True if required laps completed, False otherwise
        """
        return self.current_lap >= required_laps
