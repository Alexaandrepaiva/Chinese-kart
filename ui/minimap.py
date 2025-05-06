from panda3d.core import NodePath, Vec3, Vec4, Point3, CardMaker, Texture, PNMImage
from direct.gui.DirectGui import DirectFrame

class Minimap:
    def __init__(self, base, track_curve_points, kart):
        """
        Create a minimap for the game that shows the track and kart position
        
        Args:
            base: The main game instance (ShowBase)
            track_curve_points: List of points that define the track centerline
            kart: The kart NodePath to track on the minimap
        """
        self.base = base
        self.track_curve_points = track_curve_points
        self.kart = kart
        
        # Minimap configuration
        self.map_size = 0.2  # Size in aspect2d coordinates (0.2 of screen height - smaller)
        self.map_padding = 0.0  # No padding from right edge
        self.track_color = Vec4(0.3, 0.3, 0.3, 1)  # Gray for track
        self.kart_color = Vec4(1, 0, 0, 1)  # Red for player kart marker
        self.bg_color = Vec4(0.8, 0.8, 0.8, 0.7)  # Light gray, semi-transparent
        
        # Create the minimap frame
        self._create_minimap_frame()
        
        # Create texture for drawing the track and kart
        self._create_minimap_texture()
        
        # Initially hide the minimap (will be shown during gameplay)
        self.minimap_frame.hide()
        
        # Set up task to update minimap
        self.base.taskMgr.add(self.update_minimap, "update_minimap_task")

    def _create_minimap_frame(self):
        """
        Create the frame to hold the minimap in the corner of the screen
        """
        # Position the minimap at the far right edge
        # In Panda3D, right edge is at x=1.0, so we position our map there and offset by its size
        pos_x = 1.45 - self.map_size  # Exactly at the right edge
        pos_y = -1 + self.map_size + 0.02  # Small padding from bottom
        
        # Create a frame to hold the minimap
        self.minimap_frame = DirectFrame(
            frameColor=self.bg_color,
            frameSize=(-self.map_size, self.map_size, -self.map_size, self.map_size),
            pos=(pos_x, 0, pos_y),  # Far right corner
            parent=self.base.aspect2d  # Attach to 2D layer
        )
        
        # Create a card to display the minimap texture
        cm = CardMaker('minimap_card')
        cm.setFrame(-self.map_size, self.map_size, -self.map_size, self.map_size)
        self.minimap_card = self.minimap_frame.attachNewNode(cm.generate())

    def _create_minimap_texture(self):
        """
        Create a texture to draw the track and kart position
        """
        # Create a texture to render the minimap
        self.map_tex_size = 256  # Texture resolution
        self.map_texture = Texture("minimap_texture")
        self.map_image = PNMImage(self.map_tex_size, self.map_tex_size)
        self.map_image.fill(self.bg_color[0], self.bg_color[1], self.bg_color[2])
        self.map_image.alphaFill(self.bg_color[3])
        
        # Find track bounds for scaling
        self._find_track_bounds()
        
        # Draw the track on the texture
        self._draw_track()
        
        # Apply the texture to the card
        self.map_texture.load(self.map_image)
        self.minimap_card.setTexture(self.map_texture)
    
    def _find_track_bounds(self):
        """
        Find the min/max coordinates of the track for scaling
        """
        x_coords = [p.getX() for p in self.track_curve_points]
        y_coords = [p.getY() for p in self.track_curve_points]
        
        self.min_x = min(x_coords)
        self.max_x = max(x_coords)
        self.min_y = min(y_coords)
        self.max_y = max(y_coords)
        
        # Add some padding
        padding = 10
        self.min_x -= padding
        self.max_x += padding
        self.min_y -= padding
        self.max_y += padding
        
        # Calculate scale factors to fit track in texture
        self.x_scale = self.map_tex_size / (self.max_x - self.min_x)
        self.y_scale = self.map_tex_size / (self.max_y - self.min_y)
        
        # Use the smaller scale to ensure the track fits and maintains aspect ratio
        self.scale = min(self.x_scale, self.y_scale)
        
        # Calculate centering offsets
        self.center_x = (self.min_x + self.max_x) / 2
        self.center_y = (self.min_y + self.max_y) / 2
    
    def _draw_track(self):
        """
        Draw the track outline on the minimap texture
        """
        # Clear the image
        self.map_image.fill(self.bg_color[0], self.bg_color[1], self.bg_color[2])
        self.map_image.alphaFill(self.bg_color[3])
        
        # Convert track points to texture coordinates
        for i in range(len(self.track_curve_points) - 1):
            p1 = self.track_curve_points[i]
            p2 = self.track_curve_points[i + 1]
            
            # Convert world coordinates to texture coordinates
            x1, y1 = self._world_to_texture_coords(p1.getX(), p1.getY())
            x2, y2 = self._world_to_texture_coords(p2.getX(), p2.getY())
            
            # Draw a line between points using Bresenham's line algorithm
            self._draw_line(
                int(x1), int(y1), int(x2), int(y2),
                self.track_color[0], self.track_color[1], self.track_color[2]
            )
        
        # Connect last point to first point to close the loop
        p1 = self.track_curve_points[-1]
        p2 = self.track_curve_points[0]
        x1, y1 = self._world_to_texture_coords(p1.getX(), p1.getY())
        x2, y2 = self._world_to_texture_coords(p2.getX(), p2.getY())
        self._draw_line(
            int(x1), int(y1), int(x2), int(y2),
            self.track_color[0], self.track_color[1], self.track_color[2]
        )
    
    def _world_to_texture_coords(self, world_x, world_y):
        """
        Convert world coordinates to texture coordinates
        """
        # Center the coordinates
        centered_x = world_x - self.center_x
        centered_y = world_y - self.center_y
        
        # Scale and center in the texture
        tex_x = (centered_x * self.scale) + self.map_tex_size / 2
        tex_y = (centered_y * self.scale) + self.map_tex_size / 2
        
        return tex_x, tex_y
        
    def _draw_line(self, x0, y0, x1, y1, r, g, b):
        """
        Draw a line using Bresenham's line algorithm
        """
        # Ensure coordinates are within texture bounds
        x0 = max(0, min(x0, self.map_tex_size - 1))
        y0 = max(0, min(y0, self.map_tex_size - 1))
        x1 = max(0, min(x1, self.map_tex_size - 1))
        y1 = max(0, min(y1, self.map_tex_size - 1))
        
        # Set line width for better visibility
        line_width = 2
        
        # Implementation of Bresenham's line algorithm
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            # Draw a thicker line (square of pixels)
            for tx in range(-line_width//2, line_width//2 + 1):
                for ty in range(-line_width//2, line_width//2 + 1):
                    px = x0 + tx
                    py = y0 + ty
                    if 0 <= px < self.map_tex_size and 0 <= py < self.map_tex_size:
                        self.map_image.setXel(px, py, r, g, b)
            
            if x0 == x1 and y0 == y1:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
    
    def _draw_kart_marker(self, temp_image, position, color, marker_size=3):
        """
        Draw a kart marker at the given position with the specified color
        
        Args:
            temp_image: The PNMImage to draw on
            position: (x, y) tuple with texture coordinates
            color: Vec4 color to use for the marker
            marker_size: Size of the marker in pixels
        """
        kart_x, kart_y = position
        for dx in range(-marker_size, marker_size + 1):
            for dy in range(-marker_size, marker_size + 1):
                if dx*dx + dy*dy <= marker_size*marker_size:  # Circle equation
                    # Draw pixel if it's within the image bounds
                    pixel_x = int(kart_x + dx)
                    pixel_y = int(kart_y + dy)
                    if (0 <= pixel_x < self.map_tex_size and 
                        0 <= pixel_y < self.map_tex_size):
                        temp_image.setXel(pixel_x, pixel_y, 
                                        color[0], color[1], color[2])
    
    def update_minimap(self, task):
        """
        Update the kart markers on the minimap
        """
        # Only update if the minimap is visible
        if not self.minimap_frame.isHidden():
            # Get a copy of the current map image with the track
            temp_image = PNMImage(self.map_image)
            
            # Convert player kart position to texture coordinates
            player_kart_pos = self._world_to_texture_coords(
                self.kart.getX(), self.kart.getY()
            )
            
            # Draw player kart marker (slightly larger than AI karts)
            self._draw_kart_marker(temp_image, player_kart_pos, self.kart_color, marker_size=4)
            
            # Draw AI kart markers if they exist
            if hasattr(self.base, 'ai_karts') and self.base.ai_karts:
                for ai_kart in self.base.ai_karts:
                    # Get the kart node and color from the ai_kart data
                    kart_node = ai_kart['node']
                    kart_color = ai_kart['color']
                    
                    # Convert AI kart position to texture coordinates
                    ai_kart_pos = self._world_to_texture_coords(
                        kart_node.getX(), kart_node.getY()
                    )
                    
                    # Draw the AI kart marker
                    self._draw_kart_marker(temp_image, ai_kart_pos, kart_color, marker_size=3)
            
            # Update the texture with the new image
            self.map_texture.load(temp_image)
        
        return task.cont
    
    def show(self):
        """
        Show the minimap
        """
        self.minimap_frame.show()
    
    def hide(self):
        """
        Hide the minimap
        """
        self.minimap_frame.hide()
