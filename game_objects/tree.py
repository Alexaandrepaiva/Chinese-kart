from panda3d.core import Vec3
from direct.showbase.DirectObject import DirectObject
from .simple_objects import create_prism, create_sphere

# Tree creation utility
def create_tree(start_pos, trunk_height=2.0, trunk_radius=0.2, leaf_radius=0.7):
    """
    Creates a tree at the given start_pos, with trunk and leaf vertically aligned.
    - trunk_height: height of the trunk
    - trunk_radius: thickness of the trunk
    - leaf_radius: radius of the leaf sphere
    """
    tree_np = render.attachNewNode('tree')
    
    # Trunk (brown)
    trunk_color = (0.55, 0.27, 0.07, 1)
    trunk_direction = Vec3(0, 0, 1)  # Upwards
    trunk_pos = start_pos
    trunk = create_prism(
        pos=trunk_pos,
        direction=trunk_direction,
        color=trunk_color,
        base_size=trunk_radius,
        height=trunk_height
    )
    trunk.reparentTo(tree_np)

    # Leaves (green)
    leaf_color = (0.13, 0.55, 0.13, 1)
    leaf_direction = Vec3(0, 0, 1)
    leaf_pos = start_pos + Vec3(0, 0, trunk_height + leaf_radius * 0.5)
    leaf = create_sphere(
        pos=leaf_pos,
        direction=leaf_direction,
        color=leaf_color,
        radius=leaf_radius
    )
    leaf.reparentTo(tree_np)

    return tree_np

# Example usage: place at starting line
# You may want to import and call this from the track or starting_line module, e.g.
# tree = create_tree(Vec3(0, 0, 0))
# tree.reparentTo(render)
