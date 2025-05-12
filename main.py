import sys
import time
import math
from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties, Vec3, Point3, loadPrcFileData
from direct.task import Task

# Load default config
loadPrcFileData('', 'window-title Chinese Kart')
loadPrcFileData('', 'win-size 1200 800')
loadPrcFileData('', 'sync-video #t') # Try enabling vsync
loadPrcFileData('', 'show-frame-rate-meter #t') # Show FPS meter

# Import game utilities
from utils.lighting import setup_lighting
# from utils.camera import update_camera, setup_camera_transition # Moved to game_loop/game_state

# Import game objects
from game_objects.ground import create_ground
from game_objects.track import create_track
from game_objects.kart import create_kart
from game_objects.starting_line import create_starting_line

# Import physics
from physics.kart_physics import KartPhysics

# Import UI
from ui.menus import MenuManager
from ui.minimap import Minimap
from ui.hud_display import HUDDisplay
from ui.start_countdown import StartCountdown

# Import new game logic components
from game_logic.game_state import GameStateManager
from game_logic.game_loop import GameLoop
from utils.progress_tracker import ProgressTracker

class KartGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Set explicit near/far clipping planes
        self.camLens.setNearFar(5, 5000) # Near=5 units, Far=5000 units

        # --- Core variables needed by multiple components ---
        # Track game time - managed by GameLoop, but might be needed for display
        self.game_start_time = 0
        self.game_time = 0
        # Lawn timer - managed by GameLoop
        self.lawn_timer = 0

        # --- Basic window setup ---
        self.disableMouse()
        # Properties set via loadPrcFileData now
        # props = WindowProperties()
        # props.setTitle("Chinese Kart")
        # props.setSize(1200, 800)
        # self.win.requestProperties(props)
        self.setBackgroundColor(0.5, 0.7, 1.0)

        # --- Scene Graph Setup ---
        self.gameRoot = self.render.attachNewNode("GameRoot")
        # GameStateManager will handle showing/hiding

        # --- Lighting ---
        setup_lighting(self.render)

        # --- Game Object Creation ---
        self.ground = create_ground(self.gameRoot, self.loader)
        track_data = create_track(self.gameRoot)
        self.track = track_data[0]
        self.trackCurvePoints = track_data[1]
        # Ensure anti-clockwise track direction for all racers
        # Reversing the point order if the original order is clockwise.
        # This assumes create_track might produce points in an order
        # that needs reversal for the desired anti-clockwise flow.
        self.trackCurvePoints.reverse() 
        
        # Create the starting line
        self.starting_line = create_starting_line(self.gameRoot, self.trackCurvePoints)

        self.kart, self.kart_collider = create_kart(self.gameRoot, self.loader, show_collider=False)
        # --- Kart Position Logging for Object Placement ---
        # This is a debug utility that logs kart positions - commenting out to prevent extra karts from appearing
        # from utils.object_placement import log_kart_position_every_second
        # log_kart_position_every_second(self.kart)

        # --- Collision Traverser and Handler ---
        from panda3d.core import CollisionTraverser, BitMask32
        from panda3d.core import CollisionHandlerEvent, CollisionHandlerPusher
        self.cTrav = CollisionTraverser('main traverser')
        
        # Handler de eventos para detectar colisões
        self.collision_handler = CollisionHandlerEvent()
        self.collision_handler.add_in_pattern('collision_%fn-into-%in')
        
        # Handler de físicas para evitar que objetos se atravessem
        self.pusher = CollisionHandlerPusher()
        # Configurar padrões de mensagem para o pusher
        self.pusher.add_in_pattern('pusher_%fn-into-%in')
        
        # Configurar o kart do jogador com o pusher para prevenção de atravessamento
        self.pusher.add_collider(self.kart_collider, self.kart)
        self.cTrav.add_collider(self.kart_collider, self.pusher)
        
        # Listen for kart into barrier event with correct node names
        # Usar o padrão de mensagem correto para o pusher
        self.accept('pusher_kart_collision-into-barrier_collision', self.on_kart_barrier_collision)
        self.accept('pusher_kart_collision-into-kart_collision', self.on_kart_kart_collision)
        
        # Enable this for debugging collisions
        # self.cTrav.showCollisions(self.render)

        # --- Core Components Initialization ---
        self.physics = KartPhysics(self.kart)
        self.progress_tracker = ProgressTracker(self.kart, self.trackCurvePoints)
        self.state_manager = GameStateManager(self)
        self.game_loop = GameLoop(self) # Handles the 'playing' state updates

        # --- UI Initialization ---
        self.menu_manager = MenuManager(self)
        self.menu_manager.create_start_menu(self.state_manager.start_game) # Use state manager

        self.minimap = Minimap(self, self.trackCurvePoints, self.kart)
        self.hud_display = HUDDisplay(self)

        # --- Countdown (block input until done) ---
        self.input_blocked = False
        self.waiting_for_camera_transition = False
        self.countdown = StartCountdown(self, on_finish=self._on_countdown_finish)

        # --- Input Handling ---
        self.physics.setup_controls(self.accept)
        self.accept("escape", self.state_manager.toggle_pause) # Use state manager

        # --- Camera View Control ---
        self.accept("1", self.toggle_first_person_view)
        self.accept("3", self.toggle_third_person_view)

        # --- Initial State ---
        self.state_manager.show_menu() # Start by showing the menu
        # print("Game Initialized.") # State manager handles prints

    def block_input(self):
        self.input_blocked = True
        self.physics.reset()  # Make sure no movement
        self.countdown.text.hide()  # Hide countdown if blocking input for camera

    def unblock_input(self):
        self.input_blocked = False

    def _on_countdown_finish(self):
        self.unblock_input()
        self.run_timer = True
        self.timer_start_time = time.time()
        self.timer_elapsed = 0.0

    # --- Collision: Stop kart on barrier ---
    def on_kart_barrier_collision(self, entry):
        """
        Trata colisões entre kart e barreiras 
        O CollisionHandlerPusher já cuida de impedir que o kart atravesse a barreira
        """
        # Identificar qual objeto kart colidiu
        from_node_path = entry.getFromNodePath()
        
        # Se foi o kart do jogador
        if from_node_path == self.kart_collider:
            # Stop the kart instantly
            self.physics.velocity = 0
        else:
            # Verificar se foi um AI kart
            for i, controller in enumerate(self.ai_controllers):
                ai_collider = self.ai_karts[i]['collider']
                if from_node_path == ai_collider:
                    # Usar o manipulador de colisão específico para AI
                    controller.handle_barrier_collision()
                    break
                    
    # --- Collision: Handle kart-to-kart collision ---
    def on_kart_kart_collision(self, entry):
        """
        Trata colisões entre karts para ajustar comportamentos após colisões
        O CollisionHandlerPusher já cuida de impedir que os karts se atravessem
        """
        # Obter as informações da colisão
        from_node_path = entry.getFromNodePath()
        into_node_path = entry.getIntoNodePath()
        
        # Obter o ponto de contato e a normal da colisão
        from panda3d.core import Vec3, Point3
        contact_pos = entry.getSurfacePoint(self.render)
        contact_normal = entry.getSurfaceNormal(self.render)
        
        # Se o kart do jogador colidiu com outro kart
        if from_node_path == self.kart_collider:
            kart_pos = self.kart.getPos()
            kart_forward = self.kart.getQuat().getForward()
            
            # Encontrar o kart com o qual colidiu (para determinar sua direção)
            collided_kart = None
            for ai_kart in self.ai_karts:
                if into_node_path == ai_kart['collider']:
                    collided_kart = ai_kart['node']
                    break
            
            if collided_kart:
                # Determinar a direção relativa dos dois karts
                collided_kart_forward = collided_kart.getQuat().getForward()
                
                # Calcular o vetor da colisão (do jogador para o kart colidido)
                collision_vector = collided_kart.getPos() - kart_pos
                collision_vector.normalize()
                
                # Produto escalar para determinar o ângulo entre as direções
                dot_forward = kart_forward.dot(collision_vector)
                
                # Calcular ângulo entre as direções para determinar se é colisão lateral
                dot_sideways = abs(kart_forward.cross(collision_vector).z)
                
                # Colisão frontal (o jogador bateu na traseira do outro kart)
                if dot_forward > 0.7:
                    # Reduzir velocidade significativamente em colisões traseiras
                    self.physics.velocity *= 0.7
                # Colisão traseira (o jogador foi atingido por trás)
                elif dot_forward < -0.7:
                    # O jogador foi atingido por trás - não reduzir velocidade 
                    pass
                # Colisão lateral (o impacto foi pela lateral)
                elif dot_sideways > 0.7:
                    # Em colisão lateral, reduzir menos a velocidade
                    self.physics.velocity *= 0.9
        
        # Se um kart AI colidiu com outro kart
        else:
            # Identificar qual AI kart colidiu
            for i, controller in enumerate(self.ai_controllers):
                ai_collider = self.ai_karts[i]['collider']
                if from_node_path == ai_collider:
                    ai_kart_node = self.ai_karts[i]['node']
                    ai_pos = ai_kart_node.getPos()
                    ai_forward = ai_kart_node.getQuat().getForward()
                    
                    # Encontrar o kart com o qual colidiu
                    collided_with_player = (into_node_path == self.kart_collider)
                    collided_ai_index = -1
                    
                    if not collided_with_player:
                        for j, other_ai in enumerate(self.ai_karts):
                            if i != j and into_node_path == other_ai['collider']:
                                collided_ai_index = j
                                break
                    
                    # Determinar a direção da colisão
                    if collided_with_player:
                        collision_vector = self.kart.getPos() - ai_pos
                        collided_forward = self.kart.getQuat().getForward()
                    elif collided_ai_index >= 0:
                        other_kart = self.ai_karts[collided_ai_index]['node']
                        collision_vector = other_kart.getPos() - ai_pos
                        collided_forward = other_kart.getQuat().getForward()
                    else:
                        # Não encontrou com quem colidiu, usar normal da colisão
                        collision_vector = -contact_normal
                        collided_forward = Vec3(0, 0, 0)
                    
                    collision_vector.normalize()
                    
                    # Determinar o tipo de colisão baseado no ângulo
                    dot_forward = ai_forward.dot(collision_vector)
                    dot_sideways = abs(ai_forward.cross(collision_vector).z)
                    
                    # Notificar o AI controller sobre a colisão com informações adicionais
                    is_frontal = (dot_forward > 0.5)  # Colisão frontal (AI bateu em algo)
                    is_rear = (dot_forward < -0.5)    # Colisão traseira (AI foi atingido)
                    is_side = (dot_sideways > 0.5)    # Colisão lateral
                    
                    controller.handle_kart_collision(collision_vector, is_frontal, is_rear, is_side)
                    break

    # The core game update task - delegates based on state
    def updateGame(self, task):
        """
        Main task loop. Checks the current game state and calls the appropriate update logic.
        """
        from utils.camera import update_camera
        update_camera(self.cam, self.kart)

        if self.state_manager.is_state('playing'):
            # If waiting for camera transition, poll is_transitioning
            if self.waiting_for_camera_transition:
                from utils import camera as camera_utils
                if not camera_utils.is_transitioning:
                    self.waiting_for_camera_transition = False
                    self.countdown.show_countdown()
                self.physics.reset()
                return Task.cont
            if self.input_blocked:
                # Block all movement by resetting physics and skipping update
                self.physics.reset()
                return Task.cont
            # If playing and input is allowed, delegate to the GameLoop's update method
            return self.game_loop.update(task)
        else:
            # If paused, menu, game_over, game_won, just continue the task
            # without running game logic. This prevents dt issues on resume.
            # The GameStateManager handles starting/stopping this task appropriately.
            return Task.cont

    def toggle_first_person_view(self):
        """
        Toggles the camera to first-person view
        """
        if self.state_manager.is_state('playing') and not self.input_blocked:
            print("First-person view key (1) pressed")
            from utils.camera import set_view_mode
            set_view_mode(1)  # 1 = first-person view

    def toggle_third_person_view(self):
        """
        Toggles the camera to third-person view
        """
        if self.state_manager.is_state('playing') and not self.input_blocked:
            print("Third-person view key (3) pressed")
            from utils.camera import set_view_mode
            set_view_mode(3)  # 3 = third-person view

# --- Application Entry Point ---
if __name__ == "__main__":
    app = KartGame()
    app.run()