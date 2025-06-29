import pygame
import math
import colorsys

# Pygame initialisieren
pygame.init()

# Bildschirmgröße und Farben definieren
WIDTH, HEIGHT = 1024, 1024
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mikado-Modell mit kontinuierlichen Regenbogen-Pfaden")

BLACK = (0, 0, 0)
center = (WIDTH // 2, HEIGHT // 2)
max_radius = min(WIDTH, HEIGHT) // 2 - 20

# (Anzahl Ecken, Radius)
shapes = [
    (2, max_radius),
    (3, max_radius * 0.75),
    (4, max_radius * 0.65),
    (5, max_radius * 0.55),
    (6, max_radius * 0.45),
    (7, max_radius * 0.35),
    (8, max_radius * 0.25)
]

def get_shape_points(center, sides, radius, angle):
    pts = []
    for i in range(sides):
        a = angle + i * 2 * math.pi / sides
        x = center[0] + radius * math.cos(a)
        y = center[1] + radius * math.sin(a)
        pts.append((x, y))
    return pts

def hsv2rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)

# Jede Form bekommt eine eigene Basis-Farbe
shape_colors = [
    hsv2rgb(i / len(shapes), 1.0, 1.0)
    for i in range(len(shapes))
]

# Rotationsgeschwindigkeiten (proportional zur Anzahl der Ecken für Pirouetten-Effekt)
base_speed = 0.5
rotation_speeds = [base_speed * (s / 2) for s, _ in shapes]  # Mehr Ecken = schnellere Rotation

# Pro Eckpunkt: Spur-Listen
vertex_paths = [[] for _ in range(sum(s for s, _ in shapes))]

clock = pygame.time.Clock()
running = True

while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    idx_offset = 0
    for si, (sides, radius) in enumerate(shapes):
        # Rotationswinkel
        t = pygame.time.get_ticks() / 1000.0
        angle = t * rotation_speeds[si]
        pts = get_shape_points(center, sides, radius, angle)

        form_col = shape_colors[si]

        # 1) Leuchtender Umriss in Formfarbe
        for width, alpha in [(14, 20), (8, 40), (4, 80)]:
            col = (*form_col, alpha)
            if sides == 2:
                pygame.draw.line(glow, col, pts[0], pts[1], width)
            else:
                pygame.draw.polygon(glow, col, pts, width)

        # 2) Bunte Trails je Ecke mit breiterem Regenbogen-Effekt
        for j, p in enumerate(pts):
            vidx = idx_offset + j
            vertex_paths[vidx].append(p)
            path = vertex_paths[vidx]
            if len(path) > 200:  # Begrenzte Pfadlänge, um Speicher zu schonen
                path.pop(0)
            if len(path) > 1:
                # Dynamischer Regenbogen-Effekt
                hue = (t * 0.1 + j / sides + si / len(shapes)) % 1.0
                trail_col = hsv2rgb(hue, 1.0, 0.8)
                for k in range(1, len(path)):
                    alpha = int(60 * (1 - k / len(path)))  # Verblassen der Spur
                    pygame.draw.line(glow, (*trail_col, alpha), path[k-1], path[k], 8)

        idx_offset += sides

    # Glow-Additive Compositing
    screen.blit(glow, (0, 0), special_flags=pygame.BLEND_ADD)

    # 3) Scharfe, farbige Umrisse zum Abschluss
    idx_offset = 0
    for si, (sides, radius) in enumerate(shapes):
        t = pygame.time.get_ticks() / 1000.0
        angle = t * rotation_speeds[si]
        pts = get_shape_points(center, sides, radius, angle)
        col = shape_colors[si]
        if sides == 2:
            pygame.draw.line(screen, col, pts[0], pts[1], 2)
        else:
            pygame.draw.polygon(screen, col, pts, 2)
        idx_offset += sides

    pygame.display.flip()
    clock.tick(15)

pygame.quit()