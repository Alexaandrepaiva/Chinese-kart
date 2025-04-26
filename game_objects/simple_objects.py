from panda3d.core import NodePath, GeomNode, GeomVertexFormat, GeomVertexData, Geom, GeomTriangles, GeomVertexWriter, GeomVertexRewriter, GeomVertexReader, GeomPoints, GeomLines, GeomVertexArrayFormat, GeomEnums, LVector3f, LPoint3f, Material, Vec3, Vec4
from direct.showbase.DirectObject import DirectObject

# Utility to create a NodePath for a colored primitive

def create_cube(pos, direction, color, size):
    """Create a cube at pos, facing direction, with color (r,g,b,1) and size (float)"""
    cube = loader.loadModel('models/box')
    cube.setScale(size)
    cube.setPos(pos)
    cube.lookAt(pos + direction)
    cube.setColor(color)
    return cube

def create_cylinder(pos, direction, color, radius, height):
    """Create a cylinder at pos, facing direction, with color and dimensions"""
    cylinder = loader.loadModel('models/cylinder')
    cylinder.setScale(radius, radius, height)
    cylinder.setPos(pos)
    cylinder.lookAt(pos + direction)
    cylinder.setColor(color)
    return cylinder

def create_sphere(pos, direction, color, radius):
    """Create a sphere at pos, facing direction, with color and radius"""
    sphere = loader.loadModel('models/smiley')
    sphere.setScale(radius)
    sphere.setPos(pos)
    # Spheres are symmetric, so direction doesn't matter
    sphere.setColor(color)
    return sphere

def create_prism(pos, direction, color, base_size, height):
    """Create a triangular prism at pos, upright (Z axis as height), with color, base_size (float), height (float)"""
    # For simplicity, use a box as a placeholder for the prism
    # The box is scaled so Z is up (height), X and Y are base size
    prism = loader.loadModel('models/box')
    prism.setScale(base_size, base_size, height)
    prism.setPos(pos)
    # Do NOT rotate the prism; keep it upright
    prism.setColor(color)
    return prism

def create_pyramid(pos, direction, color, base_size, height):
    """Create a pyramid at pos, facing direction, with color, base_size (float), height (float)"""
    # Placeholder: use a box as a stand-in for a pyramid
    pyramid = loader.loadModel('models/box')
    pyramid.setScale(base_size, base_size, height)
    pyramid.setPos(pos)
    pyramid.lookAt(pos + direction)
    pyramid.setColor(color)
    return pyramid
