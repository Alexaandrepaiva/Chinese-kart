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

# AI turn handling based on difficulty
# Higher values mean more reduction in speed when taking turns
AI_TURN_HANDLING = {
    "easy": 0.8,      # AI karts slow down significantly on turns in easy mode
    "regular": 0.6,   # AI karts slow down moderately on turns in regular mode
    "hard": 0.2       # AI karts maintain more speed on turns in hard mode
}

# AI path deviation range based on difficulty
# Controls how much AI karts can deviate from the center of the track
AI_PATH_DEVIATION = {
    "easy": 2.0,      # AI karts can deviate more from center line (less optimal paths)
    "regular": 1.5,   # Moderate deviation from center line
    "hard": 1.0       # Less deviation (more optimal racing line)
}

# Function to get current AI speed modifier
def get_ai_speed_modifier():
    """
    Returns the speed modifier for AI karts based on current difficulty
    """
    return AI_SPEED_MODIFIERS.get(DIFFICULTY, 1.0)

# Function to get current AI turn handling factor
def get_ai_turn_factor():
    """
    Returns the turn handling factor for AI karts based on current difficulty.
    Higher values mean more slowing down on turns.
    """
    return AI_TURN_HANDLING.get(DIFFICULTY, 0.6)

# Function to get current AI path deviation range
def get_ai_path_deviation():
    """
    Returns the maximum path deviation from track center for AI karts.
    Higher values create more varied/random paths.
    """
    return AI_PATH_DEVIATION.get(DIFFICULTY, 1.5)

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