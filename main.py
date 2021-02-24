from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from enum import Enum
import numpy as np

class State(Enum):
    PRE_ROUND = 1
    ROUND = 2
    POST_ROUND = 3

app = Ursina()

coal_texture = load_texture('assets/coal_block.png')
stone_texture = load_texture('assets/stone_block.png')
dirt_texture  = load_texture('assets/dirt_block.png')
sky_texture   = load_texture('assets/skybox.png')
arm_texture   = load_texture('assets/arm_texture.png')
punch_sound   = Audio('assets/punch_sound', loop = False, autoplay = False, eternal=True)

textures = [ dirt_texture, stone_texture, coal_texture ]

GAME_STATE: State = State.ROUND
upgrade_pickaxe_button: Button

class Player(Entity):
    depth: int
    pickaxe_durability: int
    pickaxe_max_durability: int
    money: int
    money_text: Text
    pickaxe_durability_text: Text
    controller: FirstPersonController

    def __init__(self):
        super().__init__(eternal=True)
        self.eternal = True
        self.pickaxe_durability = 10
        self.pickaxe_max_durability = 10
        self.money = 0
        self.depth = 0

        self.set_controller()

        self.money_text = Text("Money: " + str(self.money) + '$', origin=(0,0), x=-0.76, y=0.4, scale=2, eternal=True)
        self.pickaxe_durability_text = Text("Hits left: " + str(self.pickaxe_durability) + "/" + str(self.pickaxe_max_durability), origin=(0,0), x=-0.7, y=0.45, scale=2, eternal=True)

    def set_controller(self):
        self.controller = FirstPersonController(jump_height = 0, jump_duration = 0)
        self.controller.world_x = 4
        self.controller.world_y = 0.25
        self.controller.world_z = 4
        self.controller.collider = 'mesh'

    def update_info(self):
        self.money_text.text = "Money: " + str(self.money) + '$'
        self.pickaxe_durability_text.text = "Hits left: " + str(self.pickaxe_durability) + "/" + str(self.pickaxe_max_durability)

    def upgrade_pickaxe(self):
        if self.money >= self.pickaxe_max_durability:
            self.money -= self.pickaxe_max_durability
            self.pickaxe_max_durability += 1
            self.pickaxe_durability = self.pickaxe_max_durability
            self.update_info()

            global upgrade_pickaxe_button
            upgrade_pickaxe_button.text = 'Upgrade pickaxe (' + str(player.pickaxe_max_durability) + ')'


    def reset(self):
        self.pickaxe_durability = self.pickaxe_max_durability
        self.update_info()

        if not self.controller:
            self.set_controller()
        else:
            self.controller.world_x = 4
            self.controller.world_y = 0.25
            self.controller.world_z = 4

    def dig_block(self, block):
        if sqrt(pow(self.controller.x - block.position.x, 2) + pow(self.controller.y - block.position.y, 2) + pow(self.controller.z - block.position.z, 2)) <= 3:
            if (self.pickaxe_durability > 0) == True:
                punch_sound.play()
                self.money += block.value
                self.depth = int(block.position.y)
                self.pickaxe_durability -= block.durability
                self.update_info()
                destroy(block)
        
player = Player()

class SolidVoxel(Entity):
    def __init__(self, position = (0,0,0), texture = stone_texture):
        super().__init__(
            parent = scene,
            position = position,
            origin_y = 0,
            model = 'assets/block',
            texture = texture,
            scale = 0.5,
            collider='box')

class Voxel(Entity):
    value: int
    durability: int

    def __init__(self, player, block_random, position = (0, 0, 0)):
        super().__init__(
            parent = scene,
            position = position,
            model = 'assets/block',
            origin_y = 0.5,
            scale = 0.5,
            collider='box',
            on_click=(lambda: player.dig_block(self)))

        if block_random < 750:
            self.texture = textures[0]
            self.durability = 1
            self.value = 1
        elif block_random < 970:
            self.texture = textures[1]
            self.durability = 2
            self.value = 1
        else:
            self.texture = textures[2]
            self.durability = 1
            self.value = 2

class Layer():
    voxels = [[[]]]
    def __init__(self):
        self.voxels = [[None for x in range(8)] for z in range(8)] 

    def set_voxel(self, voxel, x, z):
        self.voxels[z][x] = voxel

    def destroy_layer(self):
        for z in range(8):
            for x in range(8):
                voxel = self.voxels[z][x]
                if voxel is not None:
                    destroy(voxel)

        del(self)

class Hand(Entity):
    def __init__(self):
        super().__init__(
            parent = camera.ui,
            model = 'assets/arm',
            texture = arm_texture,
            scale = 0.2,
            rotation = Vec3(150,-10,0),
            position = Vec2(0.4,-0.6),
            eternal=True)

    def active(self):
        self.position = Vec2(0.3,-0.5)

    def passive(self):
        self.position = Vec2(0.4,-0.6)

layers: Layer = [None for x in range(8)]

def init_dig_zone():
    for y in range(8):
        layers[y] = Layer()
        for z in range(8):
            for x in range(8):
                block_random = random.randint(0, 999)
                voxel = Voxel(player=player, block_random=block_random, position = (x, -y, z))
                layers[y].set_voxel(voxel, x, z)

def init_dig_border():
    for y in range(-3, 8):
        for z in range(-1, 9):
            voxel = SolidVoxel(position = (-1, -y, z))
            voxel = SolidVoxel(position = (8, -y, z))
        for x in range(8):
            voxel = SolidVoxel(position = (x, -y, -1))
            voxel = SolidVoxel(position = (x, -y, 8))

def init_area():
    init_dig_zone()
    init_dig_border()

def go_dig():
    global GAME_STATE

    scene.clear()
    init_area()
    player.reset()
    GAME_STATE = State.ROUND

def update():
    global GAME_STATE
    global upgrade_pickaxe_button

    if held_keys['escape']:
        quit()

    if GAME_STATE == State.ROUND:
        if held_keys['left mouse'] or held_keys['right mouse']:
            hand.active()
        else:
            hand.passive()

        if (player.pickaxe_durability > 0) == False:
            GAME_STATE = State.POST_ROUND

    elif GAME_STATE == State.POST_ROUND:
        for layer in layers:
            layer.destroy_layer()
        scene.clear()
        mouse.locked = False
        mouse.visible = False

        game_over_text = Text('Pickaxe is broken!', origin=(0,0), x=0, scale=2)

        upgrade_pickaxe_button = Button(
            parent=camera.ui,
            scale = (.5,.1),
            x = -.5,
            color = color.orange.tint(-.25),
            text = 'Upgrade pickaxe (' + str(player.pickaxe_max_durability) + ')',
            tooltip = Tooltip('+1 to pickaxe`s maximum durability'),
            on_click = player.upgrade_pickaxe
            )

        go_dig_button = Button(
            parent=camera.ui,
            scale = (.5,.1),
            x = .5,
            color = color.green.tint(-.25),
            text = 'Repair pickaxe and go dig!',
            tooltip = Tooltip('Repair pickaxe and go dig!'),
            on_click = go_dig
            )

        Cursor(texture='cursor', scale=.1, parent=camera.ui)

        GAME_STATE = State.PRE_ROUND

hand = Hand()

sky = Sky(parent = scene,
          model = 'sphere',
          texture = sky_texture,
          scale = 150,
          double_sided = True,
          eternal=True)

if __name__ == '__main__':
    mouse.visible = False
    window.fps_counter.enabled = True
    window.exit_button.visible = False

    init_area()

    app.run()

    player.reset()
