import os
import random
import math
import pygame
import pygame.font
from os import listdir
from os.path import isfile, join
pygame.init()

pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5
MENU_FONT_SIZE = 64
MENU_COLOR = (255, 255, 255)
MENU_HOVER_COLOR = (255, 215, 0)

window = pygame.display.set_mode((WIDTH, HEIGHT))

class Menu:
    def __init__(self, window):
        self.window = window
        self.font = pygame.font.Font(None, MENU_FONT_SIZE)

        
        # Load the Play button image
        self.play_button = pygame.image.load(join("assets", "Menu", "Buttons", "Play.png")).convert_alpha()
        self.exit_button = pygame.image.load(join("assets", "Menu", "Buttons", "Close.png")).convert_alpha()
        
        self.play_button = pygame.transform.scale2x(self.play_button)  # Scale it up if needed
        self.exit_button = pygame.transform.scale2x(self.exit_button)
        
        self.options = ["Play", "Quit"]
        self.selected = 0
        
        # Calculate button positions
        self.play_rect = self.play_button.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.exit_rect = self.exit_button.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))
        
        # Use the existing background
        self.background, self.bg_image = get_background("Green.png")
        
        # Create an idle player animation for the menu
        self.menu_player = Player(WIDTH//2 - 50, HEIGHT//2 - 100, 50, 50)
        self.menu_player.direction = "right"
        
        # Create platform blocks for the player to stand on
        self.block_size = 96
        self.menu_blocks = [
            Block(WIDTH//2 - 200, HEIGHT - 200, self.block_size),
            Block(WIDTH//2 - 100, HEIGHT - 200, self.block_size),
            Block(WIDTH//2, HEIGHT - 200, self.block_size),
            Block(WIDTH//2 + 100, HEIGHT - 200, self.block_size),
        ]
        
        # Create decorative fire
        self.menu_fire = Fire(WIDTH//2 - 50, HEIGHT - 264, 16, 32)
        self.menu_fire.on()
        
    def update(self):
        # Apply physics and collision
        self.menu_player.loop(FPS)
        handle_vertical_collision(self.menu_player, self.menu_blocks, self.menu_player.y_vel)
        
    def draw(self):
        # Draw background
        for tile in self.background:
            self.window.blit(self.bg_image, tile)
            
        # Draw decorative elements
        for block in self.menu_blocks:
            block.draw(self.window, 0)
            
        self.menu_fire.loop()
        self.menu_fire.draw(self.window, 0)
        
        # Update and draw animated player
        self.update()
        self.menu_player.draw(self.window, 0)
        
        # Draw title
        title = self.font.render("PLATFORMER", True, (0, 0, 0))
        title_rect = title.get_rect(center=(WIDTH//2, HEIGHT//4))
        self.window.blit(title, title_rect)
        
        # Draw Play button
        if self.selected == 0:
            pygame.draw.rect(self.window, MENU_HOVER_COLOR, self.play_rect.inflate(10, 10), 3)
        self.window.blit(self.play_button, self.play_rect)
        
        # Draw Exit button
        if self.selected == 1:
            pygame.draw.rect(self.window, MENU_HOVER_COLOR, self.exit_rect.inflate(10, 10), 3)
        self.window.blit(self.exit_button, self.exit_rect)
        
        pygame.display.update()
        
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, "quit"
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    if self.selected == 0:  # Play
                        return False, "play"
                    else:  # Quit
                        return False, "quit"
        
        return True, None
    
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "VirtualGuy", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.inventory = Inventory()

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

class Inventory:
    def __init__(self):
        self.items = []
        self.item_images = {}
        # Load inventory item images
        self.item_images["banana"] = pygame.image.load(join("assets", "Items", "Fruits", "Bananas.png")).convert_alpha()
        self.item_images["banana"] = pygame.transform.scale2x(self.item_images["banana"])

    def add_item(self, item_name):
        self.items.append(item_name)

    def draw(self, window, player_x, player_y, offset_x):
        # Draw items above player
        for idx, item in enumerate(self.items):
            window.blit(self.item_images[item], (player_x - offset_x, player_y - 30))
            
class Banana(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "banana")
        self.sprites = load_sprite_sheets("Items", "Fruits", width, height)
        self.image = self.sprites["Bananas"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.collected = False
        
    def collect(self):
        self.collected = True
        # Create a slice of the banana by getting only part of the sprite
        original = self.sprites["Bananas"][0]
        # Create a smaller surface for the slice
        slice_width = self.width // 2
        slice_height = self.height // 2
        sliced = pygame.Surface((slice_width, slice_height), pygame.SRCALPHA)
        # Copy only a portion of the original sprite
        sliced.blit(original, (0, 0), (0, 0, slice_width, slice_height))
        self.image = sliced
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))

    def loop(self):
        if not self.collected:
            sprites = self.sprites["Bananas"]
            sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
            self.image = sprites[sprite_index]
            self.animation_count += 1

            self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
            self.mask = pygame.mask.from_surface(self.image)

            if self.animation_count // self.ANIMATION_DELAY > len(sprites):
                self.animation_count = 0
            
class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    # Draw player
    player.draw(window, offset_x)
    
    # Draw inventory items above player
    player.inventory.draw(window, player.rect.x, player.rect.y, offset_x)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if isinstance(obj, Block):
                if dy > 0:
                    player.rect.bottom = obj.rect.top
                    player.landed()
                elif dy < 0:
                    player.rect.top = obj.rect.bottom
                    player.hit_head()
                collided_objects.append(obj)
            elif isinstance(obj, Fire):
                player.make_hit()
                return "menu"
            elif isinstance(obj, Banana):
                player.inventory.add_item("banana")
                objects.remove(obj)
                
    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            if isinstance(obj, Banana):
                objects.remove(obj)  # Just remove the banana
            break

    player.move(-dx, 0)
    player.update()
    return collided_object

def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collision = handle_vertical_collision(player, objects, player.y_vel)
    
    # Check if we got the menu signal
    if vertical_collision == "menu":
        return "menu"
        
    to_check = [collide_left, collide_right]
    if isinstance(vertical_collision, list):
        to_check.extend(vertical_collision)

    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()
            return "menu"  # Return menu signal when hitting fire
            
    return None

def create_fire_group(start_x, num_fires, spacing):
    block_size = 96  # Add this at the start of the function
    fires = []
    for i in range(num_fires):
        fire = Fire(start_x + (i * 50), HEIGHT - block_size - 64, 16, 32)
        fire.on()
        fires.append(fire)
    return fires

def create_block_group(start_x, num_blocks, spacing, height_level):
    """Creates a group of adjacent blocks at specified height"""
    block_size = 96
    blocks = []
    for i in range(num_blocks):
        block = Block(start_x + (i * spacing), HEIGHT - block_size * height_level, block_size)
        blocks.append(block)
    return blocks

def main(window):
    clock = pygame.time.Clock()
    
    while True:  # Main game loop
        menu = Menu(window)
        in_menu = True
        while in_menu:
            clock.tick(FPS)
            in_menu, action = menu.handle_input()
            menu.draw()
            
            if action == "quit":
                pygame.quit()
                quit()
            elif action == "play":
                break
            
        background, bg_image = get_background("Green.png")
        block_size = 96
        
        player = Player(0, 100, 50, 50)
        fire_groups = [
            create_fire_group(block_size * 3, 3, 20),
            create_fire_group(block_size * 8, 4, 20),
            create_fire_group(block_size * 15, 3, 20)
        ]
        
        block_groups = [
           create_block_group(block_size * 1, 2, block_size, 2),
           create_block_group(block_size * 5, 4, block_size, 3),
           create_block_group(block_size * 10, 3, block_size, 2)
        ]
        
        # Create banana and place it on the middle platform
        banana = Banana(block_size * 6, HEIGHT - block_size * 5, 32, 32)  # Adjust position as needed
        
        blocks = [block for group in block_groups for block in group]
        fires = [fire for group in fire_groups for fire in group]
        floor = [Block(i * block_size, HEIGHT - block_size, block_size)
                 for i in range(-WIDTH // block_size, (WIDTH * 2) // block_size)]
        
        objects = [*floor, *blocks, *fires, banana]
        
        for fire in fires:
            fire.on()
            
        offset_x = 0
        scroll_area_width = 200

        run = True
        while run:
            clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and player.jump_count < 2:
                        player.jump()

            player.loop(FPS)
            for fire in fires:
                fire.loop()
            banana.loop()
            
            move_result = handle_move(player, objects)
            if move_result == "menu":
                break  # Break inner loop to return to menu
                
            draw(window, background, bg_image, player, objects, offset_x)

            if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                    (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
                offset_x += player.x_vel

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)

