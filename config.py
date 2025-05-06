# Game Configuration Constants

# Race settings
LAPS_TO_FINISH = 1  # Number of laps required to finish the race

# Track settings
ROAD_WIDTH = 15.0
SAND_BORDER_WIDTH = 12.0
STRIPE_WIDTH = 1.0

# Game rules
MAX_LAWN_TIME = 3  # Maximum time allowed on lawn before game over

# Global configuration settings for Chinese Kart

# Game difficulty settings
DIFFICULTY = "regular"  # Default difficulty (options: "easy", "regular", "hard")

# AI speed modifiers based on difficulty
AI_SPEED_MODIFIERS = {
    "easy": 0.8,      # AI karts move at 80% speed in easy mode
    "regular": 1.0,   # AI karts move at 100% speed in regular mode
    "hard": 1.2       # AI karts move at 120% speed in hard mode
}

# Function to get current AI speed modifier
def get_ai_speed_modifier():
    """
    Returns the speed modifier for AI karts based on current difficulty
    """
    return AI_SPEED_MODIFIERS.get(DIFFICULTY, 1.0)

# Function to update difficulty setting
def set_difficulty(difficulty):
    """
    Updates the global difficulty setting
    
    Args:
        difficulty: The difficulty level to set ("easy", "regular", or "hard")
    """
    global DIFFICULTY
    if difficulty in AI_SPEED_MODIFIERS:
        DIFFICULTY = difficulty
        print(f"Difficulty set to: {difficulty}")
    else:
        print(f"Invalid difficulty: {difficulty}, using regular")
        DIFFICULTY = "regular" 