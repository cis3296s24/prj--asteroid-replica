import pygame
from config import *
import math
import random

class Player(pygame.sprite.Sprite):
    
    def __init__(self, game, x, y):

        self.game = game
        self._layer = PLAYER_LAYER
        self.groups = self.game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups) #add player to all sprites group


        self.lives = PLAYER_LIVES

        # player position based on tile
        self.x = x * TILESIZE
        self.y = y * TILESIZE
        # player size - one tile
        self.width = TILESIZE
        self.height = TILESIZE

        # create player (TEMPORARY look)
        self.og_image = pygame.image.load('Images/ships/ship-a/ship-a1.png').convert_alpha()
        self.image = self.og_image
        self.damaged_image = pygame.image.load('Images/ships/ship-a/ship-a-damaged.png').convert_alpha()
        self.damage_loop = 0

        # self.image.get_rect() returns a new rectangle covering the entire surface of `self.image`. This rectangle (rect) is used to position the sprite on the screen.
        # it's important for collision detection and rendering the sprite at its current position.
        self.rect = self.image.get_rect()

        # set player's rect x, y positions
        self.rect.x = self.x
        self.rect.y = self.y

        #acceleration
        self.velocity = pygame.math.Vector2(0, 0)  # Initialize velocity vector
        self.acceleration = 0.2  # Adjust as needed for acceleration rate
        self.deceleration = 0.98  # Adjust as needed for deceleration rate

        #temporary value at init
        self.x_change = 0
        self.y_change = 0
        self.angle = 0


 

        self.player_bullets = self.game.player_bullets

        
        
    #update player sprite
    def update(self):

        current_time = pygame.time.get_ticks()           
        #update movement
        self.rotate()
        self.movement()
        #update collision check
        #self.collide_asteroid()

        
        #check collisions
        self.collide(self.game.ship_reg_bullets)
        self.collide(self.game.asteroids)
        self.collide(self.game.ships)
        self.collide(self.game.ship_sp_bullets)

        #update acceleration
        self.rect.center += self.velocity  # Apply velocity to the player's position
        self.decelerate()  # Apply deceleration to slow down the player over time
        self.wrap_around_screen()

        #update player rect position based on return value of movement()
        self.rect.x += self.x_change
        self.rect.y += self.y_change

        #reset _change vars
        self.x_change = 0
        self.y_change = 0
        

        # Flickering logic: Change image back and forth if within invulnerability period
        if current_time <= self.damage_loop + 3000:  # 3000 ms invulnerability
            if current_time // 250 % 2 == 0:  # Change image every 250 ms
                self.image = self.damaged_image
            else:
                self.image = self.og_image
        else:
            self.image = self.og_image  # Outside invulnerability period, use original image

        self.rotate()

        self.handle_input()

    def shoot_regular_bullet(self):
        bullet = RegularBullet(self.rect.centerx, self.rect.centery)
        # Set velocity based on player's direction
        bullet.vel_x = math.cos(math.radians(self.angle)) * bullet.speed
        bullet.vel_y = -math.sin(math.radians(self.angle)) * bullet.speed
        self.game.all_sprites.add(bullet)
        self.player_bullets.add(bullet)

    def shoot_special_bullet(self):
        bullet = SpecialBullet(self.rect.centerx, self.rect.centery)
        # Set velocity based on player's direction
        bullet.vel_x = math.cos(math.radians(self.angle)) * bullet.speed
        bullet.vel_y = -math.sin(math.radians(self.angle)) * bullet.speed
        self.game.all_sprites.add(bullet)
        self.player_bullets.add(bullet)

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            PLAYER_CHANNEL.play(PLAYER_BULLET_MUSIC)
            self.shoot_regular_bullet()  # Shoot regular bullet when space key is pressed
        elif keys[pygame.K_LSHIFT]:
            PLAYER_CHANNEL.play(PLAYER_BULLET_MUSIC)
            self.shoot_special_bullet()
            
    def wrap_around_screen(self):
        if self.rect.right < 0:
            self.rect.left = WIN_WIDTH
        if self.rect.left > WIN_WIDTH:
            self.rect.right = 0
        if self.rect.bottom < 0:
            self.rect.top = WIN_HEIGHT
        if self.rect.top > WIN_HEIGHT:
            self.rect.bottom = 0

    def decelerate(self):
        self.velocity *= self.deceleration
        if self.velocity.length() < 0.1:  # If the velocity is very small, make it zero
            self.velocity = pygame.math.Vector2(0, 0)

    def turnRight(self):
        self.angle += 5 # Adjust rotation speed as needed
        if self.angle > 360:
            self.angle -= 360

    def turnLeft(self):
        self.angle -= 5  # Adjust rotation speed as needed
        if self.angle < 0:
            self.angle += 360

    def moveForward(self):
        rad_angle = math.radians(self.angle)  # Convert angle to radians
        acceleration_vector = pygame.math.Vector2(math.cos(rad_angle), math.sin(rad_angle)) * self.acceleration
        self.velocity += acceleration_vector

    def rotate(self):
        original_center = self.rect.center  # Save the sprite's center
        self.image = pygame.transform.rotate(self.image, -self.angle)  # Rotate the original image
        self.rect = self.image.get_rect(center=original_center)  # Create a new rect with the old center

    #function to make player move based on arrow keys
    def movement(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.turnLeft()
        if keys[pygame.K_RIGHT]:
            self.turnRight()
        if keys[pygame.K_UP]:
            self.moveForward()


    def collide_asteroid(self):
        current_time = pygame.time.get_ticks()
        for enemy in self.game.enemies:
            distance = math.sqrt((self.rect.centerx - enemy.rect.centerx) ** 2 + (self.rect.centery - enemy.rect.centery) ** 2)
            collision_threshold = max(self.rect.width, self.rect.height) / 2 + max(enemy.rect.width, enemy.rect.height) / 2 - 2 * TILESIZE
            
            # Check if within collision threshold and not currently invulnerable
            if distance < collision_threshold and current_time > self.damage_loop + 3000:  # Assuming 3000 ms invulnerability
                self.lives -= 1
                ASTEROID_CHANNEL.play(ASTEROID_MUSIC)
                self.damage_loop = current_time  # Reset invulnerability timer
                
                if self.lives <= 0:
                    self.kill()
                    self.game.playing = False
                    break
            
    def collide(self, spriteGroup):
        current_time = pygame.time.get_ticks()
        for sprite in spriteGroup:
            distance = math.sqrt((self.rect.centerx - sprite.rect.centerx) ** 2 + (self.rect.centery - sprite.rect.centery) ** 2)
            collision_threshold = max(self.rect.width, self.rect.height) / 2 + max(sprite.rect.width, sprite.rect.height) / 2 - 2 * TILESIZE
            
            # Check if within collision threshold and not currently invulnerable
            if distance < collision_threshold and current_time > self.damage_loop + 3000:  # Assuming 3000 ms invulnerability
                self.lives -= 1
                PLAYER_DESTROYED_CHANNEL.play(PLAYER_DESTROYED_MUSIC)
                self.damage_loop = current_time  # Reset invulnerability timer
                
                if self.lives <= 0:
                    self.kill()
                    self.game.playing = False
                    break
            

class RegularBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((BULLET_SIZE, BULLET_SIZE))
        self.image.fill(BULLET_COLOR)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = BULLET_SPEED
        self.vel_x = 0  # Velocity in the x direction
        self.vel_y = -self.speed  # Velocity in the y direction (initially upwards)

    def update(self):
        # Update bullet position based on velocity
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Remove bullet if it goes off-screen
        if self.rect.bottom < 0 or self.rect.top > WIN_HEIGHT or self.rect.right < 0 or self.rect.left > WIN_WIDTH:
            self.kill()

class SpecialBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((BULLET_SIZE, BULLET_SIZE))
        self.image.fill(SPECIAL_BULLET_COLOR)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = SPECIAL_BULLET_SPEED
        self.vel_x = 0  # Velocity in the x direction
        self.vel_y = -self.speed  # Velocity in the y direction (initially upwards)

    def update(self):
        # Update bullet position based on velocity
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Remove bullet if it goes off-screen
        if self.rect.bottom < 0 or self.rect.top > WIN_HEIGHT or self.rect.right < 0 or self.rect.left > WIN_WIDTH:
            self.kill()

        
        
