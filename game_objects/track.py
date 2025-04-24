from panda3d.core import Point3, Vec3, Vec4, GeomVertexFormat, GeomVertexData, GeomVertexWriter, Geom, GeomTriangles, GeomNode, LineSegs, NodePath
import math
from utils.spline import eval_catmull_rom, tangent_catmull_rom

def create_track(game_root):
    """
    Creates the track for the game with a road surface and sand border
    Returns track object and track curve points for kart positioning
    """
    track_node = game_root.attachNewNode("Track")
    track_color = Vec4(0.3, 0.3, 0.3, 1)  # Dark gray for the road surface
    start_line_color = Vec4(0.9, 0.9, 0.9, 1)  # White for the start line
    sand_color = Vec4(0.87, 0.77, 0.54, 1)  # Beige/sand color for the border
    warning_stripe_white = Vec4(1.0, 1.0, 1.0, 1)  # White for warning stripes
    warning_stripe_red = Vec4(1.0, 0.2, 0.2, 1)  # Red for warning stripes
    road_width = 15.0  # Width of the actual drivable road
    sand_border_width = 12.0  # Width of the sand border on each side (increased for difficult curves)
    track_width = road_width + (sand_border_width * 2)  # Total width including sand borders
    segments_per_curve = 30  # Further increased for smoother curves
    world_up = Vec3(0, 0, 1)

    # Define the control points for the Catmull-Rom spline.
    # We need points before the start and after the end for the spline calculation.
    # Make the track loop by repeating start/end points appropriately.
    raw_track_points = [
        Point3(250, -120, 0),   # P11: Final corner returning to start
        Point3(200, -60, 0),    # P10: Sharp curve before returning to start
        Point3(140, -100, 0),   # P9: Short straight before final section
        Point3(60, -80, 0),     # P8: Exit of tight curve
        Point3(20, -20, 0),     # P7: Tight technical curve
        Point3(80, 40, 0),      # P6: Middle of S-curves
        Point3(30, 120, 0),     # P5: Entry to S-curves
        Point3(80, 200, 0),     # P4: Approaching technical section
        Point3(150, 240, 0),    # P3: Continuing first curve
        Point3(230, 220, 0),    # P2: First corner after straight
        Point3(280, 150, 0),    # P1: End of long straight section
        Point3(280, -100, 0),    # P0: Start/finish line (bottom of straight)
    ]
    num_points = len(raw_track_points)
    track_points = []  # This will hold points including wraparound for spline calc
    track_points.append(raw_track_points[num_points - 1])  # Add last point as P_{-1}
    track_points.extend(raw_track_points)
    track_points.append(raw_track_points[0])  # Add P0 as P_{n}
    track_points.append(raw_track_points[1])  # Add P1 as P_{n+1}

    # --- Generate Spline Points and Track Vertices ---
    track_curve_points = []  # Store centerline points for kart positioning
    road_vertex_list = []  # Stores vertices for the road surface
    sand_vertex_list = []  # Stores vertices for the sand borders

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

            # Calculate road vertices (inner part of the track)
            v_road_left = point - binormal * road_width / 2.0
            v_road_right = point + binormal * road_width / 2.0
            
            # Add stripes to all track sections, not just difficult curves
            stripe_width = 1.0
            v_stripe_left = v_road_left - binormal * stripe_width
            v_stripe_right = v_road_right + binormal * stripe_width
            stripe_color = warning_stripe_white if (j % 2 == 0) else warning_stripe_red
            
            # Store vertices
            road_vertex_list.append({
                'left': v_road_left, 
                'right': v_road_right, 
                'start_line': is_start_segment,
                'stripe_color': stripe_color,
                'stripe_left': v_stripe_left,
                'stripe_right': v_stripe_right
            })
            
            # Calculate sand border vertices (outer part of the track)
            v_sand_left = point - binormal * track_width / 2.0
            v_sand_right = point + binormal * track_width / 2.0
            
            # Store vertices
            sand_vertex_list.append({
                'inner_left': v_road_left,
                'outer_left': v_sand_left,
                'inner_right': v_road_right,
                'outer_right': v_sand_right
            })

            # Store centerline point (except the very last duplicate)
            if not (j == segments_per_curve - 1 and i == num_points):
                track_curve_points.append(point)

        # Add the final point of the segment explicitly (t=1)
        point = eval_catmull_rom(p0, p1, p2, p3, 1.0)
        tangent = tangent_catmull_rom(p0, p1, p2, p3, 1.0)
        tangent.normalize()
        binormal = tangent.cross(world_up)
        binormal.normalize()
        
        # Road vertices
        v_road_left = point - binormal * road_width / 2.0
        v_road_right = point + binormal * road_width / 2.0
        
        # Add stripes to all track sections, not just difficult curves
        stripe_width = 1.0
        v_stripe_left = v_road_left - binormal * stripe_width
        v_stripe_right = v_road_right + binormal * stripe_width
        stripe_color = warning_stripe_white if (i % 2 == 0) else warning_stripe_red
        
        # Store vertices
        road_vertex_list.append({
            'left': v_road_left, 
            'right': v_road_right, 
            'start_line': is_start_segment,
            'stripe_color': stripe_color,
            'stripe_left': v_stripe_left,
            'stripe_right': v_stripe_right
        })
        
        # Sand border vertices
        v_sand_left = point - binormal * track_width / 2.0
        v_sand_right = point + binormal * track_width / 2.0
        
        # Store vertices
        sand_vertex_list.append({
            'inner_left': v_road_left,
            'outer_left': v_sand_left,
            'inner_right': v_road_right,
            'outer_right': v_sand_right
        })
        # Don't add final centerline point here, it's the start of the next segment

    # --- Create Sand Border Geometry ---
    def create_border_geometry():
        format = GeomVertexFormat.getV3n3c4()  # Vertex, Normal, Color
        vdata = GeomVertexData('sand_border_geom', format, Geom.UHStatic)
        # Each cross-section has 4 vertices (inner_left, outer_left, inner_right, outer_right)
        num_vertices = len(sand_vertex_list)
        vdata.setNumRows(num_vertices * 4)
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        
        for i in range(num_vertices):
            v_info = sand_vertex_list[i]
            
            # Add vertices for left border (inner_left to outer_left)
            # Inner left
            vertex.addData3(v_info['inner_left'])
            normal.addData3(world_up)
            color.addData4(sand_color)
            # Outer left
            vertex.addData3(v_info['outer_left'])
            normal.addData3(world_up)
            color.addData4(sand_color)
            
            # Add vertices for right border (inner_right to outer_right)
            # Inner right
            vertex.addData3(v_info['inner_right'])
            normal.addData3(world_up)
            color.addData4(sand_color)
            # Outer right
            vertex.addData3(v_info['outer_right'])
            normal.addData3(world_up)
            color.addData4(sand_color)
        
        tris = GeomTriangles(Geom.UHStatic)
        # Add triangles for the left and right sand borders
        for i in range(num_vertices - 1):
            # Base index for this segment
            idx = i * 4
            
            # Left sand border - Two triangles
            # First triangle: (inner_left_i, outer_left_i, inner_left_{i+1})
            tris.addVertices(idx, idx + 1, idx + 4)
            # Second triangle: (outer_left_i, outer_left_{i+1}, inner_left_{i+1})
            tris.addVertices(idx + 1, idx + 5, idx + 4)
            
            # Right sand border - Two triangles
            # First triangle: (inner_right_i, outer_right_i, inner_right_{i+1})
            tris.addVertices(idx + 2, idx + 3, idx + 6)
            # Second triangle: (outer_right_i, outer_right_{i+1}, inner_right_{i+1})
            tris.addVertices(idx + 3, idx + 7, idx + 6)
        
        tris.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        
        node = GeomNode('sand_border_geom_node')
        node.addGeom(geom)
        return node
    
    # --- Create Warning Stripes Geometry ---
    def create_warning_stripes_geometry():
        format = GeomVertexFormat.getV3n3c4()  # Vertex, Normal, Color
        vdata = GeomVertexData('warning_stripes_geom', format, Geom.UHStatic)
        
        # Count vertices needed (2 vertices per stripe section)
        num_stripe_vertices = len(road_vertex_list)
        vdata.setNumRows(num_stripe_vertices * 2)
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        
        # Keep track of vertex indices for triangles
        vertex_indices = []
        current_idx = 0
        
        for i in range(len(road_vertex_list) - 1):
            v_info = road_vertex_list[i]
            next_v_info = road_vertex_list[i + 1]
            
            # Left stripe
            vertex.addData3(v_info['stripe_left'])
            normal.addData3(world_up)
            color.addData4(v_info['stripe_color'])
            
            # Right stripe
            vertex.addData3(v_info['stripe_right'])
            normal.addData3(world_up)
            color.addData4(v_info['stripe_color'])
            
            vertex_indices.append((current_idx, current_idx + 1))
            current_idx += 2
        
        tris = GeomTriangles(Geom.UHStatic)
        
        # Create triangles connecting consecutive stripe sections
        for i in range(len(vertex_indices) - 1):
            curr_left, curr_right = vertex_indices[i]
            next_left, next_right = vertex_indices[i + 1]
            
            # Left stripe triangle
            tris.addVertices(curr_left, curr_right, next_left)
            # Right stripe triangle
            tris.addVertices(curr_right, next_right, next_left)
        
        tris.closePrimitive()
        
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        
        node = GeomNode('warning_stripes_geom_node')
        node.addGeom(geom)
        return node

    # --- Create Road Geometry ---
    def create_road_geometry():
        format = GeomVertexFormat.getV3n3c4()  # Vertex, Normal, Color
        vdata = GeomVertexData('road_geom', format, Geom.UHStatic)
        # Pre-allocate rows (2 vertices per cross-section * num cross-sections)
        num_vertices = len(road_vertex_list)
        vdata.setNumRows(num_vertices * 2)
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        
        for i in range(num_vertices):
            v_info = road_vertex_list[i]
            
            # Left edge - use regular track color for all sections
            vertex.addData3(v_info['left'])
            normal.addData3(world_up)
            color.addData4(track_color)
            
            # Right edge - use regular track color for all sections
            vertex.addData3(v_info['right'])
            normal.addData3(world_up)
            color.addData4(track_color)
        
        tris = GeomTriangles(Geom.UHStatic)
        
        # Create triangles connecting each segment
        for i in range(num_vertices - 1):
            idx = i * 2
            
            # First triangle (left_i, right_i, left_{i+1})
            tris.addVertices(idx, idx + 1, idx + 2)
            
            # Second triangle (right_i, right_{i+1}, left_{i+1})
            tris.addVertices(idx + 1, idx + 3, idx + 2)
        
        tris.closePrimitive()
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        
        node = GeomNode('road_geom_node')
        node.addGeom(geom)
        return node
    
    # Create and attach geometries
    # sand_border_node = create_border_geometry()  # Sand borders removed
    road_node = create_road_geometry()
    warning_stripes_node = create_warning_stripes_geometry()
    
    # The track_node is the parent for the road and warning stripes
    # track_node.attachNewNode(sand_border_node)  # Sand borders removed
    warning_stripes_np = track_node.attachNewNode(warning_stripes_node)
    warning_stripes_np.setZ(-0.01)  # Slightly below the road so track appears on top
    track_node.attachNewNode(road_node)
    
    # Ensure track is at Z=0
    track_node.setPos(0, 0, 0)

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
