from panda3d.core import CardMaker, Vec4, CollisionNode, CollisionBox, Point3

def create_kart(game_root, loader, color=Vec4(1, 0, 0, 1)):
    """
    Creates the kart for the game
    Accepts a color parameter to set the kart's color.
    """
    try:
         # Try loading the model first
         kart = loader.loadModel("models/box")
         kart.reparentTo(game_root)
         kart.setScale(1, 1, 1)  # Set scale if model loaded
    except OSError:
         # Fallback if models/box is not found
         print("Warning: models/box.egg not found. Using CardMaker fallback for kart.")
         cm = CardMaker("kart-card")  # Use CardMaker to create a flat card initially

         # Create the 6 faces of the cube using CardMaker
         kart_node = game_root.attachNewNode("kart")
         for i in range(6):
             face = kart_node.attachNewNode(cm.generate())
             if i == 0: face.setPosHpr(0, 0, 0.5, 0, 0, 0)      # Top
             elif i == 1: face.setPosHpr(0, 0, -0.5, 0, 180, 0)  # Bottom
             elif i == 2: face.setPosHpr(0, 0.5, 0, 0, -90, 0)   # Front
             elif i == 3: face.setPosHpr(0, -0.5, 0, 0, 90, 0)   # Back
             elif i == 4: face.setPosHpr(0.5, 0, 0, 0, -90, -90) # Right
             elif i == 5: face.setPosHpr(-0.5, 0, 0, 0, -90, 90) # Left
         kart = kart_node  # Assign the parent node as the kart

    # Set common properties outside try/except
    kart.setColor(color)  # Use the provided color
    
    # --- Rotate the kart 180 degrees to align its visual front with +Y ---
    kart.setH(180)

    # --- Attach a collision box to the kart ---
    cnode = CollisionNode('kart_collision')
    cbox = CollisionBox(Point3(0, 0, 0.5), 0.6, 0.6, 0.5)  # Centered, fits default kart size
    cnode.add_solid(cbox)
    cnode.set_from_collide_mask(0x1)  # Matches barrier's into mask
    cnode.set_into_collide_mask(0)
    collider = kart.attach_new_node(cnode)

    return kart, collider
