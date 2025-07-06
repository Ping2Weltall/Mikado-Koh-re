#!/usr/bin/env python3

import pygame
import random
import math
from dataclasses import dataclass, field
import colorsys

# Konfiguration
WIDTH, HEIGHT = 1024, 2048
SIM_HEIGHT = 1024
FPS = 30

INIT_FOAM = 1024
INIT_NEUTRINO = 0
MAX_PARTICLES_SUM = 20

FOAM_RADIAL = 360/60
FOAM_TANG = 3.0
FOAM_GRAVITY = -0.25

NEUTRINO_SPEED = 3.0
NEUTRINO_JIT = 0.05
NEUTRINO_OUTER_FOAM_CONVERSION_FACTOR = 3 # 1 outer foam to 3 inner foam

DRAIN_RADIUS = 50
RIMZONEWIDTH = 20
BOWL_MARGIN = 50
FOAMTONEUTRINO_THRESHOLD = 5
NEUTRINOTOELECTRON_THRESHOLD = 5

MAGNET_SPREAD = math.pi/1.1
MAGNET_ROTATION_SPEED = 0.03
MAGNET_RELEASE_PROB = 0.05
MAGNET_REPULSION_FORCE = 0.1
MAGNET_LIFETIME = 60
ELECTROMAGNETIC_IMPULSE_SPEED = 5.0
ELECTROMAGNETIC_IMPULSE_JIT = 0.1
IMPULSE_INITIAL_PHOTONS = 10
MAX_IMPULSE_TRAIL_LENGTH = 20
IMPULSE_OUTER_FOAM_CONVERSION_FACTOR = 3 # 1 outer foam to 3 inner foam

MAGNET_LIFETIME_DECAY_SOLO_FACTOR = 2.0
MAGNET_LIFETIME_STABLE_BONUS = 5
FOAM_ATTRACTION_TO_MAGNET_LINE_STRENGTH = 0.05

SINGLE_MAGNET_ATTRACTION_TO_LINE_FACTOR = 0.15
SINGLE_MAGNET_ALONG_LINE_STRENGTH = 2.0

NUM_MAGNETS_TO_SIDES = {0: 0, 1: 0, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8}
MAX_POLYGON_SIDES = 8

FOAM_ATTRACTION_TO_GUIDELINE_STRENGTH = 0.02
DRAIN_IMPULSE_SPEED_FACTOR = 0.3
DRAIN_IMPULSE_TRAIL_LENGTH_FACTOR = 2
PHOTON_RELEASE_SPEED = 7.0
ATOM_SIZE_FACTOR = 0.8
OUTER_FOAM_SPAWN_INTERVAL = FPS * 1
OUTER_FOAM_SPAWN_AMOUNT = 15
OUTER_FOAM_SPEED = 2.5
OUTER_FOAM_ATTRACTION_TO_MAGNET_STRENGTH = 0.08
FOAM_TO_POSITRON_THRESHOLD = 10
POSITRON_SPEED = 5.0
POSITRON_REPULSION_FORCE = 0.8
POSITRON_ATTRACTION_TO_DRAIN_STRENGTH = 0.1
POSITRON_ATTRACTION_TO_GUIDELINE_STRENGTH = 0.05
ELECTRON_POSITRON_ATTRACTION_STRENGTH = 0.15 # New: Attraction strength between electron and positron

# Farben
BG_COLOR = (11, 11, 30)
WALL_COLOR = (200, 200, 200)
YELLOW_COLOR = (255, 255, 0)
MAGNET_COLOR = (80, 220, 255)
MAGNETLINECOLOR = (80, 220, 255)
GUIDELINE_COLOR = (150, 150, 150)
FOAM_COLOR = (0, 200, 0)
NEUTRINO_COLOR = (200, 0, 200)
ELECTRON_COLOR = (0, 200, 255)
MAGNET_DIAG_COLOR = (80, 220, 255)
IMPULSE_INITIAL_HUE = 0.66
IMPULSE_FINAL_HUE = 0.0
DRAIN_REDSHIFT_HUE = 0.05
OUTER_FOAM_COLOR = (50, 255, 50)
POSITRON_COLOR = (255, 0, 255)
NEUTRON_COLOR = (150, 150, 150)
TEXT_COLOR = (255, 255, 255)
PANEL_BG = (20, 20, 40)
IDEAL_FORM_COLOR = (100, 100, 100)

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
    trapped_outer_foam: list = field(default_factory=list)
    rotation_speed: float = MAGNET_ROTATION_SPEED
    lifetime: int = 0
    initial_angle: float = 0.0
    contained_photons: int = 0
    color_hue: float = IMPULSE_INITIAL_HUE
    original_dx: float = 0.0
    original_dy: float = 0.0
    is_in_drain: bool = False
    current_trail_length: int = 10
    max_photons_at_spawn: int = 0
    is_stuck_to_drain: bool = False
    contained_outer_foam: int = 0
    neutron_foam_content: int = 0
    # New: Flag for impulse reflected from drain
    reflected_from_drain: bool = False 

def spawn_foam(x, y):
    return Particle(x, y, 0, 0, "foam", current_trail_length=5)

def spawn_electron(x, y, dx, dy):
    return Particle(x, y, dx, dy, "electron", current_trail_length=10)

def spawn_neutrino(x, y, dx, dy):
    return Particle(x, y, dx, dy, "neutrino", current_trail_length=8)

def spawn_magnetfoam(x, y, angle):
    return Particle(x, y, 0, 0, "magnetfoam", angle=angle, lifetime=MAGNET_LIFETIME, current_trail_length=15)

def spawn_electromagnetic_impulse(x, y, angle, bonus_photons=0, reflected_from_drain=False):
    initial_total_photons = IMPULSE_INITIAL_PHOTONS + bonus_photons
    return Particle(x, y, ELECTROMAGNETIC_IMPULSE_SPEED * math.cos(angle),
                    ELECTROMAGNETIC_IMPULSE_SPEED * math.sin(angle), "electromagnetic_impulse",
                    angle=angle, contained_photons=initial_total_photons, current_trail_length=MAX_IMPULSE_TRAIL_LENGTH,
                    max_photons_at_spawn=initial_total_photons, reflected_from_drain=reflected_from_drain)

def spawn_photon(x, y, dx, dy):
    return Particle(x, y, dx, dy, "photon", current_trail_length=5)

def spawn_outer_foam_randomly(cx, cy, bowl_r, sim_max_r):
    angle = random.uniform(0, 2 * math.pi)
    r = random.uniform(bowl_r + 5, sim_max_r - BOWL_MARGIN)
    x = cx + r * math.cos(angle)
    y = cy + r * math.sin(angle)
    return Particle(x, y, 0, 0, "outer_foam", current_trail_length=5)

def spawn_positron(x, y, dx, dy, contained_outer_foam=0):
    return Particle(x, y, dx, dy, "positron", current_trail_length=10, contained_outer_foam=contained_outer_foam)

def spawn_neutron(x, y, dx, dy, foam_content):
    return Particle(x, y, dx, dy, "neutron", neutron_foam_content=foam_content, current_trail_length=15)

def dist(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)

def hsv2rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r*255), int(g*255), int(b*255)

def closest_point_on_segment(px, py, ax, ay, bx, by):
    ab_x, ab_y = bx - ax, by - ay
    ap_x, ap_y = px - ax, py - ay
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

def draw_simulation(screen, particles, cx, cy, bowl_r, magnet_ideal_polygon_points, actual_magnet_positions, sides_for_polygon, num_magnets, collision_marks):
    pygame.draw.rect(screen, BG_COLOR, (0, 0, WIDTH, SIM_HEIGHT))
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), int(bowl_r), 3)
    pygame.draw.circle(screen, WALL_COLOR, (int(cx), int(cy)), DRAIN_RADIUS, 2)
    
    if num_magnets > 0:
        for magnet_pos in actual_magnet_positions:
            pygame.draw.line(screen, GUIDELINE_COLOR, magnet_pos, (cx, cy), 1)

    for p in particles:
        if p.type is None:
            continue
        r = dist(p.x, p.y, cx, cy)
        color, radius = (255, 255, 255), 2 # Default values

        if p.type == "foam":
            cf = min(1.0, max(0.0, r / bowl_r))
            color = (int(255 * cf), int(255 * (1 - cf) * 0.5), int(255 * (1 - cf)))
            radius = 3
        elif p.type == "neutrino":
            cf = min(1.0, max(0.0, r / bowl_r))
            color = (int(255 * cf), 0, int(255 * (1 - cf)))
            radius = 2
        elif p.type == "electron":
            color = ELECTRON_COLOR
            radius = 7
        elif p.type == "magnetfoam":
            size_factor = min(len(p.trapped_foam) + len(p.trapped_outer_foam), 10)
            lifetime_factor = min(p.lifetime / MAGNET_LIFETIME, 1.0)
            radius = 7 + size_factor * lifetime_factor
            color = (int(80 * lifetime_factor), int(220 * lifetime_factor), int(255 * lifetime_factor))
        elif p.type == "electromagnetic_impulse":
            radius = 5
            color = hsv2rgb(DRAIN_REDSHIFT_HUE if p.is_in_drain else p.color_hue, 1.0, 1.0)
        elif p.type == "photon":
            color = FOAM_COLOR
            radius = 3
        elif p.type == "outer_foam":
            color = OUTER_FOAM_COLOR
            radius = 4
        elif p.type == "positron":
            color = POSITRON_COLOR
            radius = 6
        elif p.type == "neutron":
            color = NEUTRON_COLOR
            radius = 8

        if p.trail:
            trail_length = p.current_trail_length
            if p.type == "electromagnetic_impulse" and p.is_in_drain:
                trail_length = int(trail_length * DRAIN_IMPULSE_TRAIL_LENGTH_FACTOR)
            trail_length = max(0, trail_length)
            for i in range(max(0, len(p.trail) - trail_length), len(p.trail)):
                tx, ty = p.trail[i]
                alpha = int(255 * ((i - (len(p.trail) - trail_length)) / trail_length))
                if alpha > 0:
                    pygame.draw.circle(screen, (*color, alpha), (int(tx), int(ty)), radius)
        
        pygame.draw.circle(screen, color, (int(p.x), int(p.y)), radius)

    for x, y, rad in collision_marks:
        pygame.draw.circle(screen, YELLOW_COLOR, (int(x), int(y)), rad)

    if num_magnets > 1:
        if sides_for_polygon >= 3:
            pygame.draw.lines(screen, MAGNETLINECOLOR, True, actual_magnet_positions, 2)
        elif sides_for_polygon == 2 and len(actual_magnet_positions) == 2:
            pygame.draw.line(screen, MAGNETLINECOLOR, actual_magnet_positions[0], actual_magnet_positions[1], 2)

def draw_statistics(screen, history, counts, sides_for_polygon, current_polygon_angle_offset, SIM_HEIGHT, fonts):
    pygame.draw.rect(screen, PANEL_BG, (0, SIM_HEIGHT, WIDTH, HEIGHT - SIM_HEIGHT))
    text_y = SIM_HEIGHT + 40
    screen.blit(fonts['large'].render("PARTIKEL-STATISTIK", True, TEXT_COLOR), (40, text_y))
    text_y += 70

    particle_types = [
        ("Foam", counts['foam'], FOAM_COLOR),
        ("Neutrino", counts['neutrino'], NEUTRINO_COLOR),
        ("Electron", counts['electron'], ELECTRON_COLOR),
        ("Magnet", counts['magnetfoam'], MAGNET_DIAG_COLOR),
        ("Impuls", counts['electromagnetic_impulse'], hsv2rgb(IMPULSE_INITIAL_HUE, 1.0, 1.0)),
        ("Photon", counts['photon'], FOAM_COLOR),
        ("Quantenschaum", counts['outer_foam'], OUTER_FOAM_COLOR),
        ("Positron", counts['positron'], POSITRON_COLOR),
        ("Neutron", counts['neutron'], NEUTRON_COLOR)
    ]

    for label, count, color in particle_types:
        screen.blit(fonts['medium'].render(f"{label}:", True, color), (60, text_y))
        screen.blit(fonts['medium'].render(f"{count}", True, TEXT_COLOR), (300, text_y))
        text_y += 70
        
    screen.blit(fonts['medium'].render(f"Max E + M + I: {MAX_PARTICLES_SUM}", True, TEXT_COLOR), (60, text_y + 30))

    ideal_form_display_center = (WIDTH - 200, SIM_HEIGHT + 100)
    ideal_form_display_radius = 60
    if sides_for_polygon > 1:
        ideal_form_points = get_polygon_points(ideal_form_display_center, sides_for_polygon, ideal_form_display_radius, current_polygon_angle_offset)
        if sides_for_polygon >= 3:
            pygame.draw.polygon(screen, IDEAL_FORM_COLOR, ideal_form_points, 2)
        elif sides_for_polygon == 2:
            pygame.draw.line(screen, IDEAL_FORM_COLOR, ideal_form_points[0], ideal_form_points[1], 2)
    screen.blit(fonts['medium'].render("Idealform:", True, TEXT_COLOR), (ideal_form_display_center[0] - 100, ideal_form_display_center[1] - ideal_form_display_radius - 40))

    diagram_size = 600
    diagram_x, diagram_y = WIDTH - diagram_size - 40, SIM_HEIGHT + 200
    diagram_rect = pygame.Rect(diagram_x, diagram_y, diagram_size, diagram_size)
    pygame.draw.rect(screen, BG_COLOR, diagram_rect)
    pygame.draw.rect(screen, TEXT_COLOR, diagram_rect, 2)
    screen.blit(fonts['large'].render("PARTIKEL-ENTWICKLUNG", True, TEXT_COLOR), (diagram_x, diagram_y - 50))

    max_val = max(1, max(max(values) for values in history.values() if values))
    grid_color = (80, 80, 100)
    for i in range(1, 5):
        y_pos = diagram_y + diagram_size - i * diagram_size/4
        pygame.draw.line(screen, grid_color, (diagram_x, y_pos), (diagram_x + diagram_size, y_pos), 1)
        screen.blit(fonts['small'].render(str(int(i * max_val / 4)), True, grid_color), (diagram_x - 60, y_pos - 15))

    colors = {'foam': FOAM_COLOR, 'neutrino': NEUTRINO_COLOR, 'electron': ELECTRON_COLOR, 'magnetfoam': MAGNET_DIAG_COLOR,
              'electromagnetic_impulse': hsv2rgb(IMPULSE_INITIAL_HUE, 1.0, 1.0), 'photon': FOAM_COLOR, 'outer_foam': OUTER_FOAM_COLOR,
              'positron': POSITRON_COLOR, 'neutron': NEUTRON_COLOR}

    legend_x, legend_y = diagram_x + diagram_size - 200, diagram_y + 30
    for ptype, values in history.items():
        if len(values) < 2:
            continue
        points = [(diagram_x + (i / (len(values)-1)) * diagram_size, diagram_y + diagram_size - (value / max_val) * diagram_size) for i, value in enumerate(values)]
        if len(points) > 1:
            pygame.draw.lines(screen, colors[ptype], False, points, 3)
            pygame.draw.line(screen, colors[ptype], (legend_x, legend_y), (legend_x + 50, legend_y), 3)
            screen.blit(fonts['small'].render(ptype.replace('_', ' ').capitalize(), True, colors[ptype]), (legend_x + 60, legend_y - 12))
            legend_y += 35

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Particle Simulation")
    clock = pygame.time.Clock()

    fonts = {'large': pygame.font.SysFont('Arial', 40, bold=True), 'medium': pygame.font.SysFont('Arial', 36, bold=True), 'small': pygame.font.SysFont('Arial', 24, bold=True)}

    cx, cy = WIDTH / 2, SIM_HEIGHT / 2
    bowl_r = (min(WIDTH, SIM_HEIGHT) / 2 - BOWL_MARGIN) * ATOM_SIZE_FACTOR
    rim_inner = bowl_r - RIMZONEWIDTH

    particles = []
    history = {ptype: [] for ptype in ['foam', 'neutrino', 'electron', 'magnetfoam', 'electromagnetic_impulse', 'photon', 'outer_foam', 'positron', 'neutron']}
    MAX_HISTORY = 100

    for _ in range(INIT_FOAM):
        ang = random.uniform(0, 2 * math.pi)
        r = random.uniform(DRAIN_RADIUS, bowl_r)
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
        particles.append(spawn_foam(x, y))

    for _ in range(INIT_NEUTRINO):
        ang = random.uniform(0, 2 * math.pi)
        r = random.uniform(rim_inner, bowl_r)
        x, y = cx + r * math.cos(ang), cy + math.sin(ang)
        dx, dy = NEUTRINO_SPEED * math.cos(ang), NEUTRINO_SPEED * math.sin(ang)
        particles.append(spawn_neutrino(x, y, dx, dy))

    foam_fusion_buffer = []
    running = True

    while running:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False

        counts = {ptype: sum(1 for p in particles if p.type == ptype) for ptype in history}
        all_magnets_current_frame = [p for p in particles if p.type == "magnetfoam"]
        num_magnets_current_frame = len(all_magnets_current_frame)
        current_special_particles = counts['electron'] + counts['magnetfoam'] + counts['electromagnetic_impulse'] + counts['positron'] + counts['neutron']

        sides_for_polygon_current_frame = NUM_MAGNETS_TO_SIDES.get(min(num_magnets_current_frame, MAX_POLYGON_SIDES), 0)
        current_polygon_angle_offset = pygame.time.get_ticks() / 1000.0 * MAGNET_ROTATION_SPEED
        magnet_ideal_polygon_points = get_polygon_points((cx, cy), sides_for_polygon_current_frame, bowl_r, current_polygon_angle_offset) if num_magnets_current_frame > 1 and sides_for_polygon_current_frame > 1 else []

        next_particles, ids_to_remove, collision_marks = [], set(), []

        if pygame.time.get_ticks() % OUTER_FOAM_SPAWN_INTERVAL == 0:
            for _ in range(OUTER_FOAM_SPAWN_AMOUNT):
                next_particles.append(spawn_outer_foam_randomly(cx, cy, bowl_r, min(WIDTH, SIM_HEIGHT) / 2))

        # Separate lists for particles that might attract each other
        electrons = [p for p in particles if p.type == "electron" and id(p) not in ids_to_remove]
        positrons = [p for p in particles if p.type == "positron" and id(p) not in ids_to_remove]

        for p in particles:
            if id(p) in ids_to_remove:
                continue
            r = dist(p.x, p.y, cx, cy)

            # --- Electron-Positron Attraction (Point 3) ---
            if p.type == "electron":
                for pos in positrons:
                    if pos != p and id(pos) not in ids_to_remove:
                        d = dist(p.x, p.y, pos.x, pos.y)
                        if d > 0:
                            # Apply attraction force
                            force = ELECTRON_POSITRON_ATTRACTION_STRENGTH / (d + 0.1) # Add 0.1 to prevent division by zero
                            angle_to_pos = math.atan2(pos.y - p.y, pos.x - p.x)
                            p.dx += math.cos(angle_to_pos) * force
                            p.dy += math.sin(angle_to_pos) * force
            elif p.type == "positron":
                for e in electrons:
                    if e != p and id(e) not in ids_to_remove:
                        d = dist(p.x, p.y, e.x, e.y)
                        if d > 0:
                            # Apply attraction force
                            force = ELECTRON_POSITRON_ATTRACTION_STRENGTH / (d + 0.1)
                            angle_to_electron = math.atan2(e.y - p.y, e.x - p.x)
                            p.dx += math.cos(angle_to_electron) * force
                            p.dy += math.sin(angle_to_electron) * force


            if p.type == "foam":
                foam_radial_factor, foam_tang_factor, magnet_attraction_dx, magnet_attraction_dy = 1.0, 1.0, 0, 0

                if num_magnets_current_frame > 1 and magnet_ideal_polygon_points:
                    min_dist_sq, closest_pt_on_line = float('inf'), None
                    for i in range(len(magnet_ideal_polygon_points)):
                        p1, p2 = magnet_ideal_polygon_points[i], magnet_ideal_polygon_points[(i + 1) % len(magnet_ideal_polygon_points)]
                        cx_seg, cy_seg, dist_sq = closest_point_on_segment(p.x, p.y, p1[0], p1[1], p2[0], p2[1])
                        if dist_sq < min_dist_sq:
                            min_dist_sq, closest_pt_on_line = dist_sq, (cx_seg, cy_seg)
                    if closest_pt_on_line:
                        attraction_dist = math.sqrt(min_dist_sq)
                        if attraction_dist > 0:
                            attraction_force = FOAM_ATTRACTION_TO_MAGNET_LINE_STRENGTH / attraction_dist
                            magnet_attraction_dx = (closest_pt_on_line[0] - p.x) * attraction_force
                            magnet_attraction_dy = (closest_pt_on_line[1] - p.y) * attraction_force
                    foam_radial_factor, foam_tang_factor = 0.3, 0.2
                elif num_magnets_current_frame == 1:
                    nearest = all_magnets_current_frame[0]
                    angle, r_foam = nearest.angle, math.hypot(p.x - cx, p.y - cy)
                    target_x, target_y = cx + math.cos(angle) * r_foam, cy + math.sin(angle) * r_foam
                    to_line_dx, to_line_dy = (target_x - p.x) * SINGLE_MAGNET_ATTRACTION_TO_LINE_FACTOR, (target_y - p.y) * SINGLE_MAGNET_ATTRACTION_TO_LINE_FACTOR
                    radial_dx, radial_dy = -math.cos(angle) * SINGLE_MAGNET_ALONG_LINE_STRENGTH, -math.sin(angle) * SINGLE_MAGNET_ALONG_LINE_STRENGTH
                    magnet_attraction_dx, magnet_attraction_dy = to_line_dx + radial_dx, to_line_dy + radial_dy
                    foam_radial_factor, foam_tang_factor = 0.3, 0.2

                if num_magnets_current_frame > 0:
                    nearest_magnet = min(all_magnets_current_frame, key=lambda m: dist(p.x, p.y, m.x, m.y))
                    closest_pt_on_guideline_x, closest_pt_on_guideline_y, dist_sq_guideline = closest_point_on_segment(p.x, p.y, nearest_magnet.x, nearest_magnet.y, cx, cy)
                    attraction_dist_guideline = math.sqrt(dist_sq_guideline)
                    if attraction_dist_guideline > 0:
                        attraction_force_guideline = FOAM_ATTRACTION_TO_GUIDELINE_STRENGTH / attraction_dist_guideline
                        magnet_attraction_dx += (closest_pt_on_guideline_x - p.x) * attraction_force_guideline
                        magnet_attraction_dy += (closest_pt_on_guideline_y - p.y) * attraction_force_guideline

                foam_radial, foam_tang = FOAM_RADIAL * foam_radial_factor, FOAM_TANG * foam_tang_factor
                nx, ny = ((p.x - cx) / r, (p.y - cy) / r) if r != 0 else (0, 0)
                vrx, vry = -foam_radial * nx, -foam_radial * ny
                tx, ty = -ny, nx
                vtx, vty = foam_tang * tx, foam_tang * ty
                gravity = FOAM_GRAVITY / max(r, 1)
                gravx, gravy = -gravity * nx, -gravity * ny

                p.dx = vrx + vtx + vtx + gravx + magnet_attraction_dx
                p.dy = vry + vty + gravy + magnet_attraction_dy
                
                current_speed = math.hypot(p.dx, p.dy)
                max_foam_speed = 5.0
                if current_speed > max_foam_speed:
                    scale = max_foam_speed / current_speed
                    p.dx *= scale
                    p.dy *= scale

                p.x += p.dx
                p.y += p.dy

                if p.trail is not None:
                    p.trail.append((p.x, p.y))
                    if len(p.trail) > p.current_trail_length:
                        p.trail.pop(0)

                for other in particles:
                    if other != p and other.type == "foam" and dist(p.x, p.y, other.x, other.y) < 10 and id(other) not in ids_to_remove:
                        dx, dy = p.x - other.x, p.y - other.y
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
                        next_particles.append(spawn_neutrino(last.x, last.y, last.dx, last.dy))
                        foam_fusion_buffer.clear()
                    ids_to_remove.add(id(p))
                    continue

                if all_magnets_current_frame:
                    nearest = min(all_magnets_current_frame, key=lambda m: dist(p.x, p.y, m.x, m.y))
                    d_to_magnet = dist(p.x, p.y, nearest.x, nearest.y)
                    if d_to_magnet < 8 and abs(r - bowl_r) < 8:
                        if id(p) not in nearest.trapped_foam:
                            nearest.trapped_foam.append(id(p))
                        ids_to_remove.add(id(p))
                        continue

                if r >= bowl_r:
                    nx, ny = ((p.x - cx) / r, (p.y - cy) / r) if r != 0 else (0, 0)
                    vdotn = p.dx * nx + p.dy * ny
                    p.dx -= 2 * vdotn * nx
                    p.dy -= 2 * vdotn * ny
                    p.x = cx + nx * (bowl_r - 1)
                    p.y = cy + ny * (bowl_r - 1)

                next_particles.append(p)

            elif p.type == "neutrino":
                p.x += p.dx
                p.y += p.dy
                if p.trail:
                    p.trail.append((p.x, p.y))
                    if len(p.trail) > p.current_trail_length:
                        p.trail.pop(0)
                if r >= rim_inner:
                    # Point 1: Neutrino attracts outer foam
                    outer_foam_to_attract = [of for of in particles if of.type == "outer_foam" and abs(dist(of.x, of.y, cx, cy) - bowl_r) < 10 and id(of) not in ids_to_remove]
                    if outer_foam_to_attract:
                        # Take one outer foam and convert it to inner foam
                        of_to_convert = random.choice(outer_foam_to_attract)
                        ids_to_remove.add(id(of_to_convert))
                        for _ in range(NEUTRINO_OUTER_FOAM_CONVERSION_FACTOR):
                            next_particles.append(spawn_foam(of_to_convert.x + random.uniform(-5, 5), of_to_convert.y + random.uniform(-5, 5)))
                    
                    for _ in range(FOAMTONEUTRINO_THRESHOLD):
                        angle = random.uniform(0, 2 * math.pi)
                        rad = random.uniform(0, 6)
                        nx, ny = p.x + math.cos(angle) * rad, p.y + math.sin(angle) * rad
                        next_particles.append(spawn_foam(nx, ny))
                    ids_to_remove.add(id(p))
                    continue
                next_particles.append(p)

            elif p.type == "electron":
                p.x += p.dx
                p.y += p.dy
                if p.trail:
                    p.trail.append((p.x, p.y))
                    if len(p.trail) > p.current_trail_length:
                        p.trail.pop(0)
                if r >= bowl_r:
                    if num_magnets_current_frame < MAX_POLYGON_SIDES:
                        angle = math.atan2(p.y - cy, p.x - cx)
                        mx, my = cx + math.cos(angle) * bowl_r, cy + math.sin(angle) * bowl_r
                        next_particles.append(spawn_magnetfoam(mx, my, angle))
                    else:
                        angle = math.atan2(p.y - cy, p.x - cx)
                        mx, my = cx + math.cos(angle) * bowl_r, cy + math.sin(angle) * bowl_r
                        next_particles.append(spawn_electromagnetic_impulse(mx, my, angle + math.pi))
                    ids_to_remove.add(id(p))
                    continue
                next_particles.append(p)

            elif p.type == "magnetfoam":
                if num_magnets_current_frame == 1:
                    p.lifetime -= MAGNET_LIFETIME_DECAY_SOLO_FACTOR
                    p.angle += p.rotation_speed
                    p.x, p.y = cx + bowl_r * math.cos(p.angle), cy + bowl_r * math.sin(p.angle)
                    p.dx, p.dy = 0, 0
                elif num_magnets_current_frame > 1:
                    p.lifetime += MAGNET_LIFETIME_STABLE_BONUS
                    repulsion_dx, repulsion_dy = 0, 0
                    for other in all_magnets_current_frame:
                        if other != p:
                            d = dist(p.x, p.y, other.x, other.y)
                            if d < 100:
                                force = MAGNET_REPULSION_FORCE / (d * d + 0.1)
                                angle_to_other = math.atan2(p.y - other.y, p.x - other.x)
                                repulsion_dx += math.cos(angle_to_other) * force
                                repulsion_dy += math.sin(angle_to_other) * force
                    p.dx, p.dy = repulsion_dx, repulsion_dy
                    try:
                        p_index = all_magnets_current_frame.index(p)
                        if p_index < len(magnet_ideal_polygon_points):
                            target_x, target_y = magnet_ideal_polygon_points[p_index]
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
                        p.x, p.y = cx + (p.x - cx) * scale_factor, cy + (p.y - cy) * scale_factor
                    p.angle = math.atan2(p.y - cy, p.x - cx)

                p.trapped_foam = [f_id for f_id in p.trapped_foam if any(id(f) == f_id and f.type == "foam" for f in particles)]
                if p.trapped_foam and p.lifetime > 0 and random.random() < MAGNET_RELEASE_PROB:
                    foam_id = random.choice(p.trapped_foam)
                    for foam_particle in particles:
                        if id(foam_particle) == foam_id and foam_particle.type == "foam":
                            angle = math.atan2(cy - foam_particle.y, cx - foam_particle.x)
                            speed = random.uniform(1.0, 3.0)
                            foam_particle.dx, foam_particle.dy = math.cos(angle) * speed, math.sin(angle) * speed
                            p.trapped_foam.remove(foam_id)
                            break

                if len(p.trapped_outer_foam) >= FOAM_TO_POSITRON_THRESHOLD:
                    excess_outer_foam_count = len(p.trapped_outer_foam) - FOAM_TO_POSITRON_THRESHOLD
                    for _ in range(excess_outer_foam_count):
                        spawn_x, spawn_y = p.x + random.uniform(-10, 10), p.y + random.uniform(-10, 10)
                        next_particles.append(spawn_foam(spawn_x, spawn_y))
                    next_particles.append(spawn_positron(p.x, p.y, p.dx, p.dy, contained_outer_foam=0))
                    ids_to_remove.add(id(p))
                    for foam_id in p.trapped_outer_foam: 
                        ids_to_remove.add(foam_id) 
                    for foam_id in p.trapped_foam:
                        ids_to_remove.add(foam_id)
                    continue
                elif p.lifetime <= 0:
                    if current_special_particles < MAX_PARTICLES_SUM:
                        bonus_photons = len(p.trapped_outer_foam)
                        next_particles.append(spawn_electromagnetic_impulse(p.x, p.y, p.angle + math.pi, bonus_photons))
                        for foam_id in p.trapped_outer_foam: 
                            ids_to_remove.add(foam_id) 
                    ids_to_remove.add(id(p))
                    for foam_id in p.trapped_foam:
                        ids_to_remove.add(foam_id)
                    continue
                next_particles.append(p)

            elif p.type == "electromagnetic_impulse":
                if r <= DRAIN_RADIUS and not p.is_in_drain:
                    p.is_in_drain = True
                    p.original_dx, p.original_dy = p.dx, p.dy
                    p.dx *= DRAIN_IMPULSE_SPEED_FACTOR
                    p.dy *= DRAIN_IMPULSE_SPEED_FACTOR
                    p.current_trail_length = int(MAX_IMPULSE_TRAIL_LENGTH * DRAIN_IMPULSE_TRAIL_LENGTH_FACTOR)
                    p.reflected_from_drain = True # Mark as reflected from drain
                elif p.is_in_drain and r > DRAIN_RADIUS:
                    p.is_in_drain = False
                    p.dx, p.dy = p.original_dx, p.original_dy
                    p.current_trail_length = max(1, int(MAX_IMPULSE_TRAIL_LENGTH * (p.contained_photons / p.max_photons_at_spawn)))

                p.x += p.dx
                p.y += p.dy
                p.dx += random.uniform(-ELECTROMAGNETIC_IMPULSE_JIT, ELECTROMAGNETIC_IMPULSE_JIT)
                p.dy += random.uniform(-ELECTROMAGNETIC_IMPULSE_JIT, ELECTROMAGNETIC_IMPULSE_JIT)
                current_r = dist(p.x, p.y, cx, cy)

                if current_r >= bowl_r:
                    # Point 2: Impulse attracts outer foam
                    outer_foam_to_attract = [of for of in particles if of.type == "outer_foam" and abs(dist(of.x, of.y, cx, cy) - bowl_r) < 10 and id(of) not in ids_to_remove]
                    if outer_foam_to_attract:
                        of_to_convert = random.choice(outer_foam_to_attract)
                        ids_to_remove.add(id(of_to_convert))
                        for _ in range(IMPULSE_OUTER_FOAM_CONVERSION_FACTOR):
                            next_particles.append(spawn_foam(of_to_convert.x + random.uniform(-5, 5), of_to_convert.y + random.uniform(-5, 5)))

                    nx, ny = ((p.x - cx) / current_r, (p.y - cy) / current_r) if current_r != 0 else (0, 0)
                    vdotn = p.dx * nx + p.dy * ny
                    p.dx -= 2 * vdotn * nx
                    p.dy -= 2 * vdotn * ny
                    p.x, p.y = cx + nx * (bowl_r - 1), cy + ny * (bowl_r - 1)
                    p.angle = math.atan2(p.dy, p.dx)
                    if p.contained_photons > 0:
                        p.contained_photons -= 1
                        photon_dx, photon_dy = nx * PHOTON_RELEASE_SPEED, ny * PHOTON_RELEASE_SPEED
                        next_particles.append(spawn_photon(p.x, p.y, photon_dx, photon_dy))
                        if p.max_photons_at_spawn > 0:
                            remaining_photons_ratio = p.contained_photons / p.max_photons_at_spawn
                            p.color_hue = IMPULSE_FINAL_HUE + (IMPULSE_INITIAL_HUE - IMPULSE_FINAL_HUE) * remaining_photons_ratio
                            p.current_trail_length = max(1, int(MAX_IMPULSE_TRAIL_LENGTH * remaining_photons_ratio))

                if p.trail:
                    p.trail.append((p.x, p.y))
                    if len(p.trail) > p.current_trail_length:
                        p.trail.pop(0)
                if p.contained_photons > 0:
                    next_particles.append(p)
                else:
                    ids_to_remove.add(id(p))

            elif p.type == "photon":
                p.x += p.dx
                p.y += p.dy
                if p.trail:
                    p.trail.append((p.x, p.y))
                    if len(p.trail) > p.current_trail_length:
                        p.trail.pop(0)
                if r > max(WIDTH, SIM_HEIGHT) / 2 + 50:
                    ids_to_remove.add(id(p))
                    continue
                next_particles.append(p)

            elif p.type == "outer_foam":
                if num_magnets_current_frame > 0:
                    nearest = min(all_magnets_current_frame, key=lambda m: dist(p.x, p.y, m.x, m.y))
                    target_dx, target_dy = nearest.x - p.x, nearest.y - p.y
                    target_dist = dist(p.x, p.y, nearest.x, nearest.y)
                    if target_dist > 0:
                        if target_dist < 10:
                            if id(p) not in nearest.trapped_outer_foam: 
                                nearest.trapped_outer_foam.append(id(p)) 
                            ids_to_remove.add(id(p))
                            continue
                        norm_dx, norm_dy = target_dx / target_dist, target_dy / target_dist
                        p.dx, p.dy = norm_dx * OUTER_FOAM_SPEED, norm_dy * OUTER_FOAM_SPEED
                else:
                    target_dx, target_dy = cx - p.x, cy - p.y
                    target_dist = dist(p.x, p.y, cx, cy)
                    if target_dist > 0:
                        norm_dx, norm_dy = target_dx / target_dist, target_dy / target_dist
                        p.dx, p.dy = norm_dx * OUTER_FOAM_SPEED, norm_dy * OUTER_FOAM_SPEED

                p.x += p.dx
                p.y += p.dy
                if p.trail:
                    p.trail.append((p.x, p.y))
                    if len(p.trail) > p.current_trail_length:
                        p.trail.pop(0)
                if r <= bowl_r:
                    nx, ny = ((p.x - cx) / r, (p.y - cy) / r) if r != 0 else (0, 0)
                    vdotn = p.dx * nx + p.dy * ny
                    p.dx -= 2 * vdotn * nx
                    p.dy -= 2 * vdotn * ny
                    p.x, p.y = cx + nx * (bowl_r + 1), cy + ny * (bowl_r + 1)
                next_particles.append(p)

            elif p.type == "positron":
                if p.is_stuck_to_drain:
                    next_particles.append(p)
                    continue
                target_dx, target_dy = cx - p.x, cy - p.y
                target_dist = dist(p.x, p.y, cx, cy)
                if target_dist > 0:
                    norm_dx, norm_dy = target_dx / target_dist, target_dy / target_dist
                    p.dx, p.dy = norm_dx * POSITRON_SPEED, norm_dy * POSITRON_SPEED

                # Repulsion from other positrons (existing logic)
                for other_p in particles:
                    if other_p != p and other_p.type == "positron" and id(other_p) not in ids_to_remove:
                        d = dist(p.x, p.y, other_p.x, other_p.y)
                        if d < 30:
                            force = POSITRON_REPULSION_FORCE / (d * d + 0.1)
                            angle_to_other = math.atan2(p.y - other_p.y, p.x - other_p.x)
                            p.dx += math.cos(angle_to_other) * force
                            p.dy += math.sin(angle_to_other) * force

                if num_magnets_current_frame > 0:
                    nearest = min(all_magnets_current_frame, key=lambda m: dist(p.x, p.y, m.x, m.y))
                    closest_pt_on_guideline_x, closest_pt_on_guideline_y, dist_sq_guideline = closest_point_on_segment(p.x, p.y, nearest.x, nearest.y, cx, cy)
                    attraction_dist_guideline = math.sqrt(dist_sq_guideline)
                    if attraction_dist_guideline > 0:
                        attraction_force_guideline = POSITRON_ATTRACTION_TO_GUIDELINE_STRENGTH / attraction_dist_guideline
                        p.dx += (closest_pt_on_guideline_x - p.x) * attraction_force_guideline
                        p.dy += (closest_pt_on_guideline_y - p.y) * attraction_force_guideline

                p.x += p.dx
                p.y += p.dy
                if p.trail:
                    p.trail.append((p.x, p.y))
                    if len(p.trail) > p.current_trail_length:
                        p.trail.pop(0)
                if r <= DRAIN_RADIUS + 5:
                    if counts['positron'] >= num_magnets_current_frame and num_magnets_current_frame > 0:
                        next_particles.append(spawn_electromagnetic_impulse(p.x, p.y, math.atan2(p.dy, p.dx)))
                        ids_to_remove.add(id(p))
                        continue
                    else:
                        p.is_stuck_to_drain = True
                        nx, ny = ((p.x - cx) / r, (p.y - cy) / r) if r != 0 else (0, 0)
                        p.x, p.y = cx + nx * (DRAIN_RADIUS + 2), cy + ny * (DRAIN_RADIUS + 2)
                        p.dx, p.dy = 0, 0
                next_particles.append(p)

            elif p.type == "neutron":
                p.x += p.dx
                p.y += p.dy
                for other_foam in particles:
                    if other_foam.type == "foam" and id(other_foam) not in ids_to_remove:
                        d = dist(p.x, p.y, other_foam.x, other_foam.y)
                        if d < 10 and d != 0:
                            nx, ny = (p.x - other_foam.x) / d, (p.y - other_foam.y) / d
                            vx, vy = p.dx - other_foam.dx, p.dy - other_foam.dy
                            vn = vx * nx + vy * ny
                            if vn < 0:
                                impulse_x, impulse_y = -2 * vn * nx, -2 * vn * ny
                                p.dx += impulse_x * 0.5
                                p.dy += impulse_y * 0.5
                                other_foam.dx -= impulse_x * 0.5
                                other_foam.dy -= impulse_y * 0.5
                                overlap = 10 - d
                                p.x += nx * overlap * 0.5
                                p.y += ny * overlap * 0.5
                                other_foam.x -= nx * overlap * 0.5
                                other_foam.y -= ny * overlap * 0.5
                                collision_marks.append((p.x, p.y, 5))

                if r >= bowl_r:
                    # Point 4: Neutron decays into an impulse
                    # The impulse will reflect from the drain and release photons at bowl_r
                    angle = math.atan2(p.y - cy, p.x - cx)
                    next_particles.append(spawn_electromagnetic_impulse(p.x, p.y, angle + math.pi, bonus_photons=p.neutron_foam_content, reflected_from_drain=True))
                    ids_to_remove.add(id(p))
                    continue
                p.dx *= 0.99
                p.dy *= 0.99
                if p.trail:
                    p.trail.append((p.x, p.y))
                    if len(p.trail) > p.current_trail_length:
                        p.trail.pop(0)
                next_particles.append(p)

        neutrinos_for_fusion = [p for p in next_particles if p.type == "neutrino" and dist(p.x, p.y, cx, cy) <= DRAIN_RADIUS and id(p) not in ids_to_remove]
        neutrinos_for_fusion.sort(key=lambda p: (p.x, p.y))
        used_neutrinos_for_fusion, newly_spawned_electrons = set(), []
        i = 0
        while i < len(neutrinos_for_fusion):
            p = neutrinos_for_fusion[i]
            if id(p) in used_neutrinos_for_fusion:
                i += 1
                continue
            cluster = [q for q in neutrinos_for_fusion if dist(p.x, p.y, q.x, q.y) < 7 and id(q) not in used_neutrinos_for_fusion]
            if len(cluster) >= NEUTRINOTOELECTRON_THRESHOLD and current_special_particles < MAX_PARTICLES_SUM:
                mx, my = sum(q.x for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]) / NEUTRINOTOELECTRON_THRESHOLD, sum(q.y for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]) / NEUTRINOTOELECTRON_THRESHOLD
                mdx, mdy = sum(q.dx for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]) / NEUTRINOTOELECTRON_THRESHOLD, sum(q.dy for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]) / NEUTRINOTOELECTRON_THRESHOLD
                newly_spawned_electrons.append(spawn_electron(mx, my, mdx, mdy))
                for q in cluster[:NEUTRINOTOELECTRON_THRESHOLD]:
                    used_neutrinos_for_fusion.add(id(q))
                    ids_to_remove.add(id(q))
            i += 1

        electrons_for_collision = [p for p in next_particles if p.type == "electron" and id(p) not in ids_to_remove]
        positrons_for_collision = [p for p in next_particles if p.type == "positron" and id(p) not in ids_to_remove]
        collided_e_pos_ids, newly_spawned_neutrons, newly_spawned_inner_foam_from_positron = set(), [], []
        for e in electrons_for_collision:
            if id(e) in collided_e_pos_ids:
                continue
            for pos in positrons_for_collision:
                if id(pos) in collided_e_pos_ids:
                    continue
                if dist(e.x, e.y, pos.x, pos.y) < 10:
                    neutron_x, neutron_y = (e.x + pos.x) / 2, (e.y + pos.y) / 2
                    neutron_dx, neutron_dy = (e.dx + pos.dx) / 2, (e.dy + pos.dy) / 2
                    neutron_foam_amount = NEUTRINOTOELECTRON_THRESHOLD * 2
                    newly_spawned_neutrons.append(spawn_neutron(neutron_x, neutron_y, neutron_dx, neutron_dy, neutron_foam_amount))
                    for _ in range(pos.contained_outer_foam):
                        foam_x, foam_y = neutron_x + random.uniform(-5, 5), neutron_y + random.uniform(-5, 5)
                        newly_spawned_inner_foam_from_positron.append(spawn_foam(foam_x, foam_y))
                    collided_e_pos_ids.add(id(e))
                    collided_e_pos_ids.add(id(pos))
                    ids_to_remove.add(id(e))
                    ids_to_remove.add(id(pos))
                    break

        particles = [p for p in next_particles if id(p) not in ids_to_remove] + newly_spawned_electrons + newly_spawned_neutrons + newly_spawned_inner_foam_from_positron
        counts = {ptype: sum(1 for p in particles if p.type == ptype) for ptype in history}
        final_magnets_for_drawing = [p for p in particles if p.type == "magnetfoam"]
        num_magnets_final_for_drawing = len(final_magnets_for_drawing)
        actual_magnet_positions_for_drawing = [(m.x, m.y) for m in sorted(final_magnets_for_drawing, key=lambda m: math.atan2(m.y - cy, m.x - cx))] if num_magnets_final_for_drawing > 0 else []
        sides_for_polygon_final_for_drawing = NUM_MAGNETS_TO_SIDES.get(min(num_magnets_final_for_drawing, MAX_POLYGON_SIDES), 0)

        for key in history:
            history[key].append(counts[key])
            if len(history[key]) > MAX_HISTORY:
                history[key] = history[key][-MAX_HISTORY:]

        screen.fill(BG_COLOR)
        draw_simulation(screen, particles, cx, cy, bowl_r, magnet_ideal_polygon_points, actual_magnet_positions_for_drawing, sides_for_polygon_final_for_drawing, num_magnets_final_for_drawing, collision_marks)
        draw_statistics(screen, history, counts, sides_for_polygon_final_for_drawing, current_polygon_angle_offset, SIM_HEIGHT, fonts)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

