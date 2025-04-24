from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel

class MenuManager:
    def __init__(self, base):
        self.base = base
        self.menu_frame = None
        self.pause_menu = None

    def create_start_menu(self, start_game_callback):
        """
        Create the start menu with a start button
        """
        # Menu frame
        self.menu_frame = DirectFrame(frameColor=(0.2, 0.2, 0.2, 0.8),
                                     frameSize=(-0.7, 0.7, -0.5, 0.5),
                                     parent=self.base.aspect2d)  # Attach to 2D layer

        # Title label
        self.title_label = DirectLabel(text="Chinese Kart",
                                      scale=0.15,
                                      pos=(0, 0, 0.3),
                                      text_fg=(1, 1, 1, 1),
                                      frameColor=(0, 0, 0, 0),  # Transparent background
                                      parent=self.menu_frame)

        # Start button
        self.start_button = DirectButton(text="Start Game",
                                        scale=0.1,
                                        pos=(0, 0, -0.2),
                                        command=start_game_callback,
                                        parent=self.menu_frame)

    def create_pause_menu(self, resume_callback, restart_callback, quit_callback):
        """
        Create the pause menu with resume, restart and quit buttons
        """
        self.pause_menu = DirectFrame(frameColor=(0.2, 0.2, 0.2, 0.8),
                                    frameSize=(-0.7, 0.7, -0.5, 0.5),
                                    parent=self.base.aspect2d)
        self.pause_menu.hide()  # Initially hidden

        DirectLabel(text="Paused",
                    scale=0.15,
                    pos=(0, 0, 0.3),
                    text_fg=(1, 1, 1, 1),
                    frameColor=(0, 0, 0, 0),
                    parent=self.pause_menu)

        DirectButton(text="Resume",
                    scale=0.1,
                    pos=(0, 0, 0),
                    command=resume_callback,
                    parent=self.pause_menu)

        DirectButton(text="Restart",
                    scale=0.1,
                    pos=(0, 0, -0.15),
                    command=restart_callback,
                    parent=self.pause_menu)

        DirectButton(text="Quit",
                    scale=0.1,
                    pos=(0, 0, -0.3),
                    command=quit_callback,
                    parent=self.pause_menu)

    def hide_menu(self):
        """
        Hide the start menu
        """
        if hasattr(self, 'menu_frame') and self.menu_frame:
            self.menu_frame.hide()

    def show_menu(self):
        """
        Show the start menu
        """
        if hasattr(self, 'menu_frame') and self.menu_frame:
            self.menu_frame.show()

    def hide_pause_menu(self):
        """
        Hide the pause menu
        """
        if self.pause_menu:
            self.pause_menu.hide()

    def show_pause_menu(self):
        """
        Show the pause menu
        """
        if self.pause_menu:
            self.pause_menu.show()
