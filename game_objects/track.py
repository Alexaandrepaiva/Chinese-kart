from panda3d.core import Point3, Vec3, Vec4, GeomVertexFormat, GeomVertexData, GeomVertexWriter, Geom, GeomTriangles, GeomNode, LineSegs
from utils.spline import eval_catmull_rom, tangent_catmull_rom

def create_track(game_root):
    """
    Creates the track for the game
    Returns track object and track curve points for kart positioning
    """
    track_node = game_root.attachNewNode("Track")
    track_color = Vec4(0.3, 0.3, 0.3, 1)
    start_line_color = Vec4(0.9, 0.9, 0.9, 1)
    track_width = 10.0
    segments_per_curve = 20  # Increase for smoother curves
    world_up = Vec3(0, 0, 1)

    # Define the control points for the Catmull-Rom spline.
    # We need points before the start and after the end for the spline calculation.
    # Make the track loop by repeating start/end points appropriately.
    raw_track_points = [
        Point3(0, -150, 0),    # P0: Start of long straight
        Point3(0, 150, 0),     # P1: End of long straight / Start of first curve
        Point3(150, 250, 0),   # P2: Top of first curve
        Point3(300, 150, 0),   # P3: End of first curve / Start of short straight
        Point3(300, 50, 0),    # P4: End of short straight / Start of second curve
        Point3(150, -50, 0),   # P5: Bottom of second curve
        # Point3(0, -150, 0)   # P6 = P0: End of second curve (back to start)
    ]
    num_points = len(raw_track_points)
    track_points = []  # This will hold points including wraparound for spline calc
    track_points.append(raw_track_points[num_points - 1])  # Add last point as P_{-1}
    track_points.extend(raw_track_points)
    track_points.append(raw_track_points[0])  # Add P0 as P_{n}
    track_points.append(raw_track_points[1])  # Add P1 as P_{n+1}

    # --- Generate Spline Points and Track Vertices ---
    track_curve_points = []  # Store centerline points for kart positioning
    vertex_list = []  # Stores (left_vertex, right_vertex) pairs

    for i in range(1, num_points + 1):
        p0 = track_points[i - 1]
        p1 = track_points[i]    # Segment starts here
        p2 = track_points[i + 1]  # Segment ends here
        p3 = track_points[i + 2]

        is_start_segment = (i == 1)  # Is this the first segment (for start line color)?

        # Generate points along this segment
        for j in range(segments_per_curve):
            t = float(j) / segments_per_curve
            point = eval_catmull_rom(p0, p1, p2, p3, t)
            tangent = tangent_catmull_rom(p0, p1, p2, p3, t)
            tangent.normalize()

            if j == 0 and i == 1:
                track_curve_points.append(point)  # Add first point

            # Calculate the perpendicular vector (binormal)
            binormal = tangent.cross(world_up)
            binormal.normalize()

            # Calculate left and right vertices
            v_left = point - binormal * track_width / 2.0
            v_right = point + binormal * track_width / 2.0
            vertex_list.append({'left': v_left, 'right': v_right, 'start_line': is_start_segment})

            # Store centerline point (except the very last duplicate)
            if not (j == segments_per_curve - 1 and i == num_points):
                track_curve_points.append(point)

        # Add the final point of the segment explicitly (t=1)
        point = eval_catmull_rom(p0, p1, p2, p3, 1.0)
        tangent = tangent_catmull_rom(p0, p1, p2, p3, 1.0)
        tangent.normalize()
        binormal = tangent.cross(world_up)
        binormal.normalize()
        v_left = point - binormal * track_width / 2.0
        v_right = point + binormal * track_width / 2.0
        vertex_list.append({'left': v_left, 'right': v_right, 'start_line': is_start_segment})
        # Don't add final centerline point here, it's the start of the next segment

    # --- Create Geometry from Vertices ---
    format = GeomVertexFormat.getV3n3c4()  # Vertex, Normal, Color
    vdata = GeomVertexData('track_geom', format, Geom.UHStatic)
    # Pre-allocate rows (2 vertices per cross-section * num cross-sections)
    num_vertices = len(vertex_list)
    vdata.setNumRows(num_vertices * 2)

    vertex = GeomVertexWriter(vdata, 'vertex')
    normal = GeomVertexWriter(vdata, 'normal')
    color = GeomVertexWriter(vdata, 'color')

    for i in range(num_vertices):
        v_info = vertex_list[i]
        col = start_line_color if v_info['start_line'] else track_color
        # Left vertex
        vertex.addData3(v_info['left'])
        normal.addData3(world_up)
        color.addData4(col)
        # Right vertex
        vertex.addData3(v_info['right'])
        normal.addData3(world_up)
        color.addData4(col)

    tris = GeomTriangles(Geom.UHStatic)
    # Add triangles connecting consecutive vertices
    for i in range(num_vertices - 1):
        idx = i * 2
        # Triangle 1: (left_i, right_i, left_{i+1})
        tris.addVertices(idx, idx + 1, idx + 2)
        # Triangle 2: (right_i, right_{i+1}, left_{i+1})
        tris.addVertices(idx + 1, idx + 3, idx + 2)
    tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)

    node = GeomNode('track_geom_node')
    node.addGeom(geom)
    track_node.attachNewNode(node)
    track_node.setPos(0, 0, 0)  # Ensure track is at Z=0

    return track_node, track_curve_points, track_points


def debug_draw_spline(render, track_curve_points, track_points):
    """
    Helper to visualize the generated spline
    """
    lines = LineSegs()
    lines.setColor(1, 0, 0, 1)
    lines.moveTo(track_curve_points[0])
    for p in track_curve_points[1:]:
        lines.drawTo(p)
    render.attachNewNode(lines.create())

    # Draw control points
    lines_ctrl = LineSegs()
    lines_ctrl.setColor(0, 1, 0, 1)
    for p in track_points[1:-2]:  # Draw the actual raw points used
        lines_ctrl.drawSphere(p, 1.0)
    render.attachNewNode(lines_ctrl.create())
