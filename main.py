import sys
import time
import math
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, Vec3, Point3
from direct.task import Task

# Import game utilities
from utils.lighting import setup_lighting
from utils.camera import update_camera, setup_camera_transition

# Import game objects
from game_objects.ground import create_ground
from game_objects.track import create_track, debug_draw_spline
from game_objects.kart import create_kart

# Import physics
from physics.kart_physics import KartPhysics

# Import UI
from ui.menus import MenuManager
from ui.minimap import Minimap
from ui.speed_display import SpeedDisplay

class KartGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Game state ('menu', 'playing', 'paused', 'game_over', 'game_won')
        self.gameState = 'menu'
        
        # Track game time
        self.game_start_time = 0
        self.game_time = 0
        
        # Lawn timer variables
        self.lawn_timer = 0
        self.MAX_LAWN_TIME = 3  # Maximum time allowed on lawn (in seconds)

        # Lap tracking variables
        self.kart_progress = 0.0       # Current progress around the track (0.0 to 1.0)
        self.max_progress_reached = 0.0 # Max progress achieved this lap attempt
        self.lap_completed = False     # Flag for lap completion

        # Basic window setup
        self.disableMouse()
        props = WindowProperties()
        props.setTitle("Chinese Kart")
        props.setSize(1200, 800)
        self.win.requestProperties(props)
        self.setBackgroundColor(0.5, 0.7, 1.0)  # Sky blue background

        # Setup scene graph root for game elements
        # Initially hide the game root, show it when game starts
        self.gameRoot = self.render.attachNewNode("GameRoot")
        self.gameRoot.hide()

        # Add basic lighting (attached to render so it's always there)
        setup_lighting(self.render)

        # Create game elements (ground, track, kart) but don't show yet
        self.ground = create_ground(self.gameRoot, self.loader)
        
        # Create track and get track points
        track_data = create_track(self.gameRoot)
        self.track = track_data[0]
        self.trackCurvePoints = track_data[1]
        self.trackPoints = track_data[2]
        
        # Create kart
        self.kart = create_kart(self.gameRoot, self.loader)

        # Initialize the physics engine for kart
        self.physics = KartPhysics(self.kart)
        self.physics.setup_controls(self.accept)

        # Initialize UI manager
        self.menu_manager = MenuManager(self)
        self.menu_manager.create_start_menu(self.startGame)

        # Initialize the minimap (but don't show it yet)
        self.minimap = Minimap(self, self.trackCurvePoints, self.kart)
        
        # Initialize the speed display (but don't show it yet)
        self.speed_display = SpeedDisplay(self)

        # Exit handling - Changed to toggle pause
        self.accept("escape", self.togglePause)

        print("Game Initialized, showing menu.")

    def showMenu(self):
        # Show the menu and hide game elements
        self.menu_manager.show_menu()
        self.gameRoot.hide()
        self.minimap.hide()  # Hide minimap in menu
        self.speed_display.hide()  # Hide speed display in menu
        # Potentially reset camera to a menu view if desired
        # self.cam.setPos(0, 0, 50)
        # self.cam.lookAt(0, 0, 0)

    def startGame(self):
        print("Starting Game!")
        # Hide all menus
        self.menu_manager.hide_menu()
        self.menu_manager.hide_pause_menu()
        if hasattr(self.menu_manager, 'game_over_menu') and self.menu_manager.game_over_menu:
            self.menu_manager.hide_game_over_menu()
        if hasattr(self.menu_manager, 'game_won_menu') and self.menu_manager.game_won_menu: # Hide win menu if exists
            self.menu_manager.hide_game_won_menu()

        # Reset timers and lap state
        self.game_start_time = time.time()
        self.game_time = 0
        self.lawn_timer = 0
        self.kart_progress = 0.0
        self.max_progress_reached = 0.0
        self.lap_completed = False
        
        self.gameState = 'playing'
        self.gameRoot.show()  # Show the game world
        self.minimap.show()  # Show the minimap during gameplay
        self.speed_display.show()  # Show the speed display during gameplay

        # --- Change Kart Starting Position and Orientation for Reverse Direction ---
        # Use the first generated spline point as reference
        start_pos = self.trackCurvePoints[0]
        # Use the *last* spline point to get initial direction (for reverse travel)
        end_pos = self.trackCurvePoints[-1]
        start_dir = start_pos - end_pos # Direction from last point TO point 0
        start_dir.normalize()

        # Position the kart slightly *past* point 0 along the reversed direction
        # (effectively placing it between the last point and point 0)
        kart_start_pos = start_pos + start_dir * 3
        kart_start_pos.setZ(self.track.getZ() + 0.5) # Track Z + half kart height
        self.kart.setPos(kart_start_pos)
        # Look towards the *last* point on the track
        self.kart.lookAt(self.trackCurvePoints[-1])

        # Reset physics
        self.physics.reset()

        # --- Camera setup remains the same ---
        # Set camera to initial "sky view"
        sky_view_offset = Vec3(0, -10, 50) # Offset relative to kart, high up
        initial_cam_pos = self.kart.getPos() + sky_view_offset
        self.cam.setPos(initial_cam_pos)
        self.cam.lookAt(self.kart.getPos() + Vec3(0, 0, 2)) # Look towards the kart from above
        
        # Start smooth camera transition (will now start from the sky view)
        setup_camera_transition(self.cam, self.kart)

        # Make sure the game update task isn't already running
        self.taskMgr.remove("updateGameTask")
        # Start the game update task
        self.taskMgr.add(self.updateGame, "updateGameTask")

    def togglePause(self):
        if self.gameState == 'playing':
            self.gameState = 'paused'
            print("Game Paused")
            self.showPauseMenu()
            self.minimap.hide()  # Hide minimap when paused
            self.speed_display.hide()  # Hide speed display when paused
            # Keep task running but it will check state
        elif self.gameState == 'paused':
            self.resumeGame()

    def showPauseMenu(self):
        # Create pause menu if it doesn't exist yet
        if not hasattr(self.menu_manager, 'pause_menu') or not self.menu_manager.pause_menu:
            self.menu_manager.create_pause_menu(
                resume_callback=self.resumeGame,
                restart_callback=self.restartGameFromPause,
                quit_callback=self.quitGame
            )
        self.menu_manager.show_pause_menu()

    def resumeGame(self):
        if self.gameState == 'paused':
            self.gameState = 'playing'
            self.menu_manager.hide_pause_menu()
            self.minimap.show()  # Show minimap when resuming
            self.speed_display.show()  # Show speed display when resuming
            print("Game Resumed")

    def restartGameFromPause(self):
        print("Restarting game from pause menu...")
        self.menu_manager.hide_pause_menu()
        # Stop the current game task before starting a new one
        self.taskMgr.remove("updateGameTask")
        # Call start game which resets everything
        self.startGame()

    def quitGame(self):
        print("Quitting game...")
        sys.exit()
        
    def gameOver(self):
        print("Game Over! Player spent too much time on the lawn.")
        self.gameState = 'game_over'
        
        # Hide game elements
        self.minimap.hide()
        self.speed_display.hide()
        
        # Create and show game over menu with current game time
        self.menu_manager.create_game_over_menu(
            game_time=self.game_time,
            restart_callback=self.startGame
        )
        self.menu_manager.show_game_over_menu()

    def gameWon(self):
        print(f"Lap Completed! Time: {self.game_time:.2f} seconds")
        self.gameState = 'game_won'
        
        # Hide game elements
        self.minimap.hide()
        self.speed_display.hide()
        
        # Create and show game won menu
        self.menu_manager.create_game_won_menu(
            game_time=self.game_time,
            restart_callback=self.startGame
        )
        self.menu_manager.show_game_won_menu()

    def _point_segment_distance_sq(self, p, a, b):
        """Calculate the squared distance from point p to line segment (a, b)."""
        l2 = (b - a).lengthSquared()
        if l2 == 0.0:
            return (p - a).lengthSquared()
        # Consider the line extending the segment, parameterized as a + t (b - a).
        # We find projection of point p onto the line.
        # It falls where t = [(p-a) . (b-a)] / |b-a|^2
        t = (p - a).dot(b - a) / l2
        t = max(0, min(1, t))  # We clamp t from [0,1] to handle points outside the segment
        vector_ab = Vec3(b - a) # Explicitly cast the result of point subtraction to Vec3
        scalar_t = float(t)

        # Debug print statements
        print(f"DEBUG: Type of vector_ab: {type(vector_ab)}, Value: {vector_ab}")
        print(f"DEBUG: Type of scalar_t: {type(scalar_t)}, Value: {scalar_t}")
        print(f"DEBUG: Type of a: {type(a)}, Value: {a}")

        # Re-attempt multiplication
        scaled_vector = vector_ab * scalar_t
        projection = a + scaled_vector
        return (p - projection).lengthSquared()

    def _calculate_kart_progress(self):
        """Calculates the kart's progress along the track spline (0.0 to 1.0)."""
        kart_pos = self.kart.getPos()
        min_dist_sq = float('inf')
        closest_segment_index = -1
        num_segments = len(self.trackCurvePoints) - 1

        if num_segments < 1:
            return 0.0 # Not enough points

        # Find the closest track segment to the kart
        for i in range(num_segments):
            p1 = self.trackCurvePoints[i]
            p2 = self.trackCurvePoints[i+1]
            dist_sq = self._point_segment_distance_sq(kart_pos, p1, p2)
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest_segment_index = i
                
        if closest_segment_index == -1:
             return self.kart_progress # Keep last progress if error

        # Approximate progress based on the index of the closest segment start point
        # A more accurate calculation would involve projecting onto the segment
        # and calculating the length along the polyline, but this is simpler for now.
        progress = float(closest_segment_index) / num_segments
        return progress
        
    def updateGame(self, task):
        # Skip updates if not in playing state
        if self.gameState != 'playing':
            # Keep the task running, but do nothing if paused or game over
            # This prevents dt from becoming huge when resuming
            return Task.cont

        dt = globalClock.getDt()  # Get time elapsed since last frame
        
        # Update total game time
        self.game_time = time.time() - self.game_start_time

        # Update physics with track data for terrain detection
        road_width = 10.0  # Width of the actual road
        track_width = 20.0  # Total width including sand borders
        self.physics.update(dt, self.track.getZ(), self.trackCurvePoints, road_width, track_width)
        
        # Check terrain and update lawn timer
        if self.physics.current_terrain == 'lawn':
            self.lawn_timer += dt
            # Check if player has spent too much time on the lawn
            if self.lawn_timer >= self.MAX_LAWN_TIME:
                self.gameOver()
        else:
            # Reset timer when not on lawn
            self.lawn_timer = 0

        # --- Update Kart Progress ---
        previous_progress = self.kart_progress
        self.kart_progress = self._calculate_kart_progress()
        self.max_progress_reached = max(self.max_progress_reached, self.kart_progress)

        # --- Check for Lap Completion ---
        # Condition: Progress is near the start (< 5%) AND max progress was high (> 90%)
        # AND we just crossed the start line (progress decreased significantly crossing 0)
        crossed_start_line_forward = self.kart_progress < 0.05 and previous_progress > 0.95
        
        if crossed_start_line_forward and self.max_progress_reached > 0.90:
            if not self.lap_completed:
                self.lap_completed = True
                self.gameWon() # Trigger win state
                return Task.done # Stop further updates this frame after winning
                
        # If kart goes backwards significantly after reaching far, reset max progress
        # This prevents winning by going 90% forward then reversing over the line
        if self.kart_progress < 0.1 and self.max_progress_reached > 0.9 and not crossed_start_line_forward:
             # Might need refinement: Resetting if kart reverses near start after almost finishing
             pass # For now, just crossing forward counts

        # Update camera with delta time for smooth transitions
        update_camera(self.cam, self.kart, dt)
        
        # Update speed display
        self.speed_display.update(self.physics.velocity)

        return Task.cont  # Continue task next frame



app = KartGame()
app.run() 