#!/usr/bin/env python3
# Mikado-Modell - Foam, Drain-zentrierte Gravitation, elastische Reflexion

import pygame
import random
import math
from dataclasses import dataclass

# +++ Einstellungen +++
WIDTH, HEIGHT    = 1024, 1024
FPS              = 60

INIT_FOAM        = 512
INIT_NEUTRINO    = 0
FOAM_RADIAL      = 1.2    # Radiale Startgeschwindigkeit
FOAM_TANG        = 0.8    # Optional: leichte Tangentialbewegung
FOAM_GRAVITY     = 0.0    # KEINE allgemeine Gravitation, nur Drain
DRAIN_GRAVITY    = 2.0    # Hauptkraft: Sog zum Zentrum

NEUTRINO_SPEED   = 6.0
NEUTRINO_JIT     = 0.5
NEUTRINO_PULL    = 0.0

DRAIN_RADIUS     = 25
RIM_ZONE_WIDTH   = 20
BOWL_MARGIN      = 50
FOAM_TO_NEUTRINO_THRESHOLD = 5  # wie viele Foam für 1 Neutrino

BG_COLOR         = (11, 11, 30)
WALL_COLOR       = (200, 200, 200)
YELLOW_COLOR     = (255, 255, 0)
CENTER_COLOR     = (255, 0, 0)

@dataclass
class Particle:
    x: float
    y: float
    dx: float
    dy: float
    type: str    # "foam" oder "neutrino"
    trail: list = None

def spawn_foam(x, y, outward=True):
    """Erzeugt ein Foam-Partikel.
    outward=True gibt radialen (nach innen) Impuls am Rand,
    sonst zufällige kleine Geschwindigkeit."""
    angle = math.atan2(y - HEIGHT/2, x - WIDTH/2)
    if outward:
        # Richtung Zentrum
        speed = FOAM_RADIAL + random.uniform(-0.3, 0.3)
        dx = -math.cos(angle) * speed
        dy = -math.sin(angle) * speed
    else:
        ang = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0, 0.5)
        dx = math.cos(ang) * speed
        dy = math.sin(ang) * speed
    return Particle(x, y, dx, dy, "foam", trail=[])

def spawn_neutrino(x, y):
    ang = random.uniform(0, 2 * math.pi)
    return Particle(x, y,
                    NEUTRINO_SPEED * math.cos(ang),
                    NEUTRINO_SPEED * math.sin(ang),
                    "neutrino",
                    trail=[])

def dist(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

cx, cy = WIDTH / 2, HEIGHT / 2
bowl_r = min(WIDTH, HEIGHT) / 2 - BOWL_MARGIN
rim_inner = bowl_r - RIM_ZONE_WIDTH

particles = []

# Foam mit zufälliger Verteilung im Becken
for _ in range(INIT_FOAM):
    ang = random.uniform(0, 2 * math.pi)
    r = random.uniform(DRAIN_RADIUS, bowl_r)
    x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
    particles.append(spawn_foam(x, y, outward=False))

# Neutrinos (meist 0 am Start, außer zu Testzwecken)
for _ in range(INIT_NEUTRINO):
    ang = random.uniform(0, 2 * math.pi)
    r = random.uniform(rim_inner, bowl_r)
    x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
    particles.append(spawn_neutrino(x, y))

foam_count = 0

running = True
while running:
    clock.tick(FPS)
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    screen.fill(BG_COLOR)
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), int(bowl_r), 3)
    pygame.draw.circle(screen, CENTER_COLOR, (int(cx), int(cy)), DRAIN_RADIUS, 0)

    new_list = []
    collision_marks = []

    for p in particles:
        r = dist(p.x, p.y, cx, cy)

        if p.type == "foam":
            # Richtung zum Zentrum (Drain)
            if r != 0:
                nx, ny = (cx - p.x) / r, (cy - p.y) / r
                tx, ty = -ny, nx
            else:
                nx, ny = 0, 0
                tx, ty = 0, 0

            # Kräfte – nur Drain-Gravitation und FOAM_RADIAL!
            # Drain ist anziehend, FOAM_RADIAL gibt einen konstanten (leichten) Stoß nach innen
            drain_grav = DRAIN_GRAVITY / max(r*r, 1)
            # Radialer Drift (bleibt erhalten für Foam am Rand)
            p.dx += FOAM_RADIAL * nx * 0.25  # 0.25 ist ein Dämpfungsfaktor
            # Optional: leichte Tangentialbewegung
            p.dx += FOAM_TANG * tx * 0.1
            p.dy += FOAM_RADIAL * ny * 0.25
            p.dy += FOAM_TANG * ty * 0.1
            # Drain-Gravitation
            p.dx += drain_grav * nx
            p.dy += drain_grav * ny

            # Leichte Dämpfung (wie Reibung)
            p.dx *= 0.97
            p.dy *= 0.97

            # Position aktualisieren
            p.x += p.dx
            p.y += p.dy

            # Trail aktualisieren
            if p.trail is not None:
                p.trail.append((p.x, p.y))
                if len(p.trail) > 10:
                    p.trail.pop(0)

            # Kollisionen (Gasverhalten)
            for other in particles:
                if other != p and other.type == "foam" and dist(p.x, p.y, other.x, other.y) < 10:
                    dx = p.x - other.x
                    dy = p.y - other.y
                    dist_val = dist(p.x, p.y, other.x, other.y)
                    if dist_val > 0:
                        force = 10 / (dist_val * dist_val)
                        p.x += dx * force / dist_val
                        p.y += dy * force / dist_val
                        collision_marks.append((p.x, p.y, 3))

            # Reflexion an der Wand
            r_new = dist(p.x, p.y, cx, cy)
            if r_new >= bowl_r:
                nxr, nyr = (p.x - cx) / r_new, (p.y - cy) / r_new
                v_dot_n = p.dx * nxr + p.dy * nyr
                p.dx -= 2 * v_dot_n * nxr
                p.dy -= 2 * v_dot_n * nyr
                # Position knapp innerhalb des Beckens setzen
                p.x = cx + nxr * (bowl_r - 1)
                p.y = cy + nyr * (bowl_r - 1)

            # Neutrino-Umwandlung am Drain
            if r_new <= DRAIN_RADIUS:
                foam_count += 1
                if foam_count >= FOAM_TO_NEUTRINO_THRESHOLD:
                    new_list.append(spawn_neutrino(cx, cy))
                    foam_count = 0
                continue

        elif p.type == "neutrino":
            # Bewegung (Neutrinos sind schnell und diffus)
            speed = math.hypot(p.dx, p.dy)
            if speed > 0:
                p.x += (p.dx / speed) * NEUTRINO_SPEED + random.uniform(-NEUTRINO_JIT, NEUTRINO_JIT)
                p.y += (p.dy / speed) * NEUTRINO_SPEED + random.uniform(-NEUTRINO_JIT, NEUTRINO_JIT)
            else:
                p.x += random.uniform(-NEUTRINO_JIT, NEUTRINO_JIT)
                p.y += random.uniform(-NEUTRINO_JIT, NEUTRINO_JIT)

            # Trail
            if p.trail is not None:
                p.trail.append((p.x, p.y))
                if len(p.trail) > 10:
                    p.trail.pop(0)

            # Neutrino zerfällt zu Foam an der Außenhülle
            r_new = dist(p.x, p.y, cx, cy)
            if r_new >= bowl_r:
                for _ in range(FOAM_TO_NEUTRINO_THRESHOLD):
                    # Mit radialem Impuls ins Becken und leichter Streuung
                    angle = math.atan2(p.y - cy, p.x - cx) + random.uniform(-0.2, 0.2)
                    radius = bowl_r - 2
                    fx = cx + math.cos(angle) * radius
                    fy = cy + math.sin(angle) * radius
                    new_list.append(spawn_foam(fx, fy, outward=True))
                continue

        new_list.append(p)

    # Zeichnen wie gehabt
    for p in new_list:
        r = dist(p.x, p.y, cx, cy)
        cf = min(1.0, max(0.0, r / bowl_r))
        if p.type == "foam":
            rc = int(255 * (1 - cf))
            gc = int(255 * (1 - cf) * 0.5)
            bc = int(255 * (1 - cf))
            radius = 3
            if p.trail:
                for i, (tx, ty) in enumerate(p.trail):
                    alpha = int(255 * (1 - i / len(p.trail)))
                    if alpha > 0:
                        pygame.draw.circle(screen, (rc, gc, bc, alpha), (int(tx), int(ty)), radius)
        else:
            rc = int(255 * cf)
            gc = 0
            bc = int(255 * (1 - cf))
            radius = 2
            if p.trail:
                for i, (tx, ty) in enumerate(p.trail):
                    alpha = int(255 * (1 - i / len(p.trail)))
                    if alpha > 0:
                        pygame.draw.circle(screen, (rc, gc, bc, alpha), (int(tx), int(ty)), radius)
        pygame.draw.circle(screen, (rc, gc, bc), (int(p.x), int(p.y)), radius)

    # Kollisionsmarkierungen
    for x, y, rad in collision_marks[:]:
        pygame.draw.circle(screen, YELLOW_COLOR, (int(x), int(y)), rad)
        collision_marks.remove((x, y, rad))

    particles = new_list
    pygame.display.flip()

pygame.quit()