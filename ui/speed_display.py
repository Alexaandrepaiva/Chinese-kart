from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

class SpeedDisplay:
    def __init__(self, base):
        """
        Creates a speed display for the kart in the top-left corner
        
        Args:
            base: The ShowBase instance (game)
        """
        self.base = base
        
        # Create the display text
        self.speed_text = OnscreenText(
            text="Speed: 0 km/h",
            pos=(-1.3, 0.9),  # Top-left position
            scale=0.07,
            fg=(1, 1, 1, 1),  # White text
            bg=(0.1, 0.1, 0.1, 0.7),  # Semi-transparent black background
            align=TextNode.ALeft,
            mayChange=True,
            shadow=(0, 0, 0, 0.5),  # Add shadow for better visibility
        )
        # Hide the display initially
        self.hide()
        
    def update(self, velocity):
        """
        Updates the speed display with current velocity
        
        Args:
            velocity: The current velocity of the kart
        """
        # Convert to km/h and round to integer for display
        speed_kmh = abs(int(velocity * 3.6))  # Convert to km/h (assuming velocity is in m/s)
        self.speed_text.setText(f"Speed: {speed_kmh} km/h")
        
    def show(self):
        """
        Shows the speed display
        """
        self.speed_text.show()
        
    def hide(self):
        """
        Hides the speed display
        """
        self.speed_text.hide()
