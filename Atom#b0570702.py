#!/usr/bin/env python3

# Mikado-Modell mit Magnetpunkt-Logik: Elektron wird am Rand zum Magnetpunkt, löst sich bei 5 Foams in 5 Neutrinos auf

import pygame
import random
import math
from dataclasses import dataclass, field

# +++ Einstellungen +++
WIDTH, HEIGHT    = 1024, 2048  # Höhere Auflösung für Smartphone
SIM_HEIGHT       = 1024        # Höhe des Simulationsbereichs
FPS              = 30

INIT_FOAM        = 512
INIT_NEUTRINO    = 0

# --- NEUE REGEL: Maximale Anzahl von Elektronen, Magneten und ElektroMagnetimpulsen ---
MAX_PARTICLES_SUM = 20  # Overall maximum for these specific particle types

FOAM_RADIAL      = 360/60
FOAM_TANG        = 3.0
FOAM_GRAVITY     = -0.25

NEUTRINO_SPEED   = 3.0
NEUTRINO_JIT     = 0.05

DRAIN_RADIUS     = 50
RIMZONEWIDTH     = 20
BOWL_MARGIN      = 50
FOAMTONEUTRINO_THRESHOLD = 5
NEUTRINOTOELECTRON_THRESHOLD = 5

MAGNET_SPREAD    = math.pi/1.1
MAGNET_ROTATION_SPEED = 0.03  # Geschwindigkeit der Magnetbewegung
MAGNET_RELEASE_PROB = 0.05    # Reduzierte Wahrscheinlichkeit, ein Foam freizugeben (für längere Lebensdauer)
MAGNET_REPULSION_FORCE = 0.1  # Stärke der Abstoßung zwischen Magneten
MAGNET_LIFETIME = 300         # Magnet remains active for some time steps (300 frames)
ELECTROMAGNETIC_IMPULSE_SPEED = 5.0 # Speed of the new electromagnetic impulse
ELECTROMAGNETIC_IMPULSE_JIT = 0.1 # Randomness in impulse movement due to quantum foam

BG_COLOR         = (11, 11, 30)
WALL_COLOR       = (200, 200, 200)
YELLOW_COLOR     = (255, 255, 0)
MAGNET_COLOR     = (80, 220, 255)
MAGNETLINECOLOR  = (80, 220, 255)

# Farben für Diagramme und Text
FOAM_COLOR       = (0, 200, 0)      # Grün
NEUTRINO_COLOR   = (200, 0, 200)    # Magenta
ELECTRON_COLOR   = (0, 200, 255)    # Cyan
MAGNET_DIAG_COLOR= (80, 220, 255)   # Hellblau
ELECTROMAGNETIC_IMPULSE_COLOR = [(255,0,0), (255,127,0), (255,255,0), (0,255,0), (0,0,255), (75,0,130), (148,0,211)] # Rainbow
TEXT_COLOR       = (255, 255, 255)
PANEL_BG         = (20, 20, 40)     # Dunkler Hintergrund für Statistik

@dataclass
class Particle:
    x: float
    y: float
    dx: float
    dy: float
    type: str    # "foam", "neutrino", "electron", "magnetfoam", "electromagnetic_impulse"
    angle: float = 0.0  # Für Magnetlinien und Impulse: Richtung
    trail: list = field(default_factory=list)
    trapped_foam: list = field(default_factory=list)  # Nur für magnet_foam: Liste der gefangenen Foam-IDs
    rotation_speed: float = MAGNET_ROTATION_SPEED  # Rotationsgeschwindigkeit für Magnete
    lifetime: int = 0  # Lebensdauer-Zähler für Magnete/Impulse
    initial_angle: float = 0.0 # Initial angle for electromagnetic impulse reflection

def spawn_foam(x, y):
    return Particle(x, y, 0, 0, "foam")

def spawn_electron(x, y, dx, dy):
    return Particle(x, y, dx, dy, "electron")

def spawn_neutrino(x, y, dx, dy):
    return Particle(x, y, dx, dy, "neutrino")

def spawn_magnetfoam(x, y, angle):
    return Particle(x, y, 0, 0, "magnetfoam", angle=angle, trapped_foam=[],
                   rotation_speed=MAGNET_ROTATION_SPEED, lifetime=MAGNET_LIFETIME)

def spawn_electromagnetic_impulse(x, y, angle):
    return Particle(x, y,
                    ELECTROMAGNETIC_IMPULSE_SPEED * math.cos(angle),
                    ELECTROMAGNETIC_IMPULSE_SPEED * math.sin(angle),
                    "electromagnetic_impulse", angle=angle, lifetime=1000, # Long lifetime
                    initial_angle=angle)

def dist(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)

# === Pygame Init ===
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Particle Simulation")
clock = pygame.time.Clock()
# Größere Schriftarten
font_large = pygame.font.SysFont('Arial', 40, bold=True)  # Große Schrift für Überschriften
font_medium = pygame.font.SysFont('Arial', 36, bold=True)  # Mittelgroß für Werte
font_small = pygame.font.SysFont('Arial', 24, bold=True)  # Klein für Legende

# Zentrum der Simulation (oberer Bereich)
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

# Für Diagramm und Statistiken
history = {'foam': [], 'neutrino': [], 'electron': [], 'magnetfoam': [], 'electromagnetic_impulse': []}
MAX_HISTORY = 100

running = True
while running:
    clock.tick(FPS)
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    # Hintergrund für den gesamten Bildschirm
    screen.fill(BG_COLOR)

    # Simulationsbereich (obere Hälfte)
    pygame.draw.rect(screen, BG_COLOR, (0, 0, WIDTH, SIM_HEIGHT))
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), int(bowl_r), 3)
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), DRAIN_RADIUS, 2)

    new_list = []
    collision_marks = []

    # Zähle Partikel für Statistik
    counts = {'foam': 0, 'neutrino': 0, 'electron': 0, 'magnetfoam': 0, 'electromagnetic_impulse': 0}
    for p in particles:
        if p.type in counts:
            counts[p.type] += 1

    # Finde alle Magnete für Abstoßungsberechnung
    all_magnets = [p for p in particles if p.type == "magnetfoam"]
    
    # Check current counts for the new rule
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

            if p.trail is not None:
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

            # Fusion im Zentrum
            if r <= DRAIN_RADIUS:
                foam_fusion_buffer.append(p)
                if len(foam_fusion_buffer) >= FOAMTONEUTRINO_THRESHOLD:
                    last = foam_fusion_buffer[-1]
                    new_list.append(spawn_neutrino(last.x, last.y, last.dx, last.dy))
                    foam_fusion_buffer.clear()
                continue

            # Am Rand: Magnetpunkt-Fang-Logik
            if magnet_foams:
                nearest = min(magnet_foams, key=lambda m: dist(p.x, p.y, m.x, m.y))
                d_to_magnet = dist(p.x, p.y, nearest.x, nearest.y)
                if d_to_magnet < 8 and abs(r - bowl_r) < 8:
                    if nearest.trapped_foam is not None and id(p) not in nearest.trapped_foam:
                        nearest.trapped_foam.append(id(p))
                        # Foam bleibt am Magnetpunkt "kleben"
                        p.x = nearest.x
                        p.y = nearest.y
                        p.dx = 0
                        p.dy = 0
                        continue

            # Reflexion am Rand
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

            if p.trail is not None:
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

            if p.trail is not None:
                p.trail.append((p.x, p.y))
                if len(p.trail) > 10:
                    p.trail.pop(0)

            if r >= bowl_r:
                # --- NEUE REGEL: Max Anzahl check for Electron to Magnetfoam ---
                if current_special_particles < MAX_PARTICLES_SUM:
                    angle = math.atan2(p.y - cy, p.x - cx)
                    mx = cx + math.cos(angle) * bowl_r
                    my = cy + math.sin(angle) * bowl_r
                    new_list.append(spawn_magnetfoam(mx, my, angle))
                    current_special_particles += 1 # Increment count immediately
                continue # Electron is consumed at the rim

            new_list.append(p)

        elif p.type == "magnetfoam":
            p.lifetime -= 1

            # Bewege den Magneten entlang der Atomhülle
            p.angle += p.rotation_speed

            # Neue Position auf dem Rand berechnen
            new_x = cx + bowl_r * math.cos(p.angle)
            new_y = cy + bowl_r * math.sin(p.angle)

            # Abstoßung von anderen Magneten berechnen
            repulsion_dx, repulsion_dy = 0, 0
            for other in all_magnets:
                if other != p:
                    d = dist(p.x, p.y, other.x, other.y)
                    if d < 100:  # Nur bei ausreichender Nähe abstoßen
                        force = MAGNET_REPULSION_FORCE / (d * d + 0.1)
                        angle = math.atan2(p.y - other.y, p.x - other.x)
                        repulsion_dx += math.cos(angle) * force
                        repulsion_dy += math.sin(angle) * force

            # Winkel anpassen basierend auf Abstoßung
            if repulsion_dx != 0 or repulsion_dy != 0:
                repulsion_angle = math.atan2(repulsion_dy, repulsion_dx)
                # Drehrichtung umkehren wenn nötig für natürlichere Bewegung
                p.rotation_speed = abs(p.rotation_speed) * (1 if repulsion_angle > p.angle else -1)

            # Endgültige Position setzen
            p.x = new_x
            p.y = new_y

            # Aktualisiere Position der gefangenen Foams
            for foam_id in p.trapped_foam[:]:
                # Find the actual foam particle to update its position
                found_foam = False
                for foam in new_list: # Search in new_list, as foam particles might have been moved there already
                    if id(foam) == foam_id and foam.type == "foam":
                        foam.x = p.x
                        foam.y = p.y
                        foam.dx = 0 # Ensure it stays put
                        foam.dy = 0 # Ensure it stays put
                        found_foam = True
                        break
                if not found_foam: # If foam somehow disappeared, remove its ID from trapped list
                    p.trapped_foam.remove(foam_id)

            # Gelegentlich ein Foam freigeben (nur wenn Lebensdauer noch nicht abgelaufen)
            if p.trapped_foam and p.lifetime > 0 and random.random() < MAGNET_RELEASE_PROB:
                # Entferne ein zufälliges Foam aus der Falle
                foam_id = random.choice(p.trapped_foam)
                p.trapped_foam.remove(foam_id)

                # Finde das entsprechende Foam-Partikel
                for foam in new_list:
                    if id(foam) == foam_id and foam.type == "foam":
                        # Gib dem Foam eine zufällige Geschwindigkeit nach innen
                        angle = math.atan2(cy - foam.y, cx - foam.x)
                        speed = random.uniform(1.0, 3.0)
                        foam.dx = math.cos(angle) * speed
                        foam.dy = math.sin(angle) * speed
                        break

            # --- NEUE REGEL: Zerfall des Magneten in einen elektromagnetischen Impuls ---
            if p.lifetime <= 0:
                if current_special_particles < MAX_PARTICLES_SUM:
                    # Transformiere in einen elektromagnetischen Impuls
                    new_list.append(spawn_electromagnetic_impulse(p.x, p.y, p.angle + math.pi)) # Impulse moves inwards
                    current_special_particles += 1
                # Magnet wird nicht wieder hinzugefügt
            else:
                new_list.append(p)
                
        elif p.type == "electromagnetic_impulse":
            p.lifetime -= 1
            
            # Bewegung
            p.x += p.dx
            p.y += p.dy
            
            # Vom Quantenschaum abgelenkt werden
            p.dx += random.uniform(-ELECTROMAGNETIC_IMPULSE_JIT, ELECTROMAGNETIC_IMPULSE_JIT)
            p.dy += random.uniform(-ELECTROMAGNETIC_IMPULSE_JIT, ELECTROMAGNETIC_IMPULSE_JIT)

            current_r = dist(p.x, p.y, cx, cy)

            # Reflexion an der Außenhülle (bowl_r)
            if current_r >= bowl_r:
                if current_r != 0:
                    nxr, nyr = (p.x - cx) / current_r, (p.y - cy) / current_r
                else:
                    nxr, nyr = 0, 0
                vdotn = p.dx * nxr + p.dy * nyr
                p.dx -= 2 * vdotn * nxr
                p.dy -= 2 * vdotn * nyr
                p.x = cx + nxr * (bowl_r - 1) # Reposition slightly inside
                p.y = cy + nyr * (bowl_r - 1)
                
                # Adjust angle for trail
                p.angle = math.atan2(p.dy, p.dx)


            # Reflexion am Drain (DRAIN_RADIUS)
            elif current_r <= DRAIN_RADIUS:
                if current_r != 0:
                    nxr, nyr = (p.x - cx) / current_r, (p.y - cy) / current_r
                else:
                    nxr, nyr = 0, 0
                vdotn = p.dx * nxr + p.dy * nyr
                p.dx -= 2 * vdotn * nxr
                p.dy -= 2 * vdotn * nyr
                p.x = cx + nxr * (DRAIN_RADIUS + 1) # Reposition slightly outside
                p.y = cy + nyr * (DRAIN_RADIUS + 1)
                
                # Adjust angle for trail
                p.angle = math.atan2(p.dy, p.dx)

            if p.trail is not None:
                p.trail.append((p.x, p.y))
                if len(p.trail) > 20: # Longer trail for visual effect
                    p.trail.pop(0)
            
            # --- NEUE REGEL: Impulse verschwinden, wenn Lebensdauer abgelaufen ---
            if p.lifetime > 0:
                new_list.append(p)


    # --- 2. Neutrino→Elektron-Fusion im Drain ---
    drain_neutrinos = [p for p in new_list if p.type == "neutrino" and dist(p.x, p.y, cx, cy) <= DRAIN_RADIUS]
    used = set()
    i = 0
    while i < len(drain_neutrinos):
        if i in used:
            i += 1
            continue
        p = drain_neutrinos[i]
        cluster = [q for q in drain_neutrinos if dist(p.x, p.y, q.x, q.y) < 7 and drain_neutrinos.index(q) not in used]
        if len(cluster) >= NEUTRINOTOELECTRON_THRESHOLD:
            # --- NEUE REGEL: Max Anzahl check for Neutrino to Electron ---
            if current_special_particles < MAX_PARTICLES_SUM:
                mx = sum(q.x for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]) / NEUTRINOTOELECTRON_THRESHOLD
                my = sum(q.y for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]) / NEUTRINOTOELECTRON_THRESHOLD
                mdx = sum(q.dx for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]) / NEUTRINOTOELECTRON_THRESHOLD
                mdy = sum(q.dy for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]) / NEUTRINOTOELECTRON_THRESHOLD
                remove_ids = set(id(q) for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD])
                new_list = [part for part in new_list if not (part.type == "neutrino" and id(part) in remove_ids)]
                used |= set(drain_neutrinos.index(q) for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD])
                new_list.append(spawn_electron(mx, my, mdx, mdy))
                current_special_particles += 1 # Increment count immediately
        i += 1

    # Aktualisiere Partikelzähler nach allen Spawns/removals
    counts = {'foam': 0, 'neutrino': 0, 'electron': 0, 'magnetfoam': 0, 'electromagnetic_impulse': 0}
    for p in new_list:
        if p.type in counts:
            counts[p.type] += 1
    
    # Füge Werte zur Historie hinzu
    for key in history:
        history[key].append(counts[key])
        if len(history[key]) > MAX_HISTORY:
            history[key] = history[key][-MAX_HISTORY:]

    # Zeichne Partikel
    for p in new_list:
        r = dist(p.x, p.y, cx, cy)
        cf = min(1.0, max(0.0, r / bowl_r))
        
        radius = 0 # Default to 0, overridden by type
        color = (0,0,0) # Default color, overridden by type

        if p.type == "foam":
            rc = int(255 * cf)
            gc = int(255 * (1 - cf) * 0.5)
            bc = int(255 * (1 - cf))
            radius = 3
            color = (rc, gc, bc)
        elif p.type == "neutrino":
            rc = int(255 * cf)
            gc = 0
            bc = int(255 * (1 - cf))
            radius = 2
            color = (rc, gc, bc)
        elif p.type == "electron":
            rc = 0
            gc = 220
            bc = 255
            radius = 7
            color = (rc, gc, bc)
        elif p.type == "magnetfoam":
            # Größe basierend auf Anzahl gefangener Foams und Lebensdauer
            size_factor = min(len(p.trapped_foam), 10)
            lifetime_factor = min(p.lifetime / MAGNET_LIFETIME, 1.0) # Normalisiert auf 0-1
            radius = 7 + size_factor * lifetime_factor
            # Farbe wird mit Lebensdauer schwächer
            rc = int(80 * lifetime_factor)
            gc = int(220 * lifetime_factor)
            bc = int(255 * lifetime_factor)
            color = (rc, gc, bc)
        elif p.type == "electromagnetic_impulse":
            radius = 5
            # Regenbogenfarben basierend auf Zeit oder Position
            color_index = int((pygame.time.get_ticks() / 100) % len(ELECTROMAGNETIC_IMPULSE_COLOR))
            color = ELECTROMAGNETIC_IMPULSE_COLOR[color_index]
        else:
            color = (255, 255, 255) # Default white
            radius = 2

        if p.trail:
            for i, (tx, ty) in enumerate(p.trail):
                alpha = int(255 * (1 - i / len(p.trail)))
                if alpha > 0:
                    trail_color = list(color) # Copy color to modify alpha
                    if len(trail_color) == 3: # Add alpha if not present
                        trail_color.append(alpha)
                    pygame.draw.circle(screen, tuple(trail_color), (int(tx), int(ty)), radius)
        pygame.draw.circle(screen, color, (int(p.x), int(p.y)), radius)

    for x, y, rad in collision_marks[:]:
        pygame.draw.circle(screen, YELLOW_COLOR, (int(x), int(y)), rad)
        collision_marks.remove((x, y, rad))

    particles = new_list

    # === Statistik-Anzeige (unterer Bereich) ===
    # Hintergrund für Statistikbereich
    pygame.draw.rect(screen, PANEL_BG, (0, SIM_HEIGHT, WIDTH, HEIGHT - SIM_HEIGHT))

    # Partikelzahlen anzeigen (links)
    text_y = SIM_HEIGHT + 40
    particle_types = [
        ("Foam", counts['foam'], FOAM_COLOR),
        ("Neutrino", counts['neutrino'], NEUTRINO_COLOR),
        ("Electron", counts['electron'], ELECTRON_COLOR),
        ("Magnet", counts['magnetfoam'], MAGNET_DIAG_COLOR),
        ("Impuls", counts['electromagnetic_impulse'], ELECTROMAGNETIC_IMPULSE_COLOR[0]) # Use first rainbow color for legend
    ]

    # Zeichne Titel
    title = font_large.render("PARTIKEL-STATISTIK", True, TEXT_COLOR)
    screen.blit(title, (40, text_y))
    text_y += 70

    # Zeichne Partikelzahlen in einer Tabelle (mit größerer Schrift)
    for label, count, color in particle_types:
        # Beschriftung
        label_surface = font_medium.render(f"{label}:", True, color)
        screen.blit(label_surface, (60, text_y))

        # Wert
        count_surface = font_medium.render(f"{count}", True, TEXT_COLOR)
        screen.blit(count_surface, (300, text_y))

        text_y += 70
        
    # Display the MAX_PARTICLES_SUM rule
    rule_text = font_medium.render(f"Max E + M + I: {MAX_PARTICLES_SUM}", True, TEXT_COLOR)
    screen.blit(rule_text, (60, text_y + 30))


    # Quadratisches Diagramm zeichnen (rechts ausgerichtet)
    diagram_size = 600
    diagram_x = WIDTH - diagram_size - 40  # 40px Abstand vom rechten Rand
    diagram_y = SIM_HEIGHT + 200
    diagram_rect = pygame.Rect(diagram_x, diagram_y, diagram_size, diagram_size)

    # Diagramm-Hintergrund
    pygame.draw.rect(screen, BG_COLOR, diagram_rect)
    pygame.draw.rect(screen, TEXT_COLOR, diagram_rect, 2)

    # Diagramm-Titel
    title = font_large.render("PARTIKEL-ENTWICKLUNG", True, TEXT_COLOR)
    screen.blit(title, (diagram_x, diagram_y - 50))

    # Finde den maximalen Wert für die Skalierung
    max_val = 1
    for values in history.values():
        if values:
            max_val = max(max_val, max(values))

    # Zeichne Gitternetz
    grid_color = (80, 80, 100)
    for i in range(1, 5):
        y_pos = diagram_y + diagram_size - i * diagram_size/4
        pygame.draw.line(screen, grid_color,
                         (diagram_x, y_pos),
                         (diagram_x + diagram_size, y_pos), 1)
        val = int(i * max_val / 4)
        grid_text = font_small.render(str(val), True, grid_color)
        screen.blit(grid_text, (diagram_x - 60, y_pos - 15))

    # Zeichne Partikelkurven
    colors = {
        'foam': FOAM_COLOR,
        'neutrino': NEUTRINO_COLOR,
        'electron': ELECTRON_COLOR,
        'magnetfoam': MAGNET_DIAG_COLOR,
        'electromagnetic_impulse': ELECTROMAGNETIC_IMPULSE_COLOR[0] # Use first rainbow color for graph
    }

    # Legende oben rechts im Diagramm
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

            # Zeichne Legende (rechts oben im Diagramm)
            pygame.draw.line(screen, colors[ptype],
                            (legend_x, legend_y),
                            (legend_x + 50, legend_y), 3)
            legend_text = font_small.render(ptype.replace('_', ' ').capitalize(), True, colors[ptype])
            screen.blit(legend_text, (legend_x + 60, legend_y - 12))
            legend_y += 35

    pygame.display.flip()

pygame.quit()
