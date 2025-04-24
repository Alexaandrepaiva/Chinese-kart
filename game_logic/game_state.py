import sys
import time
from panda3d.core import Vec3
from direct.task import Task

# Import necessary components from the main game or other modules
# Assuming these are accessible or passed in
from utils.camera import setup_camera_transition

class GameStateManager:
    def __init__(self, app):
        self.app = app  # Keep a reference to the main application
        self.current_state = 'menu' # Initial state

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
        self.app.speed_display.hide()
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

            # Reset timers and progress
            self.app.game_start_time = time.time()
            self.app.game_time = 0
            self.app.lawn_timer = 0
            self.app.progress_tracker.reset()

            # Show game elements
            self.app.gameRoot.show()
            self.app.minimap.show()
            self.app.speed_display.show()

            # --- Kart Starting Position ---
            start_pos = self.app.trackCurvePoints[0]
            end_pos = self.app.trackCurvePoints[-1]
            start_dir = (start_pos - end_pos).normalized()
            kart_start_pos = start_pos + start_dir * 3
            kart_start_pos.setZ(self.app.track.getZ() + 0.5)
            self.app.kart.setPos(kart_start_pos)
            self.app.kart.lookAt(self.app.trackCurvePoints[-1])

            # Reset physics
            self.app.physics.reset()

            # --- Camera setup ---
            sky_view_offset = Vec3(0, -10, 50)
            initial_cam_pos = self.app.kart.getPos() + sky_view_offset
            self.app.cam.setPos(initial_cam_pos)
            self.app.cam.lookAt(self.app.kart.getPos() + Vec3(0, 0, 2))
            setup_camera_transition(self.app.cam, self.app.kart)

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
            self.app.speed_display.hide()
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
            self.app.speed_display.show()
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
            self.app.speed_display.hide()

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
            print(f"Lap Completed! Time: {self.app.game_time:.2f} seconds")
            self.change_state('game_won')

            # Hide game elements
            self.app.minimap.hide()
            self.app.speed_display.hide()

            # Create and show game won menu
            self.app.menu_manager.create_game_won_menu(
                game_time=self.app.game_time,
                restart_callback=self.start_game # Use start_game for restart
            )
            self.app.menu_manager.show_game_won_menu()
            # Stop game loop
            self.app.taskMgr.remove("updateGameTask")
