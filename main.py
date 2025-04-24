import sys
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, Vec3
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

class KartGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Game state ('menu', 'playing', 'paused')
        self.gameState = 'menu'

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

        # Exit handling - Changed to toggle pause
        self.accept("escape", self.togglePause)

        print("Game Initialized, showing menu.")

    def showMenu(self):
        # Show the menu and hide game elements
        self.menu_manager.show_menu()
        self.gameRoot.hide()
        # Potentially reset camera to a menu view if desired
        # self.cam.setPos(0, 0, 50)
        # self.cam.lookAt(0, 0, 0)

    def startGame(self):
        print("Starting Game!")
        # Hide menus
        self.menu_manager.hide_menu()
        self.menu_manager.hide_pause_menu()

        self.gameState = 'playing'
        self.gameRoot.show()  # Show the game world

        # Reset kart position and physics - Corrected position
        # Use the first generated spline point as reference
        start_pos = self.trackCurvePoints[0]
        # Use the second spline point to get initial direction
        start_dir = self.trackCurvePoints[1] - self.trackCurvePoints[0]
        start_dir.normalize()

        kart_start_pos = start_pos - start_dir * 3  # Position 3 units behind point 0
        # Ensure Z position is relative to the track surface (which should be at Z=0)
        kart_start_pos.setZ(self.track.getZ() + 0.5)  # Track Z + half kart height
        self.kart.setPos(kart_start_pos)
        self.kart.lookAt(self.trackCurvePoints[1])     # Look towards point 1

        # Reset physics
        self.physics.reset()

        # Setup camera for gameplay with a smooth transition
        # Set initial camera position (top-down view)
        self.cam.setPos(self.kart.getPos() + Vec3(0, 0, 30))
        self.cam.lookAt(self.kart)
        
        # Start smooth camera transition
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

    def updateGame(self, task):
        # Skip updates if not in playing state
        if self.gameState != 'playing':
            # Keep the task running, but do nothing if paused
            # This prevents dt from becoming huge when resuming
            return Task.cont

        dt = globalClock.getDt()  # Get time elapsed since last frame

        # Update physics
        self.physics.update(dt, self.track.getZ())

        # Update camera with delta time for smooth transitions
        update_camera(self.cam, self.kart, dt)

        return Task.cont  # Continue task next frame



app = KartGame()
app.run() 