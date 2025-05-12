import numpy as np
from panda3d.core import NodePath, CollisionNode, CollisionBox, Vec3, Point3

class BarrierBlock:
    def __init__(self, parent, position, size=(2, 0.5, 1), hpr=(0, 0, 0), face_color=(0.36, 0.23, 0.13, 1), border_color=(0, 0, 0, 1)):
        """
        Create a barrier block at the given position, with the given size and orientation.
        :param parent: NodePath to attach the barrier to
        :param position: (x, y, z) tuple for the barrier's center
        :param size: (width, depth, height) tuple
        :param hpr: (heading, pitch, roll) tuple for orientation
        :param face_color: RGBA tuple for the main face color (brown)
        :param border_color: RGBA tuple for the border color (black)
        """
        self.node = NodePath('barrier_block')
        self.node.set_pos(*position)
        self.node.set_hpr(*hpr)
        self._create_visual(size, face_color, border_color)
        self._create_collision(size)
        self.node.reparent_to(parent)

    def _create_visual(self, size, face_color, border_color):
        # Create a 3D box for the barrier (visible from all sides)
        from panda3d.core import GeomNode, GeomVertexFormat, GeomVertexData, GeomVertexWriter, Geom, GeomTriangles, NodePath, Vec4
        format = GeomVertexFormat.getV3c4()
        vdata = GeomVertexData('barrier_box', format, Geom.UHStatic)
        vdata.setNumRows(8)
        vertex = GeomVertexWriter(vdata, 'vertex')
        color = GeomVertexWriter(vdata, 'color')
        w, d, h = size[0]/2, size[1]/2, size[2]/2
        # 8 corners of the box
        corners = [
            (-w, -d, -h), (w, -d, -h), (w, d, -h), (-w, d, -h),
            (-w, -d, h), (w, -d, h), (w, d, h), (-w, d, h)
        ]
        for x, y, z in corners:
            vertex.addData3(x, y, z)
            color.addData4(*face_color)  # Brown face color
        tris = GeomTriangles(Geom.UHStatic)
        # 12 triangles (2 per face)
        faces = [
            (0,1,2,3), # bottom
            (4,5,6,7), # top
            (0,1,5,4), # front
            (2,3,7,6), # back
            (1,2,6,5), # right
            (3,0,4,7)  # left
        ]
        for a,b,c,d in faces:
            tris.addVertices(a,b,c)
            tris.addVertices(a,c,d)
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode('barrier_box_geom')
        node.addGeom(geom)
        box_np = self.node.attach_new_node(node)
        box_np.set_transparency(True)

        # Draw black borders using LineSegs
        from panda3d.core import LineSegs
        border = LineSegs()
        border.setThickness(3.0)
        border.setColor(*border_color)
        edge_indices = [
            (0,1),(1,2),(2,3),(3,0), # bottom
            (4,5),(5,6),(6,7),(7,4), # top
            (0,4),(1,5),(2,6),(3,7)  # verticals
        ]
        for i,j in edge_indices:
            border.moveTo(*corners[i])
            border.drawTo(*corners[j])
        border_np = self.node.attach_new_node(border.create())
        border_np.set_transparency(True)

    def _create_collision(self, size):
        # Add a collision box
        cnode = CollisionNode('barrier_collision')
        # Adicionar um pequeno padding ao colisor para melhorar a detecção
        padding = 0.05
        padded_size = (size[0]/2 + padding, size[1]/2 + padding, size[2]/2 + padding)
        cbox = CollisionBox(Point3(0,0,0), padded_size[0], padded_size[1], padded_size[2])
        cnode.add_solid(cbox)
        # Configuração correta das máscaras de colisão
        # A barreira deve ser colidida mas não testar colisão com outros objetos
        cnode.set_into_collide_mask(0x1)  # Objects can collide into this barrier
        cnode.set_from_collide_mask(0)    # Barrier won't test for collisions itself
        
        # Para o CollisionHandlerPusher funcionar corretamente, a barreira precisa ser 
        # um nó estático, mas isso já é o comportamento padrão para objetos sem uma
        # configuração especial do traverser
        cnp = self.node.attach_new_node(cnode)
        cnp.set_pos(0, 0, 0)
        cnp.set_hpr(0, 0, 0)
