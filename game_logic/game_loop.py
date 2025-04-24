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

        # Update total game time
        self.app.game_time = time.time() - self.app.game_start_time

        # Update physics
        road_width = 10.0
        track_width = 20.0
        self.app.physics.update(dt, self.app.track.getZ(), self.app.trackCurvePoints, road_width, track_width)

        # Check terrain and update lawn timer
        if self.app.physics.current_terrain == 'lawn':
            self.app.lawn_timer += dt
            if self.app.lawn_timer >= self.MAX_LAWN_TIME:
                self.app.state_manager.game_over("Player spent too much time on the lawn.")
                return Task.done # Stop the loop
        else:
            self.app.lawn_timer = 0 # Reset timer

        # Update Kart Progress and check for lap completion
        lap_just_completed = self.app.progress_tracker.update()
        if lap_just_completed:
             self.app.state_manager.game_won()
             return Task.done # Stop the loop

        # Update camera
        update_camera(self.app.cam, self.app.kart, dt)

        # Update speed display
        self.app.speed_display.update(self.app.physics.velocity)

        return Task.cont # Continue task next frame
