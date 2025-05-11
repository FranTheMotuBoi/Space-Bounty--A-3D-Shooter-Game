from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import sys
import random
import time
import os

import math
last_enemy_fire_time = 0
enemies = []
camera_mode = 'third'  
enemies_destroyed = 0
enemies_left = len(enemies)
player_bullets = []
player_missiles = []  # New list for missiles
score = 0  
current_weapon = 'bullet' 
# Bullet list
bullets = []
ship_pos = [0.0, 0.0, 0.0]
spaceship_level = 1  # Level 1 at start
game_over = False  # Track game over state

# Button positions and sizes (in orthographic coordinates)
RESTART_BTN_POS = None
RESTART_BTN_SIZE = None
QUIT_BTN_POS = None
QUIT_BTN_SIZE = None

# Add global variable for difficulty
difficulty = 'easy'  


cheat_mode = False


bounty = 0

spaceship_color = [0.0, 0.8, 1.0]  # Initial color (bright blue)


space_color = [0.0, 0.0, 0.0]  # Initial black color
enemy_color = [1.0, 0.0, 0.0]  # Initial red color


clouds = []  # List to store cloud particles

class Cloud:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        self.size = random.uniform(0.5, 2.0)  # Random size for variety
        self.opacity = random.uniform(0.1, 0.3)  # Random opacity
        self.color = [0.8, 0.8, 0.8, self.opacity]  # Light gray with opacity

    def update(self):
        # Move clouds slowly
        self.pos[2] += 0.01  # Move forward
        # Reset position if too far
        if self.pos[2] > 50:
            self.pos[2] = -50
            self.pos[0] = random.uniform(-20, 20)
            self.pos[1] = random.uniform(-15, 15)

    def draw(self):
        glPushMatrix()
        glTranslatef(*self.pos)
        
        # Enable blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        # Draw cloud particle
        glColor4f(*self.color)
        glutSolidSphere(self.size, 8, 8)
        
        glDisable(GL_BLEND)
        glPopMatrix()

def generate_clouds():
    global clouds
    clouds = []
    # Generate initial clouds
    for _ in range(50):  # Number of cloud particles
        x = random.uniform(-20, 20)
        y = random.uniform(-15, 15)
        z = random.uniform(-50, 50)
        clouds.append(Cloud(x, y, z))

def draw_clouds():
    global clouds
    for cloud in clouds:
        cloud.update()
        cloud.draw()

# Bullet class
class Bullet:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        self.speed = 0.2
        self.damage = 1  # Basic damage
        self.alive = True

    def update(self):
        self.pos[2] -= self.speed  # Move bullet forward

    def draw(self):
        if self.alive:
            glPushMatrix()
            glTranslatef(self.pos[0], self.pos[1], self.pos[2])
            glColor3f(1.0, 0.0, 0.0)  # Red color for bullets
            glutSolidSphere(0.05, 8, 8)
            glPopMatrix()

# Missile class
class Missile:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        self.speed = 0.3
        self.damage = 5  # Increased damage for missiles
        self.alive = True
        self.target = None  # Will store nearest enemy when fired
        self.explosion_radius = 2.0  # Area of effect for missile explosion

    def update(self):
        if self.alive:
            if self.target and self.target.alive:
                # Calculate direction to target
                dx = self.target.pos[0] - self.pos[0]
                dy = self.target.pos[1] - self.pos[1]
                dz = self.target.pos[2] - self.pos[2]
                dist = (dx*dx + dy*dy + dz*dz)**0.5
                
                # Move towards target
                if dist > 0:
                    self.pos[0] += (dx/dist) * self.speed
                    self.pos[1] += (dy/dist) * self.speed
                    self.pos[2] += (dz/dist) * self.speed
            else:
                # If no target, move forward
                self.pos[2] -= self.speed

    def draw(self):
        if self.alive:
            glPushMatrix()
            glTranslatef(self.pos[0], self.pos[1], self.pos[2])
            glColor3f(1.0, 0.5, 0.0)  # Orange color for missiles
            # Draw missile body
            glPushMatrix()
            glRotatef(90, 1, 0, 0)
            glutSolidCone(0.1, 0.3, 8, 8)
            glPopMatrix()
            # Draw missile trail
            glColor3f(1.0, 0.3, 0.0)
            glBegin(GL_LINES)
            glVertex3f(0, 0, 0.3)
            glVertex3f(0, 0, 0.5)
            glEnd()
            glPopMatrix()

# Generate 300 random stars
stars = []
def generate_star(z_offset):
    x = random.uniform(-20, 20)
    y = random.uniform(-15, 15)
    z = z_offset
    return (x, y, z)
# Fill initial space with stars ahead of the spaceship
for i in range(200):
    stars.append(generate_star(random.uniform(-100, 0)))

    x = random.uniform(-20, 20)
    y = random.uniform(-15, 15)
    z = random.uniform(-100, -1)
    stars.append((x, y, z))
def draw_stars():
    global stars

    # Remove distant stars
    stars = [s for s in stars if abs(s[2] - ship_pos[2]) < 100]

    # Add stars ahead and behind
    while len(stars) < 300:
        offset = random.uniform(-100, 100)
        stars.append(generate_star(ship_pos[2] + offset))

    glColor3f(1.0, 1.0, 1.0)
    glPointSize(1.5)
    glBegin(GL_POINTS)
    for (x, y, z) in stars:
        glVertex3f(x, y, z)
    glEnd()


def draw_spaceship():
    glPushMatrix()
    glTranslatef(ship_pos[0], ship_pos[1], ship_pos[2])
    glRotatef(180, 0, 1, 0)  # Flip to face forward
    glScalef(1.0, 1.0, 1.5)  # Adjust proportions for fighter jet look
    
    # Main body (fuselage)
    glColor3f(*spaceship_color)
    glPushMatrix()
    glScalef(0.3, 0.2, 1.0)  # Elongated body
    glutSolidSphere(1.0, 16, 16)
    glPopMatrix()
    
    # Cockpit
    glColor3f(0.7, 0.8, 1.0)  # Light blue for cockpit
    glPushMatrix()
    glTranslatef(0, 0.1, 0.2)  # Position on top of body
    glRotatef(90, 1, 0, 0)
    glScalef(0.15, 0.2, 0.15)
    glutSolidSphere(1.0, 16, 16)
    glPopMatrix()
    
    # Main wings
    glColor3f(0.0, 0.5, 1.0)  # Medium blue
    # Left wing
    glPushMatrix()
    glTranslatef(-0.4, 0, 0)
    glRotatef(45, 0, 0, 1)  # Angle the wing
    glScalef(0.6, 0.05, 0.2)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Right wing
    glPushMatrix()
    glTranslatef(0.4, 0, 0)
    glRotatef(-45, 0, 0, 1)  # Angle the wing
    glScalef(0.6, 0.05, 0.2)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Tail wings
    glColor3f(0.0, 0.4, 0.8)  # Darker blue
    # Left tail
    glPushMatrix()
    glTranslatef(-0.2, 0, -0.4)
    glRotatef(30, 0, 0, 1)
    glScalef(0.2, 0.05, 0.1)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Right tail
    glPushMatrix()
    glTranslatef(0.2, 0, -0.4)
    glRotatef(-30, 0, 0, 1)
    glScalef(0.2, 0.05, 0.1)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Vertical stabilizer (tail fin)
    glPushMatrix()
    glTranslatef(0, 0.1, -0.4)
    glRotatef(90, 0, 0, 1)
    glScalef(0.2, 0.05, 0.2)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Engine nozzles
    glColor3f(0.3, 0.3, 0.3)  # Dark gray
    # Left engine
    glPushMatrix()
    glTranslatef(-0.15, 0, -0.5)
    glRotatef(90, 1, 0, 0)
    glScalef(0.1, 0.1, 0.1)
    glutSolidCylinder(1.0, 1.0, 8, 8)
    glPopMatrix()
    
    # Right engine
    glPushMatrix()
    glTranslatef(0.15, 0, -0.5)
    glRotatef(90, 1, 0, 0)
    glScalef(0.1, 0.1, 0.1)
    glutSolidCylinder(1.0, 1.0, 8, 8)
    glPopMatrix()
    
    # Engine glow
    glColor3f(0.8, 0.4, 0.0)  # Orange glow
    # Left engine glow
    glPushMatrix()
    glTranslatef(-0.15, 0, -0.55)
    glRotatef(90, 1, 0, 0)
    glScalef(0.08, 0.08, 0.05)
    glutSolidCylinder(1.0, 1.0, 8, 8)
    glPopMatrix()
    
    # Right engine glow
    glPushMatrix()
    glTranslatef(0.15, 0, -0.55)
    glRotatef(90, 1, 0, 0)
    glScalef(0.08, 0.08, 0.05)
    glutSolidCylinder(1.0, 1.0, 8, 8)
    glPopMatrix()
    
    # Weapon pods
    glColor3f(0.2, 0.2, 0.2)  # Dark gray
    # Left weapon pod
    glPushMatrix()
    glTranslatef(-0.3, -0.05, 0)
    glScalef(0.1, 0.1, 0.3)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Right weapon pod
    glPushMatrix()
    glTranslatef(0.3, -0.05, 0)
    glScalef(0.1, 0.1, 0.3)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPopMatrix()

def draw_bullets():
    # Draw regular bullets
    for bullet in player_bullets:
        bullet.draw()
    
    # Draw missiles
    for missile in player_missiles:
        missile.draw()
    
    # Draw enemy bullets
    for bullet in enemy_bullets:
        bullet.draw()

enemies = []

class Enemy:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        self.alive = True

    def update(self):
        # Move toward the player
        speed = 0.05
        if spaceship_level >= 2:
            speed = 0.12  # Increase speed at level 2
        self.pos[2] += speed  # Speed towards player

    def draw(self):
        if self.alive:
            glPushMatrix()
            glTranslatef(*self.pos)
            glScalef(0.5, 0.5, 0.5)  # Make enemy smaller than player
            glColor3f(*enemy_color)  # Use enemy_color

            # Body (cone)
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            glutSolidCone(0.4, 1.0, 10, 10)
            glPopMatrix()

            # Wings (mini cubes)
            glColor3f(0.8, 0.0, 0.0)  # Darker red
            glPushMatrix()
            glTranslatef(-0.4, 0, 0)
            glScalef(0.2, 0.05, 0.3)
            glutSolidCube(1)
            glPopMatrix()

            glPushMatrix()
            glTranslatef(0.4, 0, 0)
            glScalef(0.2, 0.05, 0.3)
            glutSolidCube(1)
            glPopMatrix()

            glPopMatrix()

for _ in range(5):
    x = random.uniform(-10, 10)
    y = 0.0
    z = ship_pos[2] - random.uniform(30, 50)
    enemies.append(Enemy(x, y, z))

enemy_bullets = []

class EnemyBullet:
    def __init__(self, x, y, z, direction):
        self.pos = [x, y, z]
        self.direction = direction  # A unit vector toward the player
        self.alive = True

    def update(self):
        if self.alive:
            self.pos[0] += self.direction[0] * 0.2
            self.pos[1] += self.direction[1] * 0.2
            self.pos[2] += self.direction[2] * 0.2

    def draw(self):
        if self.alive:
            
            glPushMatrix()
            glTranslatef(*self.pos)
            glColor3f(1.0, 0.5, 0.0)
            glutSolidSphere(0.1, 8, 8)
            glPopMatrix()

last_enemy_fire_time = 0

def fire_enemy_bullets():
    global last_enemy_fire_time
    now = time.time()
    if now - last_enemy_fire_time < 1.5:  # 1.5 seconds between shots
        return
    last_enemy_fire_time = now

    for enemy in enemies:
        if enemy.alive:
            dx = ship_pos[0] - enemy.pos[0]
            dy = ship_pos[1] - enemy.pos[1]
            dz = ship_pos[2] - enemy.pos[2]
            mag = (dx**2 + dy**2 + dz**2)**0.5
            direction = [dx/mag, dy/mag, dz/mag]
            bullet = EnemyBullet(enemy.pos[0], enemy.pos[1], enemy.pos[2], direction)
            enemy_bullets.append(bullet)

def draw_radar():
    # Save the current matrix
    glPushMatrix()
    
    # Switch to orthographic projection for 2D drawing
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(-10, 10, -10, 10, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Move radar to right side, centered vertically, and scale it down
    glTranslatef(8.0, 0.0, 0)  # Move to right edge, center vertically
    glScalef(0.15, 0.15, 1.0)  # Make radar smaller

    # Draw radar background (circle)
    glColor3f(0.2, 0.2, 0.2)  # Dark gray
    glBegin(GL_POLYGON)
    for i in range(360):
        angle = math.radians(i)
        x = 7 * math.cos(angle)
        y = 7 * math.sin(angle)
        glVertex2f(x, y)
    glEnd()
    
    # Draw radar border
    glColor3f(0.0, 1.0, 0.0)  # Green
    glBegin(GL_LINE_LOOP)
    for i in range(360):
        angle = math.radians(i)
        x = 7 * math.cos(angle)
        y = 7 * math.sin(angle)
        glVertex2f(x, y)
    glEnd()
    
    # Draw crosshair lines
    glColor3f(0.0, 1.0, 0.0)  # Green
    glBegin(GL_LINES)
    glVertex2f(-7, 0)
    glVertex2f(7, 0)
    glVertex2f(0, -7)
    glVertex2f(0, 7)
    glEnd()
    
    # Draw enemy blips
    glColor3f(1.0, 0.0, 0.0)  # Red
    for enemy in enemies:
        if enemy.alive:
            # Calculate relative position to player
            rel_x = enemy.pos[0] - ship_pos[0]
            rel_z = enemy.pos[2] - ship_pos[2]
            
            # Scale and clamp the position to radar size
            scale = 7.0 / 50.0  # Scale factor to fit radar
            radar_x = rel_x * scale
            radar_z = rel_z * scale
            
            # Only show enemies within radar range
            if abs(radar_x) <= 7 and abs(radar_z) <= 7:
                glBegin(GL_POLYGON)
                for i in range(360):
                    angle = math.radians(i)
                    x = 0.3 * math.cos(angle) + radar_x
                    y = 0.3 * math.sin(angle) + radar_z
                    glVertex2f(x, y)
                glEnd()
    
    # Restore the original projection matrix
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

def draw_buttons():
    # Save OpenGL state
    glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_LINE_BIT)
    glPushMatrix()
    # Set up orthographic projection for 2D overlay
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(-10, 10, -10, 10, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    # Disable depth test and lighting
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    # Get window size and calculate button positions
    width = glutGet(GLUT_WINDOW_WIDTH)
    height = glutGet(GLUT_WINDOW_HEIGHT)
    ortho_left, ortho_right = -10, 10
    ortho_bottom, ortho_top = -10, 10
    margin_x = 0.5
    margin_y = 0.5
    btn_width = 2.5
    btn_height = 1.5
    spacing = 0.5
    restart_x = ortho_left + margin_x
    restart_y = ortho_top - margin_y - btn_height
    quit_x = restart_x + btn_width + spacing
    quit_y = restart_y
    # Draw shadow for both buttons
    glColor3f(0.0, 0.0, 0.0)
    for dx, dy in [(0.08, -0.08), (0.12, -0.12)]:
        # Restart shadow
        glBegin(GL_QUADS)
        glVertex2f(restart_x + dx, restart_y + dy)
        glVertex2f(restart_x + btn_width + dx, restart_y + dy)
        glVertex2f(restart_x + btn_width + dx, restart_y + btn_height + dy)
        glVertex2f(restart_x + dx, restart_y + btn_height + dy)
        glEnd()
        # Quit shadow
        glBegin(GL_QUADS)
        glVertex2f(quit_x + dx, quit_y + dy)
        glVertex2f(quit_x + btn_width + dx, quit_y + dy)
        glVertex2f(quit_x + btn_width + dx, quit_y + btn_height + dy)
        glVertex2f(quit_x + dx, quit_y + btn_height + dy)
        glEnd()
    # Draw Restart (Play) button
    glColor3f(0.2, 0.6, 0.2)  # Greenish background
    glBegin(GL_QUADS)
    glVertex2f(restart_x, restart_y)
    glVertex2f(restart_x + btn_width, restart_y)
    glVertex2f(restart_x + btn_width, restart_y + btn_height)
    glVertex2f(restart_x, restart_y + btn_height)
    glEnd()
    # Draw play triangle (centered)
    glColor3f(1.0, 1.0, 1.0)
    tri_margin = 0.4
    glBegin(GL_TRIANGLES)
    glVertex2f(restart_x + tri_margin, restart_y + tri_margin)
    glVertex2f(restart_x + btn_width - tri_margin, restart_y + btn_height / 2)
    glVertex2f(restart_x + tri_margin, restart_y + btn_height - tri_margin)
    glEnd()
    # Draw Quit (Cross) button
    glColor3f(0.7, 0.2, 0.2)  # Reddish background
    glBegin(GL_QUADS)
    glVertex2f(quit_x, quit_y)
    glVertex2f(quit_x + btn_width, quit_y)
    glVertex2f(quit_x + btn_width, quit_y + btn_height)
    glVertex2f(quit_x, quit_y + btn_height)
    glEnd()
    # Draw cross (X) (centered)
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(3.0)
    cross_margin = 0.5
    glBegin(GL_LINES)
    glVertex2f(quit_x + cross_margin, quit_y + cross_margin)
    glVertex2f(quit_x + btn_width - cross_margin, quit_y + btn_height - cross_margin)
    glVertex2f(quit_x + btn_width - cross_margin, quit_y + cross_margin)
    glVertex2f(quit_x + cross_margin, quit_y + btn_height - cross_margin)
    glEnd()
    glLineWidth(1.0)
    # Restore OpenGL state
    glPopMatrix()  # modelview
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glPopAttrib()

mirror_enabled = True  # Rear-view mirror is on by default

def draw_mirror():
    if not mirror_enabled:
        return
    # Save current viewport and matrices
    glPushAttrib(GL_VIEWPORT_BIT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()

    # Set up a tiny viewport for the mirror (like an eye button, top right corner)
    width = glutGet(GLUT_WINDOW_WIDTH)
    height = glutGet(GLUT_WINDOW_HEIGHT)
    mirror_w = int(width * 0.045)
    mirror_h = int(height * 0.03)
    mirror_x = int(width - mirror_w - 10)
    mirror_y = int(height - mirror_h - 10)
    glViewport(mirror_x, mirror_y, mirror_w, mirror_h)

    # Set up projection for the mirror
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, mirror_w / mirror_h, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    # Rear view: camera at ship, looking backward
    gluLookAt(
        ship_pos[0], ship_pos[1] + 1, ship_pos[2],
        ship_pos[0], ship_pos[1], ship_pos[2] + 5,  # Look behind
        0, 1, 0
    )
    # Draw scene in mirror (stars, enemies, bullets, but not HUD/radar)
    draw_stars()
    for enemy in enemies:
        enemy.draw()
    for bullet in player_bullets:
        bullet.draw()
    for missile in player_missiles:
        missile.draw()
    for bullet in enemy_bullets:
        bullet.draw()
    draw_spaceship()  # Optionally show your own ship in the mirror

    # Draw eye icon (ellipse with a pupil) as the border/button
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glViewport(0, 0, width, height)
    cx = mirror_x + mirror_w / 2
    cy = mirror_y + mirror_h / 2
    rx = mirror_w / 2
    ry = mirror_h / 2
    # Eye outline
    glColor3f(1.0, 1.0, 0.0)  # Yellow border
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    for i in range(100):
        theta = 2.0 * math.pi * i / 100
        x = cx + rx * math.cos(theta)
        y = cy + ry * math.sin(theta)
        glVertex2f(x, y)
    glEnd()
    # Eye pupil
    glColor3f(0.0, 0.0, 0.0)
    prx = rx * 0.35
    pry = ry * 0.35
    glBegin(GL_POLYGON)
    for i in range(100):
        theta = 2.0 * math.pi * i / 100
        x = cx + prx * math.cos(theta)
        y = cy + pry * math.sin(theta)
        glVertex2f(x, y)
    glEnd()
    glLineWidth(1.0)

    # Restore viewport and matrices
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glPopAttrib()

def draw_upgrade_menu():
    glPushMatrix()
    glColor3f(1.0, 1.0, 1.0)  # White color for menu
    glRasterPos2f(-5, 5)  # Position in the top-left
    message = f"Bounty: {bounty} | Press 'U' to upgrade spaceship"
    for char in message:
        glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(char))
    glPopMatrix()

def upgrade_spaceship():
    global bounty, spaceship_level, spaceship_color
    if bounty >= 200:
        bounty -= 200
        spaceship_level += 1
        # Randomly change spaceship color
        spaceship_color = [random.random(), random.random(), random.random()]
        print('Spaceship upgraded! Level:', spaceship_level)

def change_level_colors():
    global space_color, enemy_color, clouds
    if difficulty == 'medium':
        # Dark blue space with green enemies
        space_color = [0.0, 0.0, 0.2]  # Dark blue
        enemy_color = [0.0, 1.0, 0.0]  # Green
        # Update cloud colors for medium level
        for cloud in clouds:
            cloud.color = [0.6, 0.8, 1.0, cloud.opacity]  # Light blue clouds
    elif difficulty == 'hard':
        # Dark purple space with yellow enemies
        space_color = [0.2, 0.0, 0.2]  # Dark purple
        enemy_color = [1.0, 1.0, 0.0]  # Yellow
        # Update cloud colors for hard level
        for cloud in clouds:
            cloud.color = [0.8, 0.6, 1.0, cloud.opacity]  # Light purple clouds
    else:  # easy
        # Black space with red enemies
        space_color = [0.0, 0.0, 0.0]  # Black
        enemy_color = [1.0, 0.0, 0.0]  # Red
        # Update cloud colors for easy level
        for cloud in clouds:
            cloud.color = [0.8, 0.8, 0.8, cloud.opacity]  # Light gray clouds
    
    # Update the background color
    glClearColor(*space_color, 1.0)

def display():
    global ship_pos, camera_mode, enemies_left, enemies_destroyed, game_over

    # Clear with the current space color
    glClearColor(*space_color, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Set up camera view
    if camera_mode == 'third':
        gluLookAt(
            ship_pos[0], ship_pos[1] + 2, ship_pos[2] + 5,
            ship_pos[0], ship_pos[1], ship_pos[2],
            0, 1, 0
        )
    elif camera_mode == 'first':
        gluLookAt(
            ship_pos[0], ship_pos[1] + 0.5, ship_pos[2] + 0.5,
            ship_pos[0], ship_pos[1], ship_pos[2] - 1,
            0, 1, 0
        )

    # Draw background stars
    draw_stars()
    
    # Draw clouds before other objects
    draw_clouds()

    # Draw player spaceship
    draw_spaceship()

    # Update and draw bullets
    draw_bullets()

    # Check bullet-enemy collisions
    check_bullet_enemy_collision()

    # Draw all enemies
    for enemy in enemies:
        enemy.update()
        enemy.draw()

    # Draw the HUD (showing remaining and destroyed enemies)
    draw_hud()
    
    # Draw the radar
    draw_radar()

    # Draw the rear-view mirror
    draw_mirror()

    # Draw the upgrade menu
    draw_upgrade_menu()

    # Check for game over conditions
    if not game_over:
        if check_enemy_player_collision() or check_bullet_player_collision():
            game_over = True

    if game_over:
        glPushMatrix()
        glColor3f(1.0, 0.0, 0.0)
        glRasterPos2f(-2, 0)
        for char in "GAME OVER":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
        glPopMatrix()
        # Draw restart and quit buttons
        draw_buttons()

    glutSwapBuffers()




def check_collision(obj1_pos, obj2_pos, threshold=1.0):
    """Returns True if the distance between obj1 and obj2 is within the threshold."""
    dx = obj1_pos[0] - obj2_pos[0]
    dy = obj1_pos[1] - obj2_pos[1]
    dz = obj1_pos[2] - obj2_pos[2]
    distance = math.sqrt(dx**2 + dy**2 + dz**2)
    return distance < threshold
def check_bullet_enemy_collision():
    global enemies_destroyed, enemies_left, score, spaceship_level, difficulty, bounty
    collision_occurred = False
    
    # Check bullet collisions
    for bullet in player_bullets:
        for enemy in enemies:
            if bullet.alive and enemy.alive and check_collision(bullet.pos, enemy.pos, threshold=0.5):
                bullet.alive = False
                enemy.alive = False
                enemies_destroyed += 1
                enemies_left -= 1
                score += 100  # Basic points for bullet kills
                bounty += 50  # Increase bounty
                collision_occurred = True
                # Level up after 10 enemies destroyed
                if enemies_destroyed == 10 and spaceship_level == 1:
                    spaceship_level = 2
                    print('Level Up! Missiles unlocked and enemies move faster!')
    
    # Check missile collisions
    for missile in player_missiles:
        for enemy in enemies:
            if missile.alive and enemy.alive:
                # Check for direct hit
                if check_collision(missile.pos, enemy.pos, threshold=0.8):
                    missile.alive = False
                    enemy.alive = False
                    enemies_destroyed += 1
                    enemies_left -= 1
                    score += 300  # Increased points for missile kills
                    bounty += 150  # Increase bounty
                    collision_occurred = True
                    # Level up after 10 enemies destroyed
                    if enemies_destroyed == 10 and spaceship_level == 1:
                        spaceship_level = 2
                        print('Level Up! Missiles unlocked and enemies move faster!')
                    # Check for nearby enemies that might be affected by explosion
                    for other_enemy in enemies:
                        if other_enemy != enemy and other_enemy.alive:
                            if check_collision(missile.pos, other_enemy.pos, threshold=missile.explosion_radius):
                                other_enemy.alive = False
                                enemies_destroyed += 1
                                enemies_left -= 1
                                score += 150  # Bonus points for explosion kills
                                bounty += 75  # Increase bounty
                                collision_occurred = True
    
    # Check difficulty level change after all collisions are processed
    if enemies_left == 0:
        if difficulty == 'easy':
            difficulty = 'medium'
            print('Difficulty increased to Medium!')
            reset_game()
        elif difficulty == 'medium':
            difficulty = 'hard'
            print('Difficulty increased to Hard!')
            reset_game()
        elif difficulty == 'hard':
            print('Congratulations! You have completed all difficulty levels!')
            game_over = True
    
    return collision_occurred


def check_enemy_player_collision():
    for enemy in enemies:
        if enemy.alive and check_collision(enemy.pos, ship_pos, threshold=0.7):
            return True
    return False

def check_bullet_player_collision():
    for bullet in enemy_bullets:
        if check_collision(bullet.pos, ship_pos, threshold=0.5):
            bullet.alive = False  # Destroy enemy bullet
            return True
    return False


def idle():
    global bullets, player_bullets, player_missiles, enemy_bullets, game_over
    if game_over:
        return  # Stop updating if game is over
    # Update bullet positions
    for bullet in player_bullets:
        bullet.update()
    # Update missile positions
    for missile in player_missiles:
        missile.update()
    # Update enemy bullet positions
    for bullet in enemy_bullets:
        bullet.update()
    # Remove bullets that are far away
    player_bullets = [b for b in player_bullets if b.alive and b.pos[2] > -50]
    player_missiles = [m for m in player_missiles if m.alive and m.pos[2] > -50]
    enemy_bullets = [b for b in enemy_bullets if b.alive and abs(b.pos[2] - ship_pos[2]) < 100]
    glutPostRedisplay()
    fire_enemy_bullets()
    glutPostRedisplay()

def keyboard(key, x, y):
    global ship_pos, camera_mode, current_weapon, spaceship_level, game_over, mirror_enabled, cheat_mode
    key = key.decode('utf-8')
    
    # Move the spaceship
    if key == 's':
        ship_pos[2] += 1  # Move forward (Z-axis)
    elif key == 'w':
        ship_pos[2] -= 1  # Move backward (Z-axis)
    elif key == 'a':
        ship_pos[0] -= 1  # Move left (X-axis)
    elif key == 'd':
        ship_pos[0] += 1  # Move right (X-axis)
    elif key == 'v':
        # Toggle camera view
        camera_mode = 'first' if camera_mode == 'third' else 'third'
    elif key == 'q':
        # Only allow missile if spaceship_level >= 2 or difficulty is medium or hard
        if spaceship_level >= 2 or difficulty in ['medium', 'hard']:
            current_weapon = 'missile' if current_weapon == 'bullet' else 'bullet'
        else:
            current_weapon = 'bullet'  # Missiles locked
    elif key == 'm':
        mirror_enabled = not mirror_enabled
    elif key == 'r' and game_over:
        reset_game()
    elif key == 'q' and game_over:
        os._exit(0)
    elif key == 'c':
        cheat_mode = not cheat_mode
        print('Cheat mode:', 'ON' if cheat_mode else 'OFF')
    elif key == 'u':
        upgrade_spaceship()

    glutPostRedisplay()

def mouse(button, state, x, y):
    global current_weapon, spaceship_level, game_over
    width = glutGet(GLUT_WINDOW_WIDTH)
    height = glutGet(GLUT_WINDOW_HEIGHT)
    # Calculate ortho size
    ortho_left, ortho_right = -10, 10
    ortho_bottom, ortho_top = -10, 10
    margin_x = 0.5
    margin_y = 0.5
    btn_width = 2.5
    btn_height = 1.5
    spacing = 0.5
    restart_x = ortho_left + margin_x
    restart_y = ortho_top - margin_y - btn_height
    quit_x = restart_x + btn_width + spacing
    quit_y = restart_y
    if game_over and state == GLUT_DOWN:
        # Convert mouse x, y to orthographic coordinates
        ortho_x = (x / width) * 20 - 10
        ortho_y = 10 - (y / height) * 20
        # Check Restart button
        if (restart_x <= ortho_x <= restart_x + btn_width and
            restart_y <= ortho_y <= restart_y + btn_height):
            reset_game()
            return
        # Check Quit button
        if (quit_x <= ortho_x <= quit_x + btn_width and
            quit_y <= ortho_y <= quit_y + btn_height):
            os._exit(0)
            return
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        if cheat_mode:
            # Find nearest enemy and fire a bullet that hits it
            nearest_enemy = None
            min_dist = float('inf')
            for enemy in enemies:
                if enemy.alive:
                    dx = enemy.pos[0] - ship_pos[0]
                    dy = enemy.pos[1] - ship_pos[1]
                    dz = enemy.pos[2] - ship_pos[2]
                    dist = dx*dx + dy*dy + dz*dz
                    if dist < min_dist:
                        min_dist = dist
                        nearest_enemy = enemy
            if nearest_enemy:
                bullet = Bullet(ship_pos[0], ship_pos[1], ship_pos[2])
                bullet.pos = nearest_enemy.pos.copy()
                player_bullets.append(bullet)
        else:
            player_bullets.append(Bullet(ship_pos[0], ship_pos[1], ship_pos[2]))
    elif button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and (spaceship_level >= 2 or difficulty in ['medium', 'hard']):
        # Find nearest enemy for missile targeting
        nearest_enemy = None
        min_dist = float('inf')
        for enemy in enemies:
            if enemy.alive:
                dx = enemy.pos[0] - ship_pos[0]
                dy = enemy.pos[1] - ship_pos[1]
                dz = enemy.pos[2] - ship_pos[2]
                dist = dx*dx + dy*dy + dz*dz
                if dist < min_dist:
                    min_dist = dist
                    nearest_enemy = enemy
        missile = Missile(ship_pos[0], ship_pos[1], ship_pos[2])
        missile.target = nearest_enemy
        player_missiles.append(missile)

def draw_hud():
    # Save the current matrix
    glPushMatrix()
    
    # Switch to orthographic projection for 2D drawing
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(-10, 10, -10, 10, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    # Draw HUD text
    glColor3f(1.0, 1.0, 1.0)  # White color for HUD
    
    # Position the text in the top-left corner
    glRasterPos2f(-9.5, 9.0)  # Adjusted position
    
    # Create the message
    weapon_display = current_weapon.upper()
    if current_weapon == 'missile' and spaceship_level < 2:
        weapon_display = 'MISSILE (LOCKED)'
    
    # Split the message into parts for better readability
    message_parts = [
        f"Score: {score}",
        f"Enemies Left: {enemies_left}",
        f"Destroyed: {enemies_destroyed}",
        f"Weapon: {weapon_display}",
        f"Level: {spaceship_level}",
        f"Difficulty: {difficulty}"
    ]
    
    # Draw each part of the message
    for i, part in enumerate(message_parts):
        # Position each line
        glRasterPos2f(-9.5, 9.0 - (i * 0.5))  # Each line 0.5 units below the previous
        for char in part:
            glutBitmapCharacter(GLUT_BITMAP_8_BY_13, ord(char))
    
    # Restore the original projection matrix
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


def init():
    global enemies, enemies_left, space_color, enemy_color, clouds
    # Set initial colors
    space_color = [0.0, 0.0, 0.0]  # Black
    enemy_color = [1.0, 0.0, 0.0]  # Red
    glClearColor(*space_color, 1.0)  # Space background
    glEnable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 800 / 600, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(0, 0, 0,  # Eye position
              0, 0, -1,  # Look at point
              0, 1, 0)   # Up vector
    
    # Initialize enemies for easy level
    enemies = []
    for _ in range(5):
        x = random.uniform(-10, 10)
        y = 0.0
        z = ship_pos[2] - random.uniform(30, 50)
        enemies.append(Enemy(x, y, z))
    enemies_left = len(enemies)
    
    # Generate initial clouds
    generate_clouds()

def reset_game():
    global ship_pos, enemies, player_bullets, player_missiles, enemy_bullets, score, enemies_destroyed, enemies_left, spaceship_level, game_over, difficulty
    ship_pos[:] = [0.0, 0.0, 0.0]
    enemies = []
    if difficulty == 'easy':
        for _ in range(5):
            x = random.uniform(-10, 10)
            y = 0.0
            z = ship_pos[2] - random.uniform(30, 50)
            enemies.append(Enemy(x, y, z))
    elif difficulty == 'medium':
        for _ in range(10):
            x = random.uniform(-10, 10)
            y = 0.0
            z = ship_pos[2] - random.uniform(30, 50)
            enemies.append(Enemy(x, y, z))
    elif difficulty == 'hard':
        for _ in range(15):
            x = random.uniform(-10, 10)
            y = 0.0
            z = ship_pos[2] - random.uniform(30, 50)
            enemies.append(Enemy(x, y, z))
    player_bullets = []
    player_missiles = []
    enemy_bullets = []
    score = 0
    enemies_destroyed = 0
    enemies_left = len(enemies)
    spaceship_level = 1
    game_over = False
    # Update colors when resetting game
    change_level_colors()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Space Bounty Hunter - 3D OpenGL")

    init()

    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutMouseFunc(mouse)

    glutMainLoop()

if __name__ == '__main__':
    main()
