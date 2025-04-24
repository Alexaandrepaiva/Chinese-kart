from panda3d.core import CardMaker, Vec4

def create_ground(game_root, loader):
    """
    Creates the ground for the game
    """
    try:
        # Try loading the model first
        ground = loader.loadModel("models/plane")
        ground.reparentTo(game_root)
    except OSError:
        # Fallback if models/plane is not found
        print("Warning: models/plane.egg not found. Using CardMaker fallback.")
        cm = CardMaker("ground")
        cm.setFrame(-500, 500, -500, 500)
        ground = game_root.attachNewNode(cm.generate())
        # Need to set rotation for CardMaker plane to be horizontal
        ground.setP(-90)

    ground.setScale(1000, 1000, 1)  # Make it large
    ground.setPos(0, 0, -0.1)  # Slightly below zero
    ground.setColor(Vec4(0.2, 0.6, 0.2, 1))  # Green color
    
    return ground
