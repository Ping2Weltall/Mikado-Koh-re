#!/usr/bin/env python3

# Mikado-Modell mit Magnetpunkt-Logik: Elektron wird am Rand zum Magnetpunkt, löst sich bei 5 Foams in 5 Neutrinos auf

import pygame
import random
import math
from dataclasses import dataclass, field
import colorsys

# +++ Einstellungen +++
WIDTH, HEIGHT = 1024, 2048
SIM_HEIGHT = 1024
FPS = 30

INIT_FOAM = 512
INIT_NEUTRINO = 0
FOAM_RADIAL = 360/60
FOAM_TANG = 3.0
FOAM_GRAVITY = -0.25

NEUTRINO_SPEED = 3.0
NEUTRINO_JIT = 0.05

DRAIN_RADIUS = 50
RIMZONEWIDTH = 20
BOWL_MARGIN = 50
FOAMTONEUTRINO_THRESHOLD = 5
NEUTRINOTOELECTRON_THRESHOLD = 5

MAGNET_SPREAD = math.pi/1.1
MAGNET_ROTATION_SPEED = 0.03
MAGNET_RELEASE_PROB = 0.05
MAGNET_REPULSION_FORCE = 0.1
MAGNET_LIFETIME = 300
ELECTROMAGNETIC_IMPULSE_SPEED = 5.0
ELECTROMAGNETIC_IMPULSE_JIT = 0.1

# --- Neue Zähler für Fusionen und Spaltungen ---
fusion_count = 0
fission_count = 0

# --- NEUE REGELN ---
MAGNET_LIFETIME_DECAY_SOLO_FACTOR = 2.0
MAGNET_LIFETIME_STABLE_BONUS = 5
FOAM_ATTRACTION_TO_MAGNET_LINE_STRENGTH = 0.05
SINGLE_MAGNET_ATTRACTION_TO_LINE_FACTOR = 0.15
SINGLE_MAGNET_ALONG_LINE_STRENGTH = 2.0
MAX_PARTICLES_SUM = 20
MAX_POLYGON_SIDES = 8

BG_COLOR = (11, 11, 30)
WALL_COLOR = (200, 200, 200)
YELLOW_COLOR = (255, 255, 0)
MAGNET_COLOR = (80, 220, 255)
MAGNETLINECOLOR = (80, 220, 255)

# Farben für Diagramme und Text
FOAM_COLOR = (0, 200, 0)
NEUTRINO_COLOR = (200, 0, 200)
ELECTRON_COLOR = (0, 200, 255)
MAGNET_DIAG_COLOR = (80, 220, 255)
ELECTROMAGNETIC_IMPULSE_COLOR = [
    (255,0,0), (255,127,0), (255,255,0), 
    (0,255,0), (0,0,255), (75,0,130), (148,0,211)
]
TEXT_COLOR = (255, 255, 255)
PANEL_BG = (20, 20, 40)
IDEAL_FORM_COLOR = (100, 100, 100)
FUSION_COLOR = (255, 100, 100)
FISSION_COLOR = (100, 255, 100)

# Mapping für Polygonseiten
NUM_MAGNETS_TO_SIDES = {
    0: 0, 1: 0, 2: 2, 3: 3, 4: 4, 
    5: 5, 6: 6, 7: 7, 8: 8
}

@dataclass
class Particle:
    x: float
    y: float
    dx: float
    dy: float
    type: str
    angle: float = 0.0
    trail: list = field(default_factory=list)
    trapped_foam: list = field(default_factory=list)
    rotation_speed: float = MAGNET_ROTATION_SPEED
    lifetime: int = 0
    initial_angle: float = 0.0

def spawn_foam(x, y):
    return Particle(x, y, 0, 0, "foam")

def spawn_electron(x, y, dx, dy):
    return Particle(x, y, dx, dy, "electron")

def spawn_neutrino(x, y, dx, dy):
    return Particle(x, y, dx, dy, "neutrino")

def spawn_magnetfoam(x, y, angle):
    return Particle(x, y, 0, 0, "magnetfoam", angle=angle, 
                   trapped_foam=[], rotation_speed=MAGNET_ROTATION_SPEED, 
                   lifetime=MAGNET_LIFETIME)

def spawn_electromagnetic_impulse(x, y, angle):
    return Particle(x, y,
                    ELECTROMAGNETIC_IMPULSE_SPEED * math.cos(angle),
                    ELECTROMAGNETIC_IMPULSE_SPEED * math.sin(angle),
                    "electromagnetic_impulse", angle=angle, lifetime=1000,
                    initial_angle=angle)

def dist(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)

def hsv2rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r*255), int(g*255), int(b*255)

def closest_point_on_segment(px, py, ax, ay, bx, by):
    ab_x = bx - ax
    ab_y = by - ay
    ap_x = px - ax
    ap_y = py - ay
    dot_prod = ap_x * ab_x + ap_y * ab_y
    len_sq_ab = ab_x * ab_x + ab_y * ab_y

    if len_sq_ab == 0:
        return ax, ay, (px - ax)**2 + (py - ay)**2

    t = max(0, min(1, dot_prod / len_sq_ab))
    closest_x = ax + t * ab_x
    closest_y = ay + t * ab_y
    dist_sq = (px - closest_x)**2 + (py - closest_y)**2
    return closest_x, closest_y, dist_sq

def get_polygon_points(center_coords, sides, radius, angle_offset=0):
    pts = []
    for i in range(sides):
        angle = angle_offset + i * 2 * math.pi / sides
        x = center_coords[0] + radius * math.cos(angle)
        y = center_coords[1] + radius * math.sin(angle)
        pts.append((x, y))
    return pts

# Funktionen für Zuwachs der Zähler
def increment_fusion_count():
    global fusion_count
    fusion_count += 1

def increment_fission_count():
    global fission_count
    fission_count += 1

# Funktionen für Statistikwerte
def get_fusion_count():
    global fusion_count
    return fusion_count

def get_fission_count():
    global fission_count
    return fission_count

# === Pygame Init ===
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Particle Simulation")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont('Arial', 40, bold=True)
font_medium = pygame.font.SysFont('Arial', 36, bold=True)
font_small = pygame.font.SysFont('Arial', 24, bold=True)

cx, cy = WIDTH / 2, SIM_HEIGHT / 2
bowl_r = min(WIDTH, SIM_HEIGHT) / 2 - BOWL_MARGIN
rim_inner = bowl_r - RIMZONEWIDTH

particles = []

for _ in range(INIT_FOAM):
    ang = random.uniform(0, 2 * math.pi)
    r = random.uniform(DRAIN_RADIUS, bowl_r)
    x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
    particles.append(spawn_foam(x, y))

for _ in range(INIT_NEUTRINO):
    ang = random.uniform(0, 2 * math.pi)
    r = random.uniform(rim_inner, bowl_r)
    x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
    dx = NEUTRINO_SPEED * math.cos(ang)
    dy = NEUTRINO_SPEED * math.sin(ang)
    particles.append(spawn_neutrino(x, y, dx, dy))

foam_fusion_buffer = []
history = {'foam': [], 'neutrino': [], 'electron': [], 'magnetfoam': [], 'electromagnetic_impulse': []}
MAX_HISTORY = 100

running = True
while running:
    clock.tick(FPS)
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    screen.fill(BG_COLOR)
    pygame.draw.rect(screen, BG_COLOR, (0, 0, WIDTH, SIM_HEIGHT))
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), int(bowl_r), 3)
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), DRAIN_RADIUS, 2)

    new_list = []
    collision_marks = []
    counts = {'foam': 0, 'neutrino': 0, 'electron': 0, 'magnetfoam': 0, 'electromagnetic_impulse': 0}
    
    all_magnets = [p for p in particles if p.type == "magnetfoam"]
    num_magnets = len(all_magnets)
    
    magnet_ideal_polygon_points = []
    sides_for_polygon = 0
    
    if num_magnets > 1:
        sides_for_polygon = NUM_MAGNETS_TO_SIDES.get(min(num_magnets, MAX_POLYGON_SIDES), 0)
        if sides_for_polygon > 1:
            current_polygon_angle_offset = pygame.time.get_ticks() / 1000.0 * MAGNET_ROTATION_SPEED
            magnet_ideal_polygon_points = get_polygon_points(
                (cx, cy), sides_for_polygon, bowl_r, current_polygon_angle_offset
            )

    current_special_particles = counts['electron'] + counts['magnetfoam'] + counts['electromagnetic_impulse']

    for p in particles:
        r = dist(p.x, p.y, cx, cy)

        if p.type == "foam":
            magnet_foams = [q for q in particles if q.type == "magnetfoam"]
            nearest = None
            if magnet_foams:
                nearest = min(magnet_foams, key=lambda m: dist(p.x, p.y, m.x, m.y))
                angle = nearest.angle
                r_foam = math.hypot(p.x - cx, p.y - cy)
                target_x = cx + math.cos(angle) * r_foam
                target_y = cy + math.sin(angle) * r_foam
                to_line_dx = (target_x - p.x) * 0.15
                to_line_dy = (target_y - p.y) * 0.15
                along_line_strength = 2.0
                radial_dx = -math.cos(angle) * along_line_strength
                radial_dy = -math.sin(angle) * along_line_strength
            else:
                to_line_dx = to_line_dy = radial_dx = radial_dy = 0

            foam_radial = FOAM_RADIAL * (0.3 if magnet_foams else 1.0)
            foam_tang = FOAM_TANG * (0.2 if magnet_foams else 1.0)
            if r != 0:
                nx, ny = (p.x - cx) / r, (p.y - cy) / r
            else:
                nx, ny = 0, 0
            vrx, vry = -foam_radial * nx, -foam_radial * ny
            tx, ty = -ny, nx
            vtx, vty = foam_tang * tx, foam_tang * ty
            gravity = FOAM_GRAVITY / max(r, 1)
            gravx, gravy = -gravity * nx, -gravity * ny

            p.dx = vrx + vtx + gravx + to_line_dx + radial_dx
            p.dy = vry + vty + gravy + to_line_dy + radial_dy
            p.x += p.dx
            p.y += p.dy

            if p.trail:
                p.trail.append((p.x, p.y))
                if len(p.trail) > 10:
                    p.trail.pop(0)

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

            if r <= DRAIN_RADIUS:
                foam_fusion_buffer.append(p)
                if len(foam_fusion_buffer) >= FOAMTONEUTRINO_THRESHOLD:
                    last = foam_fusion_buffer[-1]
                    new_list.append(spawn_neutrino(last.x, last.y, last.dx, last.dy))
                    foam_fusion_buffer.clear()
                    increment_fusion_count()  # Fusion hinzugefügt
                continue

            if magnet_foams:
                nearest = min(magnet_foams, key=lambda m: dist(p.x, p.y, m.x, m.y))
                d_to_magnet = dist(p.x, p.y, nearest.x, nearest.y)
                if d_to_magnet < 8 and abs(r - bowl_r) < 8:
                    if nearest.trapped_foam is not None and id(p) not in nearest.trapped_foam:
                        nearest.trapped_foam.append(id(p))
                        p.x = nearest.x
                        p.y = nearest.y
                        p.dx = 0
                        p.dy = 0
                        continue

            if r >= bowl_r:
                if r != 0:
                    nxr, nyr = (p.x - cx) / r, (p.y - cy) / r
                else:
                    nxr, nyr = 0, 0
                vdotn = p.dx * nxr + p.dy * nyr
                p.dx -= 2 * vdotn * nxr
                p.dy -= 2 * vdotn * nyr
                p.x = cx + nxr * (bowl_r - 1)
                p.y = cy + nyr * (bowl_r - 1)

            new_list.append(p)

        elif p.type == "neutrino":
            p.x += p.dx
            p.y += p.dy

            if p.trail:
                p.trail.append((p.x, p.y))
                if len(p.trail) > 10:
                    p.trail.pop(0)

            if r >= rim_inner:
                for _ in range(FOAMTONEUTRINO_THRESHOLD):
                    angle = random.uniform(0, 2 * math.pi)
                    rad = random.uniform(0, 6)
                    nx = p.x + math.cos(angle) * rad
                    ny = p.y + math.sin(angle) * rad
                    new_list.append(spawn_foam(nx, ny))
                continue

            new_list.append(p)

        elif p.type == "electron":
            p.x += p.dx
            p.y += p.dy

            if p.trail:
                p.trail.append((p.x, p.y))
                if len(p.trail) > 10:
                    p.trail.pop(0)

            if r >= bowl_r:
                if current_special_particles < MAX_PARTICLES_SUM:
                    angle = math.atan2(p.y - cy, p.x - cx)
                    mx = cx + math.cos(angle) * bowl_r
                    my = cy + math.sin(angle) * bowl_r
                    new_list.append(spawn_magnetfoam(mx, my, angle))
                continue

            new_list.append(p)

        elif p.type == "magnetfoam":
            if num_magnets == 1:
                p.lifetime -= MAGNET_LIFETIME_DECAY_SOLO_FACTOR
                p.angle += p.rotation_speed
                p.x = cx + bowl_r * math.cos(p.angle)
                p.y = cy + bowl_r * math.sin(p.angle)
                p.dx = 0
                p.dy = 0
            elif num_magnets > 1:
                p.lifetime += MAGNET_LIFETIME_STABLE_BONUS
                repulsion_dx, repulsion_dy = 0, 0
                for other in all_magnets:
                    if other != p:
                        d = dist(p.x, p.y, other.x, other.y)
                        if d < 100:
                            force = MAGNET_REPULSION_FORCE / (d * d + 0.1)
                            angle_to_other = math.atan2(p.y - other.y, p.x - other.x)
                            repulsion_dx += math.cos(angle_to_other) * force
                            repulsion_dy += math.sin(angle_to_other) * force
                
                p.dx = repulsion_dx
                p.dy = repulsion_dy
                try:
                    p_index_in_sorted_magnets = all_magnets.index(p)
                    if p_index_in_sorted_magnets < len(magnet_ideal_polygon_points):
                        target_x, target_y = magnet_ideal_polygon_points[p_index_in_sorted_magnets]
                        align_strength = 0.1
                        p.dx += (target_x - p.x) * align_strength
                        p.dy += (target_y - p.y) * align_strength
                except ValueError:
                    pass

                p.x += p.dx
                p.y += p.dy
                current_r = dist(p.x, p.y, cx, cy)
                if current_r != 0:
                    scale_factor = bowl_r / current_r
                    p.x = cx + (p.x - cx) * scale_factor
                    p.y = cy + (p.y - cy) * scale_factor
                p.angle = math.atan2(p.y - cy, p.x - cx)

            for foam_id in p.trapped_foam[:]:
                found_foam = False
                for foam in new_list:
                    if id(foam) == foam_id and foam.type == "foam":
                        foam.x = p.x
                        foam.y = p.y
                        foam.dx = 0
                        foam.dy = 0
                        found_foam = True
                        break
                if not found_foam and foam_id in p.trapped_foam:
                    p.trapped_foam.remove(foam_id)

            if p.trapped_foam and p.lifetime > 0 and random.random() < MAGNET_RELEASE_PROB:
                foam_id = random.choice(p.trapped_foam)
                p.trapped_foam.remove(foam_id)
                increment_fission_count()  # Spaltung hinzugefügt
                for foam in new_list:
                    if id(foam) == foam_id and foam.type == "foam":
                        angle = math.atan2(cy - foam.y, cx - foam.x)
                        speed = random.uniform(1.0, 3.0)
                        foam.dx = math.cos(angle) * speed
                        foam.dy = math.sin(angle) * speed
                        break

            if p.lifetime <= 0:
                if current_special_particles < MAX_PARTICLES_SUM:
                    new_list.append(spawn_electromagnetic_impulse(p.x, p.y, p.angle + math.pi))
                    increment_fission_count()  # Spaltung hinzugefügt
            else:
                new_list.append(p)

        elif p.type == "electromagnetic_impulse":
            p.lifetime -= 1
            p.x += p.dx
            p.y += p.dy
            p.dx += random.uniform(-ELECTROMAGNETIC_IMPULSE_JIT, ELECTROMAGNETIC_IMPULSE_JIT)
            p.dy += random.uniform(-ELECTROMAGNETIC_IMPULSE_JIT, ELECTROMAGNETIC_IMPULSE_JIT)
            current_r = dist(p.x, p.y, cx, cy)

            # Reflexion am äußeren Rand beibehalten
            if current_r >= bowl_r:
                if current_r != 0:
                    nxr, nyr = (p.x - cx) / current_r, (p.y - cy) / current_r
                else:
                    nxr, nyr = 0, 0
                vdotn = p.dx * nxr + p.dy * nyr
                p.dx -= 2 * vdotn * nxr
                p.dy -= 2 * vdotn * nyr
                p.x = cx + nxr * (bowl_r - 1)
                p.y = cy + nyr * (bowl_r - 1)
                p.angle = math.atan2(p.dy, p.dx)

            # Keine Reflexion am Drain - Impulse verschwinden einfach
            elif current_r <= DRAIN_RADIUS:
                continue

            if p.trail:
                p.trail.append((p.x, p.y))
                if len(p.trail) > 20:
                    p.trail.pop(0)

            if p.lifetime > 0:
                new_list.append(p)

    # Neutrino→Elektron-Fusion
    drain_neutrinos = [p for p in new_list if p.type == "neutrino" and dist(p.x, p.y, cx, cy) <= DRAIN_RADIUS]
    used = set()
    i = 0
    while i < len(drain_neutrinos):
        if i in used:
            i += 1
            continue
        p = drain_neutrinos[i]
        cluster = [q for q in drain_neutrinos if dist(p.x, p.y, q.x, q.y) < 7 and drain_neutrinos.index(q) not in used]
        if len(cluster) >= NEUTRINOTOELECTRON_THRESHOLD and current_special_particles < MAX_PARTICLES_SUM:
            increment_fusion_count()  # Fusion hinzugefügt
            mx = sum(q.x for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]) / NEUTRINOTOELECTRON_THRESHOLD
            my = sum(q.y for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]) / NEUTRINOTOELECTRON_THRESHOLD
            mdx = sum(q.dx for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]) / NEUTRINOTOELECTRON_THRESHOLD
            mdy = sum(q.dy for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]) / NEUTRINOTOELECTRON_THRESHOLD
            remove_ids = set(id(q) for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD])
            new_list = [part for part in new_list if not (part.type == "neutrino" and id(part) in remove_ids)]
            used |= set(drain_neutrinos.index(q) for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD])
            new_list.append(spawn_electron(mx, my, mdx, mdy))
        i += 1

    for p in new_list:
        if p.type in counts:
            counts[p.type] += 1
    
    for key in history:
        history[key].append(counts[key])
        if len(history[key]) > MAX_HISTORY:
            history[key] = history[key][-MAX_HISTORY:]

    actual_magnet_positions_for_display = []
    if num_magnets > 0:
        current_magnets_in_new_list = [p for p in new_list if p.type == "magnetfoam"]
        current_magnets_in_new_list.sort(key=lambda m: math.atan2(m.y - cy, m.x - cx))
        actual_magnet_positions_for_display = [(m.x, m.y) for m in current_magnets_in_new_list]

    particles = new_list

    # Zeichnen der Partikel
    for p in new_list:
        r = dist(p.x, p.y, cx, cy)
        cf = min(1.0, max(0.0, r / bowl_r))
        if p.type == "foam":
            rc = int(255 * (1 - cf))  # Näher am Rand heller
            gc = int(255 * (1 - cf) * 0.5)
            bc = int(255 * (1 - cf))
            radius = 3
            if p.trail:
                for i, (tx, ty) in enumerate(p.trail):
                    alpha = int(255 * (1 - i / len(p.trail)))  # Verblassender Effekt
                    if alpha > 0:
                        pygame.draw.circle(screen, (rc, gc, bc, alpha), (int(tx), int(ty)), radius)
        elif p.type == "neutrino":
            rc = int(255 * cf)
            gc = 0
            bc = int(255 * (1 - cf))
            radius = 2
            if p.trail:
                for i, (tx, ty) in enumerate(p.trail):
                    alpha = int(255 * (1 - i / len(p.trail)))  # Verblassender Effekt
                    if alpha > 0:
                        pygame.draw.circle(screen, (rc, gc, bc, alpha), (int(tx), int(ty)), radius)
        elif p.type == "electron":
            rc = 0
            gc = int(255 * cf)
            bc = int(255 * (1 - cf))
            radius = 4
            if p.trail:
                for i, (tx, ty) in enumerate(p.trail):
                    alpha = int(255 * (1 - i / len(p.trail)))  # Verblassender Effekt
                    if alpha > 0:
                        pygame.draw.circle(screen, (rc, gc, bc, alpha), (int(tx), int(ty)), radius)
        elif p.type == "magnetfoam":
            rc = 80
            gc = 220
            bc = 255
            radius = 5
            if p.trail:
                for i, (tx, ty) in enumerate(p.trail):
                    alpha = int(255 * (1 - i / len(p.trail)))  # Verblassender Effekt
                    if alpha > 0:
                        pygame.draw.circle(screen, (rc, gc, bc, alpha), (int(tx), int(ty)), radius)
        elif p.type == "electromagnetic_impulse":
            idx = int(p.lifetime / 150) % len(ELECTROMAGNETIC_IMPULSE_COLOR)
            rc, gc, bc = ELECTROMAGNETIC_IMPULSE_COLOR[idx]
            radius = 3
            if p.trail:
                for i, (tx, ty) in enumerate(p.trail):
                    alpha = int(255 * (1 - i / len(p.trail)))  # Verblassender Effekt
                    if alpha > 0:
                        pygame.draw.circle(screen, (rc, gc, bc, alpha), (int(tx), int(ty)), radius)
        pygame.draw.circle(screen, (rc, gc, bc), (int(p.x), int(p.y)), radius)

    # Zeichnen der Kollisionsmarkierungen
    for x, y, rad in collision_marks[:]:
        pygame.draw.circle(screen, YELLOW_COLOR, (int(x), int(y)), rad)
        collision_marks.remove((x, y, rad))

    # === Statistik-Anzeige ===
    pygame.draw.rect(screen, PANEL_BG, (0, SIM_HEIGHT, WIDTH, HEIGHT - SIM_HEIGHT))
    
    # Partikelzahlen
    text_y = SIM_HEIGHT + 40
    particle_types = [
        ("Foam", counts['foam'], FOAM_COLOR),
        ("Neutrino", counts['neutrino'], NEUTRINO_COLOR),
        ("Electron", counts['electron'], ELECTRON_COLOR),
        ("Magnet", counts['magnetfoam'], MAGNET_DIAG_COLOR),
        ("Impuls", counts['electromagnetic_impulse'], ELECTROMAGNETIC_IMPULSE_COLOR[0])
    ]
    
    title = font_large.render("PARTIKEL-STATISTIK", True, TEXT_COLOR)
    screen.blit(title, (40, text_y))
    text_y += 70
    
    for label, count, color in particle_types:
        label_surface = font_medium.render(f"{label}:", True, color)
        screen.blit(label_surface, (60, text_y))
        count_surface = font_medium.render(f"{count}", True, TEXT_COLOR)
        screen.blit(count_surface, (300, text_y))
        text_y += 70
        
    rule_text = font_medium.render(f"Max E + M + I: {MAX_PARTICLES_SUM}", True, TEXT_COLOR)
    screen.blit(rule_text, (60, text_y + 30))

    # Balkendiagramme für Partikelverteilung
    bar_start_y = SIM_HEIGHT + 400
    bar_height = 30
    bar_spacing = 10
    bar_width = 300
    max_count = max(1, max(counts.values()))
    
    # Partikelverteilung
    title = font_medium.render("Partikelverteilung", True, TEXT_COLOR)
    screen.blit(title, (60, bar_start_y))
    
    bar_y = bar_start_y + 50
    for ptype, color in [('foam', FOAM_COLOR), ('neutrino', NEUTRINO_COLOR), 
                         ('electron', ELECTRON_COLOR), ('magnetfoam', MAGNET_DIAG_COLOR),
                         ('electromagnetic_impulse', ELECTROMAGNETIC_IMPULSE_COLOR[0])]:
        count_val = counts.get(ptype, 0)
        ratio = count_val / max_count
        bar_fill_width = ratio * bar_width
        
        # Balken zeichnen
        pygame.draw.rect(screen, (50, 50, 70), (60, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, color, (60, bar_y, bar_fill_width, bar_height))
        
        # Textbeschriftung
        label = font_small.render(f"{ptype}: {count_val}", True, TEXT_COLOR)
        screen.blit(label, (70, bar_y + 5))
        
        bar_y += bar_height + bar_spacing
    
    # Fusion/Spaltung Verhältnis
    fusion_y = bar_y + 30
    title = font_medium.render("Fusion/Spaltung", True, TEXT_COLOR)
    screen.blit(title, (60, fusion_y))
    
    total_events = get_fusion_count() + get_fission_count()
    if total_events > 0:
        fusion_ratio = get_fusion_count() / total_events
        fission_ratio = get_fission_count() / total_events
    else:
        fusion_ratio = 0
        fission_ratio = 0
    
    # Fusion Balken
    fusion_bar_y = fusion_y + 50
    fusion_fill_width = fusion_ratio * bar_width
    pygame.draw.rect(screen, (50, 50, 70), (60, fusion_bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, FUSION_COLOR, (60, fusion_bar_y, fusion_fill_width, bar_height))
    fusion_text = font_small.render(f"Fusion: {get_fusion_count()} ({fusion_ratio*100:.1f}%)", True, TEXT_COLOR)
    screen.blit(fusion_text, (70, fusion_bar_y + 5))
    
    # Spaltung Balken
    fission_bar_y = fusion_bar_y + bar_height + bar_spacing
    fission_fill_width = fission_ratio * bar_width
    pygame.draw.rect(screen, (50, 50, 70), (60, fission_bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, FISSION_COLOR, (60, fission_bar_y, fission_fill_width, bar_height))
    fission_text = font_small.render(f"Spaltung: {get_fission_count()} ({fission_ratio*100:.1f}%)", True, TEXT_COLOR)
    screen.blit(fission_text, (70, fission_bar_y + 5))

    # Quadratisches Diagramm
    diagram_size = 600
    diagram_x = WIDTH - diagram_size - 40
    diagram_y = SIM_HEIGHT + 200
    diagram_rect = pygame.Rect(diagram_x, diagram_y, diagram_size, diagram_size)
    
    pygame.draw.rect(screen, BG_COLOR, diagram_rect)
    pygame.draw.rect(screen, TEXT_COLOR, diagram_rect, 2)
    
    title = font_large.render("PARTIKEL-ENTWICKLUNG", True, TEXT_COLOR)
    screen.blit(title, (diagram_x, diagram_y - 50))
    
    max_val = 1
    for values in history.values():
        if values:
            max_val = max(max_val, max(values))
    
    grid_color = (80, 80, 100)
    for i in range(1, 5):
        y_pos = diagram_y + diagram_size - i * diagram_size/4
        pygame.draw.line(screen, grid_color, (diagram_x, y_pos), (diagram_x + diagram_size, y_pos), 1)
        val = int(i * max_val / 4)
        grid_text = font_small.render(str(val), True, grid_color)
        screen.blit(grid_text, (diagram_x - 60, y_pos - 15))
    
    colors = {
        'foam': FOAM_COLOR,
        'neutrino': NEUTRINO_COLOR,
        'electron': ELECTRON_COLOR,
        'magnetfoam': MAGNET_DIAG_COLOR,
        'electromagnetic_impulse': ELECTROMAGNETIC_IMPULSE_COLOR[0]
    }
    
    legend_x = diagram_x + diagram_size - 200
    legend_y = diagram_y + 30
    
    for ptype, values in history.items():
        if len(values) < 2:
            continue
            
        points = []
        for i, value in enumerate(values):
            if max_val > 0:
                y_pos = diagram_y + diagram_size - (value / max_val) * diagram_size
            else:
                y_pos = diagram_y + diagram_size
                
            x_pos = diagram_x + (i / (len(values)-1)) * diagram_size
            points.append((x_pos, y_pos))
        
        if len(points) > 1:
            pygame.draw.lines(screen, colors[ptype], False, points, 3)
            
            pygame.draw.line(screen, colors[ptype], (legend_x, legend_y), (legend_x + 50, legend_y), 3)
            legend_text = font_small.render(ptype.replace('_', ' ').capitalize(), True, colors[ptype])
            screen.blit(legend_text, (legend_x + 60, legend_y - 12))
            legend_y += 35
    
    pygame.display.flip()

pygame.quit()