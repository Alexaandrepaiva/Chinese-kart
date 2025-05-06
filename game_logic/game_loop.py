import time
from direct.task import Task
from utils.camera import update_camera # Assuming update_camera is in utils
import config  # Import the config module directly

class GameLoop:
    def __init__(self, app):
        self.app = app
        self.MAX_LAWN_TIME = config.MAX_LAWN_TIME  # Using the constant from config

    def calculate_race_positions(self):
        """
        Calculates the current position of each racer (including player)
        
        Returns:
            tuple: (player_position, total_racers) 
                   player_position is 1-based (1st, 2nd, etc.)
                   total_racers is the total number of karts in the race
        """
        # Create list of all racers with their progress
        racers = []
        
        # Player data
        player_data = {
            'is_player': True,
            'lap': self.app.progress_tracker.current_lap,
            'progress': self.app.progress_tracker.kart_progress
        }
        racers.append(player_data)
        
        # AI data
        if hasattr(self.app, 'ai_karts'):
            for ai_kart in self.app.ai_karts:
                ai_data = {
                    'is_player': False,
                    'lap': ai_kart.get('current_lap', 0),
                    'progress': ai_kart.get('lap_progress', 0)
                }
                racers.append(ai_data)
        
        # Sort racers by lap (descending) and progress (descending)
        racers.sort(key=lambda x: (-x['lap'], -x['progress']))
        
        # Find player's position
        player_position = 1  # Default to 1st place
        for i, racer in enumerate(racers):
            if racer['is_player']:
                player_position = i + 1  # positions are 1-based
                break
        
        total_racers = len(racers)
        return player_position, total_racers

    def update(self, task):
        # This method is called by the task manager ONLY when state is 'playing'
        dt = globalClock.getDt()

        # --- Update AI Karts ---
        if hasattr(self.app, 'ai_controllers'):
            for controller in self.app.ai_controllers:
                controller.update(dt)

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
        
        # Print debug info about laps when one is completed
        if lap_just_completed:
            print(f"Lap completed! Current lap: {self.app.progress_tracker.current_lap}, Required laps: {config.LAPS_TO_FINISH}")
            
        # Check if player has completed the required number of laps
        if self.app.progress_tracker.current_lap >= config.LAPS_TO_FINISH:
            print(f"Race finished! Completed all {config.LAPS_TO_FINISH} laps.")
            self.app.state_manager.game_won()
            self.app.run_timer = False  # Stop timer
            return Task.done # Stop the loop

        # Calculate current race positions
        player_position, total_racers = self.calculate_race_positions()

        # Update camera
        update_camera(self.app.cam, self.app.kart, dt)

        # Update HUD display with speed, timer, position, and lap info
        self.app.hud_display.update(
            velocity=self.app.physics.velocity, 
            timer_seconds=self.app.timer_elapsed if self.app.run_timer else 0.0,
            position=player_position,
            total_racers=total_racers,
            current_lap=self.app.progress_tracker.current_lap,
            total_laps=config.LAPS_TO_FINISH
        )

        return Task.cont # Continue task next frame
