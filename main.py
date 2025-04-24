import sys
import time
import math
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, Vec3, Point3, loadPrcFileData
from direct.task import Task

# Load default config
loadPrcFileData('', 'window-title Chinese Kart')
loadPrcFileData('', 'win-size 1200 800')
loadPrcFileData('', 'sync-video #t') # Try enabling vsync
loadPrcFileData('', 'show-frame-rate-meter #t') # Show FPS meter

# Import game utilities
from utils.lighting import setup_lighting
# from utils.camera import update_camera, setup_camera_transition # Moved to game_loop/game_state

# Import game objects
from game_objects.ground import create_ground
from game_objects.track import create_track
from game_objects.kart import create_kart

# Import physics
from physics.kart_physics import KartPhysics

# Import UI
from ui.menus import MenuManager
from ui.minimap import Minimap
from ui.speed_display import SpeedDisplay

# Import new game logic components
from game_logic.game_state import GameStateManager
from game_logic.game_loop import GameLoop
from utils.progress_tracker import ProgressTracker

class KartGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # --- Core variables needed by multiple components ---
        # Track game time - managed by GameLoop, but might be needed for display
        self.game_start_time = 0
        self.game_time = 0
        # Lawn timer - managed by GameLoop
        self.lawn_timer = 0

        # --- Basic window setup ---
        self.disableMouse()
        # Properties set via loadPrcFileData now
        # props = WindowProperties()
        # props.setTitle("Chinese Kart")
        # props.setSize(1200, 800)
        # self.win.requestProperties(props)
        self.setBackgroundColor(0.5, 0.7, 1.0)

        # --- Scene Graph Setup ---
        self.gameRoot = self.render.attachNewNode("GameRoot")
        # GameStateManager will handle showing/hiding

        # --- Lighting ---
        setup_lighting(self.render)

        # --- Game Object Creation ---
        self.ground = create_ground(self.gameRoot, self.loader)
        track_data = create_track(self.gameRoot)
        self.track = track_data[0]
        self.trackCurvePoints = track_data[1]
        # self.trackPoints = track_data[2] # Currently unused? Remove if not needed

        self.kart = create_kart(self.gameRoot, self.loader)

        # --- Core Components Initialization ---
        self.physics = KartPhysics(self.kart)
        self.progress_tracker = ProgressTracker(self.kart, self.trackCurvePoints)
        self.state_manager = GameStateManager(self)
        self.game_loop = GameLoop(self) # Handles the 'playing' state updates

        # --- UI Initialization ---
        self.menu_manager = MenuManager(self)
        self.menu_manager.create_start_menu(self.state_manager.start_game) # Use state manager

        self.minimap = Minimap(self, self.trackCurvePoints, self.kart)
        self.speed_display = SpeedDisplay(self)

        # --- Input Handling ---
        self.physics.setup_controls(self.accept)
        self.accept("escape", self.state_manager.toggle_pause) # Use state manager

        # --- Initial State ---
        self.state_manager.show_menu() # Start by showing the menu
        # print("Game Initialized.") # State manager handles prints

    # The core game update task - delegates based on state
    def updateGame(self, task):
        """
        Main task loop. Checks the current game state and calls the appropriate update logic.
        """
        if self.state_manager.is_state('playing'):
            # If playing, delegate to the GameLoop's update method
            return self.game_loop.update(task)
        else:
            # If paused, menu, game_over, or game_won, just continue the task
            # without running game logic. This prevents dt issues on resume.
            # The GameStateManager handles starting/stopping this task appropriately.
            return Task.cont

# --- Application Entry Point ---
if __name__ == "__main__":
    app = KartGame()
    app.run()