from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
import time

class MenuManager:
    def __init__(self, base):
        self.base = base
        self.loader = base.loader  # Get the asset loader
        self.menu_frame = None
        self.pause_menu = None
        self.game_over_menu = None
        self.game_won_menu = None

        # Load custom fonts
        try:
            self.title_font = self.loader.loadFont('fonts/SpaceGrotesk-Regular.ttf')
            self.options_font = self.loader.loadFont('fonts/Poppins-Regular.ttf')
            print("Custom fonts loaded successfully.")
        except Exception as e:
            print(f"Error loading custom fonts: {e}")
            print("Falling back to default fonts.")
            self.title_font = None # Or use default font: DirectGuiGlobals.getDefaultFont()
            self.options_font = None

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
                                      text_font=self.title_font, # Apply title font
                                      parent=self.menu_frame)

        # Start button
        self.start_button = DirectButton(text="Start Game",
                                        scale=0.1,
                                        pos=(0, 0, -0.2),
                                        command=start_game_callback,
                                        text_font=self.options_font, # Apply options font
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
                    text_font=self.title_font, # Apply title font
                    parent=self.pause_menu)

        DirectButton(text="Resume",
                    scale=0.1,
                    pos=(0, 0, 0),
                    command=resume_callback,
                    text_font=self.options_font, # Apply options font
                    parent=self.pause_menu)

        DirectButton(text="Restart",
                    scale=0.1,
                    pos=(0, 0, -0.15),
                    command=restart_callback,
                    text_font=self.options_font, # Apply options font
                    parent=self.pause_menu)

        DirectButton(text="Quit",
                    scale=0.1,
                    pos=(0, 0, -0.3),
                    command=quit_callback,
                    text_font=self.options_font, # Apply options font
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
            
    def create_game_over_menu(self, game_time, restart_callback):
        """
        Create a game over menu showing game time and restart button
        """
        # If menu already exists, destroy it first
        if self.game_over_menu:
            self.game_over_menu.destroy()
            
        self.game_over_menu = DirectFrame(frameColor=(0.2, 0.2, 0.2, 0.8),
                                        frameSize=(-0.7, 0.7, -0.5, 0.5),
                                        parent=self.base.aspect2d)

        DirectLabel(text="Game Over!",
                    scale=0.15,
                    pos=(0, 0, 0.3),
                    text_fg=(1, 0.3, 0.3, 1),  # Red text for game over
                    frameColor=(0, 0, 0, 0),
                    text_font=self.title_font, # Apply title font
                    parent=self.game_over_menu)
                    
        # Format time as minutes:seconds
        minutes = int(game_time) // 60
        seconds = int(game_time) % 60
        time_str = f"Time: {minutes:02d}:{seconds:02d}"
        
        DirectLabel(text=time_str,
                    scale=0.1,
                    pos=(0, 0, 0.1),
                    text_fg=(1, 1, 1, 1),
                    frameColor=(0, 0, 0, 0),
                    text_font=self.options_font, # Apply options font
                    parent=self.game_over_menu)
                    
        # Show reason for game over
        DirectLabel(text="You spent too much time off-track!",
                    scale=0.08,
                    pos=(0, 0, 0),
                    text_fg=(1, 1, 1, 1),
                    frameColor=(0, 0, 0, 0),
                    text_font=self.options_font, # Apply options font
                    parent=self.game_over_menu)

        DirectButton(text="Restart",
                    scale=0.1,
                    pos=(0, 0, -0.2),
                    command=restart_callback,
                    text_font=self.options_font, # Apply options font
                    parent=self.game_over_menu)
                    
        self.game_over_menu.hide()

    def show_game_over_menu(self):
        if hasattr(self, 'game_over_menu') and self.game_over_menu:
            self.game_over_menu.show()

    def hide_game_over_menu(self):
        if hasattr(self, 'game_over_menu') and self.game_over_menu:
            self.game_over_menu.hide()
            
    # --- Game Won Menu ---
    def create_game_won_menu(self, game_time, restart_callback):
        if hasattr(self, 'game_won_menu') and self.game_won_menu:
            self.game_won_menu.destroy()
            
        self.game_won_menu = DirectFrame(
            frameColor=(0.1, 0.6, 0.1, 0.9), 
            frameSize=(-0.6, 0.6, -0.4, 0.4), 
            parent=self.base.aspect2d
        )

        DirectLabel(
            text="Lap Completed!",
            scale=0.12, 
            pos=(0, 0, 0.2), 
            parent=self.game_won_menu, 
            relief=None, 
            text_fg=(1, 1, 1, 1),
            text_font=self.title_font # Apply title font
        )
        
        DirectLabel(
            text=f"Time: {game_time:.2f} s",
            scale=0.08, 
            pos=(0, 0, 0.05), 
            parent=self.game_won_menu, 
            relief=None, 
            text_fg=(1, 1, 1, 1),
            text_font=self.options_font # Apply options font
        )

        DirectButton(
            text="Play Again",
            scale=0.07, 
            pos=(0, 0, -0.15), 
            parent=self.game_won_menu, 
            command=restart_callback, 
            text_font=self.options_font, # Apply options font
            pressEffect=1
        )
        
        DirectButton(
            text="Quit",
            scale=0.07, 
            pos=(0, 0, -0.28), 
            parent=self.game_won_menu, 
            command=self.base.state_manager.quit_game, 
            text_font=self.options_font, # Apply options font
            pressEffect=1
        )
        
        self.game_won_menu.hide()
        
    def show_game_won_menu(self):
        if hasattr(self, 'game_won_menu') and self.game_won_menu:
            self.game_won_menu.show()
            
    def hide_game_won_menu(self):
        if hasattr(self, 'game_won_menu') and self.game_won_menu:
            self.game_won_menu.hide()
    # ---------------------

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
