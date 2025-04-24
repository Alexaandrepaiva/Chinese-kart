import sys
import math # Import math for curves
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from panda3d.core import AmbientLight, DirectionalLight
from panda3d.core import NodePath, PandaNode
from panda3d.core import Vec3, Vec4, Point3
from panda3d.core import CollisionTraverser, CollisionHandlerPusher, CollisionSphere, CollisionTube, CollisionNode
from panda3d.core import CardMaker
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel # Import DirectGUI elements
from direct.task import Task # Import Task
from panda3d.core import GeomVertexFormat, GeomVertexData, GeomVertexWriter # For procedural geometry
from panda3d.core import Geom, GeomTriangles, GeomNode, LineSegs # Import LineSegs

# Helper function for Catmull-Rom Spline interpolation
def evalCatmullRom(p0, p1, p2, p3, t):
    t2 = t * t
    t3 = t2 * t
    return (p1 * 2.0 +
            (-p0 + p2) * t +
            (p0 * 2.0 - p1 * 5.0 + p2 * 4.0 - p3) * t2 +
            (-p0 + p1 * 3.0 - p2 * 3.0 + p3) * t3) * 0.5

# Helper function to get tangent (derivative) of Catmull-Rom
def tangentCatmullRom(p0, p1, p2, p3, t):
    t2 = t * t
    # Derivative of the evalCatmullRom formula w.r.t. t
    return ((-p0 + p2) + 
            (p0 * 4.0 - p1 * 10.0 + p2 * 8.0 - p3 * 2.0) * t + 
            (-p0 * 3.0 + p1 * 9.0 - p2 * 9.0 + p3 * 3.0) * t2) * 0.5

class KartGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Game state ('menu', 'playing', 'paused')
        self.gameState = 'menu'

        # Basic window setup
        self.disableMouse()
        props = WindowProperties()
        props.setTitle("Chinese Kart")
        props.setSize(1200, 800)
        self.win.requestProperties(props)
        self.setBackgroundColor(0.5, 0.7, 1.0) # Sky blue background

        # Setup scene graph root for game elements
        # Initially hide the game root, show it when game starts
        self.gameRoot = self.render.attachNewNode("GameRoot")
        self.gameRoot.hide()

        # Add basic lighting (attached to render so it's always there)
        self.setupLighting()

        # Create game elements (ground, track, kart) but don't show yet
        self.createGround()
        self.createTrack()
        self.createKart()

        # Create the start menu
        self.createStartMenu()

        # Kart physics/control variables
        self.setupKartControls()

        # Initial camera setup (will be adjusted when game starts)
        # self.cam.setPos(0, -40, 15)

        # Pause Menu (initially None)
        self.pauseMenu = None

        # Exit handling - Changed to toggle pause
        self.accept("escape", self.togglePause)

        print("Game Initialized, showing menu.")

    def createStartMenu(self):
        # Menu frame
        self.menuFrame = DirectFrame(frameColor=(0.2, 0.2, 0.2, 0.8),
                                     frameSize=(-0.7, 0.7, -0.5, 0.5),
                                     parent=self.aspect2d) # Attach to 2D layer

        # Title label
        self.titleLabel = DirectLabel(text="Chinese Kart",
                                      scale=0.15,
                                      pos=(0, 0, 0.3),
                                      text_fg=(1, 1, 1, 1),
                                      frameColor=(0, 0, 0, 0), # Transparent background
                                      parent=self.menuFrame)

        # Start button
        self.startButton = DirectButton(text="Start Game",
                                        scale=0.1,
                                        pos=(0, 0, -0.2),
                                        command=self.startGame,
                                        parent=self.menuFrame)

    def hideMenu(self):
        if hasattr(self, 'menuFrame') and self.menuFrame:
            self.menuFrame.hide()

    def showMenu(self):
        # Recreate or just show if already exists
        if not hasattr(self, 'menuFrame') or not self.menuFrame:
            self.createStartMenu()
        else:
             self.menuFrame.show()
        # Ensure game elements are hidden when menu is shown
        self.gameRoot.hide()
        # Potentially reset camera to a menu view if desired
        # self.cam.setPos(0, 0, 50)
        # self.cam.lookAt(0, 0, 0)

    def startGame(self):
        print("Starting Game!")
        self.hideMenu() # Hide start menu
        if self.pauseMenu:
            self.pauseMenu.hide() # Hide pause menu if it exists

        self.gameState = 'playing'
        self.gameRoot.show() # Show the game world

        # Reset kart position and physics - Corrected position
        # Use the first generated spline point as reference
        startPos = self.trackCurvePoints[0]
        # Use the second spline point to get initial direction
        startDir = self.trackCurvePoints[1] - self.trackCurvePoints[0]
        startDir.normalize()

        kartStartPos = startPos - startDir * 3 # Position 3 units behind point 0
        # Ensure Z position is relative to the track surface (which should be at Z=0)
        kartStartPos.setZ(self.track.getZ() + 0.5) # Track Z + half kart height
        self.kart.setPos(kartStartPos)
        self.kart.lookAt(self.trackCurvePoints[1])     # Look towards point 1

        self.velocity = 0.0

        # Setup camera for gameplay
        self.updateCamera()

        # Make sure the game update task isn't already running
        self.taskMgr.remove("updateGameTask")
        # Start the game update task
        self.taskMgr.add(self.updateGame, "updateGameTask")

    def togglePause(self):
        if self.gameState == 'playing':
            self.gameState = 'paused'
            print("Game Paused")
            self.showPauseMenu()
            # Keep task running but it will check state
        elif self.gameState == 'paused':
            self.resumeGame()

    def createPauseMenu(self):
        self.pauseMenu = DirectFrame(frameColor=(0.2, 0.2, 0.2, 0.8),
                                     frameSize=(-0.7, 0.7, -0.5, 0.5),
                                     parent=self.aspect2d)
        self.pauseMenu.hide() # Initially hidden

        DirectLabel(text="Paused",
                    scale=0.15,
                    pos=(0, 0, 0.3),
                    text_fg=(1, 1, 1, 1),
                    frameColor=(0, 0, 0, 0),
                    parent=self.pauseMenu)

        DirectButton(text="Resume",
                     scale=0.1,
                     pos=(0, 0, 0),
                     command=self.resumeGame,
                     parent=self.pauseMenu)

        DirectButton(text="Restart",
                     scale=0.1,
                     pos=(0, 0, -0.15),
                     command=self.restartGameFromPause,
                     parent=self.pauseMenu)

        DirectButton(text="Quit",
                     scale=0.1,
                     pos=(0, 0, -0.3),
                     command=self.quitGame,
                     parent=self.pauseMenu)

    def showPauseMenu(self):
        if not self.pauseMenu:
            self.createPauseMenu()
        self.pauseMenu.show()

    def hidePauseMenu(self):
        if self.pauseMenu:
            self.pauseMenu.hide()

    def resumeGame(self):
        if self.gameState == 'paused':
            self.gameState = 'playing'
            self.hidePauseMenu()
            print("Game Resumed")

    def restartGameFromPause(self):
        print("Restarting game from pause menu...")
        self.hidePauseMenu()
        # Stop the current game task before starting a new one
        self.taskMgr.remove("updateGameTask")
        # Call start game which resets everything
        self.startGame()

    def quitGame(self):
        print("Quitting game...")
        sys.exit()

    def setupKartControls(self):
        self.keyMap = {
            "forward": False,
            "brake": False,
            "left": False,
            "right": False
        }
        self.velocity = 0.0
        self.maxVelocity = 50.0
        self.acceleration = 10.0
        self.brakingForce = 25.0
        self.turnSpeed = 100.0
        self.drag = 0.5 # Simple linear drag
        self.friction = 5.0 # Friction when not accelerating/braking

        # Event handlers for key presses
        self.accept("w", self.setKey, ["forward", True])
        self.accept("w-up", self.setKey, ["forward", False])
        self.accept("s", self.setKey, ["brake", True])
        self.accept("s-up", self.setKey, ["brake", False])
        self.accept("a", self.setKey, ["left", True])
        self.accept("a-up", self.setKey, ["left", False])
        self.accept("d", self.setKey, ["right", True])
        self.accept("d-up", self.setKey, ["right", False])

    def setKey(self, key, value):
        self.keyMap[key] = value

    def updateGame(self, task):
        # Skip updates if not in playing state
        if self.gameState != 'playing':
            # Keep the task running, but do nothing if paused
            # This prevents dt from becoming huge when resuming
            return Task.cont

        dt = globalClock.getDt() # Get time elapsed since last frame

        # --- Physics Calculation ---
        currentSpeed = self.velocity
        currentHeading = self.kart.getH()

        # Acceleration / Braking
        if self.keyMap["forward"]:
            self.velocity += self.acceleration * dt
        elif self.keyMap["brake"]:
            self.velocity -= self.brakingForce * dt
        else:
            # Apply friction/drag if no acceleration/brake input
            frictionForce = self.friction * dt
            dragForce = self.drag * self.velocity * dt
            if self.velocity > 0:
                self.velocity -= max(0, frictionForce + dragForce)
            elif self.velocity < 0:
                # Allow braking to reverse slightly, but friction stops forward motion
                 self.velocity += max(0, frictionForce - dragForce) # Drag opposes motion

        # Clamp velocity
        self.velocity = max(-self.maxVelocity / 4, min(self.maxVelocity, self.velocity)) # Allow slower reverse

        # Stop if velocity is very small
        if not self.keyMap["forward"] and not self.keyMap["brake"] and abs(self.velocity) < 0.1:
            self.velocity = 0

        # Turning (only when moving)
        if abs(self.velocity) > 0.1:
            turnRate = self.turnSpeed * dt
            # Scale turning speed based on velocity (optional, adds realism)
            # turnScale = min(1.0, abs(self.velocity) / (self.maxVelocity * 0.3))
            # turnRate *= turnScale

            if self.keyMap["left"]:
                currentHeading += turnRate
            if self.keyMap["right"]:
                currentHeading -= turnRate

        # --- Update Kart Position and Rotation ---
        # Update Heading first
        self.kart.setH(currentHeading)
        # Prevent kart from tilting visually (optional but helps)
        self.kart.setP(0)
        self.kart.setR(0)

        # Move kart based on velocity and HORIZONTAL direction
        forwardVec = self.kart.getQuat().getForward()
        forwardVecHorizontal = Vec3(forwardVec.x, forwardVec.y, 0) # Project onto XY plane
        if forwardVecHorizontal.lengthSquared() > 0.001: # Avoid division by zero if vector is vertical
            forwardVecHorizontal.normalize()
            deltaPos = forwardVecHorizontal * self.velocity * dt
            newPos = self.kart.getPos() + deltaPos
            # Ensure Z position stays correct (relative to track at Z=0)
            newPos.setZ(self.track.getZ() + 0.5) # Track Z + half kart height
            self.kart.setPos(newPos)
        # else: kart is pointing straight up or down, don't move horizontally

        # --- Update Camera ---
        self.updateCamera()

        return Task.cont # Continue task next frame

    def updateCamera(self):
        # Simple follow cam
        camOffset = Vec3(0, -15, 7) # Offset behind and above
        # Rotate the offset by the kart's rotation to keep it behind the kart
        rotatedOffset = self.kart.getQuat().xform(camOffset)
        targetCamPos = self.kart.getPos() + rotatedOffset
        self.cam.setPos(targetCamPos)
        self.cam.lookAt(self.kart.getPos() + Vec3(0, 0, 2)) # Look slightly above the kart's center

    def setupLighting(self):
        # Ambient light
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor(Vec4(0.4, 0.4, 0.4, 1))
        ambientLightNP = self.render.attachNewNode(ambientLight)
        self.render.setLight(ambientLightNP)

        # Directional light
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setColor(Vec4(0.8, 0.8, 0.8, 1))
        directionalLight.setDirection(Vec3(-5, -5, -5))
        directionalLightNP = self.render.attachNewNode(directionalLight)
        self.render.setLight(directionalLightNP)

    def createGround(self):
        try:
            # Try loading the model first
            self.ground = self.loader.loadModel("models/plane")
            self.ground.reparentTo(self.gameRoot)
        except OSError:
            # Fallback if models/plane is not found
            print("Warning: models/plane.egg not found. Using CardMaker fallback.")
            cm = CardMaker("ground")
            cm.setFrame(-500, 500, -500, 500)
            self.ground = self.gameRoot.attachNewNode(cm.generate())
            # Need to set rotation for CardMaker plane to be horizontal
            self.ground.setP(-90)

        self.ground.setScale(1000, 1000, 1) # Make it large
        self.ground.setPos(0, 0, -0.1) # Slightly below zero
        self.ground.setColor(Vec4(0.2, 0.6, 0.2, 1)) # Green color

    def createTrack(self):
        self.trackNode = self.gameRoot.attachNewNode("Track")
        trackColor = Vec4(0.3, 0.3, 0.3, 1)
        startLineColor = Vec4(0.9, 0.9, 0.9, 1)
        trackWidth = 10.0
        segmentsPerCurve = 20 # Increase for smoother curves
        worldUp = Vec3(0, 0, 1)

        # Define the control points for the Catmull-Rom spline.
        # We need points before the start and after the end for the spline calculation.
        # Make the track loop by repeating start/end points appropriately.
        rawTrackPoints = [
            Point3(0, -150, 0),    # P0: Start of long straight
            Point3(0, 150, 0),     # P1: End of long straight / Start of first curve
            Point3(150, 250, 0),   # P2: Top of first curve
            Point3(300, 150, 0),   # P3: End of first curve / Start of short straight
            Point3(300, 50, 0),    # P4: End of short straight / Start of second curve
            Point3(150, -50, 0),   # P5: Bottom of second curve
           # Point3(0, -150, 0)   # P6 = P0: End of second curve (back to start)
        ]
        numPoints = len(rawTrackPoints)
        self.trackPoints = [] # This will hold points including wraparound for spline calc
        self.trackPoints.append(rawTrackPoints[numPoints-1]) # Add last point as P_{-1}
        self.trackPoints.extend(rawTrackPoints)
        self.trackPoints.append(rawTrackPoints[0]) # Add P0 as P_{n}
        self.trackPoints.append(rawTrackPoints[1]) # Add P1 as P_{n+1}

        # --- Generate Spline Points and Track Vertices --- 
        self.trackCurvePoints = [] # Store centerline points for kart positioning
        vertexList = [] # Stores (left_vertex, right_vertex) pairs

        for i in range(1, numPoints + 1):
            p0 = self.trackPoints[i-1]
            p1 = self.trackPoints[i]   # Segment starts here
            p2 = self.trackPoints[i+1] # Segment ends here
            p3 = self.trackPoints[i+2]

            isStartSegment = (i == 1) # Is this the first segment (for start line color)?

            # Generate points along this segment
            for j in range(segmentsPerCurve):
                t = float(j) / segmentsPerCurve
                point = evalCatmullRom(p0, p1, p2, p3, t)
                tangent = tangentCatmullRom(p0, p1, p2, p3, t)
                tangent.normalize()

                if j==0 and i==1:
                    self.trackCurvePoints.append(point) # Add first point

                # Calculate the perpendicular vector (binormal)
                binormal = tangent.cross(worldUp)
                binormal.normalize()

                # Calculate left and right vertices
                vLeft = point - binormal * trackWidth / 2.0
                vRight = point + binormal * trackWidth / 2.0
                vertexList.append({'left': vLeft, 'right': vRight, 'start_line': isStartSegment})

                # Store centerline point (except the very last duplicate)
                if not (j == segmentsPerCurve -1 and i == numPoints): 
                   self.trackCurvePoints.append(point)

            # Add the final point of the segment explicitly (t=1)
            point = evalCatmullRom(p0, p1, p2, p3, 1.0)
            tangent = tangentCatmullRom(p0, p1, p2, p3, 1.0)
            tangent.normalize()
            binormal = tangent.cross(worldUp)
            binormal.normalize()
            vLeft = point - binormal * trackWidth / 2.0
            vRight = point + binormal * trackWidth / 2.0
            vertexList.append({'left': vLeft, 'right': vRight, 'start_line': isStartSegment})
            # Dont add final centerline point here, it's the start of the next segment

        # --- Create Geometry from Vertices ---
        format = GeomVertexFormat.getV3n3c4() # Vertex, Normal, Color
        vdata = GeomVertexData('track_geom', format, Geom.UHStatic)
        # Pre-allocate rows (2 vertices per cross-section * num cross-sections)
        numVertices = len(vertexList)
        vdata.setNumRows(numVertices * 2) 

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')

        for i in range(numVertices):
            vInfo = vertexList[i]
            col = startLineColor if vInfo['start_line'] else trackColor
            # Left vertex
            vertex.addData3(vInfo['left'])
            normal.addData3(worldUp)
            color.addData4(col)
            # Right vertex
            vertex.addData3(vInfo['right'])
            normal.addData3(worldUp)
            color.addData4(col)

        tris = GeomTriangles(Geom.UHStatic)
        # Add triangles connecting consecutive vertices
        for i in range(numVertices - 1):
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
        self.trackNode.attachNewNode(node)
        self.trackNode.setPos(0, 0, 0) # Ensure track is at Z=0

        # Keep a reference
        self.track = self.trackNode

        # Optional: Visualize track points and spline for debugging
        # self.debugDrawSpline()

    def debugDrawSpline(self):
        # Helper to visualize the generated spline
        lines = LineSegs()
        lines.setColor(1, 0, 0, 1)
        lines.moveTo(self.trackCurvePoints[0])
        for p in self.trackCurvePoints[1:]:
            lines.drawTo(p)
        self.render.attachNewNode(lines.create())

        # Draw control points
        linesCtrl = LineSegs()
        linesCtrl.setColor(0, 1, 0, 1)
        for p in self.trackPoints[1:-2]: # Draw the actual raw points used
             linesCtrl.drawSphere(p, 1.0)
        self.render.attachNewNode(linesCtrl.create())

    def createKart(self):
        try:
             # Try loading the model first
             self.kart = self.loader.loadModel("models/box")
             self.kart.reparentTo(self.gameRoot)
             self.kart.setScale(1, 1, 1) # Set scale if model loaded
        except OSError:
             # Fallback if models/box is not found
             print("Warning: models/box.egg not found. Using CardMaker fallback for kart.")
             cm = CardMaker("kart-card") # Use CardMaker to create a flat card initially

             # Create the 6 faces of the cube using CardMaker
             kartNode = self.gameRoot.attachNewNode("kart")
             for i in range(6):
                 face = kartNode.attachNewNode(cm.generate())
                 if i == 0: face.setPosHpr(0, 0, 0.5, 0, 0, 0) # Top
                 elif i == 1: face.setPosHpr(0, 0, -0.5, 0, 180, 0) # Bottom
                 elif i == 2: face.setPosHpr(0, 0.5, 0, 0, -90, 0) # Front
                 elif i == 3: face.setPosHpr(0, -0.5, 0, 0, 90, 0) # Back
                 elif i == 4: face.setPosHpr(0.5, 0, 0, 0, -90, -90) # Right
                 elif i == 5: face.setPosHpr(-0.5, 0, 0, 0, -90, 90) # Left
             self.kart = kartNode # Assign the parent node as the kart

        # Set common properties outside try/except
        # Initial position will be set in startGame
        # self.kart.setPos(0, -10, 0.5)
        self.kart.setColor(Vec4(1, 0, 0, 1)) # Red color

app = KartGame()
app.run() 