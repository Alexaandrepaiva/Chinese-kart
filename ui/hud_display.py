from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import DirectFrame
from panda3d.core import TextNode

class HUDDisplay:
    def __init__(self, base):
        """
        Creates a speed and timer display for the kart in the top-left corner
        Args:
            base: The ShowBase instance (game)
        """
        self.base = base
        # Proper rectangular background using DirectFrame
        self.bg_frame = DirectFrame(
            frameColor=(0.1, 0.1, 0.1, 0.7),
            frameSize=(-0.30, 0.30, -0.13, 0.07),  # (left, right, bottom, top)
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
            pos=(-0.25, -0.1),  # More to the right in the frame
            scale=0.07,
            fg=(1, 1, 1, 1),
            bg=(0, 0, 0, 0),
            align=TextNode.ALeft,
            mayChange=True,
            shadow=(0, 0, 0, 0.5),
            parent=self.bg_frame,
        )
        self.hide()
        
    def update(self, velocity, timer_seconds=None):
        """
        Updates the speed and timer display.
        Args:
            velocity: The current velocity of the kart
            timer_seconds: (float or None) The elapsed time in seconds to display. If None, timer is not updated.
        """
        # Speed
        speed_kmh = abs(int(velocity * 3.6))
        self.speed_text.setText(f"Speed: {speed_kmh} km/h")
        # Timer
        if timer_seconds is not None:
            mins = int(timer_seconds // 60)
            secs = int(timer_seconds % 60)
            self.timer_text.setText(f"Time: {mins:02d}:{secs:02d}")
        
    def show(self):
        """
        Shows the speed and timer display
        """
        self.bg_frame.show()
        self.timer_text.show()
        self.speed_text.show()
        
    def hide(self):
        """
        Hides the speed and timer display
        """
        self.bg_frame.hide()
        self.timer_text.hide()
        self.speed_text.hide()
