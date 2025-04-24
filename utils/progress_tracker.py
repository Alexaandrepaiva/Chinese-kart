import math
from panda3d.core import Vec3

class ProgressTracker:
    def __init__(self, kart, track_curve_points):
        self.kart = kart
        self.trackCurvePoints = track_curve_points
        self.kart_progress = 0.0
        self.max_progress_reached = 0.0
        self.lap_completed = False

    def reset(self):
        self.kart_progress = 0.0
        self.max_progress_reached = 0.0
        self.lap_completed = False

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
        self.max_progress_reached = max(self.max_progress_reached, self.kart_progress)

        # Check for lap completion
        crossed_start_line_forward = self.kart_progress < 0.05 and previous_progress > 0.95
        if crossed_start_line_forward and self.max_progress_reached > 0.90:
            if not self.lap_completed:
                self.lap_completed = True
                return True # Lap completed this frame
        return False # Lap not completed this frame
