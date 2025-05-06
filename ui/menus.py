from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
from panda3d.core import TextNode

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
    
    def create_base_menu(self, title, text=None, buttons=None):
        """
        Creates a consistent menu with the specified title, optional text, and buttons
        
        Args:
            title (str): The title to display at the top of the menu
            text (str, optional): Additional text to display below the title
            buttons (list, optional): List of dictionaries with button properties:
                                    [{'text': 'Button Text', 'command': callback_function}]
        
        Returns:
            DirectFrame: The created menu frame
        """
        # Create the menu frame with gray background
        menu = DirectFrame(
            frameColor=(0.3, 0.3, 0.3, 0.9),  # Gray background
            frameSize=(-0.8, 0.8, -0.6, 0.6),
            parent=self.base.aspect2d
        )
        
        # Add the title
        DirectLabel(
            text=title,
            scale=0.12,
            pos=(0, 0, 0.4),
            parent=menu,
            relief=None,
            text_fg=(1, 1, 1, 1), 
            text_font=self.title_font
        )
        
        # Add optional text below title
        if text:
            DirectLabel(
                text=text,
                scale=0.07,
                pos=(0, 0, 0.2),
                parent=menu,
                relief=None,
                text_fg=(1, 1, 1, 1),
                text_font=self.options_font
            )
        
        # Add buttons
        if buttons:
            # Calculate button positions
            button_count = len(buttons)
            button_height = 0.18  # Increase spacing between buttons (was 0.12)
            start_y = -0.2 if text else 0.0  # Lower if there's text
            
            # Adjust starting position based on button count to center the entire block
            start_y -= (button_count - 1) * button_height / 2  
            
            for i, button_data in enumerate(buttons):
                y_pos = start_y + (button_count - 1 - i) * button_height
                
                DirectButton(
                    text=button_data['text'],
                    scale=0.1,
                    pos=(0, 0, y_pos),
                    command=button_data['command'],
                    text_font=self.options_font,
                    frameColor=(0, 0, 0, 0),  # Transparent background
                    text_fg=(1, 1, 1, 1),     # White text
                    relief='flat',
                    pad=(0.4, 0.25),
                    parent=menu
                )
        
        menu.hide()  # Initially hidden
        return menu

    def create_start_menu(self, start_game_callback):
        """
        Create the start menu with a start button
        """
        buttons = [
            {'text': 'Start Game', 'command': start_game_callback}
        ]
        
        self.menu_frame = self.create_base_menu(
            title="Chinese Kart",
            buttons=buttons
        )

    def create_pause_menu(self, resume_callback, restart_callback, quit_callback):
        """
        Create the pause menu with resume, restart and quit buttons
        """
        buttons = [
            {'text': 'Resume', 'command': resume_callback},
            {'text': 'Restart', 'command': restart_callback},
            {'text': 'Quit', 'command': quit_callback}
        ]
        
        self.pause_menu = self.create_base_menu(
            title="Paused",
            buttons=buttons
        )

    def create_game_over_menu(self, game_time, restart_callback):
        """
        Create a game over menu showing game time and restart button
        """
        # Format time as minutes:seconds
        minutes = int(game_time) // 60
        seconds = int(game_time) % 60
        time_str = f"Time: {minutes:02d}:{seconds:02d}"
        
        buttons = [
            {'text': 'Restart', 'command': restart_callback}
        ]
        
        self.game_over_menu = self.create_base_menu(
            title="Game Over!",
            text=f"You spent too much time off-track!\n{time_str}",
            buttons=buttons
        )

    def create_game_won_menu(self, game_time, rankings, restart_callback):
        """
        Create a game won menu showing player position and time
        """
        # Find player's rank and time
        player_info = next((r for r in rankings if r.get('is_player')), None)
        if player_info:
            position = player_info['position']
            position_text = self._get_position_text(position)
            
            time = player_info['finish_time']
            minutes = int(time) // 60
            seconds = int(time) % 60
            millis = int((time - (minutes * 60) - seconds) * 100)
            time_str = f"{minutes:02d}:{seconds:02d}.{millis:02d}"
            
            result_text = f"You finished in {position_text} place!\nTime: {time_str}"
        else:
            result_text = "Race Complete!"
        
        buttons = [
            {'text': 'Play Again', 'command': restart_callback},
            {'text': 'Quit', 'command': self.base.userExit}
        ]
        
        self.game_won_menu = self.create_base_menu(
            title="Race Finished!",
            text=result_text,
            buttons=buttons
        )
    
    def _get_position_text(self, position):
        """Helper method to convert position number to text with suffix"""
        if position == 1:
            return "1st"
        elif position == 2:
            return "2nd"
        elif position == 3:
            return "3rd"
        else:
            return f"{position}th"

    def show_menu(self):
        """Show the start menu"""
        if self.menu_frame:
            self.menu_frame.show()

    def hide_menu(self):
        """Hide the start menu"""
        if self.menu_frame:
            self.menu_frame.hide()

    def show_pause_menu(self):
        """Show the pause menu"""
        if self.pause_menu:
            self.pause_menu.show()

    def hide_pause_menu(self):
        """Hide the pause menu"""
        if self.pause_menu:
            self.pause_menu.hide()

    def show_game_over_menu(self):
        """Show the game over menu"""
        if self.game_over_menu:
            self.game_over_menu.show()

    def hide_game_over_menu(self):
        """Hide the game over menu"""
        if self.game_over_menu:
            self.game_over_menu.hide()

    def show_game_won_menu(self):
        """Show the game won menu"""
        if self.game_won_menu:
            self.game_won_menu.show()

    def hide_game_won_menu(self):
        """Hide the game won menu"""
        if self.game_won_menu:
            self.game_won_menu.hide()
