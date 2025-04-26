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
    
    # Find the closest point on the track centerline
    min_distance = float('inf')
    for point in track_curve_points:
        point_2d = Point3(point.x, point.y, 0)
        distance = (point_2d - kart_pos_2d).length()
        if distance < min_distance:
            min_distance = distance
    
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
