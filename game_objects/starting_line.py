from panda3d.core import Point3, Vec3, Vec4, CardMaker, NodePath, TransparencyAttrib
from .tree import create_tree

def create_starting_line(game_root, track_curve_points):
    """
    Creates a prominent starting line at the beginning of the track
    
    Args:
        game_root: The root node to attach the starting line to
        track_curve_points: The track curve points for positioning
    
    Returns:
        NodePath: The starting line node
    """
    # Get the first segment of the track to position the starting line
    start_point = track_curve_points[0]
    next_point = track_curve_points[1]
    
    # Calculate direction and perpendicular vector
    direction = (next_point - start_point)
    direction.normalize()
    world_up = Vec3(0, 0, 1)
    perpendicular = direction.cross(world_up)
    perpendicular.normalize()
    
    # Create a node for the starting line
    starting_line_node = game_root.attachNewNode("StartingLine")
    
    # Create a card (plane) for the starting line
    road_width = 15.0  # Same as in track.py
    square_size = road_width / 32.0  # Size of each square in the pattern
    line_width = 4 * square_size  # Width of the starting line matches one square height
    
    # Create the checkered pattern card
    cm = CardMaker('starting_line_card')
    cm.setFrame(-road_width/2, road_width/2, -line_width/2, line_width/2)
    
    # Create the card and set its texture
    card = starting_line_node.attachNewNode(cm.generate())
    
    # Create a checkered pattern on the card
    # We'll use a shader to create the pattern
    card.setShader(create_checkered_shader())
    card.setShaderInput("uSquaresX", 16.0)  # Number of columns
    card.setShaderInput("uSquaresY", 2.0)   # Number of rows
    
    # Position the starting line at the track's starting point
    # Raise it slightly above the track to avoid z-fighting
    starting_line_node.setPos(start_point)
    starting_line_node.setZ(0.1)  # Slightly above the track


    # Orient the card to be perpendicular to the track direction
    # The card's default orientation is facing up (Z+)
    # We need to rotate it to face perpendicular to the track direction
    starting_line_node.lookAt(next_point)
    starting_line_node.setH(starting_line_node.getH() + 60)  # Rotate 90 degrees to make it perpendicular to track
    
    # We don't need a colored border for the classic checkered flag look
    

    return starting_line_node

    """
    Creates a pole at the specified position
    """
    # Create a card for each side of the pole
    pole_width = 0.5
    
    # Create the pole node
    pole_node = parent.attachNewNode("Pole")
    pole_node.setPos(position)
    
    # Create cards for each side of the pole
    for i in range(4):
        cm = CardMaker(f'pole_side_{i}')
        cm.setFrame(-pole_width/2, pole_width/2, 0, height)
        card = pole_node.attachNewNode(cm.generate())
        card.setH(i * 90)  # Rotate each side
        card.setPos(0, 0, 0)  # Position at the base
        
        # Alternate black and white stripes
        if i % 2 == 0:
            card.setColor(0, 0, 0, 1)  # Black
        else:
            card.setColor(1, 1, 1, 1)  # White
    
  

def create_checkered_shader():
    """
    Creates a shader that generates a checkered pattern
    """
    from panda3d.core import Shader
    
    # Vertex shader
    vertex_shader = """
    #version 120
    
    uniform mat4 p3d_ModelViewProjectionMatrix;
    
    attribute vec4 p3d_Vertex;
    attribute vec2 p3d_MultiTexCoord0;
    
    varying vec2 texCoord;
    
    void main() {
        gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
        texCoord = p3d_MultiTexCoord0;
    }
    """
    
    # Fragment shader for 2D checkered pattern
    fragment_shader = """
    #version 120
    
    uniform float uSquaresX; // columns
    uniform float uSquaresY; // rows
    
    varying vec2 texCoord;
    
    void main() {
        // Scale texture coordinates by number of squares
        float scaledCoordX = texCoord.x * uSquaresX;
        float scaledCoordY = texCoord.y * uSquaresY;
        
        // Get the integer part of the coordinates
        float cellX = floor(scaledCoordX);
        float cellY = floor(scaledCoordY);
        
        // Determine if we're in a white or black cell
        bool isWhite = mod(cellX + cellY, 2.0) == 0.0;
        
        // Set the color based on the cell
        if (isWhite) {
            gl_FragColor = vec4(1.0, 1.0, 1.0, 1.0);  // White
        } else {
            gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);  // Black
        }
    }
    """
    
    # Create and return the shader
    return Shader.make(Shader.SL_GLSL, vertex_shader, fragment_shader)