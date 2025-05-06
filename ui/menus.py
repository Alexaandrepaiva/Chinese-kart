from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel, DirectRadioButton
from panda3d.core import TextNode, LVector4f, Vec4
import config

class MenuManager:
    def __init__(self, base):
        self.base = base
        self.loader = base.loader  # Get the asset loader
        self.menu_frame = None
        self.pause_menu = None
        self.game_over_menu = None
        self.game_won_menu = None
        self.config_menu = None
        
        # Game configuration options
        self.kart_color = (1, 0, 0, 1)  # Default: red
        self.ai_kart_count = 3  # Default: 3 AI karts
        self.difficulty = config.DIFFICULTY  # Use global default difficulty
        self.laps_count = config.LAPS_TO_FINISH  # Default from config
        self.available_colors = {
            "Red": Vec4(1, 0, 0, 1),
            "Blue": Vec4(0, 0, 1, 1),
            "Green": Vec4(0, 0.8, 0, 1),
            "Yellow": Vec4(1, 1, 0, 1),
            "Purple": Vec4(0.8, 0, 0.8, 1),
            "Orange": Vec4(1, 0.5, 0, 1),
        }
        self.color_buttons = {}
        self.ai_count_underlines = {}
        self.difficulty_buttons = {}
        self.difficulty_underlines = {}
        self.laps_buttons = {}
        self.laps_underlines = {}

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
        Create the start menu with start and configure buttons
        """
        buttons = [
            {'text': 'Start Game', 'command': start_game_callback},
            {'text': 'Configure', 'command': self.show_config_menu}
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
            
        # Hide other menus to ensure they don't overlap
        if hasattr(self, 'config_menu') and self.config_menu:
            self.config_menu.hide()
        if hasattr(self, 'pause_menu') and self.pause_menu:
            self.pause_menu.hide()
        if hasattr(self, 'game_over_menu') and self.game_over_menu:
            self.game_over_menu.hide()
        if hasattr(self, 'game_won_menu') and self.game_won_menu:
            self.game_won_menu.hide()

    def hide_menu(self):
        """Hide the start menu"""
        if self.menu_frame:
            self.menu_frame.hide()
        
        # Also ensure config menu is hidden
        if hasattr(self, 'config_menu') and self.config_menu:
            self.config_menu.hide()

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

    def create_config_menu(self, back_callback):
        """
        Creates a configuration menu for the player to customize game settings
        
        Args:
            back_callback: Function to call when returning to the main menu
        """
        # Create the config menu frame
        menu = DirectFrame(
            frameColor=(0.3, 0.3, 0.3, 0.9),
            frameSize=(-0.8, 0.8, -0.6, 0.6),
            parent=self.base.aspect2d
        )
        
        # Add the title
        DirectLabel(
            text="Game Configuration",
            scale=0.12,
            pos=(0, 0, 0.5),
            parent=menu,
            relief=None,
            text_fg=(1, 1, 1, 1),
            text_font=self.title_font
        )
        
        # Smaller font scale for all options to make room
        option_scale = 0.06
        
        # Kart color selection section
        DirectLabel(
            text="Kart Color:",
            scale=option_scale,
            pos=(-0.6, 0, 0.35),
            parent=menu,
            relief=None,
            text_align=TextNode.ALeft,
            text_fg=(1, 1, 1, 1),
            text_font=self.options_font
        )
        
        # Color selection squares - all in one row
        x_start = -0.6
        y_pos = 0.27
        square_size = 0.05  # Reduced size
        spacing = 0.12      # Reduced spacing
        
        # Clear any existing color buttons
        self.color_buttons = {}
        
        for i, (color_name, color_value) in enumerate(self.available_colors.items()):
            x_pos = x_start + i * spacing
            
            # Create color square button
            self.color_buttons[color_name] = DirectButton(
                frameColor=color_value,
                frameSize=(-square_size, square_size, -square_size, square_size),
                relief="raised",
                pos=(x_pos, 0, y_pos),
                parent=menu,
                command=self.select_kart_color,
                extraArgs=[color_name]
            )
        
        # Mark the currently selected color
        self.update_color_selection()
        
        # AI Kart count selection
        DirectLabel(
            text="AI Opponents:",
            scale=option_scale,
            pos=(-0.6, 0, 0.15),
            parent=menu,
            relief=None,
            text_align=TextNode.ALeft,
            text_fg=(1, 1, 1, 1),
            text_font=self.options_font
        )
        
        # AI Count options
        ai_counts = [1, 2, 3, 4, 5]
        ai_buttons = []
        self.ai_count_underlines = {}
        
        button_spacing = 0.12
        
        for i, count in enumerate(ai_counts):
            x_pos = -0.6 + i * button_spacing
            
            button = DirectButton(
                text=str(count),
                scale=option_scale,
                pos=(x_pos, 0, 0.07),
                frameSize=(-0.08, 0.08, -0.08, 0.08),
                frameColor=(0.5, 0.5, 0.5, 0.7),
                relief="raised",
                text_fg=(1, 1, 1, 1),
                parent=menu,
                command=self.select_ai_count,
                extraArgs=[count]
            )
            
            # Add proper underline directly below the text
            underline = DirectFrame(
                frameColor=(0, 1, 0, 1),  # Green underline
                frameSize=(-0.04, 0.04, -0.004, 0.004),
                state="disabled",
                parent=menu,
                pos=(x_pos, 0, 0.04)  # Directly below the text
            )
            
            # Show underline only for selected count, hide for others
            if count == self.ai_kart_count:
                button["frameColor"] = (0.2, 0.7, 0.2, 0.7)  # Green button background
                underline.show()
            else:
                underline.hide()
                
            self.ai_count_underlines[count] = underline
            ai_buttons.append(button)
        
        # Difficulty selection
        DirectLabel(
            text="Difficulty:",
            scale=option_scale,
            pos=(-0.6, 0, -0.05),
            parent=menu,
            relief=None,
            text_align=TextNode.ALeft,
            text_fg=(1, 1, 1, 1),
            text_font=self.options_font
        )
        
        # Difficulty options
        difficulties = ["easy", "regular", "hard"]
        difficulty_labels = ["Easy", "Regular", "Hard"]
        self.difficulty_buttons = {}
        self.difficulty_underlines = {}
        
        button_spacing = 0.18
        
        for i, (diff, label) in enumerate(zip(difficulties, difficulty_labels)):
            x_pos = -0.6 + i * button_spacing
            
            button = DirectButton(
                text=label,
                scale=option_scale,
                pos=(x_pos, 0, -0.13),
                frameSize=(-0.08, 0.08, -0.08, 0.08),
                frameColor=(0.5, 0.5, 0.5, 0.7),
                relief="raised",
                text_fg=(1, 1, 1, 1),
                parent=menu,
                command=self.select_difficulty,
                extraArgs=[diff]
            )
            
            # Add proper underline directly below the text
            underline = DirectFrame(
                frameColor=(0, 1, 0, 1),  # Green underline
                frameSize=(-0.06, 0.06, -0.004, 0.004),
                state="disabled",
                parent=menu,
                pos=(x_pos, 0, -0.16)  # Directly below the text
            )
            
            # Show underline only for selected difficulty, hide for others
            if diff == self.difficulty:
                button["frameColor"] = (0.2, 0.7, 0.2, 0.7)  # Green button background
                underline.show()
            else:
                underline.hide()
                
            self.difficulty_buttons[diff] = button
            self.difficulty_underlines[diff] = underline
        
        # Number of Laps selection
        DirectLabel(
            text="Race Laps:",
            scale=option_scale,
            pos=(-0.6, 0, -0.25),
            parent=menu,
            relief=None,
            text_align=TextNode.ALeft,
            text_fg=(1, 1, 1, 1),
            text_font=self.options_font
        )
        
        # Laps options
        laps_counts = [1, 2, 3, 4, 5]
        self.laps_buttons = {}
        self.laps_underlines = {}
        
        button_spacing = 0.12
        
        for i, laps in enumerate(laps_counts):
            x_pos = -0.6 + i * button_spacing
            
            button = DirectButton(
                text=str(laps),
                scale=option_scale,
                pos=(x_pos, 0, -0.33),
                frameSize=(-0.08, 0.08, -0.08, 0.08),
                frameColor=(0.5, 0.5, 0.5, 0.7),
                relief="raised",
                text_fg=(1, 1, 1, 1),
                parent=menu,
                command=self.select_laps_count,
                extraArgs=[laps]
            )
            
            # Add proper underline directly below the text
            underline = DirectFrame(
                frameColor=(0, 1, 0, 1),  # Green underline
                frameSize=(-0.04, 0.04, -0.004, 0.004),
                state="disabled",
                parent=menu,
                pos=(x_pos, 0, -0.36)  # Directly below the text
            )
            
            # Show underline only for selected count, hide for others
            if laps == self.laps_count:
                button["frameColor"] = (0.2, 0.7, 0.2, 0.7)  # Green button background
                underline.show()
            else:
                underline.hide()
                
            self.laps_buttons[laps] = button
            self.laps_underlines[laps] = underline
        
        # Back button
        DirectButton(
            text="Back",
            scale=0.08,
            pos=(0, 0, -0.5),
            command=back_callback,
            text_font=self.options_font,
            frameColor=(0, 0, 0, 0),
            text_fg=(1, 1, 1, 1),
            relief='flat',
            pad=(0.4, 0.25),
            parent=menu
        )
        
        menu.hide()  # Initially hidden
        self.config_menu = menu
    
    def select_kart_color(self, color_name):
        """
        Sets the selected kart color
        
        Args:
            color_name: Name of the selected color
        """
        self.kart_color = self.available_colors[color_name]
        self.update_color_selection()
    
    def update_color_selection(self):
        """
        Updates the visual selection state of color buttons
        """
        for name, button in self.color_buttons.items():
            color_value = self.available_colors[name]
            # Check if this is the selected color
            if color_value == self.kart_color:
                # Add green border for selected color
                button.setFrameSize((-0.07, 0.07, -0.07, 0.07))
                button["frameColor"] = color_value
                button["relief"] = "sunken"
                # Add a border by using a slightly larger frame behind it
                if not hasattr(button, "border_frame"):
                    button.border_frame = DirectFrame(
                        frameColor=(0, 1, 0, 1),  # Green border
                        frameSize=(-0.08, 0.08, -0.08, 0.08),
                        state="disabled",
                        parent=button.getParent(),
                        pos=button.getPos()
                    )
                    button.border_frame.setBin("background", -1)
            else:
                # Normal appearance for non-selected colors
                button.setFrameSize((-0.06, 0.06, -0.06, 0.06))
                button["relief"] = "raised"
                # Remove border if exists
                if hasattr(button, "border_frame"):
                    button.border_frame.destroy()
                    delattr(button, "border_frame")
    
    def select_ai_count(self, count):
        """
        Sets the number of AI karts
        
        Args:
            count: Number of AI karts to use
        """
        self.ai_kart_count = count
        
        # Update the underlines to show only under the selected count
        for ai_count, underline in self.ai_count_underlines.items():
            if ai_count == count:
                underline.show()
                # Find the corresponding button and update its color
                for button in self.config_menu.findAllMatches("**/DirectButton"):
                    try:
                        if button.get_text() == str(count):
                            button["frameColor"] = (0.2, 0.7, 0.2, 0.7)  # Highlight selected
                    except:
                        pass
            else:
                underline.hide()
                # Reset other buttons
                for button in self.config_menu.findAllMatches("**/DirectButton"):
                    try:
                        if button.get_text() == str(ai_count):
                            button["frameColor"] = (0.5, 0.5, 0.5, 0.7)  # Reset others
                    except:
                        pass
    
    def select_difficulty(self, difficulty):
        """
        Sets the game difficulty level
        
        Args:
            difficulty: Difficulty level (easy, regular, hard)
        """
        self.difficulty = difficulty
        # Update global difficulty setting
        config.set_difficulty(difficulty)
        
        # Update visual feedback for difficulty selection
        for diff, underline in self.difficulty_underlines.items():
            if diff == difficulty:
                underline.show()
                self.difficulty_buttons[diff]["frameColor"] = (0.2, 0.7, 0.2, 0.7)  # Highlight selected
            else:
                underline.hide()
                self.difficulty_buttons[diff]["frameColor"] = (0.5, 0.5, 0.5, 0.7)  # Reset others
    
    def select_laps_count(self, laps):
        """
        Sets the number of laps for the race
        
        Args:
            laps: Number of laps (1-5)
        """
        self.laps_count = laps
        
        # Update visual feedback for lap selection
        for count, underline in self.laps_underlines.items():
            if count == laps:
                underline.show()
                self.laps_buttons[count]["frameColor"] = (0.2, 0.7, 0.2, 0.7)  # Highlight selected
            else:
                underline.hide()
                self.laps_buttons[count]["frameColor"] = (0.5, 0.5, 0.5, 0.7)  # Reset others
    
    def show_config_menu(self):
        """
        Creates and shows the configuration menu
        """
        if not self.config_menu:
            self.create_config_menu(self.hide_config_menu)
        
        # Hide the main menu and show config menu
        if self.menu_frame:
            self.menu_frame.hide()
        self.config_menu.show()
    
    def hide_config_menu(self):
        """
        Hides the configuration menu and shows the main menu
        """
        if self.config_menu:
            self.config_menu.hide()
            
        # Show the main menu
        if self.menu_frame:
            self.menu_frame.show()
    
    def get_game_config(self):
        """
        Returns the current game configuration
        
        Returns:
            dict: Configuration containing kart_color, ai_kart_count, difficulty, and laps_count
        """
        # Get all available colors except the selected one for AI karts
        ai_colors = []
        for color_name, color_value in self.available_colors.items():
            if color_value != self.kart_color:  # If not player's selected color
                ai_colors.append(color_value)
                
        return {
            "kart_color": self.kart_color,
            "ai_kart_count": self.ai_kart_count,
            "ai_colors": ai_colors,  # Pass all remaining colors for AI karts
            "difficulty": self.difficulty,  # Add difficulty setting
            "laps_count": self.laps_count  # Add laps count setting
        }
