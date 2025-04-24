import math
from panda3d.core import Vec3, Point3

def eval_catmull_rom(p0, p1, p2, p3, t):
    """
    Helper function for Catmull-Rom Spline interpolation
    """
    t2 = t * t
    t3 = t2 * t
    return (p1 * 2.0 +
            (-p0 + p2) * t +
            (p0 * 2.0 - p1 * 5.0 + p2 * 4.0 - p3) * t2 +
            (-p0 + p1 * 3.0 - p2 * 3.0 + p3) * t3) * 0.5

def tangent_catmull_rom(p0, p1, p2, p3, t):
    """
    Helper function to get tangent (derivative) of Catmull-Rom
    """
    t2 = t * t
    # Derivative of the evalCatmullRom formula w.r.t. t
    return ((-p0 + p2) + 
            (p0 * 4.0 - p1 * 10.0 + p2 * 8.0 - p3 * 2.0) * t + 
            (-p0 * 3.0 + p1 * 9.0 - p2 * 9.0 + p3 * 3.0) * t2) * 0.5
