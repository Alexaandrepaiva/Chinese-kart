from panda3d.core import CardMaker, Vec4, CollisionNode, CollisionBox, Point3, NodePath

def create_kart(game_root, loader, color=Vec4(1, 0, 0, 1), show_collider=False):
    """
    Creates a kart model and returns the node and collider
    
    Args:
        game_root: The root node to attach the kart to
        loader: The asset loader
        color: The color of the kart (Vec4)
        show_collider: Se deve mostrar o colisor para depuração
        
    Returns:
        tuple: (kart_node, collider_node)
    """
    
    # Map colors to model files
    color_to_model = {
        Vec4(0, 0, 1, 1): "models/car-blue.egg",
        Vec4(0, 0.8, 0, 1): "models/car-green.egg",
        Vec4(1, 0, 0, 1): "models/car-red.egg",
        Vec4(1, 1, 0, 1): "models/car-yellow.egg",
        Vec4(0.8, 0, 0.8, 1): "models/car-purple.egg",
        Vec4(1, 0.5, 0, 1): "models/car-orange.egg",
    }
    
    # Get the appropriate model file based on color
    model_file = color_to_model.get(color, "models/car-orange.egg")  # Default to orange if color not found
    
    try:
        # Try loading the car model from .egg file
        kart = loader.loadModel(model_file)
        kart.reparentTo(game_root)
        kart.setScale(1.0, 1.0, 1.0)  # Set scale back to 1.0 to make the car larger
        
    except OSError:
        # Fallback if model file is not found
        print(f"Warning: {model_file} not found. Using CardMaker fallback for kart.")
        cm = CardMaker("kart-card")  # Use CardMaker to create a flat card initially
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)  # Set the size of the card
        
        # Create a parent node to hold all faces
        kart_node = NodePath("kart")
        kart_node.reparentTo(game_root)
        
        # Create 6 faces for a cube
        for i in range(6):
            face = NodePath(cm.generate())
            face.reparentTo(kart_node)
            # Position and rotate each face to form a cube
            if i == 0: face.setPosHpr(0, 0, 0.5, 0, 0, 0)    # Top
            elif i == 1: face.setPosHpr(0, 0, -0.5, 180, 0, 0) # Bottom
            elif i == 2: face.setPosHpr(0, 0.5, 0, 90, 0, 0)  # Front
            elif i == 3: face.setPosHpr(0, -0.5, 0, -90, 0, 0) # Back
            elif i == 4: face.setPosHpr(0.5, 0, 0, 0, 90, 90)  # Right
            elif i == 5: face.setPosHpr(-0.5, 0, 0, 0, -90, 90) # Left
        kart = kart_node  # Assign the parent node as the kart
    
    kart.setColor(color)
    
    # Create a collider for the kart
    collider = CollisionNode("kart_collision")
    # Usar os tamanhos específicos para a caixa de colisão
    collider.addSolid(CollisionBox(Point3(0, 0, 0.2), 0.6, 0.98, 0.4))  # Ajustado o centro um pouco para cima
    
    # Configuração de colisão: o kart deve testar colisão com barreiras e outros karts
    # BitMask 0x1 corresponde às barreiras
    # BitMask 0x2 corresponde a outros karts
    collider.setFromCollideMask(0x1 | 0x2)  # Kart will test for collisions with barriers and other karts
    collider.setIntoCollideMask(0x2)  # Other karts can collide with this kart
    
    collider_node = kart.attachNewNode(collider)
    if show_collider:
        collider_node.show()  # For debugging
    
    return kart, collider_node
