#!/usr/bin/env python3

import pygame
import random
import math
import time
from typing import List, Dict, Tuple, Optional, Set
import collections # Für den Canvas-Stack
from PIL import Image # Importiere Pillow

# ==================== KONFIGURATION ====================
# Display-Einstellungen
WIDTH, HEIGHT = 1024, 2048  # Gesamtfenstergröße
SIM_HEIGHT = 1024           # Höhe des Simulationsbereichs
STATS_HEIGHT = 700          # Höhe des Statistikbereichs
LOG_HEIGHT = HEIGHT - SIM_HEIGHT - STATS_HEIGHT # Höhe des Logbereichs (restlicher Platz)
FPS = 30                    # Bilder pro Sekunde
TARGET_FPS = 60             # Ziel-FPS für konsistente Bewegungsskalierung

# Spatial Grid Einstellungen
SPATIAL_GRID_CELL_SIZE = 50 # Größe einer Zelle im Spatial Grid (in Pixeln)

# Canvas Stack Einstellungen
STACK_SIZE = 10             # Anzahl der Canvas-Elemente im Stack
REDSHIFT_INTENSITY_PER_LAYER = 10 # Wie stark sich die Rottöne pro älterer Schicht verschieben (0-255)
BLUESHIFT_INTENSITY = 80   # Wie stark der aktuelle Canvas blau verschoben wird, bevor er in den Stack geht (0-255)
# GEÄNDERT: Dieser Wert definiert jetzt den START-Alpha-Wert des ÄLTESTEN Canvas-Elements,
# um einen Verblass-Effekt zu erzielen. Er sollte niedrig sein.
ALPHA_FADE_START_PERCENT = 10 # Opazität des ältesten Canvas im Stack (10 = 10% Deckkraft, fast transparent)
CANVAS_WOBBLE_MAX_OFFSET_X = 5 # Maximaler X-Offset für wackelnde Stack-Elemente
CANVAS_WOBBLE_MAX_OFFSET_Y = 5 # Maximaler Y-Offset für wackelnde Stack-Elemente


# Farben
BG_COLOR = (11, 11, 30)       # Hintergrundfarbe
PANEL_BG = (20, 20, 40)       # Hintergrund für Panels
TEXT_COLOR = (255, 255, 255)  # Textfarbe
SIM_BORDER_COLOR = (80, 80, 100)
PARTICLE_COLORS = {
    'foam': (100, 200, 255),
    'neutrino': (180, 100, 255),
    'electron': (255, 100, 100),
    'magnet': (100, 255, 150),
    'impulse': (255, 200, 50),
    'photon': (255, 255, 100),
    'outer_foam': (50, 150, 255),
    'positron': (255, 150, 150),
    'neutron': (200, 200, 200)
}

# Log-Level und zugehörige Emojis/Farben
LOG_LEVELS = {
    'INFO': {'emoji': '💬', 'color': (200, 200, 200)},    # Grau/Weiß
    'WARNUNG': {'emoji': '⚠️', 'color': (255, 255, 0)}, # Gelb
    'FEHLER': {'emoji': '🛑', 'color': (255, 50, 50)},   # Rot
    'EREIGNIS': {'emoji': '📯', 'color': (100, 255, 100)} # Grün
}

# ==================== PARTIKELKLASSE ====================
class Particle:
    _next_id = 0 # Klassenvariable für eindeutige IDs

    def __init__(self, x: float, y: float, radius: int, p_type: str):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = PARTICLE_COLORS.get(p_type, (200, 200, 200))
        self.type = p_type
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        
        self.id = Particle._next_id # Eindeutige ID für das Partikel
        Particle._next_id += 1 # Inkrementiere für das nächste Partikel

    def update(self, dt: float):
        """
        Aktualisiert die Position des Partikels und behandelt Kollisionen mit den Rändern
        des Simulationsbereichs.
        """
        self.x += self.vx * dt * TARGET_FPS # Skalierung für konsistente Bewegung bei variabler FPS
        self.y += self.vy * dt * TARGET_FPS
        
        # Halte Partikel innerhalb der Grenzen des SIMULATIONSBEREICHS
        if self.x < self.radius:
            self.x = self.radius
            self.vx *= -0.8 # Abprall mit Dämpfung
        elif self.x > WIDTH - self.radius: # WIDTH ist die Breite des Simulationsbereichs
            self.x = WIDTH - self.radius
            self.vx *= -0.8
            
        if self.y < self.radius:
            self.y = self.radius
            self.vy *= -0.8
        elif self.y > SIM_HEIGHT - self.radius:
            self.y = SIM_HEIGHT - self.radius
            self.vy *= -0.8

# ==================== PARTIKEL-POOL ====================
class ParticlePool:
    def __init__(self, initial_size=1000):
        """
        Ein Pool zur effizienten Verwaltung von Partikelobjekten,
        um die Erstellung und Zerstörung von Objekten zu minimieren.
        """
        # Partikel werden hier vorinitialisiert, um Objekte wiederverwenden zu können
        self.particles = [Particle(0, 0, 0, 'foam') for _ in range(initial_size)]
        self.active_count = 0
    
    def add(self, x: float, y: float, radius: int, p_type: str) -> Particle:
        """
        Aktiviert ein Partikel aus dem Pool oder erstellt ein neues, wenn der Pool voll ist.
        """
        if self.active_count < len(self.particles):
            p = self.particles[self.active_count]
            p.x = x
            p.y = y
            p.radius = radius
            p.color = PARTICLE_COLORS.get(p_type, (200, 200, 200))
            p.type = p_type
            p.vx = random.uniform(-1, 1)
            p.vy = random.uniform(-1, 1)
            # p.id wird bei der Instanziierung des Partikels gesetzt und behält seine einmalige ID bei.
            # Es wird NICHT neu gesetzt, wenn ein Partikel aus dem Pool wiederverwendet wird.
        else:
            # Erweitert den Pool, falls nötig (kann Performance-Auswirkungen haben)
            p = Particle(x, y, radius, p_type)
            self.particles.append(p)
        
        self.active_count += 1
        return p
    
    def remove(self, index: int):
        """
        Deaktiviert ein Partikel, indem es mit dem letzten aktiven Partikel getauscht wird.
        Dies ist eine O(1) Operation, die die Reihenfolge der Partikel ändert.
        """
        if 0 <= index < self.active_count:
            # Tausche mit dem letzten aktiven Partikel, um Lücken zu vermeiden
            self.particles[index], self.particles[self.active_count-1] = \
                self.particles[self.active_count-1], self.particles[index]
            self.active_count -= 1
        else:
            # Dies sollte im Normalfall nicht passieren, wenn der Index korrekt verwaltet wird
            print(f"Warnung: Versuch, Partikel an ungültigem Index {index} zu entfernen.")
    
    def get_active(self) -> List[Particle]:
        """
        Gibt eine Liste der aktuell aktiven Partikel zurück.
        """
        return self.particles[:self.active_count]

# ==================== SPATIAL GRID ====================
class SpatialGrid:
    def __init__(self, width: int, height: int, cell_size: int):
        """
        Initialisiert ein Spatial Grid für die effiziente Kollisionserkennung.
        Teilt den Simulationsbereich in Zellen auf.
        """
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = math.ceil(self.width / self.cell_size)
        self.rows = math.ceil(self.height / self.cell_size)
        self.grid: List[List[List[Particle]]] = [[[] for _ in range(self.rows)] for _ in range(self.cols)]

    def _get_cell_coords(self, x: float, y: float) -> Tuple[int, int]:
        """Gibt die Gitterkoordinaten für eine gegebene (x,y) Position zurück."""
        col = int(x / self.cell_size)
        row = int(y / self.cell_size)
        return max(0, min(col, self.cols - 1)), max(0, min(row, self.rows - 1))

    def clear(self):
        """Löscht alle Partikel aus dem Gitter für den nächsten Frame."""
        for col in range(self.cols):
            for row in range(self.rows):
                self.grid[col][row].clear() # Leert die Liste in jeder Zelle

    def add_particle(self, particle: Particle):
        """Fügt ein Partikel dem Spatial Grid hinzu."""
        min_col, min_row = self._get_cell_coords(particle.x - particle.radius, particle.y - particle.radius)
        max_col, max_row = self._get_cell_coords(particle.x + particle.radius, particle.y + particle.radius)

        # Fügt das Partikel zu allen Zellen hinzu, die es überlappt
        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                if 0 <= col < self.cols and 0 <= row < self.rows:
                    self.grid[col][row].append(particle)

    def get_nearby_particles(self, particle: Particle) -> List[Particle]:
        """
        Gibt eine Liste von Partikeln zurück, die sich in der Nähe des gegebenen Partikels befinden
        (in derselben Zelle oder benachbarten Zellen).
        """
        candidates: Set[Particle] = set() # Verwende ein Set, um Duplikate zu vermeiden
        
        center_col, center_row = self._get_cell_coords(particle.x, particle.y)

        # Überprüfe die zentrale Zelle und die 8 benachbarten Zellen
        for col_offset in [-1, 0, 1]:
            for row_offset in [-1, 0, 1]:
                check_col, check_row = center_col + col_offset, center_row + row_offset
                
                if 0 <= check_col < self.cols and 0 <= check_row < self.rows:
                    candidates.update(self.grid[check_col][check_row])
        
        # Entferne das Partikel selbst aus der Liste der Kandidaten
        candidates.discard(particle)
        return list(candidates)


# ==================== SIMULATIONS-RENDERER ====================
class SimulationRenderer:
    def __init__(self, width: int, height: int, sim_height: int, stats_height: int):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Mikado-Universum Simulation")

        # Separate Pygame Oberflächen für Statistik und Log
        self.stats_surface = pygame.Surface((width, stats_height))
        self.log_surface = pygame.Surface((width, LOG_HEIGHT))
        
        # Die finale Oberfläche für den Simulationsbereich, die auf self.screen geblittet wird
        self.simulation_surface = pygame.Surface((width, sim_height), pygame.SRCALPHA)
        
        # Eine temporäre Pygame Surface NUR für die Partikel, die dann zu Pillow konvertiert wird
        # Diese Surface ist immer transparent, damit nur die Partikel darauf sichtbar sind
        self.particle_drawing_surface = pygame.Surface((width, sim_height), pygame.SRCALPHA)


        # Canvas Stack initialisieren
        # Der Stack speichert jetzt PIL.Image-Objekte
        self.canvas_stack = collections.deque(maxlen=STACK_SIZE)
        # Den Stack mit leeren, transparenten Pillow-Bildern vorfüllen
        for _ in range(STACK_SIZE):
            self.canvas_stack.append(Image.new('RGBA', (width, sim_height), (0, 0, 0, 0)))

        # Schriftarten
        self.fonts = {
            'large': pygame.font.SysFont('Arial', 40, bold=True),
            'medium': pygame.font.SysFont('Arial', 30),
            'small': pygame.font.SysFont('Arial', 20)
        }

        # Log-Nachrichten speichern Tupel (message, level)
        self.log_messages: List[Tuple[str, str]] = []
        self.max_log_messages = 15

    def log(self, message: str, level: str = 'INFO'):
        """
        Fügt eine Nachricht zum Log-Bereich hinzu, mit Zeitstempel und Level.
        """
        current_time_str = time.strftime("%H:%M:%S", time.localtime())
        valid_level = level if level in LOG_LEVELS else 'INFO'
        self.log_messages.append((f"[{current_time_str}] {message}", valid_level))
        if len(self.log_messages) > self.max_log_messages:
            self.log_messages.pop(0)

    def _apply_color_shift_pillow(self, pil_image: Image.Image, r_shift: int, g_shift: int, b_shift: int) -> Image.Image:
        """
        Wendet eine Farbverschiebung auf ein Pillow Image an.
        Nutzt Pillow's point-Methode für effiziente Pixelmanipulation.
        """
        if pil_image.mode != 'RGBA':
            pil_image = pil_image.convert('RGBA')
            
        # Erstelle eine Kopie, um das Original nicht zu ändern
        img_copy = pil_image.copy()

        # Teile die Bänder (R, G, B, A)
        r, g, b, a = img_copy.split()

        # Wende die Verschiebung auf jedes Farbband an und klemme die Werte
        r = r.point(lambda i: max(0, min(255, i + r_shift)))
        g = g.point(lambda i: max(0, min(255, i + g_shift)))
        b = b.point(lambda i: max(0, min(255, i + b_shift)))

        # Führe die Bänder wieder zusammen
        return Image.merge('RGBA', (r, g, b, a))

    def draw_simulation_area(self, particles: List[Particle]):
        """
        Zeichnet den Simulationsbereich.
        Schritte:
        1. Alten Canvas-Stack (PIL Images) auf die finale Pygame-Simulationsfläche blitten.
        2. Aktuelle Partikel auf eine TEMPORÄRE transparente Pygame-Surface zeichnen.
        3. Diese Partikel-Surface in ein PIL.Image konvertieren.
        4. Dieses PIL.Image farbverschieben (Blau-Shift) und dem Stack hinzufügen.
        5. Die Partikel-Surface (die jetzt die aktuellen Partikel enthält) auf die finale Pygame-Simulationsfläche blitten.
        6. Rahmen zeichnen.
        """
        # Fülle die finale Simulationsfläche mit dem Hintergrund (100% opak)
        self.simulation_surface.fill(BG_COLOR) 
        
        # 1. Gestapelte Canvas-Elemente zeichnen (älteste zuerst)
        # Die Stack-Elemente sind PIL.Image-Objekte
        for i, stacked_canvas_pil in enumerate(self.canvas_stack):
            # GEÄNDERTE ALPHA-BERECHNUNG FÜR VERBLASSEN
            if STACK_SIZE > 1:
                alpha_start = int(255 * (ALPHA_FADE_START_PERCENT / 100.0))
                # Alpha skaliert von alpha_start (ältestes) bis 255 (neuestes)
                current_alpha = alpha_start + (255 - alpha_start) * (i / (STACK_SIZE - 1))
            else:
                current_alpha = 255
            current_alpha = max(0, min(255, int(current_alpha)))

            # Berechne Rotverschiebung
            red_shift = i * REDSHIFT_INTENSITY_PER_LAYER
            
            # Wende Farbverschiebung mit Pillow an
            shifted_canvas_pil = self._apply_color_shift_pillow(stacked_canvas_pil, red_shift, -red_shift // 2, -red_shift // 2)
            
            # Konvertiere das Pillow Image zurück zu einem Pygame Surface zum Blitten
            raw_str = shifted_canvas_pil.tobytes()
            shifted_canvas_pygame = pygame.image.frombytes(raw_str, shifted_canvas_pil.size, "RGBA")
            shifted_canvas_pygame.set_alpha(current_alpha)

            # Zufällige Wobbel-Verschiebung hinzufügen
            wobble_x = random.uniform(-CANVAS_WOBBLE_MAX_OFFSET_X, CANVAS_WOBBLE_MAX_OFFSET_X)
            wobble_y = random.uniform(-CANVAS_WOBBLE_MAX_OFFSET_Y, CANVAS_WOBBLE_MAX_OFFSET_Y)
            
            # Gestapelte Oberfläche auf die finale Pygame Simulationsfläche blitten
            self.simulation_surface.blit(shifted_canvas_pygame, (wobble_x, wobble_y))
        
        # 2. Partikel auf der TEMPORÄREN Pygame Surface zeichnen
        # Diese Surface wird am Anfang jedes Frames geleert und ist transparent
        self.particle_drawing_surface.fill((0, 0, 0, 0)) # Vollständig transparent machen
        for particle in particles:
            if 0 <= particle.x < WIDTH and 0 <= particle.y < SIM_HEIGHT:
                pygame.draw.circle(
                    self.particle_drawing_surface, 
                    (*particle.color, 200),  # Mit Alpha-Kanal für leichte Transparenz
                    (int(particle.x), int(particle.y)), 
                    particle.radius
                )
        
        # 3. Aktuellen Partikel-Canvas (Pygame Surface) für den Stack vorbereiten (konvertieren zu Pillow Image)
        # Nur die Partikel (und nicht der Hintergrund) kommen in den Stack
        raw_data = self.particle_drawing_surface.get_view('0').raw # Direkt die Bytes
        current_particles_snapshot_pil = Image.frombytes('RGBA', self.particle_drawing_surface.get_size(), raw_data)
        
        # Wende die Blauverschiebung auf den Partikel-Schnappschuss (PIL Image) an
        blue_shifted_particles_pil = self._apply_color_shift_pillow(current_particles_snapshot_pil, 
                                                                 -BLUESHIFT_INTENSITY // 2, 
                                                                 -BLUESHIFT_INTENSITY // 2, 
                                                                 BLUESHIFT_INTENSITY)
        
        # Füge den blau verschobenen Partikel-Schnappschuss dem Pillow-basierten Stack hinzu
        self.canvas_stack.append(blue_shifted_particles_pil)

        # 4. Die Partikel-Surface (mit den aktuellen Partikeln) auf die finale Simulationsfläche blitten
        self.simulation_surface.blit(self.particle_drawing_surface, (0, 0))

        # 5. Rahmen um den Simulationsbereich zeichnen (immer sichtbar)
        pygame.draw.rect(self.simulation_surface, SIM_BORDER_COLOR, 
                         self.simulation_surface.get_rect(), 3)


    def draw_statistics_area(self, particle_counts: Dict[str, int], history: List[Dict[str, int]]):
        """
        Zeichnet den Statistikbereich mit aktuellen Zählungen und einem Verlaufsdiagramm.
        """
        self.stats_surface.fill(PANEL_BG)

        title_surface = self.fonts['large'].render("PARTIKEL-STATISTIK", True, TEXT_COLOR)
        self.stats_surface.blit(title_surface, (20, 20))

        # Aktuelle Statistiken anzeigen
        y_offset = 80
        for p_type, count in particle_counts.items():
            color = PARTICLE_COLORS.get(p_type, (200, 200, 200))
            pygame.draw.circle(self.stats_surface, color, (25, y_offset + 15), 8) # Farbkreis als Legende
            text_surface = self.fonts['medium'].render(f"{p_type.capitalize()}: {count}", True, TEXT_COLOR)
            self.stats_surface.blit(text_surface, (40, y_offset))
            y_offset += 40
        
        # Diagramm für Partikelentwicklung
        if history:
            diagram_rect = pygame.Rect(self.stats_surface.get_width() - 350, 240, 320, 200)
            pygame.draw.rect(self.stats_surface, (30, 30, 50), diagram_rect) # Diagramm-Hintergrund
            pygame.draw.rect(self.stats_surface, TEXT_COLOR, diagram_rect, 2) # Diagramm-Rahmen
            
            # Maximalwert für die Skalierung des Diagramms
            max_val = 1
            for counts_frame in history:
                if counts_frame: # Sicherstellen, dass das Dictionary nicht leer ist
                    max_val = max(max_val, max(counts_frame.values()) if counts_frame else 1)
            
            # Zeichne historische Daten als gestapeltes Balkendiagramm
            step_x = diagram_rect.width / max(1, len(history) - 1) if len(history) > 1 else diagram_rect.width
            
            for i, counts_at_frame in enumerate(history):
                x = diagram_rect.left + i * step_x
                current_y_offset = 0 # Für gestapelte Balken
                
                # Sortiere Partikeltypen für konsistente Stapelung
                sorted_particle_types = sorted(PARTICLE_COLORS.keys())

                for p_type in sorted_particle_types:
                    if p_type in counts_at_frame:
                        count = counts_at_frame[p_type]
                        height = (count / max_val) * diagram_rect.height
                        color = PARTICLE_COLORS[p_type]
                        
                        # Zeichne den Balkenabschnitt
                        pygame.draw.rect(
                            self.stats_surface, 
                            color,
                            (x, diagram_rect.bottom - height - current_y_offset, max(1, int(step_x)), int(height))
                        )
                        current_y_offset += height

            # Diagrammtitel
            title = self.fonts['small'].render("Partikelentwicklung", True, (180, 180, 180))
            self.stats_surface.blit(title, (diagram_rect.centerx - title.get_width()//2, diagram_rect.top - 30))

    def draw_log_area(self):
        """
        Zeichnet den Logbereich mit den neuesten Nachrichten, inklusive Level-Emojis und Farben.
        """
        self.log_surface.fill(PANEL_BG)
        title_surface = self.fonts['large'].render("LOG", True, TEXT_COLOR)
        self.log_surface.blit(title_surface, (20, 20))

        y_offset = 60
        # Zeigt die neuesten Nachrichten zuerst an, begrenzt auf max_log_messages
        for msg_text, msg_level in reversed(self.log_messages[-self.max_log_messages:]):
            level_info = LOG_LEVELS.get(msg_level, LOG_LEVELS['INFO'])
            emoji = level_info['emoji']
            color = level_info['color']

            # Render Text mit Emoji
            log_entry_text = f"{emoji} {msg_text}"
            text_surface = self.fonts['small'].render(log_entry_text, True, color)
            self.log_surface.blit(text_surface, (40, y_offset))
            y_offset += 25
            if y_offset > self.log_surface.get_height() - 20:
                break

    def render_frame(self, particles: List[Particle], particle_counts: Dict[str, int], history: List[Dict[str, int]]):
        """
        Rendert den gesamten Frame, indem alle Bereiche auf den Hauptbildschirm gezeichnet werden.
        """
        self.screen.fill(BG_COLOR) # Gesamten Bildschirmhintergrund füllen (wirkt sich auf den gesamten Screen aus)
        
        # Simulationsbereich zeichnen und auf den Hauptbildschirm blitten
        # draw_simulation_area kümmert sich jetzt um die Befüllung von self.simulation_surface
        self.draw_simulation_area(particles)
        self.screen.blit(self.simulation_surface, (0, 0)) # Blitte die fertige Simulationsfläche auf den Hauptbildschirm
        
        # Statistikbereich zeichnen und auf den Hauptbildschirm blitten
        self.draw_statistics_area(particle_counts, history)
        self.screen.blit(self.stats_surface, (0, SIM_HEIGHT)) # Direkt unter der Simulation
        
        # Logbereich zeichnen und auf den Hauptbildschirm blitten
        self.draw_log_area()
        self.screen.blit(self.log_surface, (0, SIM_HEIGHT + STATS_HEIGHT)) # Unter dem Statistikbereich
        
        pygame.display.flip() # Alles aktualisieren

# ==================== SIMULATIONS-LOGIK ====================
class SimulationLogic:
    def __init__(self, renderer: SimulationRenderer):
        self.renderer = renderer
        self.particle_pool = ParticlePool(initial_size=1000)
        self.spatial_grid = SpatialGrid(WIDTH, SIM_HEIGHT, SPATIAL_GRID_CELL_SIZE) # Initialisiere Spatial Grid
        
        self.particle_counts: Dict[str, int] = {k: 0 for k in PARTICLE_COLORS.keys()}
        self.history: List[Dict[str, int]] = []
        self.max_history = 100 # Anzahl der Frames, die im Diagramm gespeichert werden
        self.particle_types = list(PARTICLE_COLORS.keys()) # Liste der Partikeltypen vorab cachen

        self.init_simulation_state()

    def init_simulation_state(self):
        """
        Setzt den Anfangszustand der Simulation, erstellt initiale Partikel.
        """
        for _ in range(50):
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, SIM_HEIGHT - 50)
            p_type = random.choice(self.particle_types)
            self.create_particle(x, y, p_type)
        
        self.update_counts()
        
        self.renderer.log("Simulation gestartet.", level='INFO')
        self.renderer.log(f"Initiale Partikel: {self.particle_pool.active_count}", level='INFO')

    def update_counts(self):
        """
        Aktualisiert die Partikelzählungen und den Verlaufs-Log.
        """
        counts = {k: 0 for k in self.particle_counts.keys()}
        for particle in self.particle_pool.get_active():
            counts[particle.type] += 1
        
        self.particle_counts = counts
        self.history.append(counts.copy())
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def create_particle(self, x: float, y: float, p_type: str):
        """
        Erstellt ein neues Partikel über den Pool.
        """
        radius = {
            'foam': random.randint(3, 6),
            'neutrino': 2,
            'electron': 4,
            'magnet': 5,
            'impulse': 3,
            'photon': 3,
            'outer_foam': 4,
            'positron': 4,
            'neutron': 6
        }.get(p_type, 4)
        
        return self.particle_pool.add(x, y, radius, p_type)

    def particle_interaction(self, p1: Particle, p2: Particle):
        """
        Behandelt Kollisionen und einfache Interaktionen zwischen zwei Partikeln.
        """
        # Vermeide Kollisionen mit sich selbst, falls durch Spatial Grid doppelt gefunden
        if p1.id == p2.id:
            return

        dx = p2.x - p1.x
        dy = p2.y - p1.y
        distance_sq = dx*dx + dy*dy
        combined_radius = p1.radius + p2.radius
        
        if distance_sq < combined_radius * combined_radius:
            distance = math.sqrt(distance_sq)
            if distance == 0:
                return
            
            # Kollisionsbehandlung (einfache Abprall-Logik)
            angle = math.atan2(dy, dx)
            
            # Geschwindigkeiten anpassen (vereinfacht)
            # Dämpfung und Reflektion
            p1.vx = -math.cos(angle) * abs(p1.vx) * 0.7
            p1.vy = -math.sin(angle) * abs(p1.vy) * 0.7
            p2.vx = math.cos(angle) * abs(p2.vx) * 0.7
            p2.vy = math.sin(angle) * abs(p2.vy) * 0.7
            
            # Partikel trennen, um Überlappungen zu vermeiden
            overlap = combined_radius - distance + 1
            p1.x -= overlap * math.cos(angle) / 2
            p1.y -= overlap * math.sin(angle) / 2
            p2.x += overlap * math.cos(angle) / 2
            p2.y += overlap * math.sin(angle) / 2
            
            # Zufällige Partikelumwandlung bei Kollision
            if random.random() < 0.005:
                new_type = random.choice(self.particle_types)
                old_type = p1.type
                p1.type = new_type
                p1.color = PARTICLE_COLORS[new_type]
                self.renderer.log(f"Umwandlung bei Kollision: {old_type} → {new_type}", level='EREIGNIS')

    def update(self, dt: float):
        """
        Aktualisiert den Zustand der Simulation in jedem Frame.
        Nutzt das Spatial Grid für effiziente Kollisionserkennung.
        """
        particles = self.particle_pool.get_active()
        
        # Partikel aktualisieren (Bewegung, Randbedingungen)
        for particle in particles:
            particle.update(dt)
        
        # Spatial Grid aktualisieren
        self.spatial_grid.clear()
        for particle in particles:
            self.spatial_grid.add_particle(particle)
        
        # Kollisionserkennung und Interaktionen zwischen Partikeln
        checked_pairs: Set[Tuple[int, int]] = set() # Verhindert doppelte Prüfungen
        
        for p1 in particles:
            nearby_particles = self.spatial_grid.get_nearby_particles(p1)
            for p2 in nearby_particles:
                # Sicherstellen, dass jedes Paar nur einmal geprüft wird
                # Sortiere die IDs, um sicherzustellen, dass (id1, id2) und (id2, id1) gleich behandelt werden
                pair_id = tuple(sorted((p1.id, p2.id)))
                if pair_id in checked_pairs:
                    continue
                
                self.particle_interaction(p1, p2)
                checked_pairs.add(pair_id)
        
        # Zufällig neue Partikel erzeugen
        if random.random() < 0.05:
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, SIM_HEIGHT - 50)
            p_type = random.choice(self.particle_types)
            self.create_particle(x, y, p_type)
        
        # Zufällig alte Partikel entfernen
        if random.random() < 0.01 and self.particle_pool.active_count > 50:
            index = random.randint(0, self.particle_pool.active_count - 1)
            removed_particle = self.particle_pool.get_active()[index]
            self.particle_pool.remove(index)
            self.renderer.log(f"Partikel vom Typ '{removed_particle.type}' entfernt. Aktive: {self.particle_pool.active_count}", level='INFO')
        
        # Zählungen aktualisieren
        self.update_counts()

# ==================== HAUPTSCHLEIFE ====================
def main():
    renderer = SimulationRenderer(WIDTH, HEIGHT, SIM_HEIGHT, STATS_HEIGHT)
    simulation_logic = SimulationLogic(renderer)
    clock = pygame.time.Clock()
    last_time = time.time()

    running = True
    frame_count = 0
    
    while running:
        # Delta-Zeit berechnen
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        # Event-Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Linke Maustaste
                    x, y = event.pos
                    # Überprüfen, ob der Klick im Simulationsbereich liegt
                    if 0 <= x < WIDTH and 0 <= y < SIM_HEIGHT:
                        p_type = random.choice(simulation_logic.particle_types)
                        simulation_logic.create_particle(x, y, p_type)
                        renderer.log(f"Partikel vom Typ '{p_type}' bei ({x}, {y}) erstellt.", level='EREIGNIS')
        
        # Logik aktualisieren
        simulation_logic.update(dt)
        
        # Frame rendern
        particles = simulation_logic.particle_pool.get_active()
        renderer.render_frame(particles, simulation_logic.particle_counts, simulation_logic.history)
        
        # Periodische Log-Nachrichten
        frame_count += 1
        if frame_count % (FPS * 10) == 0: # Alle 10 Sekunden
            total_particles = simulation_logic.particle_pool.active_count
            foam_count = simulation_logic.particle_counts['foam']
            renderer.log(f"Simulationsstatus: {total_particles} aktive Partikel. Schaum: {foam_count}", level='INFO')
            
            if total_particles > 200: # Beispiel für Warnung bei zu vielen Partikeln
                renderer.log(f"Partikelanzahl erreicht {total_particles}! Performance-Warnung.", level='WARNUNG')
            if foam_count > total_particles * 0.4 and total_particles > 0:
                renderer.log("Hoher Schaumanteil im System!", level='WARNUNG')
            if simulation_logic.particle_pool.active_count == 0:
                renderer.log("Alle Partikel verschwunden! Simulation stoppt bald.", level='FEHLER')

        clock.tick(FPS)
    
    pygame.quit()

if __name__ == "__main__":
    main()
