import sys
import time
from panda3d.core import Vec3, Vec4
from direct.task import Task
import config

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

            # Get configuration settings
            game_config = self.app.menu_manager.get_game_config()
            player_kart_color = game_config["kart_color"]
            num_ai_karts = game_config["ai_kart_count"]
            ai_colors = game_config["ai_colors"]  # Get the available colors for AI
            
            # Update global difficulty setting
            difficulty = game_config["difficulty"]
            config.set_difficulty(difficulty)
            
            # Update global laps count setting
            laps_count = game_config["laps_count"]
            config.LAPS_TO_FINISH = laps_count
            
            print(f"Starting game with kart color: {player_kart_color}, {num_ai_karts} AI karts, difficulty: {difficulty}, laps: {laps_count}")

            # Hide all menus to ensure no menu is visible
            self.app.menu_manager.hide_menu()
            if hasattr(self.app.menu_manager, 'pause_menu') and self.app.menu_manager.pause_menu:
                self.app.menu_manager.hide_pause_menu()
            if hasattr(self.app.menu_manager, 'game_over_menu') and self.app.menu_manager.game_over_menu:
                self.app.menu_manager.hide_game_over_menu()
            if hasattr(self.app.menu_manager, 'game_won_menu') and self.app.menu_manager.game_won_menu:
                self.app.menu_manager.hide_game_won_menu()
            if hasattr(self.app.menu_manager, 'config_menu') and self.app.menu_manager.config_menu:
                self.app.menu_manager.config_menu.hide()

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

            # Initialize HUD with the starting position (1) and total racers
            total_racers = 1 + num_ai_karts  # Player + AI karts
            self.app.hud_display.update(
                velocity=0,
                timer_seconds=0,
                position=1,  # Start in 1st position
                total_racers=total_racers,
                current_lap=0,  # Starting on first lap (0 will display as "Lap 1" in HUD)
                total_laps=laps_count
            )

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

            # Update player kart color from configuration
            self.app.kart.setColor(player_kart_color)
            
            self.app.kart.setPos(player_kart_start_pos)
            self.app.kart.lookAt(start_pos_on_track + track_forward_dir * 10) # Look further down the track


            # --- AI Karts Setup ---
            self.app.ai_karts = [] # Clear previous AI karts if any
            self.app.ai_controllers = [] # Clear previous AI controllers
            
            # Use AI colors from the configuration 
            # If we have more AI karts than colors, we'll cycle through the available colors
            spacing = 3.0 # Increased spacing between karts for better starting positions
            
            # Karts will be positioned in a grid-like formation, with none directly behind the player
            # Calculate positions differently to avoid center spot (player position)
            for i in range(num_ai_karts):
                # Get color for this AI kart
                ai_color = ai_colors[i % len(ai_colors)]
                
                # Create AI kart
                ai_kart_node, ai_collider = create_kart(self.app.gameRoot, self.app.loader, color=ai_color, show_collider=False)
                
                # Configurar colisão para AI karts
                ai_collider.node().setFromCollideMask(0x1 | 0x2)  # AI Karts will test for collisions with barriers and other karts
                ai_collider.node().setIntoCollideMask(0x2)  # Other karts can collide with this kart
                
                # Configurar o pusher para o kart da AI para evitar atravessamento
                self.app.pusher.add_collider(ai_collider, ai_kart_node)
                self.app.cTrav.add_collider(ai_collider, self.app.pusher)
                
                # Registrar o evento de colisão específico para este kart AI
                ai_kart_index = len(self.app.ai_karts)
                if hasattr(self.app, 'accept'):
                    # Registrar tanto colisões com barreiras quanto com outros karts
                    barrier_event_name = f'pusher_kart_collision-into-barrier_collision'
                    kart_event_name = f'pusher_kart_collision-into-kart_collision'
                    self.app.accept(barrier_event_name, self.app.on_kart_barrier_collision)
                    self.app.accept(kart_event_name, self.app.on_kart_kart_collision)
                
                # Position AI karts
                # Determine the row and column for a grid-like arrangement
                # Calculate lateral position - alternate left and right sides
                if i % 2 == 0:  # Even indices: position on the left
                    lateral_offset = -spacing * (1 + i // 2)  # Increasing distance to the left
                else:  # Odd indices: position on the right
                    lateral_offset = spacing * (1 + i // 2)  # Increasing distance to the right
                
                # Stagger rows (distance behind the player)
                row = (i // 2) + 1  # Each left-right pair forms a row
                row_offset = -3.0 - (row * 2.0)  # Each row is further back
                
                # Apply calculated offsets
                ai_start_offset_forward = track_forward_dir * row_offset
                ai_kart_start_pos = start_pos_on_track + ai_start_offset_forward + (track_right_dir * lateral_offset)
                ai_kart_start_pos.setZ(self.app.track.getZ() + 0.5) # Adjust Z
                
                ai_kart_node.setPos(ai_kart_start_pos)
                ai_kart_node.lookAt(start_pos_on_track + track_forward_dir * 10) # Look further down the track
                
                ai_kart_data = {
                    'node': ai_kart_node, 
                    'collider': ai_collider, 
                    'color': ai_color,
                    'name': f'AI Racer {i+1}',
                    'lap_progress': 0,
                    'lap_times': [],
                    'current_lap': 0,
                    'finish_time': None
                }
                self.app.ai_karts.append(ai_kart_data)

                # Create and store AI Controller for this kart
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
