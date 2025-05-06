from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame
from panda3d.core import TextNode
import config  # Import the config module directly instead of just LAPS_TO_FINISH

class HUDDisplay:
    def __init__(self, base):
        """
        Creates a HUD display showing speed, timer, player position, and lap counter
        Args:
            base: The ShowBase instance (game)
        """
        self.base = base
        # Proper rectangular background using DirectFrame
        self.bg_frame = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.7),
            frameSize=(-0.30, 0.30, -0.31, 0.07),  # Increased bottom value to make room for laps
            pos=(-1.1, 0, 0.860),  # (x, y, z)
            parent=self.base.aspect2d,
        )
        # Timer text (on top, inside frame)
        self.timer_text = OnscreenText(
            text="Time: 00:00",
            pos=(-0.25, -0.005),
            scale=0.07,
            fg=(1, 1, 1, 1),
            bg=(0, 0, 0, 0),
            align=TextNode.ALeft,
            mayChange=True,
            shadow=(0, 0, 0, 0.5),
            parent=self.bg_frame,
        )
        # Speed text (below timer, inside frame)
        self.speed_text = OnscreenText(
            text="Speed: 0 km/h",
            pos=(-0.25, -0.1),
            scale=0.07,
            fg=(1, 1, 1, 1),
            bg=(0, 0, 0, 0),
            align=TextNode.ALeft,
            mayChange=True,
            shadow=(0, 0, 0, 0.5),
            parent=self.bg_frame,
        )
        # Position text (below speed, inside frame)
        self.position_text = OnscreenText(
            text="Position: 1/1",
            pos=(-0.25, -0.2),
            scale=0.07,
            fg=(1, 1, 1, 1),
            bg=(0, 0, 0, 0),
            align=TextNode.ALeft,
            mayChange=True,
            shadow=(0, 0, 0, 0.5),
            parent=self.bg_frame,
        )
        # Lap counter text (below position, inside frame)
        self.lap_text = OnscreenText(
            text=f"Lap: 1/{config.LAPS_TO_FINISH}",  # Access from config directly
            pos=(-0.25, -0.29),
            scale=0.07,
            fg=(1, 1, 1, 1),
            bg=(0, 0, 0, 0),
            align=TextNode.ALeft,
            mayChange=True,
            shadow=(0, 0, 0, 0.5),
            parent=self.bg_frame,
        )
        self.hide()
        
    def update(self, velocity, timer_seconds=None, position=None, total_racers=None, current_lap=0, total_laps=None):
        """
        Updates the HUD display with current game information
        
        Args:
            velocity: The current velocity of the kart
            timer_seconds: (float or None) The elapsed time in seconds to display. If None, timer is not updated.
            position: (int or None) Current player position in the race. If None, position is not updated.
            total_racers: (int or None) Total number of racers. If None, total racers is not updated.
            current_lap: (int) Current lap number. Default 0 (not started yet).
            total_laps: (int or None) Total number of laps. If None, uses config value.
        """
        # Speed
        speed_kmh = abs(int(velocity * 3.6))
        self.speed_text.setText(f"Speed: {speed_kmh} km/h")
        
        # Timer
        if timer_seconds is not None:
            mins = int(timer_seconds // 60)
            secs = int(timer_seconds % 60)
            self.timer_text.setText(f"Time: {mins:02d}:{secs:02d}")
        
        # Position
        if position is not None and total_racers is not None:
            self.position_text.setText(f"Position: {position}/{total_racers}")
        
        # Lap count (display current lap + 1 to show "Lap 1" at start)
        display_lap = current_lap + 1
        if total_laps is None:
            total_laps = config.LAPS_TO_FINISH  # Access config directly
        self.lap_text.setText(f"Lap: {display_lap}/{total_laps}")
        
    def show(self):
        """
        Shows the HUD display
        """
        self.bg_frame.show()
        self.timer_text.show()
        self.speed_text.show()
        self.position_text.show()
        self.lap_text.show()
        
    def hide(self):
        """
        Hides the HUD display
        """
        self.bg_frame.hide()
        self.timer_text.hide()
        self.speed_text.hide()
        self.position_text.hide()
        self.lap_text.hide()
