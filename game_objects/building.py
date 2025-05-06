from panda3d.core import Vec3
from direct.showbase.DirectObject import DirectObject
from .simple_objects import create_prism

def create_building(start_pos, building_height=10.0, building_width=1.5, building_depth=1.5):
    """
    Creates a building at the given start_pos.
    - building_height: height of the building (default 20.0, 10x tree height)
    - building_width: width of the building
    - building_depth: depth of the building
    """
    from panda3d.core import NodePath
    building_np = NodePath('building')

    # Building (solid gray)
    building_color = (0.4, 0.4, 0.4, 1)  # solid gray
    building_direction = Vec3(0, 0, 1)  # Upwards
    building_pos = start_pos
    building = create_prism(
        pos=building_pos,
        direction=building_direction,
        color=building_color,
        base_size=building_width,
        height=building_height
    )
    building.reparentTo(building_np)

    # Force the building to appear solid gray, regardless of textures or lighting
    building.setTextureOff(1)  # Disable textures
    building.setLightOff(1)    # Disable lighting
    building.setColor((0.4, 0.4, 0.4, 1), 1)  # Set solid gray color

    # Add black border using LineSegs, slightly larger than the building
    from panda3d.core import LineSegs
    border_scale = 1.04  # 4% larger for even more visibility
    half = (building_width * border_scale) / 2
    h = building_height * border_scale
    # The box model is centered at building_pos, so we must center the border as well
    z_center = building_pos.getZ()
    z_bottom = z_center - h/2
    z_top = z_center + h/2
    # 8 corners of the box (centered)
    corners = [
        Vec3(-half, -half, z_bottom), Vec3(half, -half, z_bottom), Vec3(half, half, z_bottom), Vec3(-half, half, z_bottom),
        Vec3(-half, -half, z_top), Vec3(half, -half, z_top), Vec3(half, half, z_top), Vec3(-half, half, z_top)
    ]
    edges = [
        (0,1),(1,2),(2,3),(3,0), # bottom
        (4,5),(5,6),(6,7),(7,4), # top
        (0,4),(1,5),(2,6),(3,7)  # verticals
    ]
    segs = LineSegs()
    segs.setThickness(4)  # Thicker border
    segs.setColor(0,0,0,1)
    for a,b in edges:
        segs.moveTo(corners[a])
        segs.drawTo(corners[b])
    border_np = building_np.attachNewNode(segs.create())

    return building_np

# Example usage:
# building = create_building(Vec3(10, 0, 0))
# building.reparentTo(render)
