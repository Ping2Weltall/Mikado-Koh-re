#!/usr/bin/env python3
# whirlpool_bathtub_model.py

import pygame
import random
import math
from dataclasses import dataclass

# +++ Einstellungen +++
WIDTH, HEIGHT    = 800, 800
FPS              = 60

INIT_FOAM        = 900
INIT_NEUTRINO    = 100
FOAM_RADIAL      = 2.5
FOAM_TANG        = 3.0

NEUTRINO_SPEED   = 3.0
NEUTRINO_JIT     = 0.2
NEUTRINO_PULL    = 0.1

DRAIN_RADIUS     = 20    # Zentrum: Foam → Neutrino
RIM_ZONE_WIDTH   = 20    # Peripherie: Neutrino → Foam
BOWL_MARGIN      = 50

BG_COLOR         = (10, 10, 30)
WALL_COLOR       = (200, 200, 200)
YELLOW_COLOR     = (255, 255, 0)

@dataclass
class Particle:
    x: float
    y: float
    dx: float
    dy: float
    type: str    # "foam" oder "neutrino"
    trail: list = None  # Für Neutrino-Trails (optional)

def spawn_foam(x, y):
    return Particle(x, y, 0, 0, "foam")

def spawn_neutrino(x, y):
    ang = random.uniform(0, 2 * math.pi)
    return Particle(x, y,
                    NEUTRINO_SPEED * math.cos(ang),
                    NEUTRINO_SPEED * math.sin(ang),
                    "neutrino",
                    trail=[])

def dist(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)

# === Pygame Init ===
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

cx, cy = WIDTH / 2, HEIGHT / 2
bowl_r = min(WIDTH, HEIGHT) / 2 - BOWL_MARGIN
rim_inner = bowl_r - RIM_ZONE_WIDTH

# === Partikel anlegen ===
particles = []

# Foam mit zufälliger, gleichmäßiger Verteilung im Becken
for _ in range(INIT_FOAM):
    ang = random.uniform(0, 2 * math.pi)
    r = random.uniform(DRAIN_RADIUS, bowl_r)
    x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
    particles.append(spawn_foam(x, y))

# Neutrinos mit zufälliger Verteilung in der Rim-Zone
for _ in range(INIT_NEUTRINO):
    ang = random.uniform(0, 2 * math.pi)
    r = random.uniform(rim_inner, bowl_r)
    x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
    particles.append(spawn_neutrino(x, y))

running = True
while running:
    clock.tick(FPS)
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    screen.fill(BG_COLOR)
    glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    # Wanne & Abfluss
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), int(bowl_r), 3)
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), DRAIN_RADIUS, 2)

    new_list = []
    collision_fx = []

    for p in particles:
        r = dist(p.x, p.y, cx, cy)

        if p.type == "foam":
            # Strömung
            if r != 0:
                nx, ny = (p.x - cx) / r, (p.y - cy) / r
            else:
                nx, ny = 0, 0
            vrx, vry = -FOAM_RADIAL * nx, -FOAM_RADIAL * ny
            tx, ty = -ny, nx
            p.x += vrx + FOAM_TANG * tx
            p.y += vry + FOAM_TANG * ty

            # Kollision nur für Foam
            for other in particles:
                if other != p and other.type == "foam" and dist(p.x, p.y, other.x, other.y) < 10:
                    dx = p.x - other.x
                    dy = p.y - other.y
                    dist_val = dist(p.x, p.y, other.x, other.y)
                    if dist_val > 0:
                        force = 10 / (dist_val * dist_val)
                        p.x += dx * force / dist_val
                        p.y += dy * force / dist_val
                        collision_fx.append((p.x, p.y, 5))  # Kleinerer Radius für subtileren Effekt

            # Phasenwechsel im Abfluss
            if r <= DRAIN_RADIUS:
                new_list.append(spawn_neutrino(cx, cy))
                continue

        else:  # neutrino
            # Bewegung mit Jitter + Anziehung
            pull_x = -NEUTRINO_PULL * (p.x - cx) / r if r != 0 else 0
            pull_y = -NEUTRINO_PULL * (p.y - cy) / r if r != 0 else 0
            p.x += p.dx + random.uniform(-NEUTRINO_JIT, NEUTRINO_JIT) + pull_x
            p.y += p.dy + random.uniform(-NEUTRINO_JIT, NEUTRINO_JIT) + pull_y

            # Trail aktualisieren
            if p.trail is not None:
                p.trail.append((p.x, p.y))
                if len(p.trail) > 10:  # Begrenze den Trail auf 10 Punkte
                    p.trail.pop(0)

            # Phasenwechsel in der Rim-Zone
            if r >= rim_inner:
                new_list.append(spawn_foam(p.x, p.y))
                continue

        new_list.append(p)

    # Partikel zeichnen
    for p in new_list:
        r = dist(p.x, p.y, cx, cy)
        cf = min(1.0, max(0.0, r / bowl_r))
        if p.type == "foam":
            rc = int(255 * cf)
            gc = int(255 * (1 - cf) * 0.5)
            bc = int(255 * (1 - cf))
            radius = 3
        else:
            rc = int(255 * cf)
            gc = 0
            bc = int(255 * (1 - cf))
            radius = 2
            # Zeichne den Trail
            if p.trail:
                for i, (tx, ty) in enumerate(p.trail):
                    alpha = int(255 * (1 - i / len(p.trail)))  # Verblassender Effekt
                    if alpha > 0:
                        pygame.draw.circle(screen, (rc, gc, bc, alpha), (int(tx), int(ty)), radius)

        pygame.draw.circle(screen, (rc, gc, bc), (int(p.x), int(p.y)), radius)

    # Glow für gelbe Kollisionseffekte (subtiler)
    for x, y, rad in collision_fx[:]:
        for R, alpha in [(5, 15), (3, 30), (2, 60)]:  # Kleinere Radii und niedrigere Alpha-Werte
            pygame.draw.circle(glow_surf, (YELLOW_COLOR[0], YELLOW_COLOR[1], YELLOW_COLOR[2], alpha), (int(x), int(y)), R)
        collision_fx.remove((x, y, rad))

    screen.blit(glow_surf, (0, 0), special_flags=pygame.BLEND_ADD)

    particles = new_list
    pygame.display.flip()

pygame.quit()