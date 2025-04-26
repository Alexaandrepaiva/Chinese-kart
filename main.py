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
from game_objects.starting_line import create_starting_line

# Import physics
from physics.kart_physics import KartPhysics

# Import UI
from ui.menus import MenuManager
from ui.minimap import Minimap
from ui.hud_display import HUDDisplay
from ui.start_countdown import StartCountdown

# Import new game logic components
from game_logic.game_state import GameStateManager
from game_logic.game_loop import GameLoop
from utils.progress_tracker import ProgressTracker

class KartGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Set explicit near/far clipping planes
        self.camLens.setNearFar(5, 5000) # Near=5 units, Far=5000 units

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
        
        # Create the starting line
        self.starting_line = create_starting_line(self.gameRoot, self.trackCurvePoints)

        self.kart, self.kart_collider = create_kart(self.gameRoot, self.loader)
        # --- Kart Position Logging for Object Placement ---
        # This is useful for placing new objects at the given position
        # Uncomment both lines above to use it
        from utils.object_placement import log_kart_position_every_second
        log_kart_position_every_second(self.kart)

        # --- Collision Traverser and Handler ---
        from panda3d.core import CollisionTraverser
        from panda3d.core import CollisionHandlerEvent
        self.cTrav = CollisionTraverser()
        self.collision_handler = CollisionHandlerEvent()
        self.collision_handler.add_in_pattern('%fn-into-%in')
        self.cTrav.add_collider(self.kart_collider, self.collision_handler)
        # Listen for kart into barrier event
        self.accept('kart_collision-into-barrier_collision', self.on_kart_barrier_collision)

        # --- Core Components Initialization ---
        self.physics = KartPhysics(self.kart)
        self.progress_tracker = ProgressTracker(self.kart, self.trackCurvePoints)
        self.state_manager = GameStateManager(self)
        self.game_loop = GameLoop(self) # Handles the 'playing' state updates

        # --- UI Initialization ---
        self.menu_manager = MenuManager(self)
        self.menu_manager.create_start_menu(self.state_manager.start_game) # Use state manager

        self.minimap = Minimap(self, self.trackCurvePoints, self.kart)
        self.hud_display = HUDDisplay(self)

        # --- Countdown (block input until done) ---
        self.input_blocked = False
        self.waiting_for_camera_transition = False
        self.countdown = StartCountdown(self, on_finish=self._on_countdown_finish)

        # --- Input Handling ---
        self.physics.setup_controls(self.accept)
        self.accept("escape", self.state_manager.toggle_pause) # Use state manager

        # --- Initial State ---
        self.state_manager.show_menu() # Start by showing the menu
        # print("Game Initialized.") # State manager handles prints

    def block_input(self):
        self.input_blocked = True
        self.physics.reset()  # Make sure no movement
        self.countdown.text.hide()  # Hide countdown if blocking input for camera

    def unblock_input(self):
        self.input_blocked = False

    def _on_countdown_finish(self):
        self.unblock_input()
        self.run_timer = True
        self.timer_start_time = time.time()
        self.timer_elapsed = 0.0


    # --- Collision: Stop kart on barrier ---
    def on_kart_barrier_collision(self, entry):
        # Stop the kart instantly
        self.physics.velocity = 0
        # Optionally, move the kart slightly back to prevent sticking
        from panda3d.core import Vec3
        backward = -self.kart.getQuat().getForward() * 0.5
        pos = self.kart.getPos() + Vec3(backward.x, backward.y, 0)
        self.kart.setPos(pos)

    # The core game update task - delegates based on state
    def updateGame(self, task):
        """
        Main task loop. Checks the current game state and calls the appropriate update logic.
        """
        from utils.camera import update_camera
        update_camera(self.cam, self.kart)

        if self.state_manager.is_state('playing'):
            # If waiting for camera transition, poll is_transitioning
            if self.waiting_for_camera_transition:
                from utils import camera as camera_utils
                if not camera_utils.is_transitioning:
                    self.waiting_for_camera_transition = False
                    self.countdown.show_countdown()
                self.physics.reset()
                return Task.cont
            if self.input_blocked:
                # Block all movement by resetting physics and skipping update
                self.physics.reset()
                return Task.cont
            # If playing and input is allowed, delegate to the GameLoop's update method
            return self.game_loop.update(task)
        else:
            # If paused, menu, game_over, game_won, just continue the task
            # without running game logic. This prevents dt issues on resume.
            # The GameStateManager handles starting/stopping this task appropriately.
            return Task.cont

# --- Application Entry Point ---
if __name__ == "__main__":
    app = KartGame()
    app.run()