from panda3d.core import AmbientLight, DirectionalLight, Vec4, LVector3f

def setup_lighting(render):
    """
    Sets up basic lighting for the scene
    """
    # Ambient light
    ambient_light = AmbientLight("ambientLight")
    ambient_light.setColor(Vec4(0.4, 0.4, 0.4, 1))
    ambient_light_np = render.attachNewNode(ambient_light)
    render.setLight(ambient_light_np)

    # Directional light
    directional_light = DirectionalLight("directionalLight")
    directional_light.setColor(Vec4(0.8, 0.8, 0.8, 1))
    directional_light.setDirection(LVector3f(-5, -5, -5))
    directional_light_np = render.attachNewNode(directional_light)
    render.setLight(directional_light_np)
    
    return ambient_light_np, directional_light_np
