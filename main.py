import pygame
import os
import random

pygame.init()
pygame.joystick.init()

# =========================
# Global Constants & Setup
# =========================
SCREEN_HEIGHT = 600
SCREEN_WIDTH = 1100
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dino Runner - Controller + Shield + Timer")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SHIELD_RGBA = (0, 150, 255, 110)   # Blue ring (old shield)
PROTECT_FILL = (255, 50, 50, 70)   # Red fill (new protect orb)
PROTECT_EDGE = (255, 0, 0, 150)    # Red ring edge
WARNING_RED = (200, 32, 32)

# Controller configuration (indices may vary by OS/driver)
JUMP_BUTTON_INDEX = 1          # <-- Jump is Button 1 (B on many Xbox layouts)
SHIELD_BUTTON_INDEX = 13       # Left stick movement + this = blue shield
PROTECT_BUTTON_INDEX = 9       # Left stick movement + this = red protect orb
STICK_DEADZONE = 0.30          # Movement threshold for "left stick is moving"

# Gameplay tweaks
PENALTY_POINTS = 100           # Points lost on hit (min score 0)
HIT_COOLDOWN_MS = 900          # Invulnerability after a hit (ms)
RUN_DURATION_MS = 60_000       # 1 minute in milliseconds
DEBRIS_SPAWN_CHANCE = 220      # Lower = more frequent spawns (random 0..N==0)
MAX_DEBRIS = 3

# Assets
RUNNING = [pygame.image.load(os.path.join("Assets/Dino", "DinoRun1.png")),
           pygame.image.load(os.path.join("Assets/Dino", "DinoRun2.png"))]
JUMPING = pygame.image.load(os.path.join("Assets/Dino", "DinoJump.png"))

SMALL_CACTUS = [pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus1.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus2.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "SmallCactus3.png"))]
LARGE_CACTUS = [pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus1.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus2.png")),
                pygame.image.load(os.path.join("Assets/Cactus", "LargeCactus3.png"))]

BIRD = [pygame.image.load(os.path.join("Assets/Bird", "Bird1.png")),
        pygame.image.load(os.path.join("Assets/Bird", "Bird2.png"))]

CLOUD = pygame.image.load(os.path.join("Assets/Other", "Cloud.png"))
BG = pygame.image.load(os.path.join("Assets/Other", "Track.png"))


def tint_image_red(img, add=130):
    """Return a red-tinted copy of img using additive blending."""
    base = img.copy().convert_alpha()
    overlay = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    overlay.fill((add, 0, 0, 0))
    base.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return base


class Dinosaur:
    X_POS = 80
    Y_POS = 310
    JUMP_VEL = 8.5

    def __init__(self):
        self.run_img = RUNNING
        self.jump_img = JUMPING
        # Precompute red-tinted frames for protect mode
        self.run_img_red = [tint_image_red(img) for img in RUNNING]
        self.jump_img_red = tint_image_red(JUMPING)

        self.dino_run = True
        self.dino_jump = False

        self.step_index = 0
        self.jump_vel = self.JUMP_VEL
        self.image = self.run_img[0]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS

        self.shield_active = False      # Blue ring (old shield)
        self.protect_active = False     # Red tint + orb (new mode)

    def update(self, jump_pressed: bool, shield_active: bool, protect_active: bool, can_jump: bool):
        self.shield_active = shield_active
        self.protect_active = protect_active

        if self.dino_jump:
            self.jump()
        else:
            self.run()

        if jump_pressed and not self.dino_jump and can_jump:
            self.dino_jump = True

        if self.step_index >= 10:
            self.step_index = 0

    def run(self):
        frames = self.run_img_red if self.protect_active else self.run_img
        self.image = frames[self.step_index // 5]
        self.dino_rect = self.image.get_rect()
        self.dino_rect.x = self.X_POS
        self.dino_rect.y = self.Y_POS
        self.step_index += 1

    def jump(self):
        self.image = self.jump_img_red if self.protect_active else self.jump_img
        if self.dino_jump:
            self.dino_rect.y -= self.jump_vel * 4
            self.jump_vel -= 0.8
        if self.jump_vel < - self.JUMP_VEL:
            self.dino_jump = False
            self.jump_vel = self.JUMP_VEL

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.dino_rect.x, self.dino_rect.y))

        # Draw protection visuals
        r = max(self.dino_rect.width, self.dino_rect.height) // 2 + 20
        center_x = self.dino_rect.centerx
        center_y = self.dino_rect.centery

        if self.protect_active:
            # Filled red orb with red edge
            orb = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(orb, PROTECT_FILL, (r, r), r, width=0)
            pygame.draw.circle(orb, PROTECT_EDGE, (r, r), r, width=6)
            SCREEN.blit(orb, (center_x - r, center_y - r))
        elif self.shield_active:
            # Blue ring
            shield_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, SHIELD_RGBA, (r, r), r, width=6)
            SCREEN.blit(shield_surf, (center_x - r, center_y - r))


class Cloud:
    def __init__(self):
        self.x = SCREEN_WIDTH + random.randint(800, 1000)
        self.y = random.randint(50, 100)
        self.image = CLOUD
        self.width = self.image.get_width()

    def update(self, game_speed):
        self.x -= game_speed
        if self.x < -self.width:
            self.x = SCREEN_WIDTH + random.randint(2500, 3000)
            self.y = random.randint(50, 100)

    def draw(self, SCREEN):
        SCREEN.blit(self.image, (self.x, self.y))


class Obstacle:
    def __init__(self, image, type):
        self.image = image
        self.type = type
        self.rect = self.image[self.type].get_rect()
        self.rect.x = SCREEN_WIDTH

    def update(self, game_speed, obstacles):
        self.rect.x -= game_speed
        if self.rect.x < -self.rect.width:
            if obstacles and obstacles[-1] is self:
                obstacles.pop()

    def draw(self, SCREEN):
        SCREEN.blit(self.image[self.type], self.rect)


class SmallCactus(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = 325


class LargeCactus(Obstacle):
    def __init__(self, image):
        self.type = random.randint(0, 2)
        super().__init__(image, self.type)
        self.rect.y = 300


class Bird(Obstacle):
    def __init__(self, image):
        self.type = 0
        super().__init__(image, self.type)
        self.rect.y = random.choice([240, 280, 320])
        self.index = 0

    def draw(self, SCREEN):
        if self.index >= 9:
            self.index = 0
        SCREEN.blit(self.image[self.index // 5], self.rect)
        self.index += 1


class Debris:
    """Ground debris that disables jumping while overlapping."""
    def __init__(self):
        self.image = pygame.Surface((32, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (120, 120, 120), (0, 0, 32, 16))
        pygame.draw.ellipse(self.image, (90, 90, 90), (6, 2, 20, 12), 2)
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH + random.randint(600, 1600)
        self.rect.y = 365

    def update(self, game_speed, debris_list):
        self.rect.x -= game_speed
        if self.rect.x < -self.rect.width:
            if debris_list and debris_list[-1] is self:
                debris_list.pop()

    def draw(self, SCREEN):
        SCREEN.blit(self.image, self.rect)


def draw_background(x_pos_bg, y_pos_bg, game_speed):
    image_width = BG.get_width()
    SCREEN.blit(BG, (x_pos_bg, y_pos_bg))
    SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
    if x_pos_bg <= -image_width:
        SCREEN.blit(BG, (image_width + x_pos_bg, y_pos_bg))
        x_pos_bg = 0
    x_pos_bg -= game_speed
    return x_pos_bg


def main():
    # ----- Controller detection -----
    joystick = pygame.joystick.Joystick(0) if pygame.joystick.get_count() > 0 else None
    if joystick:
        joystick.init()

    run = True
    clock = pygame.time.Clock()
    player = Dinosaur()
    cloud = Cloud()
    game_speed = 20
    x_pos_bg = 0
    y_pos_bg = 380
    points = 0
    font = pygame.font.Font('freesansbold.ttf', 20)
    big_font = pygame.font.Font('freesansbold.ttf', 28)

    obstacles = []
    debris_list = []
    last_hit_time = -HIT_COOLDOWN_MS
    start_ticks = pygame.time.get_ticks()

    def draw_hud(remaining_ms, on_debris, shield_active, protect_active):
        # Score
        text = font.render(f"Points: {points}", True, BLACK)
        SCREEN.blit(text, (930, 20))
        # Speed
        SCREEN.blit(font.render(f"Speed: {game_speed}", True, BLACK), (930, 45))
        # Timer
        rem_s = max(0, remaining_ms // 1000)
        mm, ss = divmod(rem_s, 60)
        SCREEN.blit(big_font.render(f"Time: {mm}:{ss:02d}", True, BLACK), (20, 20))
        # Status
        status = []
        if on_debris:
            status.append("Jump disabled (debris)")
        if shield_active:
            status.append("Shield")
        if protect_active:
            status.append("Protect")
        if status:
            SCREEN.blit(big_font.render(" | ".join(status), True, WARNING_RED), (20, 60))

    while run:
        now = pygame.time.get_ticks()
        elapsed = now - start_ticks
        remaining = max(0, RUN_DURATION_MS - elapsed)
        if remaining <= 0:
            break  # time's up

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        # -------- Inputs --------
        keys = pygame.key.get_pressed()

        axis_x = axis_y = 0.0
        btn_jump = False
        btn_shield = False
        btn_protect = False

        if joystick:
            try:
                axis_x = joystick.get_axis(0)
                axis_y = joystick.get_axis(1)
                if joystick.get_numbuttons() > JUMP_BUTTON_INDEX:
                    btn_jump = joystick.get_button(JUMP_BUTTON_INDEX)
                if joystick.get_numbuttons() > SHIELD_BUTTON_INDEX:
                    btn_shield = joystick.get_button(SHIELD_BUTTON_INDEX)
                if joystick.get_numbuttons() > PROTECT_BUTTON_INDEX:
                    btn_protect = joystick.get_button(PROTECT_BUTTON_INDEX)
            except Exception:
                axis_x = axis_y = 0.0
                btn_jump = btn_shield = btn_protect = False

        stick_moving = (abs(axis_x) > STICK_DEADZONE) or (abs(axis_y) > STICK_DEADZONE)

        # Mappings (as requested):
        jump_pressed = bool(keys[pygame.K_UP] or keys[pygame.K_SPACE] or btn_jump)   # no stick jump
        shield_active = bool(stick_moving and btn_shield)        # blue ring (existing shield)
        protect_active = bool(stick_moving and btn_protect)      # red tint + orb (new)

        # -------- Spawning --------
        if len(obstacles) == 0:
            r = random.randint(0, 2)
            obstacles.append([SmallCactus, LargeCactus, Bird][r]([SMALL_CACTUS, LARGE_CACTUS, BIRD][r]))

        if len(debris_list) < MAX_DEBRIS and random.randint(0, DEBRIS_SPAWN_CHANCE) == 0:
            debris_list.append(Debris())

        # -------- Update world --------
        SCREEN.fill(WHITE)

        x_pos_bg = draw_background(x_pos_bg, y_pos_bg, game_speed)
        cloud.draw(SCREEN)
        cloud.update(game_speed)

        for d in list(debris_list):
            d.draw(SCREEN)
            d.update(game_speed, debris_list)

        on_debris = any(player.dino_rect.colliderect(d.rect) for d in debris_list)

        player.update(
            jump_pressed=jump_pressed,
            shield_active=shield_active,
            protect_active=protect_active,
            can_jump=not on_debris
        )
        player.draw(SCREEN)

        for obstacle in list(obstacles):
            obstacle.draw(SCREEN)
            obstacle.update(game_speed, obstacles)

            if player.dino_rect.colliderect(obstacle.rect):
                protected = player.shield_active or player.protect_active
                if not protected and (now - last_hit_time >= HIT_COOLDOWN_MS):
                    points = max(0, points - PENALTY_POINTS)
                    last_hit_time = now

        points += 1
        if points % 100 == 0:
            game_speed += 1

        draw_hud(remaining, on_debris, shield_active, protect_active)

        pygame.display.update()
        clock.tick(60)

    results_menu(points)


def results_menu(final_points):
    run = True
    while run:
        SCREEN.fill(WHITE)
        font = pygame.font.Font('freesansbold.ttf', 30)
        title = font.render("Time's Up!", True, BLACK)
        SCREEN.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 60))

        score = font.render(f"Your Score: {final_points}", True, BLACK)
        SCREEN.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, SCREEN_HEIGHT // 2))

        info = font.render("Press any Key or Button to Restart", True, BLACK)
        SCREEN.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, SCREEN_HEIGHT // 2 + 60))

        SCREEN.blit(RUNNING[0], (SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2 - 160))

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                run = False
            if event.type == pygame.KEYDOWN or event.type == pygame.JOYBUTTONDOWN:
                main()


def start_menu():
    run = True
    while run:
        SCREEN.fill(WHITE)
        font = pygame.font.Font('freesansbold.ttf', 28)
        text = font.render("Press any Key or Button to Start", True, BLACK)
        SCREEN.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2))

        hint_lines = [
            "Jump: ↑ / Space / Controller Button 1",
            "Blue Shield: Move left stick + Button 13",
            "Red Protect: Move left stick + Button 9",
            "Collisions: -100 points unless protected",
            "Debris: disables jumping while you overlap",
            "Run time: 60 seconds"
        ]
        y = SCREEN_HEIGHT // 2 + 40
        for line in hint_lines:
            tip = font.render(line, True, BLACK)
            SCREEN.blit(tip, (SCREEN_WIDTH // 2 - tip.get_width() // 2, y))
            y += 32

        SCREEN.blit(RUNNING[0], (SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT // 2 - 170))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                run = False
            if event.type == pygame.KEYDOWN or event.type == pygame.JOYBUTTONDOWN:
                main()


if __name__ == "__main__":
    start_menu()
