import sys
import time
from panda3d.core import Vec3, Vec4
from direct.task import Task

# Import necessary components from the main game or other modules
# Assuming these are accessible or passed in
from utils.camera import setup_camera_transition, set_view_mode
from game_objects.kart import create_kart
from game_logic.ai_controller import AIController

class GameStateManager:
    def __init__(self, app):
        self.app = app  # Keep a reference to the main application
        self.current_state = 'menu' # Initial state
        self.app.ai_karts = [] # Initialize ai_karts list
        self.app.ai_controllers = [] # Initialize ai_controllers list

    def change_state(self, new_state):
        print(f"Changing state from {self.current_state} to {new_state}")
        self.current_state = new_state

    def is_state(self, state_name):
        return self.current_state == state_name

    def show_menu(self):
        self.change_state('menu')
        self.app.menu_manager.show_menu()
        self.app.gameRoot.hide()
        self.app.minimap.hide()
        self.app.hud_display.hide()
        self.app.taskMgr.remove("updateGameTask") # Stop game loop when in menu

    def start_game(self):
        if not self.is_state('playing'): # Prevent starting if already playing
            print("Starting Game!")
            self.change_state('playing')

            # Hide menus (Original logic, ensuring each menu exists before hiding)
            self.app.menu_manager.hide_menu()
            if hasattr(self.app.menu_manager, 'pause_menu') and self.app.menu_manager.pause_menu:
                self.app.menu_manager.hide_pause_menu()
            if hasattr(self.app.menu_manager, 'game_over_menu') and self.app.menu_manager.game_over_menu:
                self.app.menu_manager.hide_game_over_menu()
            if hasattr(self.app.menu_manager, 'game_won_menu') and self.app.menu_manager.game_won_menu:
                self.app.menu_manager.hide_game_won_menu()

            # Clean up any existing AI karts before creating new ones
            if hasattr(self.app, 'ai_karts') and self.app.ai_karts:
                for ai_kart in self.app.ai_karts:
                    if 'node' in ai_kart and ai_kart['node']:
                        ai_kart['node'].removeNode()
                    if 'collider' in ai_kart and ai_kart['collider']:
                        ai_kart['collider'].removeNode()

            # Reset timers and progress
            self.app.game_start_time = time.time()
            self.app.game_time = 0
            self.app.lawn_timer = 0
            self.app.progress_tracker.reset()

            # --- TIMER RESET ---
            self.app.run_timer = False
            self.app.timer_start_time = None
            self.app.timer_elapsed = 0.0

            # Show game elements
            self.app.gameRoot.show()
            self.app.minimap.show()
            self.app.hud_display.show()

            # --- Kart Starting Position ---
            start_pos_on_track = self.app.trackCurvePoints[0]
            # Ensure we look towards a point further along the track for initial orientation
            look_at_point = self.app.trackCurvePoints[1] if len(self.app.trackCurvePoints) > 1 else self.app.trackCurvePoints[0] + Vec3(0, -1, 0)


            # Calculate the forward direction of the track at the start
            track_forward_dir = (look_at_point - start_pos_on_track).normalized()
            
            # Calculate a right vector (perpendicular to forward and up)
            # Assuming standard Z-up coordinate system
            track_right_dir = track_forward_dir.cross(Vec3.up()) 
            if track_right_dir.length_squared() < 0.001: # If forward is (nearly) up/down
                 track_right_dir = Vec3(1,0,0) # Default to X-axis


            # Player kart positioning (slightly behind the actual starting line for visual appeal)
            player_start_offset = track_forward_dir * -2 # Offset slightly behind the line
            player_kart_start_pos = start_pos_on_track + player_start_offset
            player_kart_start_pos.setZ(self.app.track.getZ() + 0.5) # Adjust Z based on track height
            self.app.kart.setPos(player_kart_start_pos)
            self.app.kart.lookAt(start_pos_on_track + track_forward_dir * 10) # Look further down the track


            # --- AI Karts Setup ---
            self.app.ai_karts = [] # Clear previous AI karts if any
            self.app.ai_controllers = [] # Clear previous AI controllers
            ai_colors = [
                Vec4(0, 0, 1, 1),  # Blue
                Vec4(0, 1, 0, 1),  # Green
                Vec4(1, 1, 0, 1),  # Yellow
                Vec4(0.5, 0, 0.5, 1) # Purple
            ]
            num_ai_karts = 4
            spacing = 2.0 # Spacing between karts
            
            # Stagger AI karts slightly and place them side-by-side
            # Total width for AI karts lineup
            total_lineup_width = (num_ai_karts -1) * spacing
            
            for i in range(num_ai_karts):
                # Create AI kart
                ai_kart_node, ai_collider = create_kart(self.app.gameRoot, self.app.loader, color=ai_colors[i % len(ai_colors)])
                
                # Position AI karts
                # Offset from the center of the lineup
                lateral_offset = (i - (num_ai_karts - 1) / 2.0) * spacing
                ai_start_offset_forward = track_forward_dir * (-2 - (i * 0.5)) # Stagger them slightly behind each other
                
                ai_kart_start_pos = start_pos_on_track + ai_start_offset_forward + (track_right_dir * lateral_offset)
                ai_kart_start_pos.setZ(self.app.track.getZ() + 0.5) # Adjust Z
                
                ai_kart_node.setPos(ai_kart_start_pos)
                ai_kart_node.lookAt(start_pos_on_track + track_forward_dir * 10) # Look further down the track
                
                ai_kart_data = {
                    'node': ai_kart_node, 
                    'collider': ai_collider, 
                    'color': ai_colors[i % len(ai_colors)],
                    'name': f'AI Racer {i+1}',
                    'lap_progress': 0,
                    'lap_times': [],
                    'current_lap': 0,
                    'finish_time': None
                }
                self.app.ai_karts.append(ai_kart_data)

                # Create and store AI Controller for this kart
                # Ensure self.app.trackCurvePoints are LPoint3f or compatible for AIController
                # The AIController expects a list of LPoint3f for track_points.
                # self.app.trackCurvePoints might be a list of Vec3. If so, they need conversion.
                # For now, assuming they are compatible or will be made compatible.
                if hasattr(self.app, 'trackCurvePoints') and self.app.trackCurvePoints:
                    controller = AIController(self.app, ai_kart_data, self.app.trackCurvePoints)
                    self.app.ai_controllers.append(controller)
                else:
                    print(f"Warning: Could not create AIController for {ai_kart_data['name']} due to missing track points.")

            # Reset physics for player (AI kart physics will need to be handled)
            self.app.physics.reset()

            # --- Camera setup ---
            sky_view_offset = Vec3(0, -10, 50)
            initial_cam_pos = self.app.kart.getPos() + sky_view_offset
            self.app.cam.setPos(initial_cam_pos)
            self.app.cam.lookAt(self.app.kart.getPos() + Vec3(0, 0, 2))

            # Ensure we're using third-person view when starting the game
            set_view_mode(3)  # 3 = third-person view

            setup_camera_transition(self.app.cam, self.app.kart)

            # --- Block input and wait for camera transition ---
            self.app.block_input()
            self.app.waiting_for_camera_transition = True

            # Start the game update task if not already running
            if not self.app.taskMgr.hasTaskNamed("updateGameTask"):
                 self.app.taskMgr.add(self.app.updateGame, "updateGameTask")


    def toggle_pause(self):
        if self.is_state('playing'):
            self.pause_game()
        elif self.is_state('paused'):
            self.resume_game()

    def pause_game(self):
         if self.is_state('playing'):
            self.change_state('paused')
            print("Game Paused")
            self.show_pause_menu()
            self.app.minimap.hide()
            self.app.hud_display.hide()
            # The update task continues but checks the state

    def show_pause_menu(self):
         if not hasattr(self.app.menu_manager, 'pause_menu') or not self.app.menu_manager.pause_menu:
            self.app.menu_manager.create_pause_menu(
                resume_callback=self.resume_game,
                restart_callback=self.restart_game_from_pause,
                quit_callback=self.quit_game
            )
         self.app.menu_manager.show_pause_menu()


    def resume_game(self):
        if self.is_state('paused'):
            self.change_state('playing')
            self.app.menu_manager.hide_pause_menu()
            self.app.minimap.show()
            self.app.hud_display.show()
            print("Game Resumed")

    def restart_game_from_pause(self):
        print("Restarting game from pause menu...")
        self.app.menu_manager.hide_pause_menu()
        # Stop the current game task explicitly before starting again
        self.app.taskMgr.remove("updateGameTask")
        self.start_game() # Call start_game which resets everything

    def quit_game(self):
        print("Quitting game...")
        sys.exit()

    def game_over(self, reason=""):
        if not self.is_state('game_over'): # Prevent multiple calls
            print(f"Game Over! {reason}")
            self.change_state('game_over')

            # Hide game elements
            self.app.minimap.hide()
            self.app.hud_display.hide()

            # Create and show game over menu
            self.app.menu_manager.create_game_over_menu(
                game_time=self.app.game_time,
                restart_callback=self.start_game # Use start_game for restart
            )
            self.app.menu_manager.show_game_over_menu()
            # Stop game loop
            self.app.taskMgr.remove("updateGameTask")


    def game_won(self):
         if not self.is_state('game_won'): # Prevent multiple calls
            player_finish_time = self.app.game_time # This is self.app.timer_elapsed when game_won is called
            print(f"Race Completed! Time: {player_finish_time:.2f} seconds")
            self.change_state('game_won')

            # --- Determine Rankings ---
            all_racers = []
            # Player data
            player_data = {
                'name': 'Player',
                'laps': self.app.progress_tracker.current_lap, # Show actual number of completed laps
                'progress': 1.0, # Full progress for the completed lap
                'finish_time': player_finish_time,
                'is_player': True
            }
            all_racers.append(player_data)

            # AI data
            if hasattr(self.app, 'ai_karts'):
                for ai_kart_info in self.app.ai_karts:
                    ai_laps = ai_kart_info.get('current_lap', 0)
                    ai_finish_time = ai_kart_info.get('finish_time', None)
                    ai_progress = ai_kart_info.get('lap_progress', 0)
                    
                    # If AI finished the lap before player, its finish_time is already recorded.
                    # If AI is still racing, its finish_time is None.
                    # If AI finished after player, its finish_time might be recorded by its controller
                    # just before or after this game_won state change, ensure it's captured if available.
                    
                    all_racers.append({
                        'name': ai_kart_info.get('name', 'AI Racer'),
                        'laps': ai_laps,
                        'progress': ai_progress if ai_finish_time is None else 1.0,
                        'finish_time': ai_finish_time,
                        'is_player': False
                    })
            
            # Sort racers: 
            # 1. By laps completed (descending).
            # 2. By finish_time (ascending, None means not finished, so they come after). Handle -1 for AI early finish. 
            # 3. By progress on current lap (descending for those not finished).
            def sort_key(racer):
                laps = racer['laps']
                time = racer['finish_time']
                progress = racer['progress']

                # Primary sort: Laps (higher is better)
                sort_laps = -laps 

                # Secondary sort: Finish Time (lower is better for finished racers)
                # Racers who haven't finished (time is None) are ranked lower than those who have.
                # AI karts with finish_time == -1 finished but their time might not be comparable, rank them after timed finishers.
                if time is None:
                    sort_time = float('inf') # Not finished, rank last among same-lap racers
                elif time == -1: # AI finished, but timer context might be off (e.g. player didn't move)
                    sort_time = float('inf') -1 # Rank just above those who didn't finish at all
                else:
                    sort_time = time
                
                # Tertiary sort: Progress (higher is better for those on the same lap and not finished)
                sort_progress = -progress if time is None else 0

                return (sort_laps, sort_time, sort_progress)

            all_racers.sort(key=sort_key)
            
            # Assign positions
            for i, racer in enumerate(all_racers):
                racer['position'] = i + 1

            # Hide game elements
            self.app.minimap.hide()
            self.app.hud_display.hide()

            # Create and show game won menu
            self.app.menu_manager.create_game_won_menu(
                game_time=player_finish_time, # Player's time
                rankings=all_racers, # Pass sorted rankings
                restart_callback=self.start_game # Use start_game for restart
            )
            self.app.menu_manager.show_game_won_menu()
            # Stop game loop
            self.app.taskMgr.remove("updateGameTask")
