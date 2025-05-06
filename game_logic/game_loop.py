import time
from direct.task import Task
from utils.camera import update_camera # Assuming update_camera is in utils

class GameLoop:
    def __init__(self, app):
        self.app = app
        self.MAX_LAWN_TIME = 3 # Could be moved to a config file later

    def update(self, task):
        # This method is called by the task manager ONLY when state is 'playing'
        dt = globalClock.getDt()

        # --- TIMER LOGIC ---
        # Start timer when kart first moves (velocity > 0.1 and timer not started)
        if not hasattr(self.app, 'run_timer'):  # Initialize if not present
            self.app.run_timer = False
            self.app.timer_start_time = None
            self.app.timer_elapsed = 0.0

        if not self.app.run_timer and abs(self.app.physics.velocity) > 0.1:
            self.app.run_timer = True
            self.app.timer_start_time = time.time()
            self.app.timer_elapsed = 0.0

        # Update timer if running
        if self.app.run_timer:
            self.app.timer_elapsed = time.time() - self.app.timer_start_time
        
        # Update total game time (legacy, may be used elsewhere)
        self.app.game_time = time.time() - self.app.game_start_time

        # Update physics with correct track dimensions
        # These values should match those used in track.py
        road_width = 15.0  # Width of the actual drivable road from track.py
        sand_border_width = 12.0  # Width of the sand border on each side from track.py
        track_width = road_width + (sand_border_width * 2)  # Total width including sand borders
        stripe_width = 1.0  # Width of the warning stripes from track.py
        
        self.app.physics.update(dt, self.app.track.getZ(), self.app.trackCurvePoints, 
                                road_width, track_width, stripe_width)

        # Check terrain and update lawn timer
        if self.app.physics.current_terrain == 'lawn':
            self.app.lawn_timer += dt
            if self.app.lawn_timer >= self.MAX_LAWN_TIME:
                self.app.state_manager.game_over("Player spent too much time on the lawn.")
                self.app.run_timer = False  # Stop timer
                return Task.done # Stop the loop
        else:
            self.app.lawn_timer = 0 # Reset timer

        # Update Kart Progress and check for lap completion
        lap_just_completed = self.app.progress_tracker.update()
        if lap_just_completed:
             self.app.state_manager.game_won()
             self.app.run_timer = False  # Stop timer
             return Task.done # Stop the loop

        # Update camera
        update_camera(self.app.cam, self.app.kart, dt)

        # Update speed and timer display
        self.app.hud_display.update(self.app.physics.velocity, self.app.timer_elapsed if self.app.run_timer else 0.0)

        return Task.cont # Continue task next frame
