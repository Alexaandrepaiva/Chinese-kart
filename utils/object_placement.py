# utils/object_placement.py
"""
Utility for logging the kart's position every second to assist with object placement.
"""
import threading
import time
from panda3d.core import Vec3

def log_kart_position_every_second(kart, reference_point=None, stop_event=None):
    """
    Logs the kart's position every second as a Vec3 offset from reference_point (or world origin if None).
    Prints the Vec3 needed to place a new object at the kart's current position.
    
    Args:
        kart: The NodePath of the kart.
        reference_point: Optional Vec3. If provided, logs the offset from this point.
        stop_event: Optional threading.Event to stop logging.
    """
    def _log_loop():
        while not (stop_event and stop_event.is_set()):
            pos = kart.getPos()
            if reference_point is not None:
                offset = pos - reference_point
            else:
                offset = pos
            print(f"[Object Placement] Vec3({offset.x:.2f}, {offset.y:.2f}, {offset.z:.2f})  # Kart position at {time.strftime('%H:%M:%S')}")
            time.sleep(1)
    
    thread = threading.Thread(target=_log_loop, daemon=True)
    thread.start()
    return thread
