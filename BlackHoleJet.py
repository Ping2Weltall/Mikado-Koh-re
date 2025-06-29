#!/usr/bin/env python3
# whirlpool.py
# Simuliert dein Mikado-Whirlpool-Modell mit Pygame:
# • „Quantum Foam“ (Wasser, blau) wirbelt spiralförmig zum Abfluss in der Mitte
# • Im Abfluss kondensiert es zu Neutrinos (weiß)
# • Neutrinos driften radial nach außen zum Wannenrand
# • Am Rand kondensieren sie zurück zu Quantum Foam und werden erneut eingesogen

import pygame, random, math
from dataclasses import dataclass

# +++ Einstellungen +++
WIDTH, HEIGHT = 800, 800
FPS = 60

INIT_WATER    = 300    # Startanzahl Quantum-Foam-Partikel
RADIAL_SPEED  = 1.5    # Inward-Spiral-Geschwindigkeit (Water)
TANG_SPEED    = 2.0    # Tangentiale Drehgeschwindigkeit (Water)
NEU_RADIAL    = 2.0    # Outward-Geschwindigkeit (Neutrino)
NEU_JITTER    = 0.5    # Zufallsdrift (Neutrino)

DRAIN_RADIUS  = 20     # Radius des zentralen Abflusses
BOWL_MARGIN   = 50     # Abstand vom Rand zur Wannenwand

# Farben
BG_COLOR       = (10, 10, 30)
FOAM_COLOR     = (80, 180, 255)
NEUTRINO_COLOR = (240, 240, 240)
WALL_COLOR     = (200, 200, 200)

# +++ Partikelklasse +++
@dataclass
class Particle:
    x: float
    y: float
    type: str  # "foam" oder "neutrino"

# +++ Hilfsfunktionen +++
def dist(p, cx, cy):
    return math.hypot(p.x - cx, p.y - cy)

def spawn_foam(x, y):
    return Particle(x, y, "foam")

def spawn_neutrino(x, y):
    return Particle(x, y, "neutrino")

# +++ Pygame Setup +++
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
cx, cy = WIDTH / 2, HEIGHT / 2
bowl_radius = min(WIDTH, HEIGHT) / 2 - BOWL_MARGIN

# +++ Initialbefüllung +++
particles = []
for _ in range(INIT_WATER):
    angle = random.uniform(0, 2 * math.pi)
    r     = random.uniform(bowl_radius * 0.7, bowl_radius)
    x     = cx + r * math.cos(angle)
    y     = cy + r * math.sin(angle)
    particles.append(spawn_foam(x, y))

# +++ Haupt-Loop +++
running = True
while running:
    clock.tick(FPS)
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    screen.fill(BG_COLOR)
    # Zeichne Wannenrand
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), int(bowl_radius), 3)
    # Zeichne Abfluss
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), DRAIN_RADIUS, 2)

    new_particles = []
    for p in particles:
        # Zentralabstand
        r = dist(p, cx, cy)

        if p.type == "foam":
            # Einheitlicher radialer Einwärtsvektor
            if r > 0:
                nx, ny = (p.x - cx) / r, (p.y - cy) / r
            else:
                nx, ny = 0, 0
            v_rx = -RADIAL_SPEED * nx
            v_ry = -RADIAL_SPEED * ny
            # Tangentialer Vektor (Perp. zum radialen)
            tx, ty = -ny, nx
            v_tx, v_ty = TANG_SPEED * tx, TANG_SPEED * ty
            # Bewegung
            p.x += v_rx + v_tx
            p.y += v_ry + v_ty
            # Visualisieren
            pygame.draw.circle(screen, FOAM_COLOR, (int(p.x), int(p.y)), 3)
            # Kondensieren im Abfluss
            if r <= DRAIN_RADIUS:
                new_particles.append(spawn_neutrino(cx, cy))
                continue

        else:  # neutrino
            # Radialer Auswärtsvektor
            if r > 0:
                nx, ny = (p.x - cx) / r, (p.y - cy) / r
            else:
                nx, ny = 1, 0
            v_rx = NEU_RADIAL * nx + random.uniform(-NEU_JITTER, NEU_JITTER)
            v_ry = NEU_RADIAL * ny + random.uniform(-NEU_JITTER, NEU_JITTER)
            p.x += v_rx
            p.y += v_ry
            pygame.draw.circle(screen, NEUTRINO_COLOR, (int(p.x), int(p.y)), 2)
            # Kondensieren am Wannenrand
            if r >= bowl_radius:
                # Clamp auf Wannenrandkorridor
                angle = math.atan2(p.y - cy, p.x - cx)
                x_new = cx + (bowl_radius - 5) * math.cos(angle)
                y_new = cy + (bowl_radius - 5) * math.sin(angle)
                new_particles.append(spawn_foam(x_new, y_new))
                continue

        new_particles.append(p)

    particles = new_particles
    pygame.display.flip()

pygame.quit()