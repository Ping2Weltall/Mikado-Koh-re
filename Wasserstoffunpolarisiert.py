#!/usr/bin/env python3
# Mikado-Modell - Wasserstoff, unpolarisiert, gasförmig

import pygame
import random
import math
from dataclasses import dataclass

# +++ Einstellungen +++
WIDTH, HEIGHT    = 1024, 1024
FPS              = 60

INIT_FOAM        =  512  #1024
INIT_NEUTRINO    = 0
FOAM_RADIAL      = 360/60    # Basis radial-inward Geschwindigkeit
FOAM_TANG        = 3.0    # Tangentiale Geschwindigkeit
FOAM_GRAVITY     = -0.25  # Gravitationsbeschleunigungskonstante

NEUTRINO_SPEED   = 6.0    # Konstante Geschwindigkeit
NEUTRINO_JIT     = 0.5   # Jitter
NEUTRINO_PULL    = 0.0    # Leichte Anziehung zum Zentrum

DRAIN_RADIUS     = 25   # Zentrum: Foam → Neutrino
RIM_ZONE_WIDTH   = 20     # Peripherie: Neutrino → Foam
BOWL_MARGIN      = 50
FOAM_TO_NEUTRINO_THRESHOLD = 5  # Mengenverhältnis 5 Foam = 1 Neutrino

BG_COLOR         = (11, 11, 30)
WALL_COLOR       = (200, 200, 200)
YELLOW_COLOR     = (255, 255, 0)

@dataclass
class Particle:
    x: float
    y: float
    dx: float
    dy: float
    type: str    # "foam" oder "neutrino"
    trail: list = None  # Für Trails (Neutrinos und Foam)

def spawn_foam(x, y):
    return Particle(x, y, 0, 0, "foam", trail=[])

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

# Zähler für Foam-zu-Neutrino-Wechsel
foam_count = 0

running = True
while running:
    clock.tick(FPS)
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    screen.fill(BG_COLOR)

    # Wanne & Abfluss
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), int(bowl_r), 3)
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), DRAIN_RADIUS, 2)

    new_list = []
    collision_marks = []

    for p in particles:
        r = dist(p.x, p.y, cx, cy)

        if p.type == "foam":
            # Strömung mit Gravitation
            if r != 0:
                nx, ny = (p.x - cx) / r, (p.y - cy) / r
            else:
                nx, ny = 0, 0
            # Basis radial-inward Bewegung
            vrx, vry = -FOAM_RADIAL * nx, -FOAM_RADIAL * ny
            # Tangentiale Bewegung
            tx, ty = -ny, nx
            vtx, vty = FOAM_TANG * tx, FOAM_TANG * ty
            # Gravitationsbeschleunigung (stärker nahe dem Abfluss)
            gravity = FOAM_GRAVITY / max(r, 1)  # Inverse Entfernung, min 1 um Division durch 0 zu vermeiden
            grav_x, grav_y = -gravity * nx, -gravity * ny
            p.x += vrx + vtx + grav_x
            p.y += vry + vty + grav_y

            # Trail aktualisieren
            if p.trail is not None:
                p.trail.append((p.x, p.y))
                if len(p.trail) > 10:  # Begrenze den Trail auf 10 Punkte
                    p.trail.pop(0)

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
                        collision_marks.append((p.x, p.y, 3))  # Gelbe Markierung

            # Phasenwechsel im Abfluss mit Mengenverhältnis
            if r <= DRAIN_RADIUS:
                foam_count += 1
                if foam_count >= FOAM_TO_NEUTRINO_THRESHOLD:
                    new_list.append(spawn_neutrino(cx, cy))
                    foam_count = 0  # Zurücksetzen nach Erreichen der Schwelle
                continue

        else:  # neutrino
            # Bewegung mit konstanter Geschwindigkeit und Jitter + Anziehung
            pull_x = -NEUTRINO_PULL * (p.x - cx) / r if r != 0 else 0
            pull_y = -NEUTRINO_PULL * (p.y - cy) / r if r != 0 else 0
            speed = math.hypot(p.dx, p.dy)
            if speed > 0:
                p.x += (p.dx / speed) * NEUTRINO_SPEED + random.uniform(-NEUTRINO_JIT, NEUTRINO_JIT) + pull_x
                p.y += (p.dy / speed) * NEUTRINO_SPEED + random.uniform(-NEUTRINO_JIT, NEUTRINO_JIT) + pull_y
            else:
                p.x += random.uniform(-NEUTRINO_JIT, NEUTRINO_JIT) + pull_x
                p.y += random.uniform(-NEUTRINO_JIT, NEUTRINO_JIT) + pull_y

            # Trail aktualisieren
            if p.trail is not None:
                p.trail.append((p.x, p.y))
                if len(p.trail) > 10:  # Begrenze den Trail auf 10 Punkte
                    p.trail.pop(0)

            # Phasenwechsel in der Rim-Zone: Zerfällt in mehrere Foam!
            if r >= rim_inner:
                for _ in range(FOAM_TO_NEUTRINO_THRESHOLD):
                    angle = random.uniform(0, 2 * math.pi)
                    rad = random.uniform(0, 6)  # leichte Streuung
                    nx = p.x + math.cos(angle) * rad
                    ny = p.y + math.sin(angle) * rad
                    new_list.append(spawn_foam(nx, ny))
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
            # Zeichne den Trail
            if p.trail:
                for i, (tx, ty) in enumerate(p.trail):
                    alpha = int(255 * (1 - i / len(p.trail)))  # Verblassender Effekt
                    if alpha > 0:
                        pygame.draw.circle(screen, (rc, gc, bc, alpha), (int(tx), int(ty)), radius)
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

    # Zeichne gelbe Kollisionsmarkierungen (temporär)
    for x, y, rad in collision_marks[:]:
        pygame.draw.circle(screen, YELLOW_COLOR, (int(x), int(y)), rad)
        collision_marks.remove((x, y, rad))  # Entferne nach einem Frame

    particles = new_list
    pygame.display.flip()

pygame.quit()