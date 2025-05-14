# Chinese-kart

## 1. Introduction

Welcome to Chinese-kart! This repository hosts a thrilling 3D kart racing game developed using Python and the Panda3D game engine. The primary goal of this project is to create an engaging and fun racing experience, featuring dynamic kart physics, intelligent AI opponents, and a visually appealing environment composed of simple geometric objects.

Players can race against AI-controlled karts on a custom-designed track, navigate obstacles, and compete for the best lap times. The game emphasizes smooth gameplay, responsive controls, and a clear, intuitive user interface. It serves as an excellent example of applying object-oriented principles, Model-View-Controller (MVC) architectural patterns, and 3D game development techniques within the Panda3D framework.

The project is structured MVC, making it relatively easy to understand, maintain, and extend. Whether you're interested in game development, learning Panda3D, or exploring Python-based simulations, Chinese-kart offers a rich codebase to dive into.

Check out the [slide presentation of this game.](https://www.canva.com/design/DAGnVXLWPZI/tYvHgDeEMGna-qi35phFcg/view?utm_content=DAGnVXLWPZI&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h9b9a540e4a)

## 2. Installation

To get Chinese-kart up and running on your local machine, please follow these steps. These instructions assume you have Python 3.x installed on your system.

### Prerequisites

*   Python 3.x
*   pip (Python package installer)

### Setup and Running the Game

1.  **Clone the Repository (Optional):**
    If you haven't already, clone this repository to your local machine using Git:
    ```bash
    git clone https://github.com/Alexaandrepaiva/Chinese-kart.git
    cd Chinese-kart
    ```

2.  **Create and Activate a Virtual Environment:**
    It is highly recommended to use a virtual environment to manage project dependencies.

    *   **On macOS and Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

    *   **On Windows (Command Prompt):**
        ```bash
        python -m venv venv
        venv\Scripts\activate.bat
        ```

    *   **On Windows (PowerShell):**
        ```bash
        python -m venv venv
        .\venv\Scripts\Activate.ps1
        ```
        If you encounter an error with script execution on PowerShell, you might need to adjust your execution policy:
        ```powershell
        Set-ExecutionPolicy Unrestricted -Scope Process
        ```
        Then try activating the environment again.

3.  **Install Dependencies:**
    The project's dependencies are listed in a `requirements.txt` file (Note: This file should be created and populated with necessary libraries like Panda3D). Once your virtual environment is activated, install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Game:**
    After successfully installing the dependencies, you can start the game by running the `main.py` script:
    ```bash
    python main.py
    ```

The game window should appear, and you can start playing!

## 3. Preview

Below is a glimpse of the Chinese-kart gameplay experience.

https://github.com/user-attachments/assets/378007fe-0191-4153-9655-d7a3260820f2


## 4. Specifications

This section delves into the technical details of Chinese-kart, including its code structure, game architecture, and specific Panda3D features utilized.

### 4.1. Code Structure (MVC Approach)

The project adheres to a Model-View-Controller (MVC)-like file structure to promote separation of concerns and modularity. This makes the codebase easier to navigate, understand, and extend. Files are kept relatively short, and functions/methods are designed to be concise and focused on a single responsibility.

Here's a breakdown of the primary directories and their roles:

*   **`/` (Root Directory):**
    *   `main.py`: The main entry point of the application. It initializes the ShowBase instance (the Panda3D core), sets up the game window, loads initial configurations, and orchestrates the creation and anagement of major game components like the game state manager, UI elements, and the primary game loop.
    *   `README.md`: This file, providing information about the project.
    *   `requirements.txt`: Lists project dependencies (to be created/updated with Panda3D, etc.).

*   **`game_logic/`:**
    This directory is central to the game's operational flow and rules.
    *   `game_state.py` (`GameStateManager`): Manages the different states of the game, such as 'menu', 'playing', 'paused', 'game_over', and 'game_won'. It controls transitions between these states and ensures that appropriate actions (e.g., showing menus, starting/stopping game updates) are taken.
    *   `game_loop.py` (`GameLoop`): Contains the core logic for the 'playing' state. It handles updates per frame when the game is active, including processing player input, updating physics, managing game time, checking for win/lose conditions, and coordinating AI actions.
    *   `ai_controller.py`: Implements the artificial intelligence for opponent karts. This includes pathfinding logic (likely following the `trackCurvePoints`), obstacle avoidance, speed control, and decision-making to provide challenging and believable opponents.

*   **`game_objects/`:**
    This directory contains the Python classes and functions responsible for creating, managing, and defining the behavior of all interactive and static objects within the game world.
    *   `kart.py`: Defines the player's kart and AI karts, including loading their 3D models, setting up collision shapes, and managing kart-specific properties.
    *   `track.py`: Responsible for generating or loading the racetrack. This includes defining the track's geometry, surface properties, and potentially the B-spline curve points (`trackCurvePoints`) that define the track's centerline for AI navigation and progress tracking.
    *   `barrier_block.py`, `tree.py`, `building.py`: Define various static environmental objects. These files handle loading their models and setting up their collision properties to interact with karts.
    *   `ground.py`: Creates the ground plane or terrain.
    *   `starting_line.py`: Defines the starting line object, which is crucial for race management (e.g., lap counting, race start/finish).
    *   `simple_objects.py`: May contain utility functions for creating basic geometric primitives used in constructing more complex game objects or for placeholder visuals.
    *   `__init__.py`: Makes the directory a Python package.

*   **`physics/`:**
    Handles the physical interactions and simulations within the game.
    *   `kart_physics.py` (`KartPhysics`): Implements the physics model for the karts. This includes acceleration, deceleration, steering, friction, and handling forces. It updates the kart's position and orientation based on player input and physical parameters.
    *   `track_detection.py`: Likely contains logic for detecting if a kart is on or off the track, which can be used to apply penalties (e.g., slowing down the kart if it goes onto the grass). This might involve checking the kart's position against the track's defined boundaries.
    *   `__init__.py`: Makes the directory a Python package.

*   **`models/`:**
    This directory stores the 3D model files used in the game. Panda3D supports various model formats, with `.egg` being its native format.
    *   `car-*.egg`: These are the 3D models for the different colored karts. For example, `car-yellow.egg`, `car-blue.egg`, etc.

*   **`ui/`:**
    Contains all modules related to the User Interface (UI) and User Experience (UX).
    *   `menus.py` (`MenuManager`): Manages the game's menus, such as the start menu, pause menu, options menu, and end-game screens. It handles displaying these menus and processing user interactions with them.
    *   `minimap.py` (`Minimap`): Implements the on-screen minimap, which shows the track layout and the positions of the player and AI karts in real-time.
    *   `hud_display.py` (`HUDDisplay`): Manages the Heads-Up Display, showing crucial in-game information like speed, current lap, race position, and game time.
    *   `start_countdown.py` (`StartCountdown`): Implements the visual countdown (e.g., "3, 2, 1, GO!") that appears at the beginning of a race, during which player input is typically blocked.
    *   `__init__.py`: Makes the directory a Python package.

*   **`utils/` (Inferred from `main.py` imports):**
    This directory likely houses utility modules and helper functions that are used across different parts of the game.
    *   `lighting.py`: Contains functions to set up the lighting for the game scene (e.g., ambient light, directional lights).
    *   `camera.py`: Manages camera behavior, including setting different view modes (first-person, third-person), camera positioning relative to the kart, and smooth camera transitions.
    *   `progress_tracker.py` (`ProgressTracker`): Tracks the player's and AI karts' progress along the track, calculating lap times, current lap, and race position. This often uses the `trackCurvePoints`.
    *   `object_placement.py` (mentioned as a debug utility in `main.py`): Could be a utility for developers to log kart positions or place objects in the scene during development.

### 4.2. Game Build and Panda3D Core Concepts

Chinese-kart is built using the Panda3D engine, a powerful open-source framework for 3D game development.

*   **Scene Graph (`render` and `gameRoot`):**
    Panda3D uses a scene graph to organize all visible and logical elements in the 3D world. The `ShowBase` class (from which `KartGame` in `main.py` inherits) provides a default root node called `render`. All objects that should be visible in the game are parented to `render` or one of its children.
    In this project, `self.gameRoot = self.render.attachNewNode("GameRoot")` is used. This `gameRoot` node serves as a primary organizational node under `render`, to which game-specific elements like the track, karts, and environmental objects are attached. This helps in managing game states, for instance, by showing or hiding `gameRoot` when pausing or switching to a menu.

    The "case tree" mentioned in the prompt likely refers to this **scene graph hierarchy**. For example:
    ```
    render
      └── gameRoot
          ├── track
          ├── ground
          ├── starting_line
          ├── kart (player)
          │   └── kart_collider
          ├── ai_kart_1
          │   └── ai_kart_1_collider
          ├── ... (other AI karts)
          └── ... (other game objects like barriers, trees)
      └── camera
      └── aspect2d (for UI elements)
          ├── menu_manager_nodes
          ├── hud_display_nodes
          ├── minimap_nodes
          └── countdown_text
    ```
    Each object (`NodePath` in Panda3D terms) in the scene has a position, rotation, and scale relative to its parent, allowing for complex arrangements and movements.

*   **Game Loop and Tasks:**
    The game runs on a central game loop, managed by Panda3D's task manager. The `updateGame` method in `main.py` is added as a task that gets called every frame. This task checks the current game state (via `GameStateManager`) and delegates updates accordingly, primarily to the `GameLoop` class when in the 'playing' state. This is where physics are updated, AI decisions are made, and game logic progresses.

*   **Collision Detection and Handling:**
    Panda3D provides a robust collision system.
    1.  **Collision Solids and Nodes:** Game objects like karts and barriers are given collision geometry (e.g., `CollisionSphere`, `CollisionBox`) attached to `CollisionNode`s. These nodes are then made part of the scene graph. For instance, `self.kart_collider` is created in `main.py`.
    2.  **CollisionTraverser (`cTrav`):** A `CollisionTraverser` is set up to check for intersections between "from" colliders (e.g., kart) and "into" colliders (e.g., barriers, other karts).
    3.  **Collision Handlers:**
        *   `CollisionHandlerPusher`: This handler is used to physically prevent objects from interpenetrating. When a kart's collider (added to the `pusher` via `self.pusher.add_collider(self.kart_collider, self.kart)`) attempts to move into a barrier, the `CollisionHandlerPusher` will push it back, simulating a solid collision.
        *   `CollisionHandlerEvent`: This handler fires events when collisions occur. The game listens for these events (e.g., `self.accept('pusher_kart_collision-into-barrier_collision', self.on_kart_barrier_collision)`) to trigger specific game logic, like reducing a kart's speed or playing a sound effect. The pattern `collision_%fn-into-%in` or `pusher_%fn-into-%in` helps identify which specific colliders were involved.

*   **Input Handling:**
    Player input (keyboard for steering, acceleration, braking, camera controls, etc.) is managed using Panda3D's `accept` mechanism. For example, `self.accept("escape", self.state_manager.toggle_pause)` maps the "escape" key to the `toggle_pause` method. Kart controls are set up within the `KartPhysics` class.

*   **Models and Assets:**
    3D models are loaded using `self.loader.loadModel()`. The `.egg` files in the `/models` directory are text-based files that describe the geometry, texturing, and hierarchy of the 3D models.

### 4.3. B-Splines for Track Definition

B-splines (or similar parametric curves like Catmull-Rom splines) are commonly used in racing games to define the path of the track smoothly and mathematically. In this project:

*   The `create_track` function (from `game_objects/track.py`) returns `track_data`, which includes `self.trackCurvePoints`. These points likely represent the control points or evaluated points of a B-spline (or a series of connected Bezier curves or other splines) that define the centerline or an ideal racing line of the track.
*   The line `self.trackCurvePoints.reverse()` in `main.py` suggests that the order of these points is important, specifically to ensure an anti-clockwise track direction for consistent race logic (e.g., lap counting, AI navigation).
*   These `trackCurvePoints` are crucial for several systems:
    *   **AI Navigation:** AI karts use these points as a path to follow. They might interpolate between points to find their target position and orientation.
    *   **Progress Tracking (`ProgressTracker`):** The `ProgressTracker` uses these points to determine how far a kart has progressed along the track, to count laps, and to calculate race positions. It can project a kart's current position onto the nearest segment of the spline to find its parametric distance along the track.
    *   **Minimap (`Minimap`):** The minimap uses these points to draw the track layout.

The use of splines allows for complex and smooth track shapes that would be difficult to define with simple geometric primitives alone.

### 4.4. Camera: Far and Near Clipping Planes

The camera in a 3D scene needs to know what range of distances to render. Objects too close to the camera or too far away are "clipped" (not drawn) to save rendering resources and avoid visual artifacts. This is controlled by the near and far clipping planes.

*   In `main.py`, `self.camLens.setNearFar(5, 5000)` is called during initialization.
    *   **Near Plane (5 units):** Objects closer than 5 units to the camera will not be rendered. This helps prevent issues like the camera clipping through the player's own kart model in a third-person view if the kart is very close, or rendering the inside of objects if the camera gets too close.
    *   **Far Plane (5000 units):** Objects farther than 5000 units from the camera will not be rendered. This is an optimization, as rendering extremely distant objects that might be barely visible (or not at all) consumes performance. It also helps manage the depth buffer precision (z-buffer). The value of 5000 units suggests a fairly large visible area, suitable for a racetrack where players might need to see distant parts of the track or scenery.

Choosing appropriate near and far plane values is important for balancing visual range with rendering performance and avoiding z-fighting artifacts (where surfaces at similar depths flicker).

### 4.5. Naming Conventions and Code Style

The project aims to follow specific naming conventions and code style guidelines as per the user's custom instructions:

*   **Directories:** `kebab-case` (e.g., `game-logic`, `game-objects`). *Current structure uses `snake_case` (e.g., `game_logic`). This is a point of current deviation from the specified convention if `kebab-case` is strictly desired for future directories.*
*   **Variables and Functions:** `camelCase` (e.g., `gameStartTime`, `updateGame`). Auxiliary verbs are used for boolean variables (e.g., `isLoading`, `inputBlocked`).
*   **Components/Classes:** `PascalCase` (e.g., `KartGame`, `GameStateManager`, `KartPhysics`).
*   **Conciseness:** Code is intended to be concise and technical.
*   **Functional/Declarative:** Functional and declarative programming paradigms are preferred where possible.
*   **Modularity:** Emphasis on modularization, iteration, and props over code duplication.
*   **Syntax:** Adherence to existing syntax within files in the same directory. Unnecessary curly braces in conditionals are avoided (more relevant to languages like JavaScript or C++, but in Python, this translates to clean `if/else` structures without redundant parentheses if not needed for clarity).
*   **Comments:** Goals and use of functions/methods are explained *before* the code block, with no inline comments within the function/method bodies.

## 5. Collaboration

This project is a result of dedication and effort from its contributors.

*   **Contributors:**
    *   Alexandre Paiva - `https://github.com/Alexaandrepaiva`
    *   Bruce - `https://github.com/williams-bruce`
    *   Léo - `https://github.com/slaplacian`
    *   Laurindo - `https://github.com/diogolau`


