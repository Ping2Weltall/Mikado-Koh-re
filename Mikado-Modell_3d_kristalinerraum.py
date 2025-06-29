import pygame
import math
import colorsys

# Pygame initialisieren
pygame.init()

WIDTH, HEIGHT = 1024, 1024
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mikado-Modell: 3D mit Regenbogen-Trails")

BLACK = (0, 0, 0)
center = (WIDTH // 2, HEIGHT // 2)
max_radius = min(WIDTH, HEIGHT) // 2 - 80  # kleiner für 3D

shapes = [
    (2, max_radius),
    (3, max_radius * 0.75),
    (4, max_radius * 0.65),
    (5, max_radius * 0.55),
    (6, max_radius * 0.45),
    (7, max_radius * 0.35),
    (8, max_radius * 0.25)
]

def get_shape_points_3d(sides, radius, ang1, ang2):
    # Platziere die Eckpunkte auf einem Kreis in der XY-Ebene und rotiere dann um Z und X
    pts3d = []
    for i in range(sides):
        phi = i * 2 * math.pi / sides
        x = radius * math.cos(phi)
        y = radius * math.sin(phi)
        z = 0

        # Z-Rotation (um die Y-Achse)
        xz = x * math.cos(ang1) - z * math.sin(ang1)
        zz = x * math.sin(ang1) + z * math.cos(ang1)
        x, z = xz, zz

        # X-Rotation (um die X-Achse)
        yz = y * math.cos(ang2) - z * math.sin(ang2)
        zz = y * math.sin(ang2) + z * math.cos(ang2)
        y, z = yz, zz

        pts3d.append((x, y, z))
    return pts3d

def project_3d(pt, camera_dist=800):
    # Perspektivische Projektion auf 2D
    x, y, z = pt
    factor = camera_dist / (camera_dist - z)
    px = center[0] + x * factor
    py = center[1] + y * factor
    return (px, py)

def hsv2rgb(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)

shape_colors = [hsv2rgb(i / len(shapes), 1.0, 1.0) for i in range(len(shapes))]
base_speed = 0.4
rotation_speeds = [base_speed * (s / 2) for s, _ in shapes]
vertex_paths = [[] for _ in range(sum(s for s, _ in shapes))]

clock = pygame.time.Clock()
running = True

while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    t = pygame.time.get_ticks() / 1000.0
    idx_offset = 0

    for si, (sides, radius) in enumerate(shapes):
        ang1 = t * rotation_speeds[si]        # Y-Achse
        ang2 = t * rotation_speeds[si] * 0.6  # X-Achse
        pts3d = get_shape_points_3d(sides, radius, ang1, ang2)
        pts2d = [project_3d(pt) for pt in pts3d]
        form_col = shape_colors[si]

        # Glow-Umriss
        for width, alpha in [(14, 20), (8, 40), (4, 80)]:
            col = (*form_col, alpha)
            if sides == 2:
                pygame.draw.line(glow, col, pts2d[0], pts2d[1], width)
            else:
                pygame.draw.polygon(glow, col, pts2d, width)

        # Trails für jede Ecke
        for j, p2d in enumerate(pts2d):
            vidx = idx_offset + j
            vertex_paths[vidx].append(p2d)
            path = vertex_paths[vidx]
            if len(path) > 200:
                path.pop(0)
            if len(path) > 1:
                hue = (t * 0.1 + j / sides + si / len(shapes)) % 1.0
                trail_col = hsv2rgb(hue, 1.0, 0.8)
                for k in range(1, len(path)):
                    alpha = int(60 * (1 - k / len(path)))
                    pygame.draw.line(glow, (*trail_col, alpha), path[k-1], path[k], 8)
        idx_offset += sides

    # Glow-Additive Compositing
    screen.blit(glow, (0, 0), special_flags=pygame.BLEND_ADD)

    # Scharfe Umrisse
    idx_offset = 0
    for si, (sides, radius) in enumerate(shapes):
        ang1 = t * rotation_speeds[si]
        ang2 = t * rotation_speeds[si] * 0.6
        pts3d = get_shape_points_3d(sides, radius, ang1, ang2)
        pts2d = [project_3d(pt) for pt in pts3d]
        col = shape_colors[si]
        if sides == 2:
            pygame.draw.line(screen, col, pts2d[0], pts2d[1], 2)
        else:
            pygame.draw.polygon(screen, col, pts2d, 2)
        idx_offset += sides

    pygame.display.flip()
    clock.tick(18)

pygame.quit()