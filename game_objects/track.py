from panda3d.core import Point3, Vec3, Vec4, GeomVertexFormat, GeomVertexData, GeomVertexWriter, Geom, GeomTriangles, GeomNode, LineSegs, NodePath
import math
from utils.spline import eval_catmull_rom, tangent_catmull_rom
from game_objects.barrier_block import BarrierBlock  # Import BarrierBlock
from game_objects.tree import create_tree

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

    # We'll place the barrier after generating the track_curve_points

    # --- Place a tree at the starting line ---
    # The starting line is at the first point of the track_curve_points (after generation)
    # We'll add the tree after generating the track_curve_points below, before returning

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

    # --- Place a sequence of Barrier Blocks along the inside ground ---
    if len(track_curve_points) > 0:
        barrier_length = 4.0  # Length of each barrier
        barrier_depth = 1.0   # Depth (thickness)
        barrier_height = 2.0
        spacing = 0.001         # No gap between barriers
        arc_step = barrier_length + spacing
        # Calculate arc-lengths for the curve
        arc_lengths = [0.0]
        for i in range(1, len(track_curve_points)):
            arc_lengths.append(arc_lengths[-1] + (track_curve_points[i] - track_curve_points[i-1]).length())
        total_length = arc_lengths[-1]
        # Place barriers at constant arc-length intervals, skipping first/last few
        barrier_positions = []
        t = 0.0
        while t < total_length:
            # Find segment index for this arc-length
            for i in range(1, len(arc_lengths)):
                if arc_lengths[i] >= t:
                    break
            else:
                break
            # Interpolate between points i-1 and i
            seg_len = arc_lengths[i] - arc_lengths[i-1]
            if seg_len == 0:
                alpha = 0
            else:
                alpha = (t - arc_lengths[i-1]) / seg_len
            pos = track_curve_points[i-1] * (1-alpha) + track_curve_points[i] * alpha
            # Compute tangent and binormal
            tangent = track_curve_points[i] - track_curve_points[i-1]
            tangent_2d = Vec3(tangent.x, tangent.y, 0)
            tangent_2d.normalize()
            perp = Vec3(-tangent_2d.y, tangent_2d.x, 0)
            perp.normalize()
            heading = math.degrees(math.atan2(-perp.x, perp.y))
            inner_offset = (road_width / 2.0) + (barrier_depth / 2.0) + 4.2
            barrier_pos = pos - perp * inner_offset
            barrier_positions.append((barrier_pos, heading))
            t += arc_step
        # Remove some barriers to hide contour details
        barrier_positions = barrier_positions[0:-8]
        # Get starting line position for exclusion
        starting_line_pos = track_curve_points[0]
        skip_radius = 8.0
        for barrier_pos, heading in barrier_positions:
            if (barrier_pos - starting_line_pos).length() < skip_radius:
                continue
            b = BarrierBlock(
                track_node,
                (barrier_pos.x, barrier_pos.y, barrier_pos.z + barrier_height / 2),
                size=(barrier_length, barrier_depth, barrier_height),
                hpr=(heading, 0, 0),
                face_color=(0.32, 0.23, 0.13, 1),  # brown
                border_color=(0, 0, 0, 1)          # black
            )

        # The barriers now form a continuous fence on the inside lawn

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
    
    # --- Create Starting Line Geometry ---
    def create_starting_line_geometry():
        format = GeomVertexFormat.getV3n3c4()  # Vertex, Normal, Color
        vdata = GeomVertexData('starting_line_geom', format, Geom.UHStatic)
        
        # Get the first segment of the track to position the starting line
        start_point = track_curve_points[0]
        next_point = track_curve_points[1]
        
        # Calculate direction and perpendicular vector
        direction = (next_point - start_point)
        direction.normalize()
        perpendicular = direction.cross(world_up)
        perpendicular.normalize()
        
        # Calculate the left and right edges of the road at the starting point
        left_edge = start_point - perpendicular * (road_width / 2.0)
        right_edge = start_point + perpendicular * (road_width / 2.0)
        
        # Number of squares for the checkered pattern - reduced for larger squares
        num_squares = 4  # Fewer squares means larger checkered pattern
        
        # Starting line width (along track direction)
        start_line_width = 6.0  # Significantly increased for better visibility
        
        # Colors for the checkered pattern - made more contrasting
        white_color = Vec4(1.0, 1.0, 1.0, 1.0)  # Pure white
        black_color = Vec4(0.0, 0.0, 0.0, 1.0)  # Pure black
        red_color = Vec4(1.0, 0.0, 0.0, 1.0)    # Bright red for border
        
        # Create main checkered pattern
        main_vdata = GeomVertexData('starting_line_main_geom', format, Geom.UHStatic)
        num_vertices = (num_squares + 1) * 2  # +1 for the extra point at the end
        main_vdata.setNumRows(num_vertices)
        
        vertex = GeomVertexWriter(main_vdata, 'vertex')
        normal = GeomVertexWriter(main_vdata, 'normal')
        color = GeomVertexWriter(main_vdata, 'color')
        
        # Create vertices along the starting line
        for i in range(num_squares + 1):
            # Calculate position along the starting line
            t = float(i) / num_squares
            pos = left_edge + (right_edge - left_edge) * t
            
            # Determine color for this square
            square_color = white_color if (i // 1) % 2 == 0 else black_color
            
            # Add vertices for the front and back of the starting line
            # Front vertex (in the direction of the track)
            vertex.addData3(pos + direction * start_line_width/2)  # Extend forward
            normal.addData3(world_up)
            color.addData4(square_color)
            
            # Back vertex
            vertex.addData3(pos - direction * start_line_width/2)  # Extend backward
            normal.addData3(world_up)
            color.addData4(square_color)
        
        # Create triangles for the checkered pattern
        tris = GeomTriangles(Geom.UHStatic)
        
        for i in range(num_squares):
            idx = i * 2
            
            # First triangle (front-left, back-left, front-right)
            tris.addVertices(idx, idx + 1, idx + 2)
            
            # Second triangle (back-left, back-right, front-right)
            tris.addVertices(idx + 1, idx + 3, idx + 2)
        
        tris.closePrimitive()
        main_geom = Geom(main_vdata)
        main_geom.addPrimitive(tris)
        
        # Create a red border around the starting line
        border_width = 1.0  # Width of the border
        border_vdata = GeomVertexData('starting_line_border_geom', format, Geom.UHStatic)
        
        # We need 8 vertices for the border (4 corners, each with front and back points)
        border_vdata.setNumRows(8)
        
        vertex = GeomVertexWriter(border_vdata, 'vertex')
        normal = GeomVertexWriter(border_vdata, 'normal')
        color = GeomVertexWriter(border_vdata, 'color')
        
        # Calculate the extended edges for the border
        left_border = left_edge - perpendicular * border_width
        right_border = right_edge + perpendicular * border_width
        front_border = direction * (start_line_width/2 + border_width)
        back_border = direction * -(start_line_width/2 + border_width)
        
        # Add the 8 vertices for the border
        # Front-left outer corner
        vertex.addData3(left_border + front_border)
        normal.addData3(world_up)
        color.addData4(red_color)
        
        # Back-left outer corner
        vertex.addData3(left_border + back_border)
        normal.addData3(world_up)
        color.addData4(red_color)
        
        # Front-right outer corner
        vertex.addData3(right_border + front_border)
        normal.addData3(world_up)
        color.addData4(red_color)
        
        # Back-right outer corner
        vertex.addData3(right_border + back_border)
        normal.addData3(world_up)
        color.addData4(red_color)
        
        # Front-left inner corner
        vertex.addData3(left_edge + direction * start_line_width/2)
        normal.addData3(world_up)
        color.addData4(red_color)
        
        # Back-left inner corner
        vertex.addData3(left_edge - direction * start_line_width/2)
        normal.addData3(world_up)
        color.addData4(red_color)
        
        # Front-right inner corner
        vertex.addData3(right_edge + direction * start_line_width/2)
        normal.addData3(world_up)
        color.addData4(red_color)
        
        # Back-right inner corner
        vertex.addData3(right_edge - direction * start_line_width/2)
        normal.addData3(world_up)
        color.addData4(red_color)
        
        # Create triangles for the border
        border_tris = GeomTriangles(Geom.UHStatic)
        
        # Left side (2 triangles)
        border_tris.addVertices(0, 1, 4)  # outer front-left, outer back-left, inner front-left
        border_tris.addVertices(1, 5, 4)  # outer back-left, inner back-left, inner front-left
        
        # Right side (2 triangles)
        border_tris.addVertices(2, 3, 6)  # outer front-right, outer back-right, inner front-right
        border_tris.addVertices(3, 7, 6)  # outer back-right, inner back-right, inner front-right
        
        # Front side (2 triangles)
        border_tris.addVertices(0, 2, 4)  # outer front-left, outer front-right, inner front-left
        border_tris.addVertices(2, 6, 4)  # outer front-right, inner front-right, inner front-left
        
        # Back side (2 triangles)
        border_tris.addVertices(1, 3, 5)  # outer back-left, outer back-right, inner back-left
        border_tris.addVertices(3, 7, 5)  # outer back-right, inner back-right, inner back-left
        
        border_tris.closePrimitive()
        border_geom = Geom(border_vdata)
        border_geom.addPrimitive(border_tris)
        
        # Create the final node with both geometries
        node = GeomNode('starting_line_geom_node')
        node.addGeom(border_geom)  # Add border first (will be rendered first)
        node.addGeom(main_geom)    # Add main checkered pattern on top
        return node
    
    # Create and attach geometries
    # sand_border_node = create_border_geometry()  # Sand borders removed
    road_node = create_road_geometry()
    warning_stripes_node = create_warning_stripes_geometry()
    starting_line_node = create_starting_line_geometry()
    
    # The track_node is the parent for the road and warning stripes
    # track_node.attachNewNode(sand_border_node)  # Sand borders removed
    warning_stripes_np = track_node.attachNewNode(warning_stripes_node)
    warning_stripes_np.setZ(-0.01)  # Slightly below the road so track appears on top
    track_node.attachNewNode(road_node)
    
    # Add the starting line significantly above the track to avoid z-fighting and improve visibility
    starting_line_np = track_node.attachNewNode(starting_line_node)
    starting_line_np.setZ(0.05)  # Raised higher above the road for better visibility
    
    # Ensure track is at Z=0
    track_node.setPos(0, 0, 0)

    # --- Place a tree at the starting line ---
    if track_curve_points:
        start_point = track_curve_points[0]
        tree = create_tree(start_point + Vec3(40, 10, 0))
        tree = create_tree(start_point + Vec3(10, 10, 0))
        tree.reparentTo(game_root)

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
