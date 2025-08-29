import pygame
import random
import math
import sys
import time
import json
import os

pygame.init()

# SAVE SYSTEM
SAVE_FILE = "save_data.json"

def load_game_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    else:
        return None

def save_game_data(level):
    with open(SAVE_FILE, "w") as f:
        json.dump({"level": level}, f)

def reset_game_data():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)

# SCREEN SETUP
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Player vs AI")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
BLUE  = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW= (255, 255, 0)
CYAN  = (0, 255, 255)
MAGENTA = (255, 0, 255)

clock = pygame.time.Clock()
FPS = 60

# PLAYER + GAME VARIABLES
player_size = 50
player = pygame.Rect(WIDTH//2, HEIGHT-80, player_size, player_size)
player_speed = 5

ai_size = 50
player_bullets = []
ai_bullets = []
bullet_speed = 7
ai_bullet_speed = 5

kills = 0
font = pygame.font.SysFont("Courier", 36, bold=True)
title_font = pygame.font.SysFont("Courier", 70, bold=True)

shoot_cooldown = 0.25
last_shot_time = 0

LEVEL_GOAL = 10
level = 1
level_time = 30
level_start_time = None
ais = []
ai_speed = 1.2

# POWERUPS
class PowerUp:
    def __init__(self, x, y, type):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.type = type
        self.color = {"shield": CYAN, "speed": YELLOW, "multishot": MAGENTA}[type]

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

powerups = []
active_powerups = {}

# HUD WITH GLOW
def draw_glow_text(text, font, x, y, main_color, glow_color):
    glow = font.render(text, True, glow_color)
    for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
        screen.blit(glow, (x+dx, y+dy))
    main = font.render(text, True, main_color)
    screen.blit(main, (x, y))

# TITLE SCREEN
def title_screen():
    stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT)] for _ in range(100)]
    selected = 0

    save_data = load_game_data()
    if save_data:
        options = ["CONTINUE", "NEW GAME", "QUIT"]
    else:
        options = ["NEW GAME", "QUIT"]

    while True:
        screen.fill(BLACK)

        # Starfield animation
        for star in stars:
            star[1] += 2
            if star[1] > HEIGHT:
                star[0] = random.randint(0, WIDTH)
                star[1] = 0
            pygame.draw.circle(screen, WHITE, star, 2)

        # Blinking Title
        if pygame.time.get_ticks() // 500 % 2 == 0:
            title_text = title_font.render("RETRO SHOOTER", True, YELLOW)
        else:
            title_text = title_font.render("RETRO SHOOTER", True, RED)
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, 150))

        # Menu
        for i, option in enumerate(options):
            color = GREEN if i == selected else WHITE
            text = font.render(option, True, color)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 350 + i*60))

        pygame.display.flip()
        clock.tick(FPS)

        # Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if options[selected] == "CONTINUE":
                        return save_data["level"], False
                    elif options[selected] == "NEW GAME":
                        reset_game_data()
                        return 1, True
                    elif options[selected] == "QUIT":
                        pygame.quit()
                        sys.exit()

# LEVEL INTRO
def level_intro(level_num):
    screen.fill(BLACK)
    text = title_font.render(f"LEVEL {level_num}", True, YELLOW)
    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 40))
    pygame.display.flip()
    pygame.time.delay(2000)

# GAME OVER SCREEN (returns to title)
def game_over_screen(reason, current_level):
    screen.fill(BLACK)
    over_text = title_font.render("GAME OVER!", True, RED)
    reason_text = font.render(reason, True, WHITE)
    screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2 - 80))
    screen.blit(reason_text, (WIDTH//2 - reason_text.get_width()//2, HEIGHT//2))
    pygame.display.flip()
    pygame.time.delay(3000)
    save_game_data(current_level)

# WIN SCREEN
def win_screen():
    screen.fill(BLACK)
    text = title_font.render("YOU WIN!", True, GREEN)
    screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 40))
    pygame.display.flip()
    pygame.time.delay(4000)
    reset_game_data()  # Reset save on winning

# AI SPAWNING
def spawn_ai(level):
    num_ai = 1
    if level >= 5: num_ai = 2
    if level >= 10: num_ai = 3
    return [pygame.Rect(random.randint(50, WIDTH-50), 50, ai_size, ai_size) for _ in range(num_ai)]

# MAIN
while True:  
    level, fresh_start = title_screen()

    while level <= 10:
        # Reset per-level state
        kills = 0
        player_bullets.clear()
        ai_bullets.clear()
        powerups.clear()
        active_powerups.clear()
        last_shot_time = 0

        # Timing rules
        if level == 1:
            level_time = 30
        else:
            level_time -= random.choice([1, 2])
        if level == 5 or level == 10:
            level_time += 20

        # Speeds scale (smarter scaling with cap)
        base_speed = 1.2
        max_speed = 2.0
        ai_speed = min(base_speed + math.log(level) * 0.3, max_speed)

        # Player base speed
        base_player_speed = 5 + (level - 1) * 0.1

        ais = spawn_ai(level)
        player.x, player.y = WIDTH//2, HEIGHT-80

        level_intro(level)
        level_start_time = time.time()

        level_won = False
        level_failed = False
        fail_reason = ""

        while True:
            current_time = time.time()
            elapsed_time = int(current_time - level_start_time)
            time_left = level_time - elapsed_time

            # Win / Fail conditions
            if kills >= LEVEL_GOAL:
                level_won = True
                break
            if time_left <= 0 and kills < LEVEL_GOAL:
                level_failed = True
                fail_reason = "You failed the objective"
                break

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Active powerups check
            shield_active = ("shield" in active_powerups and pygame.time.get_ticks() < active_powerups["shield"])
            speed_active = ("speed" in active_powerups and pygame.time.get_ticks() < active_powerups["speed"])
            multishot_active = ("multishot" in active_powerups and pygame.time.get_ticks() < active_powerups["multishot"])

            # Player movement
            player_speed = base_player_speed * (1.5 if speed_active else 1)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] and player.top > 0: player.y -= player_speed
            if keys[pygame.K_s] and player.bottom < HEIGHT: player.y += player_speed
            if keys[pygame.K_a] and player.left > 0: player.x -= player_speed
            if keys[pygame.K_d] and player.right < WIDTH: player.x += player_speed

            # Shooting
            if (current_time - last_shot_time) > shoot_cooldown:
                if multishot_active:
                    if keys[pygame.K_UP] or keys[pygame.K_DOWN] or keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
                        last_shot_time = current_time
                        dirs = [
                            (0, -bullet_speed), (0, bullet_speed),
                            (-bullet_speed, 0), (bullet_speed, 0),
                            (-bullet_speed, -bullet_speed), (bullet_speed, -bullet_speed),
                            (-bullet_speed, bullet_speed), (bullet_speed, bullet_speed)
                        ]
                        for dx, dy in dirs:
                            player_bullets.append([player.centerx, player.centery, dx, dy])
                else:
                    bullet_dx, bullet_dy = 0, 0
                    if keys[pygame.K_UP]:
                        bullet_dx, bullet_dy = 0, -bullet_speed
                    elif keys[pygame.K_DOWN]:
                        bullet_dx, bullet_dy = 0, bullet_speed
                    elif keys[pygame.K_LEFT]:
                        bullet_dx, bullet_dy = -bullet_speed, 0
                    elif keys[pygame.K_RIGHT]:
                        bullet_dx, bullet_dy = bullet_speed, 0

                    if bullet_dx or bullet_dy:
                        last_shot_time = current_time
                        player_bullets.append([player.centerx, player.centery, bullet_dx, bullet_dy])

            # AI movement + shooting
            for ai in ais:
                dx = player.centerx - ai.centerx
                dy = player.centery - ai.centery
                distance = math.hypot(dx, dy)
                if distance != 0:
                    ai.x += (dx / distance) * ai_speed
                    ai.y += (dy / distance) * ai_speed

                if random.randint(1, 80) == 1:
                    dist = math.hypot(dx, dy)
                    ai_bullets.append([ai.centerx, ai.centery, (dx/dist)*ai_bullet_speed, (dy/dist)*ai_bullet_speed])

            # player bullets
            for b in player_bullets[:]:
                b[0] += b[2]
                b[1] += b[3]
                if b[0] < 0 or b[0] > WIDTH or b[1] < 0 or b[1] > HEIGHT:
                    player_bullets.remove(b)
                else:
                    for ai in ais:
                        if pygame.Rect(b[0]-5, b[1]-5, 10, 10).colliderect(ai):
                            player_bullets.remove(b)
                            kills += 1

                            # Chance to drop a powerup
                            if random.random() < 0.3:
                                ptype = random.choice(["shield","speed","multishot"])
                                powerups.append(PowerUp(ai.x, ai.y, ptype))

                            ai.x, ai.y = random.randint(50, WIDTH-50), 50
                            break

            # AI bullets
            for b in ai_bullets[:]:
                b[0] += b[2]
                b[1] += b[3]
                bullet_rect = pygame.Rect(b[0]-5, b[1]-5, 10, 10)
                if bullet_rect.colliderect(player):
                    if not shield_active:
                        level_failed = True
                        fail_reason = "You were killed"
                        break
                    else:
                        ai_bullets.remove(b)
                if b[0] < 0 or b[0] > WIDTH or b[1] < 0 or b[1] > HEIGHT:
                    ai_bullets.remove(b)
            if level_failed:
                break

            # AI touches player
            for ai in ais:
                if ai.colliderect(player):
                    level_failed = True
                    fail_reason = "You were captured"
                    break
            if level_failed:
                break

            # Powerup collection
            for p in powerups[:]:
                if player.colliderect(p.rect):
                    active_powerups[p.type] = pygame.time.get_ticks() + 7000  # 7 sec
                    powerups.remove(p)

            # Draw everything
            screen.fill(BLACK)
            pygame.draw.rect(screen, BLUE, player)
            for ai in ais:
                pygame.draw.rect(screen, RED, ai)

            for b in player_bullets:
                pygame.draw.circle(screen, WHITE, (int(b[0]), int(b[1])), 6)
            for b in ai_bullets:
                pygame.draw.circle(screen, GREEN, (int(b[0]), int(b[1])), 6)
                pygame.draw.circle(screen, (0,200,0), (int(b[0]), int(b[1])), 3)

            for p in powerups:
                p.draw(screen)

            draw_glow_text(f"Kills: {kills}/{LEVEL_GOAL}", font, 10, 10, WHITE, RED)
            draw_glow_text(f"Time: {max(0,time_left)}s", font, WIDTH-250, 10, YELLOW, RED)

            # Powerup timers bottom right
            x_offset = WIDTH-200
            y_offset = HEIGHT-80
            for i, (ptype, end_time) in enumerate(active_powerups.items()):
                if pygame.time.get_ticks() < end_time:
                    time_left_p = (end_time - pygame.time.get_ticks()) // 1000
                    text = font.render(f"{ptype}: {time_left_p}", True, WHITE)
                    screen.blit(text, (x_offset, y_offset + i*30))

            pygame.display.flip()
            clock.tick(FPS)

        if level_failed:
            game_over_screen(fail_reason, level)
            break 

        if level_won:
            level += 1
            continue

    if level > 10:
        win_screen()
