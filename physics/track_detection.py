from panda3d.core import Vec3, Point3

def get_kart_terrain(kart_pos, track_curve_points, road_width, track_width, stripe_width=1.0):
    """
    Determines what terrain the kart is on: road, sand, or lawn.
    
    Args:
        kart_pos: The kart's current position (Point3)
        track_curve_points: List of points defining the track centerline
        road_width: Width of the road part of the track
        track_width: Total width of the track (road + sand borders)
        stripe_width: Width of one stripe (default 1.0)
    
    Returns:
        str: 'road', 'sand', or 'lawn'
    """
    # Only consider X and Y for distance calculation (ignore height/Z)
    kart_pos_2d = Point3(kart_pos.x, kart_pos.y, 0)
    
    # Find the closest segment on the track and the perpendicular distance to it
    min_distance = float('inf')
    closest_point = None
    
    # Process the track as segments between consecutive points
    num_points = len(track_curve_points)
    if num_points < 2:
        return 'lawn'  # Not enough points to form a track
    
    for i in range(num_points - 1):
        p1 = Point3(track_curve_points[i].x, track_curve_points[i].y, 0)
        p2 = Point3(track_curve_points[i+1].x, track_curve_points[i+1].y, 0)
        
        # Calculate perpendicular distance from kart to this segment
        segment_vec = p2 - p1
        segment_length_squared = segment_vec.lengthSquared()
        
        # Handle extremely short segments
        if segment_length_squared < 0.0001:
            distance = (p1 - kart_pos_2d).length()
            if distance < min_distance:
                min_distance = distance
                closest_point = p1
            continue
            
        # Find the projection of kart position onto the segment
        t = max(0, min(1, (kart_pos_2d - p1).dot(segment_vec) / segment_length_squared))
        projection = p1 + segment_vec * t
        
        # Calculate the perpendicular distance
        distance = (projection - kart_pos_2d).length()
        
        if distance < min_distance:
            min_distance = distance
            closest_point = projection
    
    # Also check distance to track endpoints to handle cases near the start/end
    # This helps with circular tracks where the first and last points might be far apart
    first_point = Point3(track_curve_points[0].x, track_curve_points[0].y, 0)
    last_point = Point3(track_curve_points[-1].x, track_curve_points[-1].y, 0)
    
    first_distance = (first_point - kart_pos_2d).length()
    if first_distance < min_distance:
        min_distance = first_distance
    
    last_distance = (last_point - kart_pos_2d).length()
    if last_distance < min_distance:
        min_distance = last_distance
    
    # Determine terrain based on the perpendicular distance
    # The road includes the stripes for physics
    road_plus_stripes = (road_width / 2) + stripe_width
    if min_distance <= road_plus_stripes:
        return 'road'  # On the road or stripes (gray or red/white part)
    elif min_distance <= (track_width / 2):
        return 'sand'  # On the sand border (beige part)
    else:
        return 'lawn'  # On the lawn (green part)

def is_kart_on_track(kart_pos, track_curve_points, road_width, track_width=None, stripe_width=1.0):
    """
    Determines if the kart is on the track (road or sand) or on the lawn.
    
    Args:
        kart_pos: The kart's current position (Point3)
        track_curve_points: List of points defining the track centerline
        road_width: Width of the road part of the track
        track_width: Total width of the track (road + sand borders)
        stripe_width: Width of one stripe (default 1.0)
    
    Returns:
        bool: True if the kart is on the track (road or sand), False if it's on the lawn
    """
    # For backwards compatibility
    if track_width is None:
        track_width = road_width
        
    terrain = get_kart_terrain(kart_pos, track_curve_points, road_width, track_width, stripe_width)
    return terrain != 'lawn'  # True if road or sand, False if lawn
