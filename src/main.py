import pygame

import sys
from random import randint

class Spritesheet:
    def __init__(self, file):
        self.sheet = pygame.image.load(file).convert()

    def get_sprite(self, x, y, width, height):
        sprite = pygame.Surface([width, height])
        sprite.blit(self.sheet, (0, 0), (x, y, width, height))
        sprite.set_colorkey(Config.WHITE)
        return sprite



class Config:
    TILE_SIZE = 32
    WINDOW_WIDTH = TILE_SIZE * 60 / 2
    WINDOW_HEIGHT = TILE_SIZE * 33.75 / 2
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    GREY = (128, 128, 128)
    WHITE = (255, 255, 255)
    FPS = 30
    MAX_GRAVITY = -3
    MAX_TIME = 10
    BG_SPEED = 0






class BaseSprite(pygame.sprite.Sprite):
    def __init__(self, game, x, y, x_pos=0, y_pos=0, width=Config.TILE_SIZE, height=Config.TILE_SIZE, layer=0, groups=None, spritesheet=None):
        self._layer = layer
        groups = (game.all_sprites, ) if groups == None else (game.all_sprites, groups)
        super().__init__(groups)
        self.game = game
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.width = width
        self.height = height

        if spritesheet == None:
            self.image = pygame.Surface([self.width, self.height])
            self.image.fill(Config.GREY)
        else:
            self.spritesheet = spritesheet
            self.image = self.spritesheet.get_sprite(
                self.x_pos,
                self.y_pos,
                self.width,
                self.height
            )
        self.rect = self.image.get_rect()
        self.rect.x = x * Config.TILE_SIZE
        self.rect.y = y * Config.TILE_SIZE

    def scale(self, factor=2):
        self.rect.width *= factor
        self.rect.height *= factor
        self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))


class PlayerSprite(BaseSprite):
    def __init__(self, game, x, y, **kwargs):
        img_data = {
            'spritesheet': Spritesheet("res/zweim.png"),
        }
        super().__init__(game, x, y, groups=game.players, layer=2, **img_data, **kwargs)
        self.y_velocity = 0
        self.x_velocity = 0
        self.speed = 5
        self.standing = False
        self.color = Config.RED
        self.anim_counter = 0
        self.animation_frames = [0, 32]
        self.current_frame = 0
        self.animation_duration = 30
        

    def animate(self, x_diff):
        self.anim_counter += abs(x_diff)
        new_frame = round(self.anim_counter / self.animation_duration) % len(self.animation_frames)
        if self.current_frame != new_frame:
            new_pos = self.animation_frames[new_frame]
            self.image = self.spritesheet.get_sprite(new_pos, self.y_pos, self.width, self.height)
            self.current_frame = new_frame
            self.anim_counter = self.anim_counter % (len(self.animation_frames) * self.animation_duration)

    
    def update(self):
        self.handle_movement()
        
        self.rect.y = self.rect.y - self.y_velocity
        self.rect.x = self.rect.x - self.x_velocity
        self.y_velocity = max(self.y_velocity - 0.5, -self.speed)

        self.check_collision()
        if self.rect.bottom >= Config.WINDOW_HEIGHT:
            self.rect.x= 25*Config.TILE_SIZE
            self.rect.y= 11*Config.TILE_SIZE
        if self.rect.x <0:
            self.rect.x= 25* Config.TILE_SIZE
            self.rect.y= 11* Config.TILE_SIZE
        

    def jump(self):
        self.y_velocity = 10
        self.x_velocity = randint(5, 10)
        self.standing = False

    def handle_movement(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x = self.rect.x - self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x = self.rect.x + self.speed
        if keys[pygame.K_UP]:
            self.rect.y = self.rect.y - self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y = self.rect.y + self.speed
        if keys[pygame.K_SPACE]:
            self.jump()
        
        self.update_camera()



    def update_camera(self):
        x_c, y_c = self.game.screen.get_rect().center
        offset = 5 * Config.TILE_SIZE  # Verschiebung der Spielfigur in x-Richtung 
        x_diff = x_c + offset - self.rect.centerx
        y_diff = y_c - self.rect.centery
        for sprite in self.game.all_sprites:
            if sprite in self.game.kroko:
                break
            sprite.rect.x += x_diff
            sprite.rect.y += y_diff
        self.animate(x_diff)
    
        # Shift Background
        self.game.bg_x += x_diff * Config.BG_SPEED
        if self.game.bg_x > Config.WINDOW_WIDTH:
            self.game.bg_x = -Config.WINDOW_WIDTH
        elif self.game.bg_x < -Config.WINDOW_WIDTH:
            self.game.bg_x = Config.WINDOW_WIDTH
    

    def is_standing(self, hit):
        if abs(hit.rect.top - self.rect.bottom) > abs(self.speed):
            return False
        if abs(self.rect.left - hit.rect.right) <= abs(self.speed):
            return False
        if abs(hit.rect.left - self.rect.right) <= abs(self.speed):
            return False
        return True

    def hit_head(self, hit):
        if abs(self.rect.top - hit.rect.bottom) > abs(self.speed):
            return False
        if abs(self.rect.left - hit.rect.right) <= abs(self.speed):
            return False
        if abs(hit.rect.left - self.rect.right) <= abs(self.speed):
            return False
        return True


    def check_collision(self):
        hits = pygame.sprite.spritecollide(self, self.game.kroko, False)
        if hits:
            print("Treffer")
            self.game.time = Config.MAX_TIME
            self.rect.x= 25*Config.TILE_SIZE
            self.rect.y= 11*Config.TILE_SIZE
        hits = pygame.sprite.spritecollide(self, self.game.ground, False)
        if hits: 
            self.x_velocity = 0
        for hit in hits:
            if self.is_standing(hit):
                self.rect.bottom = hit.rect.top
                break
            if self.hit_head(hit):
                self.rect.top = hit.rect.bottom
                break

        hits = pygame.sprite.spritecollide(self, self.game.ground, False)
        for hit in hits:
            hit_dir = hit.rect.x - self.rect.x
            if hit_dir < 0:
                self.rect.left = hit.rect.right
            else:
                self.rect.right = hit.rect.left

    

class GroundSprite(BaseSprite):
    def __init__(self, game, x, y):
        img_data = {
            "spritesheet": Spritesheet("res/holz.png")
        }
        super().__init__(game, x, y, groups=game.ground, layer=1, **img_data)

class KrokodileSprite(BaseSprite):
    def __init__(self, game, x, y):
        img_data = {
            "spritesheet": Spritesheet("res/krokokl.png"),
            "width": 172,
            "height": 134,
        }
        super().__init__(game, x, y, groups=game.kroko, layer=0, **img_data)
        

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.Font(None, 30)
        self.screen = pygame.display.set_mode( (Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT) ) 
        self.clock = pygame.time.Clock()
        self.bg = load_and_scale_img("res/Hintergrund ohne krokodil.png", (Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT))
        self.go = load_and_scale_img("res/GAMEOVER.png", (Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT))
        self.bg_x = 0
        self.gameover= False
        self.playing= False
        self.waiting= False
        self.time = 10

        

    
    def load_map(self, mapfile):
        with open(mapfile, "r") as f:
            for (y, lines) in enumerate(f.readlines()):
                for (x, c) in enumerate(lines):
                    if c == "b":
                        GroundSprite(self, x, y)
                    if c == "p":
                        self.player = PlayerSprite(self, x, y)
                    if c == "k":
                        KrokodileSprite(self, x, y)

    def new(self):
        self.playing = True
        
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.ground = pygame.sprite.LayeredUpdates()
        self.players = pygame.sprite.LayeredUpdates()
        self.kroko = pygame.sprite.LayeredUpdates()

        self.load_map("maps/level-01.txt")

        # Spielfigur in die Mitte des Bildschirms setzen
        self.player.update_camera()
        self.bg_x = 0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.playing = False
                self.gameover=True
                self.waiting=False

    def update(self):
        self.all_sprites.update()

    def draw(self):
        self.screen.blit(self.bg, (self.bg_x, 0))
        tmp_bg = pygame.transform.flip(self.bg, True, False)
        second_x = Config.WINDOW_WIDTH + self.bg_x
        if self.bg_x > 0:
            second_x -= 2*Config.WINDOW_WIDTH
        self.screen.blit(tmp_bg, (second_x, 0))

        self.all_sprites.draw(self.screen)
        self.time = self.time - 1 /Config.FPS
        textsurface= self.font.render(f'{self.time:.0f}', False, Config.BLACK)
        if self.time< 0:
            self.playing= False
        self.screen.blit(textsurface,(32,32))
        pygame.display.update()




    def game_loop(self):
        while self.playing:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(Config.FPS)
        self.waiting = True
        self.screen = pygame.display.set_mode( (950,950) ) 
        while self.waiting:
            self.screen.blit(self.go, (0,0))
            self.handle_events()
            self.clock.tick(Config.FPS)
            pygame.display.update()

    def welcome(self):
        counter = 0
            
        while True:
            self.screen.fill(Config.GREEN)
            display_text = self.font.render('Klicke auf c um "Feed the croco" zu starten ', False, (0, 0, 0))
            self.screen.blit(display_text, (200, 50))
    
            pygame.display.flip()
            self.clock.tick(Config.FPS)
            

            pygame.event.get()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_c]:
                break

def load_and_scale_img(img_path, size):
    tmp = pygame.image.load(img_path)
    return pygame.transform.scale(tmp, size)

         
def main():
    g = Game()

    g.welcome()

    g.new()
  
    g.game_loop()

    pygame.quit()
    sys.exit()

