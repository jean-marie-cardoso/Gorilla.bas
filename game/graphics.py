# graphics.py — ville et rendu "QBASIC Deluxe"
import math
import random

import pygame

from config import (
    BANANA_YELLOW,
    CORAL,
    CREAM,
    EXPLOSION_RADIUS,
    HUD_ACTIVE,
    HUD_BG,
    HUD_BG_SOFT,
    HUD_BORDER,
    SKY_GLOW,
    SKY_HORIZON,
    SKY_MIDDLE,
    SKY_TOP,
    SUN_ORANGE,
    VIRTUAL_H,
    VIRTUAL_W,
    WIND_MAX,
)
from ui import clip_text, draw_panel, draw_toast, render_text


# Noms historiques conserves pour les modules externes.
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SKY = SKY_MIDDLE
BUILDING_COLORS = [
    (43, 28, 67),
    (53, 31, 78),
    (65, 35, 86),
    (76, 39, 91),
    (86, 43, 94),
    (99, 48, 97),
]


def _draw_moon(surface, center, expression="smile"):
    """Lune pleine pixelisée, avec un visage doux."""
    center_x, center_y = center
    glow = pygame.Surface((76, 76), pygame.SRCALPHA)
    pygame.draw.circle(glow, (190, 211, 225, 18), (38, 38), 37)
    pygame.draw.circle(glow, (210, 224, 230, 28), (38, 38), 31)
    surface.blit(glow, (center_x - 38, center_y - 38))

    pygame.draw.circle(surface, (42, 52, 78), center, 27)
    pygame.draw.circle(surface, (232, 235, 210), center, 24)
    pygame.draw.circle(surface, (250, 244, 211), (center_x - 5, center_y - 6), 17)
    pygame.draw.circle(surface, (185, 192, 178), (center_x - 13, center_y - 10), 3)
    pygame.draw.circle(surface, (201, 205, 185), (center_x - 13, center_y + 11), 4)
    pygame.draw.circle(surface, (174, 184, 174), (center_x + 14, center_y + 11), 3)

    ink = (64, 67, 82)
    pygame.draw.rect(surface, ink, (center_x - 8, center_y - 4, 3, 4))
    pygame.draw.rect(surface, ink, (center_x + 5, center_y - 4, 3, 4))
    if expression == "surprised":
        pygame.draw.circle(surface, ink, (center_x, center_y + 9), 3)
        pygame.draw.circle(surface, (232, 235, 210), (center_x, center_y + 9), 1)
    else:
        pygame.draw.line(surface, ink, (center_x - 6, center_y + 7), (center_x - 3, center_y + 10), 2)
        pygame.draw.line(surface, ink, (center_x - 3, center_y + 10), (center_x + 3, center_y + 10), 2)
        pygame.draw.line(surface, ink, (center_x + 3, center_y + 10), (center_x + 6, center_y + 7), 2)


ATMOSPHERES = {
    "sunset": {
        "label": "CRÉPUSCULE",
        "sky": (SKY_TOP, SKY_MIDDLE, SKY_HORIZON, SKY_GLOW),
        "stars": 54,
        "clouds": 4,
        "cloud_color": (121, 91, 145),
        "cloud_alpha": (32, 60),
        "cloud_speed": (1.0, 3.2),
        "weather": None,
        "show_sun": True,
        "wind": (-WIND_MAX, WIND_MAX),
        "window_light": 0.51,
    },
    "sunny": {
        "label": "GRAND SOLEIL",
        "sky": ((24, 105, 179), (70, 160, 217), (246, 181, 113), (255, 211, 145)),
        "stars": 0,
        "clouds": 3,
        "cloud_color": (225, 240, 249),
        "cloud_alpha": (82, 125),
        "cloud_speed": (0.5, 1.5),
        "weather": "sun_haze",
        "show_sun": True,
        "wind": (-4, 4),
        "window_light": 0.22,
    },
    "night": {
        "label": "NUIT ÉCLAIRÉE",
        "sky": ((2, 8, 28), (10, 24, 61), (28, 43, 82), (44, 52, 86)),
        "stars": 92,
        "clouds": 2,
        "cloud_color": (49, 60, 103),
        "cloud_alpha": (28, 48),
        "cloud_speed": (0.6, 1.6),
        "weather": "night",
        "show_sun": False,
        "wind": (-6, 6),
        "window_light": 0.66,
    },
    "rain": {
        "label": "PLUIE",
        "sky": ((14, 31, 52), (40, 65, 82), (76, 89, 101), (100, 104, 108)),
        "stars": 0,
        "clouds": 7,
        "cloud_color": (46, 54, 68),
        "cloud_alpha": (105, 155),
        "cloud_speed": (2.0, 4.8),
        "weather": "rain",
        "show_sun": False,
        "wind": (-8, 8),
        "window_light": 0.58,
    },
    "snow": {
        "label": "NEIGE",
        "sky": ((38, 54, 82), (83, 105, 132), (151, 158, 172), (190, 185, 188)),
        "stars": 10,
        "clouds": 6,
        "cloud_color": (174, 185, 201),
        "cloud_alpha": (72, 112),
        "cloud_speed": (0.7, 2.1),
        "weather": "snow",
        "show_sun": False,
        "wind": (-6, 6),
        "window_light": 0.61,
    },
    "storm": {
        "label": "TEMPÊTE",
        "sky": ((5, 9, 26), (22, 26, 52), (48, 48, 70), (70, 64, 76)),
        "stars": 0,
        "clouds": 9,
        "cloud_color": (24, 27, 43),
        "cloud_alpha": (145, 205),
        "cloud_speed": (5.5, 10.0),
        "weather": "storm",
        "show_sun": False,
        "wind": "storm",
        "window_light": 0.64,
    },
}
ATMOSPHERE_NAMES = tuple(ATMOSPHERES)

BUILDING_THEMES = {
    "sunset": {
        "palette": tuple(BUILDING_COLORS),
        "outline": (24, 17, 43),
        "shadow": (19, 13, 35),
        "highlight": (229, 91, 91),
        "highlight_amount": 0.18,
        "window_dark": (38, 30, 68),
        "window_lit": (255, 220, 117),
        "window_alt": (225, 103, 98),
    },
    "sunny": {
        "palette": (
            (55, 74, 105),
            (76, 91, 118),
            (125, 83, 84),
            (146, 101, 90),
            (98, 74, 105),
            (69, 90, 113),
        ),
        "outline": (20, 31, 51),
        "shadow": (28, 39, 61),
        "highlight": (255, 191, 119),
        "highlight_amount": 0.22,
        "window_dark": (28, 46, 67),
        "window_lit": (157, 211, 232),
        "window_alt": (255, 211, 133),
    },
    "night": {
        "palette": (
            (15, 24, 54),
            (20, 30, 66),
            (25, 35, 74),
            (31, 39, 82),
            (35, 43, 89),
            (23, 32, 69),
        ),
        "outline": (5, 9, 25),
        "shadow": (2, 8, 24),
        "highlight": (52, 84, 132),
        "highlight_amount": 0.16,
        "window_dark": (13, 20, 48),
        "window_lit": (255, 224, 112),
        "window_alt": (103, 190, 232),
    },
    "rain": {
        "palette": (
            (35, 52, 67),
            (43, 59, 75),
            (52, 66, 81),
            (44, 58, 72),
            (59, 67, 81),
            (47, 62, 77),
        ),
        "outline": (14, 25, 36),
        "shadow": (21, 33, 44),
        "highlight": (126, 160, 180),
        "highlight_amount": 0.19,
        "window_dark": (21, 35, 47),
        "window_lit": (255, 211, 117),
        "window_alt": (116, 189, 217),
    },
    "snow": {
        "palette": (
            (53, 58, 82),
            (63, 68, 92),
            (73, 75, 100),
            (81, 78, 101),
            (61, 72, 98),
            (74, 67, 91),
        ),
        "outline": (25, 28, 49),
        "shadow": (35, 39, 63),
        "highlight": (201, 222, 239),
        "highlight_amount": 0.25,
        "window_dark": (32, 38, 65),
        "window_lit": (255, 219, 128),
        "window_alt": (173, 215, 235),
    },
    "storm": {
        "palette": (
            (17, 21, 40),
            (22, 25, 47),
            (27, 29, 53),
            (31, 31, 57),
            (24, 26, 50),
            (35, 33, 59),
        ),
        "outline": (4, 7, 19),
        "shadow": (7, 10, 25),
        "highlight": (124, 127, 174),
        "highlight_amount": 0.17,
        "window_dark": (12, 16, 35),
        "window_lit": (250, 212, 109),
        "window_alt": (158, 160, 226),
    },
}

CITY_STYLES = {
    "new_york": {
        "label": "NEW YORK",
        "tagline": "GRATTE-CIEL • EMPIRE STATE",
        "count": (14, 18),
        "height": (112, 272),
        "roofs": ("antenna", "tank", "billboard", "lip"),
        "trim": (0, 1, 2),
        "tint": (54, 66, 91),
        "tint_amount": 0.08,
    },
    "paris": {
        "label": "PARIS",
        "tagline": "MANSARDES • TOUR EIFFEL",
        "count": (15, 20),
        "height": (76, 148),
        "roofs": ("mansard", "chimney", "mansard", "lip"),
        "trim": (1, 1, 0),
        "tint": (122, 91, 91),
        "tint_amount": 0.16,
    },
    "tokyo": {
        "label": "TOKYO",
        "tagline": "NÉONS • TOUR DE TOKYO",
        "count": (14, 19),
        "height": (86, 232),
        "roofs": ("neon", "antenna", "billboard", "tank"),
        "trim": (0, 2, 2),
        "tint": (83, 55, 112),
        "tint_amount": 0.13,
    },
    "seaside": {
        "label": "BORD DE MER",
        "tagline": "OCÉAN • PHARE • PALMIERS",
        "count": (12, 17),
        "height": (54, 112),
        "roofs": ("solar", "chimney", "lip", "tank"),
        "trim": (0, 1, 1),
        "tint": (145, 126, 118),
        "tint_amount": 0.22,
    },
    "future": {
        "label": "NÉO-CITY",
        "tagline": "DÔMES • PASSERELLES • NÉONS",
        "count": (13, 18),
        "height": (104, 260),
        "roofs": ("dome", "dish", "antenna", "neon"),
        "trim": (2, 2, 0),
        "tint": (47, 79, 111),
        "tint_amount": 0.18,
    },
}
CITY_STYLE_NAMES = tuple(CITY_STYLES)


def _lerp_color(a, b, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(int(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def _make_sky(colors=None):
    top, middle, horizon, glow = colors or (
        SKY_TOP,
        SKY_MIDDLE,
        SKY_HORIZON,
        SKY_GLOW,
    )
    sky = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    horizon_y = int(VIRTUAL_H * 0.68)
    for y in range(VIRTUAL_H):
        # Pas de 3 pixels: le degrade reste doux mais garde un grain retro.
        sample_y = (y // 3) * 3
        if sample_y <= horizon_y:
            t = sample_y / float(horizon_y)
            if t < 0.58:
                color = _lerp_color(top, middle, t / 0.58)
            else:
                color = _lerp_color(middle, horizon, (t - 0.58) / 0.42)
        else:
            t = (sample_y - horizon_y) / float(VIRTUAL_H - horizon_y)
            color = _lerp_color(horizon, glow, min(1.0, t * 0.72))
        pygame.draw.line(sky, color, (0, y), (VIRTUAL_W, y))

    # Quelques lignes de trame discretes pres de l'horizon.
    for y in range(174, 246, 8):
        color = (*_lerp_color(middle, glow, (y - 174) / 110.0),)
        for x in range((y // 8) % 2 * 4, VIRTUAL_W, 8):
            sky.set_at((x, y), color)
    return sky


def _make_cloud(width, height, color):
    cloud = pygame.Surface((width, height), pygame.SRCALPHA)
    # Blocs simples: lisibles et peu couteux a deplacer.
    pygame.draw.rect(cloud, color, (0, height // 2, width, max(3, height // 3)))
    pygame.draw.rect(
        cloud,
        color,
        (width // 5, height // 4, max(4, width // 3), max(4, height // 2)),
    )
    pygame.draw.rect(
        cloud,
        color,
        (width // 2, 0, max(5, width // 3), max(5, height * 2 // 3)),
    )
    shadow = (31, 23, 66, max(20, color[3] // 2))
    pygame.draw.rect(cloud, shadow, (width // 8, height * 3 // 4, width * 3 // 4, 2))
    return cloud


class City:
    def __init__(self):
        self.rects = []
        self.mask = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        self.atmosphere_name = "sunset"
        self.atmosphere = ATMOSPHERES[self.atmosphere_name]
        self._sky = _make_sky(self.atmosphere["sky"])
        self._far_layer = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        self._styles = []
        self._stars = []
        self._clouds = []
        self._weather_particles = []
        self._living_windows = []
        self._antenna_lights = []
        self._smoke_plumes = []
        self._debris_particles = []
        self._parachutists = []
        self._fires = []
        self._collapses = []
        self._building_hits = {}
        self._damage_revision = 0
        self._life_checked_revision = -1
        self._banana_trail = []
        self._scene_banana_active = False
        self._hud_active = 0
        self._generation = 0
        self.city_style_name = "new_york"

    @property
    def city_style_label(self):
        return CITY_STYLES[self.city_style_name]["label"]

    @property
    def city_style_tagline(self):
        return CITY_STYLES[self.city_style_name]["tagline"]

    @property
    def atmosphere_label(self):
        return self.atmosphere["label"]

    @property
    def show_sun(self):
        return bool(self.atmosphere["show_sun"])

    @property
    def show_moon(self):
        return self.atmosphere_name == "night"

    def set_atmosphere(self, name, rng, rebuild=True):
        """Prépare le ciel et les particules d'une ambiance."""
        if name not in ATMOSPHERES:
            name = "sunset"
        self.atmosphere_name = name
        self.atmosphere = ATMOSPHERES[name]
        self._sky = _make_sky(self.atmosphere["sky"])

        self._stars = [
            (
                rng.randint(5, VIRTUAL_W - 6),
                rng.randint(8, 190),
                rng.randint(0, 3),
                rng.choice((1, 1, 1, 2)),
            )
            for _ in range(self.atmosphere["stars"])
        ]

        self._clouds = []
        cloud_alpha = self.atmosphere["cloud_alpha"]
        cloud_speed = self.atmosphere["cloud_speed"]
        base_color = self.atmosphere["cloud_color"]
        for _ in range(self.atmosphere["clouds"]):
            width = rng.randint(42, 96)
            height = rng.randint(10, 20)
            color = (*base_color, rng.randint(*cloud_alpha))
            cloud = _make_cloud(width, height, color)
            self._clouds.append(
                {
                    "x": rng.uniform(-width, VIRTUAL_W),
                    "y": rng.randint(58, 182),
                    "speed": rng.uniform(*cloud_speed),
                    "surface": cloud,
                }
            )

        weather = self.atmosphere["weather"]
        count = {
            "rain": 72,
            "snow": 66,
            "storm": 100,
            "sun_haze": 18,
        }.get(weather, 0)
        self._weather_particles = [
            {
                "x": rng.uniform(0, VIRTUAL_W),
                "y": rng.uniform(0, VIRTUAL_H),
                "speed": rng.uniform(58, 105)
                if weather == "snow"
                else rng.uniform(190, 310),
                "size": rng.choice((1, 1, 2, 2, 3)),
                "phase": rng.uniform(0, math.tau),
            }
            for _ in range(count)
        ]
        if rebuild and self.rects and self._styles:
            self._build_far_layer(rng)
            self.rebuild_mask()

    def choose_wind(self, rng):
        """Le même vent pilote la banane, la flèche et toute la météo."""
        wind = self.atmosphere["wind"]
        if wind == "storm":
            return rng.choice((-1, 1)) * rng.randint(7, WIND_MAX)
        return rng.randint(wind[0], wind[1])

    def generate(self, rng: random.Random):
        self._generation += 1
        self._banana_trail.clear()
        self._smoke_plumes.clear()
        self._debris_particles.clear()
        self._parachutists.clear()
        self._fires.clear()
        self._collapses.clear()
        self._building_hits.clear()
        choices = [
            name
            for name in ATMOSPHERE_NAMES
            if self._generation == 1 or name != self.atmosphere_name
        ]
        self.set_atmosphere(rng.choice(choices), rng, rebuild=False)

        city_choices = [
            name
            for name in CITY_STYLE_NAMES
            if self._generation == 1 or name != self.city_style_name
        ]
        self.city_style_name = rng.choice(city_choices)
        city_settings = CITY_STYLES[self.city_style_name]

        width_factor = VIRTUAL_W / 640.0
        count = max(
            12,
            round(rng.randint(*city_settings["count"]) * width_factor),
        )
        remaining = VIRTUAL_W
        x = 0
        widths = []
        for index in range(count):
            slots = count - index
            if slots == 1:
                width = remaining
            else:
                ideal = remaining // slots
                minimum = 26
                maximum = remaining - minimum * (slots - 1)
                width = max(minimum, min(maximum, ideal + rng.randint(-9, 9)))
            widths.append(width)
            remaining -= width

        heights = []
        previous = None
        for index, _ in enumerate(widths):
            low, high = city_settings["height"]
            height = rng.randint(low, high)
            distance_to_center = abs(index - (len(widths) - 1) / 2)
            if self.city_style_name == "new_york":
                middle = (low + high) // 2
                if distance_to_center < 1.2:
                    height = rng.randint(high - 16, high)
                elif index % 4 == 0:
                    height = rng.randint(low, middle - 12)
                elif index % 4 == 1:
                    height = rng.randint(middle + 8, high)
            elif self.city_style_name == "paris":
                paris_bands = (
                    (low, min(high, low + 24)),
                    (max(low, high - 24), high),
                    (low + 20, high - 18),
                )
                band_low, band_high = paris_bands[index % len(paris_bands)]
                height = rng.randint(band_low, max(band_low, band_high))
            elif self.city_style_name == "tokyo":
                if index % 5 == 2:
                    height = rng.randint(max(low, 205), high)
                elif index % 4 == 0:
                    height = rng.randint(low, min(high, 128))
            elif self.city_style_name == "seaside":
                seaside_bands = (
                    (low, min(high, low + 15)),
                    (max(low, high - 18), high),
                    (low + 14, high - 14),
                )
                band_low, band_high = seaside_bands[index % len(seaside_bands)]
                height = rng.randint(band_low, max(band_low, band_high))
            elif self.city_style_name == "future":
                if index % 4 == 1:
                    height = rng.randint(max(low, 224), high)
                elif index % 4 == 3:
                    height = rng.randint(low, min(high, 154))

            # Pas de longue ligne de toits plats : deux voisins doivent être
            # franchement différents dès que la plage le permet.
            if previous is not None and abs(height - previous) < 20:
                step = rng.randint(22, 36)
                can_rise = previous + step <= high
                can_fall = previous - step >= low
                if can_rise and (not can_fall or index % 2):
                    height = previous + step
                elif can_fall:
                    height = previous - step
                else:
                    height = high if previous < (low + high) // 2 else low
            heights.append(height)
            previous = height

        # Sécurité gameplay : une ville doit toujours avoir un toit bas et
        # un toit haut dans les zones où les joueurs peuvent apparaître.
        required_spread = min(58, high - low - 4)
        if max(heights) - min(heights) < required_spread:
            heights[1] = low + 2
            heights[-2] = high - 2

        self.rects.clear()
        self._styles.clear()
        building_theme = BUILDING_THEMES[self.atmosphere_name]
        building_palette = building_theme["palette"]
        for index, (width, height) in enumerate(zip(widths, heights)):
            top = VIRTUAL_H - height
            rect = pygame.Rect(x, top, width, height)
            self.rects.append(rect)
            columns = max(1, (width - 10) // 10)
            rows = max(1, (height - 16) // 12)
            windows = []
            light_chance = self.atmosphere["window_light"]
            for row in range(rows):
                line = []
                for column in range(columns):
                    chance = rng.random()
                    if chance < light_chance:
                        state = 1
                    elif chance < min(0.96, light_chance + 0.07):
                        state = 2
                    else:
                        state = 0
                    # Une petite repetition donne une facade moins chaotique.
                    if row and column and rng.random() < 0.22:
                        state = windows[row - 1][column - 1]
                    line.append(state)
                windows.append(line)
            palette_slot = (
                index % len(building_palette)
                if rng.random() < 0.52
                else rng.randrange(len(building_palette))
            )
            base_color = building_palette[palette_slot]
            styled_color = _lerp_color(
                base_color,
                city_settings["tint"],
                city_settings["tint_amount"],
            )
            self._styles.append(
                {
                    "color": styled_color,
                    "palette_slot": palette_slot,
                    "roof": (
                        "mansard"
                        if self.city_style_name == "paris" and index % 3 != 2
                        else "neon"
                        if self.city_style_name == "tokyo" and index % 3 == 1
                        else rng.choice(city_settings["roofs"])
                    ),
                    "windows": windows,
                    "trim": rng.choice(city_settings["trim"]),
                }
            )
            x += width

        self._build_far_layer(rng)
        self.rebuild_mask()
        self._prepare_building_life(rng)

    def _prepare_building_life(self, rng):
        self._living_windows.clear()
        self._antenna_lights.clear()

        for rect, style in zip(self.rects, self._styles):
            windows = style.get("windows", ())
            start_y = rect.top + 10
            for row, line in enumerate(windows):
                yy = start_y + row * 12
                if yy + 6 >= rect.bottom or not line:
                    continue
                available = rect.w - 10
                step = max(8, available // len(line))
                for column, state in enumerate(line):
                    xx = rect.left + 5 + column * step
                    if xx + 5 >= rect.right or rng.random() >= 0.09:
                        continue
                    self._living_windows.append(
                        {
                            "rect": pygame.Rect(xx, yy, 5, 7),
                            "base_on": state != 0,
                            "alternate": state == 2,
                            "period": rng.uniform(5.5, 13.0),
                            "phase": rng.uniform(0.0, 13.0),
                            "silhouette": rng.random() < 0.24,
                            "silhouette_speed": rng.uniform(0.11, 0.22),
                            "direction": rng.choice((-1, 1)),
                            "intact": True,
                        }
                    )

            if style.get("roof") == "antenna":
                antenna_x = rect.right - max(5, rect.w // 5)
                self._antenna_lights.append(
                    {
                        "x": antenna_x,
                        "y": rect.top - 13,
                        "phase": rng.uniform(0.0, 4.0),
                    }
                )
        self._life_checked_revision = self._damage_revision

    @staticmethod
    def _living_window_is_on(window, scene_time):
        cycle = (
            (scene_time + window["phase"]) % window["period"]
        ) / window["period"]
        return cycle < (0.70 if window["base_on"] else 0.22)

    def _window_is_intact(self, rect):
        points = (
            rect.center,
            (rect.left, rect.top),
            (rect.right - 1, rect.top),
            (rect.left, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
        )
        try:
            return all(self.mask.get_at(point).a > 0 for point in points)
        except IndexError:
            return False

    def draw_building_life(self, surface, scene_time):
        """Fenêtres lentes et silhouettes, sans modifier les collisions."""
        theme = BUILDING_THEMES.get(
            self.atmosphere_name,
            BUILDING_THEMES["sunset"],
        )
        if self._life_checked_revision != self._damage_revision:
            for window in self._living_windows:
                source_rect = window["rect"]
                rect = (
                    source_rect.inflate(2, 0)
                    if window["silhouette"]
                    else source_rect
                )
                window["intact"] = self._window_is_intact(rect)
            self._life_checked_revision = self._damage_revision

        for window in self._living_windows:
            source_rect = window["rect"]
            rect = (
                source_rect.inflate(2, 0)
                if window["silhouette"]
                else source_rect
            )
            if not window["intact"]:
                continue

            pygame.draw.rect(surface, theme["window_dark"], rect)
            if not self._living_window_is_on(window, scene_time):
                continue

            light = (
                theme["window_alt"]
                if window["alternate"]
                else theme["window_lit"]
            )
            pygame.draw.rect(
                surface,
                light,
                (rect.x + 1, rect.y + 1, rect.width - 2, 5),
            )
            glint = _lerp_color(light, (255, 255, 238), 0.48)
            pygame.draw.rect(
                surface,
                glint,
                (rect.x + 1, rect.y + 1, rect.width - 2, 1),
            )

            if window["silhouette"]:
                travel = (
                    scene_time * window["silhouette_speed"]
                    + window["phase"]
                ) % 1.0
                if window["direction"] < 0:
                    travel = 1.0 - travel
                person_x = rect.x + 1 + min(
                    rect.width - 3,
                    int(travel * (rect.width - 2)),
                )
                person_color = _lerp_color(
                    theme["window_dark"],
                    theme["shadow"],
                    0.55,
                )
                pygame.draw.rect(
                    surface,
                    person_color,
                    (person_x, rect.y + 2, 1, 1),
                )
                pygame.draw.rect(
                    surface,
                    person_color,
                    (
                        min(rect.right - 2, person_x),
                        rect.y + 3,
                        2,
                        3,
                    ),
                )

        for beacon in self._antenna_lights:
            bright = int(scene_time * 1.8 + beacon["phase"]) % 4 == 0
            color = (255, 92, 92) if bright else (96, 41, 61)
            pygame.draw.rect(
                surface,
                color,
                (beacon["x"] - 1, beacon["y"], 4, 3),
            )

    def _building_index_at(self, center):
        cx, cy = int(center[0]), int(center[1])
        candidates = [
            (index, rect)
            for index, rect in enumerate(self.rects)
            if rect.left <= cx <= rect.right and rect.top <= cy <= rect.bottom
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda item: abs(item[1].centerx - cx))[0]

    def should_collapse_at(self, center):
        index = self._building_index_at(center)
        if index is None:
            return False
        rect = self.rects[index]
        collapse_line = rect.top + max(28, int(rect.height * 0.30))
        crater_bottom = int(center[1]) + EXPLOSION_RADIUS + 5
        return (
            self._building_hits.get(index, 0) >= 2
            or crater_bottom >= collapse_line
        )

    def register_building_hit(self, center):
        """Compte les coups reçus par chaque immeuble."""
        index = self._building_index_at(center)
        if index is None:
            return 0
        hit_count = self._building_hits.get(index, 0) + 1
        self._building_hits[index] = hit_count
        return hit_count

    def collapse_building_at(self, center, scene_time=None):
        """Réduit en gravats un bâtiment fragile ou touché deux fois."""
        index = self._building_index_at(center)
        if index is None or not self.should_collapse_at(center):
            return None

        old_rect = self.rects[index].copy()
        fragment = pygame.Surface(old_rect.size, pygame.SRCALPHA)
        fragment.blit(self.mask, (0, 0), old_rect)
        rubble_height = max(14, min(24, old_rect.height // 5))
        rubble = pygame.Rect(
            old_rect.x,
            old_rect.bottom - rubble_height,
            old_rect.w,
            rubble_height,
        )
        clear_rect = pygame.Rect(
            old_rect.x - 3,
            old_rect.top - 20,
            old_rect.w + 6,
            old_rect.height + 20,
        )
        pygame.draw.rect(self.mask, (0, 0, 0, 0), clear_rect)

        theme = BUILDING_THEMES.get(
            self.atmosphere_name,
            BUILDING_THEMES["sunset"],
        )
        outline = (*theme["outline"], 255)
        rubble_color = (*theme["shadow"], 255)
        points = [(rubble.left, rubble.bottom)]
        step = max(7, rubble.width // 6)
        x = rubble.left
        while x < rubble.right:
            peak = rubble.top + ((x * 7 + index * 11) % 9)
            points.append((x, peak))
            x += step
        points.extend([(rubble.right, rubble.top + 5), (rubble.right, rubble.bottom)])
        pygame.draw.polygon(self.mask, outline, points)
        inner = [
            (x, min(rubble.bottom - 2, y + 3))
            for x, y in points
        ]
        pygame.draw.polygon(self.mask, rubble_color, inner)
        for chunk in range(5):
            chunk_x = rubble.left + 4 + (chunk * 13 + index * 5) % max(5, rubble.width - 8)
            chunk_y = rubble.top + 5 + chunk % 3 * 4
            pygame.draw.rect(
                self.mask,
                outline,
                (chunk_x, chunk_y, 4 + chunk % 3, 3),
            )

        self.rects[index] = rubble
        self._damage_revision += 1
        if scene_time is not None:
            self._collapses.append(
                {
                    "rect": old_rect,
                    "image": fragment,
                    "start": float(scene_time),
                    "duration": 1.15,
                    "seed": index * 19 + old_rect.x,
                }
            )
            self._collapses = self._collapses[-2:]
        return index, old_rect, rubble

    def add_damage_effect(self, center, scene_time, strong=False):
        cx, cy = int(center[0]), int(center[1])
        seed = (cx * 31 + cy * 17) % 97
        self._smoke_plumes.append(
            {
                "x": cx,
                "y": cy,
                "start": float(scene_time),
                "duration": 8.0 if strong else 6.2,
                "seed": seed,
                "strong": bool(strong),
            }
        )
        self._smoke_plumes = self._smoke_plumes[-6:]
        chunk_count = 24 if strong else 16
        for index in range(chunk_count):
            angle = math.radians(205 + ((index * 137 + seed) % 130))
            speed = (38 if strong else 29) + (index % 6) * 8
            self._debris_particles.append(
                {
                    "x": cx,
                    "y": cy,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed - 22,
                    "start": float(scene_time),
                    "duration": 1.8 if strong else 1.35,
                    "size": 4 + index % 5,
                    "color": (
                        (76, 52, 68)
                        if index % 3
                        else (232, 111, 55)
                    ),
                }
            )
        self._debris_particles = self._debris_particles[-80:]
        fire_roll = (seed + self._damage_revision * 23) % 10
        if fire_roll < (6 if strong else 4):
            self._fires.append(
                {
                    "x": cx,
                    "y": cy,
                    "start": float(scene_time),
                    "seed": seed,
                    "direction": -1 if seed % 2 else 1,
                    "truck_start": float(scene_time) + 1.7,
                    "enter_duration": 1.25,
                    "spray_duration": 1.65,
                    "exit_duration": 1.25,
                }
            )
            self._fires = self._fires[-2:]

    def launch_parachutists(self, center, scene_time, direction=1):
        """Fait sortir les habitants par les côtés du bâtiment menacé."""
        cx, cy = int(center[0]), int(center[1])
        candidates = [
            (index, rect)
            for index, rect in enumerate(self.rects)
            if (
                rect.left <= cx <= rect.right
                and rect.top - 24 <= cy <= rect.bottom
            )
        ]
        if not candidates:
            return False
        building_index, building = min(
            candidates,
            key=lambda item: abs(item[1].top - cy),
        )
        count = 2 + (abs(cx + self._generation) % 2)
        preferred_side = 1 if direction >= 0 else -1
        exit_top = building.top + 26
        exit_bottom = max(exit_top, building.bottom - 26)
        for index in range(count):
            side = preferred_side if index % 2 == 0 else -preferred_side
            exit_y = max(
                exit_top,
                min(exit_bottom, max(building.top + 34, cy) + index * 9),
            )
            self._parachutists.append(
                {
                    "x": building.right - 3 if side > 0 else building.left + 3,
                    "y": exit_y,
                    "start": float(scene_time) + index * 0.08,
                    "drift": side * (30 + index * 4),
                    "phase": (cx * 0.07 + index * 1.7) % math.tau,
                    "duration": 3.4,
                    "building_index": building_index,
                }
            )
        self._parachutists = self._parachutists[-8:]
        return True

    @staticmethod
    def _draw_fire_truck(surface, x, y, direction, light_on):
        """Petit camion lisible, dessiné avec peu de formes."""
        sign = 1 if direction >= 0 else -1
        ink = (26, 33, 47)
        red = (210, 48, 43)
        bright_red = (242, 68, 48)
        body_rect = pygame.Rect(x - 24, y - 15, 48, 14)
        pygame.draw.rect(surface, ink, body_rect.inflate(2, 2))
        pygame.draw.rect(surface, red, body_rect)

        cabin_left = x + 7 if sign > 0 else x - 22
        cabin = pygame.Rect(cabin_left, y - 25, 15, 13)
        pygame.draw.rect(surface, ink, cabin.inflate(2, 2))
        pygame.draw.rect(surface, bright_red, cabin)
        window_left = cabin.left + (6 if sign > 0 else 2)
        pygame.draw.rect(
            surface,
            (151, 215, 231),
            (window_left, cabin.top + 3, 6, 5),
        )

        pygame.draw.rect(surface, (240, 231, 195), (x - 20, y - 12, 18, 5))
        pygame.draw.line(
            surface,
            (224, 229, 223),
            (x - 19, y - 22),
            (x + 9, y - 22),
            3,
        )
        for rung in range(5):
            rung_x = x - 17 + rung * 6
            pygame.draw.line(
                surface,
                (112, 126, 132),
                (rung_x, y - 25),
                (rung_x, y - 19),
                1,
            )

        pygame.draw.circle(surface, ink, (x - 14, y), 6)
        pygame.draw.circle(surface, ink, (x + 15, y), 6)
        pygame.draw.circle(surface, (151, 161, 166), (x - 14, y), 2)
        pygame.draw.circle(surface, (151, 161, 166), (x + 15, y), 2)
        pygame.draw.rect(surface, (255, 222, 92), (x + sign * 22 - 2, y - 11, 3, 4))
        light_color = (88, 220, 255) if light_on else (32, 102, 164)
        pygame.draw.rect(surface, light_color, (x - 3, y - 28, 7, 4))

    @staticmethod
    def _draw_water_jet(surface, start, target, scene_time):
        """Jet courbe animé entre le camion et le feu."""
        start_x, start_y = start
        target_x, target_y = target
        for index in range(3):
            offset = (index - 1) * 2
            points = []
            for step in range(9):
                progress = step / 8.0
                x = start_x + (target_x - start_x) * progress
                y = (
                    start_y
                    + (target_y - start_y) * progress
                    - math.sin(progress * math.pi) * 24
                )
                wave = math.sin(scene_time * 18 + step * 1.5 + index) * 1.4
                points.append((int(x), int(y + offset + wave)))
            pygame.draw.lines(
                surface,
                (119, 220, 247) if index != 1 else (219, 248, 255),
                False,
                points,
                2,
            )
        pygame.draw.polygon(
            surface,
            (178, 231, 244),
            [
                (target_x - 4, target_y - 2),
                (target_x + 5, target_y),
                (target_x, target_y + 5),
            ],
        )

    def draw_emergency_effects(self, surface, scene_time):
        """Parachutistes, incendies et pompiers, avec listes très limitées."""
        collapses_alive = []
        for collapse in self._collapses:
            age = scene_time - collapse["start"]
            if age < 0:
                collapses_alive.append(collapse)
                continue
            if age >= collapse["duration"]:
                continue
            collapses_alive.append(collapse)
            progress = age / collapse["duration"]
            rect = collapse["rect"]
            height = max(12, int(rect.height * (1.0 - progress * 0.88)))
            crushed = pygame.transform.scale(
                collapse["image"],
                (rect.width, height),
            )
            crushed.set_alpha(int(255 * (1.0 - progress * 0.42)))
            surface.blit(crushed, (rect.x, rect.bottom - height))
            dust_y = rect.bottom - min(22, int(progress * 28))
            for index in range(8):
                dust_x = rect.left + (index * 17 + collapse["seed"]) % rect.width
                radius = 4 + (index + int(progress * 8)) % 5
                pygame.draw.circle(
                    surface,
                    (137, 119, 120),
                    (dust_x, dust_y - index % 3 * 4),
                    radius,
                )
        self._collapses = collapses_alive

        parachutists_alive = []
        for person in self._parachutists:
            age = scene_time - person["start"]
            if age < 0:
                parachutists_alive.append(person)
                continue
            if age >= person["duration"]:
                continue
            fall = min(age, 0.18) * 88 + max(0.0, age - 0.18) * 18
            x = person["x"] + person["drift"] * age
            y = person["y"] + fall + math.sin(age * 3.0 + person["phase"]) * 2
            if not (-20 < x < VIRTUAL_W + 20 and y < VIRTUAL_H + 15):
                continue
            parachutists_alive.append(person)
            px, py = int(x), int(y)
            if age >= 0.12:
                canopy = [
                    (px - 11, py - 9),
                    (px - 9, py - 15),
                    (px, py - 19),
                    (px + 9, py - 15),
                    (px + 11, py - 9),
                    (px + 6, py - 11),
                    (px, py - 8),
                    (px - 6, py - 11),
                ]
                pygame.draw.polygon(
                    surface,
                    (245, 93, 76),
                    canopy,
                )
                pygame.draw.line(surface, (255, 196, 87), (px, py - 18), (px, py - 9), 2)
                pygame.draw.line(surface, (236, 224, 196), (px - 8, py - 11), (px, py), 1)
                pygame.draw.line(surface, (236, 224, 196), (px + 8, py - 11), (px, py), 1)
            pygame.draw.circle(surface, (245, 190, 125), (px, py + 1), 2)
            pygame.draw.line(surface, (26, 34, 53), (px, py + 3), (px, py + 9), 2)
            pygame.draw.line(surface, (26, 34, 53), (px, py + 8), (px - 3, py + 12), 1)
            pygame.draw.line(surface, (26, 34, 53), (px, py + 8), (px + 3, py + 12), 1)
        self._parachutists = parachutists_alive

        fires_alive = []
        for fire in self._fires:
            age = scene_time - fire["start"]
            truck_age = scene_time - fire["truck_start"]
            enter_duration = fire["enter_duration"]
            spray_duration = fire["spray_duration"]
            exit_duration = fire["exit_duration"]
            total_duration = enter_duration + spray_duration + exit_duration
            if age < 0 or truck_age > total_duration + 0.9:
                continue
            fires_alive.append(fire)
            direction = fire["direction"]
            extinguished = truck_age >= enter_duration + 0.72

            if not extinguished:
                flame_count = 5
                for index in range(flame_count):
                    phase = int(scene_time * 14 + fire["seed"] + index) % 5
                    flame_x = fire["x"] + (index - 2) * 4
                    flame_y = fire["y"] - 3 - phase
                    pygame.draw.polygon(
                        surface,
                        (255, 187 if index % 2 else 103, 43),
                        [
                            (flame_x - 3, fire["y"] + 3),
                            (flame_x, flame_y - 6),
                            (flame_x + 3, fire["y"] + 3),
                        ],
                    )
            elif truck_age < total_duration + 0.65:
                steam_age = max(0.0, truck_age - enter_duration - 0.72)
                for index in range(5):
                    puff_x = fire["x"] + (index - 2) * 5
                    puff_y = fire["y"] - int(steam_age * 16) - index * 3
                    pygame.draw.circle(surface, (178, 205, 214), (puff_x, puff_y), 4 + index % 2)

            if 0.0 <= truck_age <= total_duration:
                road_y = VIRTUAL_H - 8
                start_x = -38 if direction > 0 else VIRTUAL_W + 38
                end_x = VIRTUAL_W + 38 if direction > 0 else -38
                stop_x = max(
                    45,
                    min(
                        VIRTUAL_W - 45,
                        fire["x"] - direction * 68,
                    ),
                )
                if truck_age < enter_duration:
                    progress = truck_age / enter_duration
                    progress = progress * progress * (3.0 - 2.0 * progress)
                    truck_x = start_x + (stop_x - start_x) * progress
                elif truck_age < enter_duration + spray_duration:
                    truck_x = stop_x
                    nozzle_x = int(truck_x + direction * 10)
                    self._draw_water_jet(
                        surface,
                        (nozzle_x, road_y - 27),
                        (fire["x"], fire["y"]),
                        scene_time,
                    )
                else:
                    progress = (
                        truck_age - enter_duration - spray_duration
                    ) / exit_duration
                    progress = progress * progress * (3.0 - 2.0 * progress)
                    truck_x = stop_x + (end_x - stop_x) * progress
                self._draw_fire_truck(
                    surface,
                    int(truck_x),
                    road_y,
                    direction,
                    int(scene_time * 8) % 2 == 0,
                )
        self._fires = fires_alive

    def draw_damage_effects(self, surface, scene_time):
        """Fumée épaisse et gros débris après impact."""
        if not self._smoke_plumes and not self._debris_particles:
            return
        alive = []
        layer = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        for plume in self._smoke_plumes:
            age = scene_time - plume["start"]
            if age < 0 or age >= plume["duration"]:
                continue
            alive.append(plume)
            progress = age / plume["duration"]
            alpha = int(225 * (1.0 - progress) ** 0.65)
            puff_count = 10 if plume["strong"] else 8
            smoke_color = (
                (83, 86, 98)
                if self.atmosphere_name in ("night", "rain", "storm")
                else (55, 54, 62)
            )
            smoke_highlight = (
                (156, 157, 166)
                if self.atmosphere_name in ("night", "rain", "storm")
                else (116, 111, 117)
            )
            for index in range(puff_count):
                phase = plume["seed"] + index * 1.9
                x = plume["x"] + math.sin(age * 1.2 + phase) * (6 + index)
                y = plume["y"] - age * (8 + index * 0.8) - index * 5
                radius = 7 + index % 4 * 2 + int(progress * 7)
                puff_alpha = max(0, alpha - index * 8)
                pygame.draw.circle(
                    layer,
                    (*smoke_color, puff_alpha),
                    (int(x), int(y)),
                    radius,
                )
                pygame.draw.circle(
                    layer,
                    (*smoke_highlight, puff_alpha // 2),
                    (int(x - radius * 0.25), int(y - radius * 0.25)),
                    max(2, radius // 2),
                )
            if age < 0.9:
                glow_alpha = int(190 * (1.0 - age / 0.9))
                pygame.draw.circle(
                    layer,
                    (255, 115, 47, glow_alpha),
                    (plume["x"], plume["y"]),
                    8 + int(age * 8),
                    2,
                )
            if age < 4.5:
                rubble_alpha = int(235 * (1.0 - age / 4.5))
                for index in range(9):
                    angle = index * math.tau / 9.0 + plume["seed"] * 0.03
                    distance = 25 + index % 3 * 5
                    chip_x = plume["x"] + math.cos(angle) * distance
                    chip_y = plume["y"] + math.sin(angle) * distance
                    size = 3 + index % 3
                    chip_color = (
                        (234, 111, 55, rubble_alpha)
                        if index % 4 == 0
                        else (82, 61, 72, rubble_alpha)
                    )
                    pygame.draw.rect(
                        layer,
                        chip_color,
                        (int(chip_x), int(chip_y), size, size),
                    )
        self._smoke_plumes = alive

        debris_alive = []
        for chunk in self._debris_particles:
            age = scene_time - chunk["start"]
            if age < 0 or age >= chunk["duration"]:
                continue
            debris_alive.append(chunk)
            x = chunk["x"] + chunk["vx"] * age
            y = chunk["y"] + chunk["vy"] * age + 55 * age * age
            fade = max(0.0, 1.0 - age / chunk["duration"])
            size = chunk["size"]
            pygame.draw.rect(
                layer,
                (*chunk["color"], int(255 * fade)),
                (int(x) - size // 2, int(y) - size // 2, size, size),
            )
        self._debris_particles = debris_alive
        surface.blit(layer, (0, 0))

    def storm_flash_active(self, scene_time):
        if self.atmosphere["weather"] != "storm":
            return False
        phase = scene_time % 8.0
        return 0.10 < phase < 0.20 or 0.28 < phase < 0.34

    def draw_lightning_glow(self, surface, scene_time):
        if not self.storm_flash_active(scene_time):
            return
        flash = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        flash.fill((186, 199, 255, 46))
        surface.blit(flash, (0, 0))

    def _build_far_layer(self, rng):
        self._far_layer.fill((0, 0, 0, 0))
        far_palette = {
            "sunny": ((45, 63, 92), (29, 42, 70), (255, 193, 104)),
            "night": ((12, 18, 44), (6, 12, 31), (255, 221, 116)),
            "rain": ((31, 43, 57), (18, 29, 43), (229, 181, 98)),
            "snow": ((55, 63, 82), (34, 43, 64), (255, 222, 139)),
            "storm": ((20, 22, 38), (9, 12, 27), (245, 210, 125)),
        }
        base, shadow, light = far_palette.get(
            self.atmosphere_name,
            ((35, 25, 64), (22, 18, 47), (231, 133, 95)),
        )
        if self.city_style_name == "seaside":
            water = _lerp_color(base, (49, 157, 191), 0.62)
            water_light = _lerp_color(water, (214, 245, 250), 0.62)
            pygame.draw.rect(
                self._far_layer,
                (*water, 225),
                (0, 218, VIRTUAL_W, 138),
            )
            for yy in range(224, 352, 9):
                offset = (yy // 9 % 2) * 18
                for xx in range(-offset, VIRTUAL_W, 52):
                    pygame.draw.line(
                        self._far_layer,
                        (*water_light, 105),
                        (xx, yy),
                        (min(VIRTUAL_W, xx + 27), yy),
                        2,
                    )

        x = -8
        index = 0
        while x < VIRTUAL_W:
            width = rng.randint(18, 42)
            height = (
                rng.randint(22, 54)
                if self.city_style_name == "seaside"
                else rng.randint(42, 122)
            )
            bottom = 356
            rect = pygame.Rect(x, bottom - height, width, height)
            color = (
                min(255, base[0] + index % 3 * 5),
                min(255, base[1] + index % 2 * 3),
                min(255, base[2] + index % 4 * 4),
                220,
            )
            pygame.draw.rect(self._far_layer, color, rect)
            pygame.draw.rect(
                self._far_layer,
                (*shadow, 210),
                (rect.right - 3, rect.top, 3, rect.h),
            )
            if index % 4 == 0:
                pygame.draw.rect(
                    self._far_layer,
                    (*shadow, 220),
                    (rect.centerx - 1, rect.top - 10, 2, 10),
                )
            for yy in range(rect.top + 9, rect.bottom - 5, 13):
                for xx in range(rect.left + 6, rect.right - 4, 9):
                    if rng.random() < 0.16:
                        pygame.draw.rect(
                            self._far_layer,
                            (*light, 105),
                            (xx, yy, 3, 4),
                        )
            x += width + rng.randint(2, 7)
            index += 1

        landmark_x = int(VIRTUAL_W * 0.62)
        if self.city_style_name == "paris":
            tower_dark = (53, 42, 50, 255)
            tower = (147, 91, 65, 255)
            tower_light = (230, 166, 90, 230)
            left_leg = [
                (landmark_x, 101),
                (landmark_x - 12, 160),
                (landmark_x - 28, 230),
                (landmark_x - 62, 354),
            ]
            right_leg = [
                (landmark_x, 101),
                (landmark_x + 12, 160),
                (landmark_x + 28, 230),
                (landmark_x + 62, 354),
            ]
            pygame.draw.lines(
                self._far_layer,
                tower_dark,
                False,
                left_leg,
                10,
            )
            pygame.draw.lines(
                self._far_layer,
                tower_dark,
                False,
                right_leg,
                10,
            )
            pygame.draw.lines(self._far_layer, tower, False, left_leg, 5)
            pygame.draw.lines(self._far_layer, tower, False, right_leg, 5)

            # Trois grandes plateformes, signature de la tour.
            for yy, half_width in ((143, 15), (214, 34), (289, 52)):
                pygame.draw.line(
                    self._far_layer,
                    tower_dark,
                    (landmark_x - half_width, yy),
                    (landmark_x + half_width, yy),
                    9,
                )
                pygame.draw.line(
                    self._far_layer,
                    tower_light,
                    (landmark_x - half_width + 2, yy),
                    (landmark_x + half_width - 2, yy),
                    4,
                )

            # Croisillons métalliques entre les plateformes.
            for top_y, top_half, bottom_y, bottom_half in (
                (149, 16, 208, 31),
                (220, 35, 283, 49),
                (296, 54, 342, 67),
            ):
                pygame.draw.line(
                    self._far_layer,
                    tower,
                    (landmark_x - top_half, top_y),
                    (landmark_x + bottom_half, bottom_y),
                    3,
                )
                pygame.draw.line(
                    self._far_layer,
                    tower,
                    (landmark_x + top_half, top_y),
                    (landmark_x - bottom_half, bottom_y),
                    3,
                )

            # Grande arche vide entre les deux pieds.
            left_arch = [
                (landmark_x - 59, 354),
                (landmark_x - 52, 326),
                (landmark_x - 38, 306),
                (landmark_x - 18, 296),
            ]
            right_arch = [
                (landmark_x + 59, 354),
                (landmark_x + 52, 326),
                (landmark_x + 38, 306),
                (landmark_x + 18, 296),
            ]
            pygame.draw.lines(
                self._far_layer,
                tower_light,
                False,
                left_arch,
                4,
            )
            pygame.draw.lines(
                self._far_layer,
                tower_light,
                False,
                right_arch,
                4,
            )
            pygame.draw.line(
                self._far_layer,
                tower_light,
                (landmark_x - 18, 296),
                (landmark_x + 18, 296),
                4,
            )

            pygame.draw.line(
                self._far_layer,
                tower_dark,
                (landmark_x, 57),
                (landmark_x, 103),
                6,
            )
            pygame.draw.line(
                self._far_layer,
                tower_light,
                (landmark_x, 58),
                (landmark_x, 103),
                3,
            )
            pygame.draw.circle(
                self._far_layer,
                (255, 221, 119, 235),
                (landmark_x, 56),
                3,
            )
        elif self.city_style_name == "tokyo":
            tower_red = (240, 75, 82, 245)
            pygame.draw.line(
                self._far_layer,
                tower_red,
                (landmark_x, 90),
                (landmark_x - 34, 354),
                6,
            )
            pygame.draw.line(
                self._far_layer,
                tower_red,
                (landmark_x, 90),
                (landmark_x + 34, 354),
                6,
            )
            for yy, width in ((143, 14), (195, 28), (256, 45), (322, 61)):
                pygame.draw.line(
                    self._far_layer,
                    (242, 233, 206, 230),
                    (landmark_x - width // 2, yy),
                    (landmark_x + width // 2, yy),
                    4,
                )
            for offset, neon in (
                (-112, (255, 68, 171, 220)),
                (96, (60, 232, 242, 220)),
            ):
                sign = pygame.Rect(landmark_x + offset, 156, 30, 74)
                pygame.draw.rect(self._far_layer, neon, sign, 3)
                for yy in range(sign.top + 9, sign.bottom - 4, 12):
                    pygame.draw.line(
                        self._far_layer,
                        neon,
                        (sign.left + 7, yy),
                        (sign.right - 7, yy),
                        3,
                    )
        elif self.city_style_name == "future":
            neon = (73, 232, 242, 205)
            pygame.draw.ellipse(
                self._far_layer,
                (*base, 245),
                (landmark_x - 78, 190, 156, 164),
            )
            pygame.draw.arc(
                self._far_layer,
                neon,
                (landmark_x - 78, 190, 156, 164),
                math.pi,
                math.tau,
                5,
            )
            pygame.draw.ellipse(
                self._far_layer,
                neon,
                (landmark_x - 54, 218, 108, 42),
                4,
            )
            pygame.draw.line(
                self._far_layer,
                neon,
                (landmark_x, 112),
                (landmark_x, 240),
                4,
            )
        elif self.city_style_name == "seaside":
            lighthouse_x = landmark_x + 70
            pygame.draw.polygon(
                self._far_layer,
                (239, 230, 205, 245),
                [
                    (lighthouse_x - 12, 330),
                    (lighthouse_x - 7, 234),
                    (lighthouse_x + 7, 234),
                    (lighthouse_x + 12, 330),
                ],
            )
            pygame.draw.rect(
                self._far_layer,
                (226, 75, 72, 245),
                (lighthouse_x - 9, 254, 18, 12),
            )
            pygame.draw.rect(
                self._far_layer,
                (226, 75, 72, 245),
                (lighthouse_x - 10, 285, 20, 12),
            )
            pygame.draw.rect(
                self._far_layer,
                (253, 220, 111, 245),
                (lighthouse_x - 11, 225, 22, 12),
            )
            pygame.draw.polygon(
                self._far_layer,
                (129, 55, 58, 245),
                [
                    (lighthouse_x - 15, 225),
                    (lighthouse_x, 211),
                    (lighthouse_x + 15, 225),
                ],
            )
            boat_x = landmark_x - 108
            pygame.draw.polygon(
                self._far_layer,
                (108, 49, 55, 220),
                [
                    (boat_x - 21, 280),
                    (boat_x + 25, 280),
                    (boat_x + 16, 291),
                    (boat_x - 13, 291),
                ],
            )
            pygame.draw.line(
                self._far_layer,
                (245, 236, 204, 225),
                (boat_x, 279),
                (boat_x, 236),
                3,
            )
            pygame.draw.polygon(
                self._far_layer,
                (245, 236, 204, 210),
                [(boat_x + 2, 240), (boat_x + 2, 274), (boat_x + 25, 274)],
            )
            palm_x = landmark_x - 170
            pygame.draw.line(
                self._far_layer,
                (79, 58, 55, 225),
                (palm_x, 329),
                (palm_x + 5, 259),
                5,
            )
            for dx, dy in ((-25, -7), (-17, -17), (0, -20), (19, -15), (27, -4)):
                pygame.draw.line(
                    self._far_layer,
                    (40, 83, 74, 225),
                    (palm_x + 5, 259),
                    (palm_x + 5 + dx, 259 + dy),
                    5,
                )
        else:
            empire = pygame.Rect(landmark_x - 27, 137, 54, 217)
            pygame.draw.rect(
                self._far_layer,
                (*shadow, 245),
                empire,
            )
            pygame.draw.rect(
                self._far_layer,
                (*base, 245),
                (landmark_x - 20, 119, 40, 20),
            )
            pygame.draw.rect(
                self._far_layer,
                (*shadow, 245),
                (landmark_x - 13, 103, 26, 18),
            )
            pygame.draw.rect(
                self._far_layer,
                (*base, 245),
                (landmark_x - 7, 88, 14, 17),
            )
            pygame.draw.polygon(
                self._far_layer,
                (*light, 220),
                [(landmark_x, 56), (landmark_x - 4, 90), (landmark_x + 4, 90)],
            )
        pygame.draw.rect(self._far_layer, (*shadow, 235), (0, 354, VIRTUAL_W, 46))

    def draw_background(self, surface, scene_time=None, wind_value=0):
        if scene_time is None:
            scene_time = pygame.time.get_ticks() / 1000.0
        surface.blit(self._sky, (0, 0))

        # Étoiles: seulement deux niveaux de lumière, donc aucun flou.
        for x, y, phase, size in self._stars:
            bright = int(scene_time * 2.0 + phase) % 4 == 0
            color = (255, 235, 177) if bright else (157, 142, 183)
            pygame.draw.rect(surface, color, (x, y, size, size))
            if bright and size == 2:
                pygame.draw.rect(surface, (220, 183, 174), (x - 1, y, 4, 1))

        wind_strength = max(-WIND_MAX, min(WIND_MAX, float(wind_value)))
        wind_direction = -1.0 if wind_strength < 0 else (1.0 if wind_strength > 0 else 0.0)
        wind_factor = abs(wind_strength) / float(WIND_MAX)
        for cloud in self._clouds:
            image = cloud["surface"]
            span = VIRTUAL_W + image.get_width() * 2
            travel = scene_time * cloud["speed"] * wind_factor * wind_direction
            x = (cloud["x"] + travel) % span - image.get_width()
            surface.blit(image, (int(x), cloud["y"]))

        surface.blit(self._far_layer, (0, 0))
        self._draw_background_weather(surface, scene_time, wind_strength)

    def _draw_background_weather(self, surface, scene_time, wind_value):
        weather = self.atmosphere["weather"]
        if weather == "sun_haze":
            haze = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
            for particle in self._weather_particles:
                x = int(
                    (
                        particle["x"]
                        + scene_time * (2.0 + wind_value * 0.25)
                    )
                    % VIRTUAL_W
                )
                y = int(particle["y"] % 250)
                alpha = 22 + particle["size"] * 8
                pygame.draw.circle(
                    haze,
                    (255, 224, 152, alpha),
                    (x, y),
                    particle["size"] + 2,
                )
            surface.blit(haze, (0, 0))

        if weather == "storm":
            # Éclair court et déterministe, environ toutes les huit secondes.
            flash_phase = scene_time % 8.0
            if 0.10 < flash_phase < 0.20 or 0.28 < flash_phase < 0.34:
                flash = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
                flash.fill((181, 194, 255, 76))
                surface.blit(flash, (0, 0))
                bolt_x = int(VIRTUAL_W * 0.70)
                points = [
                    (bolt_x, 28),
                    (bolt_x - 19, 82),
                    (bolt_x - 2, 78),
                    (bolt_x - 34, 151),
                ]
                pygame.draw.lines(surface, (235, 240, 255), False, points, 3)

    def draw_weather_foreground(self, surface, scene_time, wind_value):
        """Météo devant la ville. Le HUD sera dessiné après."""
        weather = self.atmosphere["weather"]
        if weather not in ("rain", "snow", "storm"):
            return

        layer = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        wind_value = max(-WIND_MAX, min(WIND_MAX, float(wind_value)))
        for particle in self._weather_particles:
            speed = particle["speed"]
            y = (particle["y"] + scene_time * speed) % (VIRTUAL_H + 28) - 14
            if weather == "snow":
                drift = (
                    scene_time * wind_value * 3.0
                    + math.sin(scene_time * 1.8 + particle["phase"]) * 10.0
                )
                x = (particle["x"] + drift) % (VIRTUAL_W + 16) - 8
                radius = max(1, particle["size"])
                pygame.draw.circle(
                    layer,
                    (239, 247, 255, 205),
                    (int(x), int(y)),
                    radius,
                )
            else:
                drift_speed = wind_value * (5.2 if weather == "storm" else 3.6)
                x = (particle["x"] + scene_time * drift_speed) % (VIRTUAL_W + 28) - 14
                slant = int(wind_value * (0.95 if weather == "storm" else 0.65))
                length = 11 + particle["size"] * (3 if weather == "storm" else 2)
                color = (
                    (181, 198, 231, 185)
                    if weather == "storm"
                    else (151, 205, 229, 145)
                )
                pygame.draw.line(
                    layer,
                    color,
                    (int(x), int(y)),
                    (int(x + slant), int(y + length)),
                    2 if weather == "storm" and particle["size"] > 1 else 1,
                )

        if weather == "snow":
            # Neige sur les parties de toit encore intactes.
            for rect in self.rects:
                y = max(0, rect.top - 2)
                for x in range(rect.left + 2, rect.right - 2, 3):
                    try:
                        solid = self.mask.get_at((x, min(VIRTUAL_H - 1, rect.top + 3))).a
                    except IndexError:
                        solid = 0
                    if solid:
                        pygame.draw.rect(layer, (229, 240, 250, 235), (x, y, 3, 2))

        surface.blit(layer, (0, 0))

    def rebuild_mask(self):
        self.mask.fill((0, 0, 0, 0))
        for index, rect in enumerate(self.rects):
            if index < len(self._styles):
                style = self._styles[index]
            else:
                style = {
                    "color": BUILDING_COLORS[index % len(BUILDING_COLORS)],
                    "roof": "lip",
                    "windows": [],
                    "trim": 0,
                }
            self._draw_building(rect, style, index)
        self._damage_revision += 1
        self._life_checked_revision = -1

    def _draw_building(self, rect, style, index):
        theme = BUILDING_THEMES.get(
            self.atmosphere_name,
            BUILDING_THEMES["sunset"],
        )
        palette = theme["palette"]
        palette_slot = style.get("palette_slot")
        color = (
            palette[int(palette_slot) % len(palette)]
            if palette_slot is not None
            else style["color"]
        )
        city_settings = CITY_STYLES.get(
            self.city_style_name,
            CITY_STYLES["new_york"],
        )
        color = _lerp_color(
            color,
            city_settings["tint"],
            city_settings["tint_amount"],
        )
        outline = (*theme["outline"], 255)
        shadow = _lerp_color(color, theme["shadow"], 0.38)
        highlight = _lerp_color(
            color,
            theme["highlight"],
            theme["highlight_amount"],
        )

        pygame.draw.rect(self.mask, outline, rect)
        inner = pygame.Rect(rect.x + 2, rect.y + 3, max(1, rect.w - 4), rect.h - 3)
        pygame.draw.rect(self.mask, (*color, 255), inner)
        pygame.draw.rect(self.mask, (*highlight, 255), (rect.x + 2, rect.y + 3, 2, rect.h - 3))
        pygame.draw.rect(self.mask, (*shadow, 255), (rect.right - 5, rect.y + 3, 3, rect.h - 3))
        pygame.draw.rect(self.mask, outline, (rect.x, rect.top, rect.w, 3))

        if style.get("trim") == 1:
            for yy in range(rect.top + 12, rect.bottom, 36):
                pygame.draw.rect(self.mask, (*shadow, 255), (rect.x + 2, yy, rect.w - 4, 2))
        elif style.get("trim") == 2:
            pygame.draw.rect(
                self.mask,
                (*highlight, 255),
                (rect.centerx - 1, rect.top + 3, 2, max(1, rect.h - 3)),
            )

        roof = style.get("roof", "lip")
        if roof == "antenna":
            antenna_x = rect.right - max(5, rect.w // 5)
            pygame.draw.rect(self.mask, outline, (antenna_x, rect.top - 12, 2, 12))
            pygame.draw.rect(self.mask, (*CORAL, 255), (antenna_x - 1, rect.top - 13, 4, 3))
        elif roof == "chimney" and rect.w >= 30:
            chimney_x = rect.left + 5
            pygame.draw.rect(self.mask, outline, (chimney_x, rect.top - 8, 8, 8))
            pygame.draw.rect(self.mask, (*shadow, 255), (chimney_x + 2, rect.top - 6, 4, 6))
        elif roof == "tank" and rect.w >= 36:
            tank_x = rect.left + 4
            pygame.draw.rect(self.mask, outline, (tank_x, rect.top - 7, 13, 6))
            pygame.draw.rect(self.mask, (*highlight, 255), (tank_x + 2, rect.top - 5, 9, 3))
            pygame.draw.rect(self.mask, outline, (tank_x + 2, rect.top - 1, 2, 3))
            pygame.draw.rect(self.mask, outline, (tank_x + 9, rect.top - 1, 2, 3))
        elif roof == "billboard" and rect.w >= 38:
            sign_x = rect.left + 3
            pygame.draw.rect(self.mask, outline, (sign_x + 2, rect.top - 12, 2, 12))
            pygame.draw.rect(self.mask, outline, (sign_x + 18, rect.top - 12, 2, 12))
            pygame.draw.rect(self.mask, (*highlight, 255), (sign_x, rect.top - 17, 23, 9))
            pygame.draw.rect(self.mask, outline, (sign_x, rect.top - 17, 23, 9), 2)
        elif roof == "mansard" and rect.w >= 30:
            roof_width = min(rect.w - 5, 30)
            pygame.draw.polygon(
                self.mask,
                outline,
                [
                    (rect.left + 2, rect.top),
                    (rect.left + 7, rect.top - 11),
                    (rect.left + roof_width, rect.top - 11),
                    (rect.left + roof_width + 5, rect.top),
                ],
            )
            pygame.draw.polygon(
                self.mask,
                (*shadow, 255),
                [
                    (rect.left + 5, rect.top - 2),
                    (rect.left + 9, rect.top - 9),
                    (rect.left + roof_width - 2, rect.top - 9),
                    (rect.left + roof_width + 2, rect.top - 2),
                ],
            )
        elif roof == "neon" and rect.w >= 32:
            sign_x = rect.right - 10
            neon = (255, 75, 173) if index % 2 else (73, 226, 238)
            pygame.draw.rect(self.mask, outline, (sign_x - 2, rect.top + 7, 9, 29))
            pygame.draw.rect(self.mask, (*neon, 255), (sign_x, rect.top + 9, 5, 25))
        elif roof == "solar" and rect.w >= 34:
            solar_x = rect.left + 4
            pygame.draw.polygon(
                self.mask,
                outline,
                [
                    (solar_x, rect.top - 2),
                    (solar_x + 5, rect.top - 10),
                    (solar_x + 22, rect.top - 10),
                    (solar_x + 18, rect.top - 2),
                ],
            )
            pygame.draw.polygon(
                self.mask,
                (72, 142, 180, 255),
                [
                    (solar_x + 3, rect.top - 3),
                    (solar_x + 7, rect.top - 8),
                    (solar_x + 19, rect.top - 8),
                    (solar_x + 16, rect.top - 3),
                ],
            )
        elif roof == "dome" and rect.w >= 34:
            dome_rect = pygame.Rect(rect.left + 3, rect.top - 10, 24, 18)
            pygame.draw.arc(self.mask, outline, dome_rect, math.pi, math.tau, 5)
            pygame.draw.line(
                self.mask,
                (*highlight, 255),
                (dome_rect.left + 3, rect.top - 2),
                (dome_rect.right - 3, rect.top - 2),
                3,
            )
        elif roof == "dish" and rect.w >= 34:
            dish_x = rect.left + 13
            pygame.draw.line(
                self.mask,
                outline,
                (dish_x, rect.top),
                (dish_x, rect.top - 11),
                3,
            )
            pygame.draw.arc(
                self.mask,
                (*highlight, 255),
                (dish_x - 11, rect.top - 18, 20, 13),
                0.15,
                math.pi - 0.15,
                3,
            )
        else:
            pygame.draw.rect(self.mask, outline, (rect.x - 1, rect.top - 2, rect.w + 2, 3))
            pygame.draw.rect(self.mask, (*highlight, 255), (rect.x + 2, rect.top - 1, rect.w - 4, 1))

        windows = style.get("windows", ())
        start_y = rect.top + 10
        for row, line in enumerate(windows):
            yy = start_y + row * 12
            if yy + 6 >= rect.bottom:
                break
            if not line:
                continue
            available = rect.w - 10
            step = max(8, available // len(line))
            for column, state in enumerate(line):
                xx = rect.left + 5 + column * step
                if xx + 5 >= rect.right:
                    continue
                pygame.draw.rect(
                    self.mask,
                    (*theme["window_dark"], 255),
                    (xx, yy, 5, 7),
                )
                if state == 1:
                    pygame.draw.rect(
                        self.mask,
                        (*theme["window_lit"], 255),
                        (xx + 1, yy + 1, 3, 5),
                    )
                    window_glint = _lerp_color(
                        theme["window_lit"],
                        (255, 255, 238),
                        0.48,
                    )
                    pygame.draw.rect(
                        self.mask,
                        (*window_glint, 255),
                        (xx + 1, yy + 1, 3, 1),
                    )
                elif state == 2:
                    pygame.draw.rect(
                        self.mask,
                        (*theme["window_alt"], 255),
                        (xx + 1, yy + 1, 3, 5),
                    )


def explode_in_city(city: City, center, scene_time=None, strong=False):
    """Creuse un cratere irregulier et garde un bord sombre dans la facade."""
    cx, cy = int(center[0]), int(center[1])
    radius = EXPLOSION_RADIUS + (8 if strong else 5)
    source = city.mask.copy()
    left = max(0, cx - radius - 4)
    right = min(VIRTUAL_W - 1, cx + radius + 4)
    top = max(0, cy - radius - 4)
    bottom = min(VIRTUAL_H - 1, cy + radius + 4)

    city.mask.lock()
    source.lock()
    try:
        for y in range(top, bottom + 1):
            for x in range(left, right + 1):
                if source.get_at((x, y)).a == 0:
                    continue
                distance = math.hypot(x - cx, y - cy)
                chip = ((x * 17 + y * 31) % 7) - 3
                edge = radius + chip * 0.65
                if distance <= edge:
                    city.mask.set_at((x, y), (0, 0, 0, 0))
                elif distance <= radius + 6:
                    soot = max(15, int(47 - (distance - radius) * 5))
                    city.mask.set_at((x, y), (soot, soot - 5, soot + 5, 255))
    finally:
        source.unlock()
        city.mask.unlock()
    city._damage_revision += 1
    if scene_time is not None:
        city.add_damage_effect(center, scene_time, strong=strong)


def draw_explosion_frame(vsurf, center, progress, max_radius=42, accent=None):
    """Dessine une frame d'explosion. progress va de 0.0 a 1.0."""
    progress = max(0.0, min(1.0, float(progress)))
    cx, cy = int(center[0]), int(center[1])
    accent = accent or SUN_ORANGE
    layer = pygame.Surface(vsurf.get_size(), pygame.SRCALPHA)

    # Onde de choc.
    wave_radius = max(2, int(4 + max_radius * progress))
    wave_alpha = int(235 * (1.0 - progress))
    pygame.draw.circle(layer, (*accent, wave_alpha), (cx, cy), wave_radius, 2)
    if progress < 0.35:
        inner_wave = max(2, int(wave_radius * 0.62))
        pygame.draw.circle(layer, (255, 239, 167, 190), (cx, cy), inner_wave, 2)

    # Coeur en feu, puis fumee.
    flame_phase = max(0.0, 1.0 - progress / 0.72)
    if flame_phase > 0:
        core = max(2, int(max_radius * (0.18 + 0.42 * flame_phase)))
        pygame.draw.circle(layer, (238, 72, 63, 235), (cx, cy), core)
        pygame.draw.rect(
            layer,
            (255, 137, 53, 245),
            (cx - core, cy - core // 2, core * 2, core),
        )
        pygame.draw.circle(layer, (255, 218, 82, 255), (cx, cy), max(2, core // 2))
        if progress < 0.18:
            flash = int(max_radius * (1.0 - progress * 3.0))
            pygame.draw.rect(layer, (255, 249, 204, 230), (cx - flash, cy - 2, flash * 2, 4))
            pygame.draw.rect(layer, (255, 249, 204, 230), (cx - 2, cy - flash, 4, flash * 2))

    # Particules deterministes; aucun random global.
    for index in range(22):
        angle = index * (math.tau / 22.0) + (index % 3) * 0.11
        distance = max_radius * progress * (0.55 + (index % 5) * 0.09)
        px = int(cx + math.cos(angle) * distance)
        py = int(cy + math.sin(angle) * distance + progress * progress * 12)
        size = 4 if index % 6 == 0 else (3 if index % 3 == 0 else 2)
        if progress < 0.62:
            color = (255, 189 if index % 2 else 112, 62, int(245 * (1.0 - progress)))
        else:
            color = (68, 49, 76, int(210 * (1.0 - progress)))
        pygame.draw.rect(layer, color, (px - size // 2, py - size // 2, size, size))

    if progress > 0.38:
        smoke_t = (progress - 0.38) / 0.62
        smoke_alpha = int(170 * (1.0 - smoke_t))
        for index in range(5):
            px = cx + (index - 2) * 7
            py = cy - int(smoke_t * (14 + index % 2 * 7))
            radius = 5 + index % 3 * 2
            pygame.draw.circle(layer, (53, 39, 66, smoke_alpha), (px, py), radius)

    vsurf.blit(layer, (0, 0))


def draw_explosion_wave(vsurf, center, max_radius=40, color=(255, 165, 0), progress=0.42):
    """Ancien appel conserve; accepte maintenant une progression optionnelle."""
    draw_explosion_frame(vsurf, center, progress, max_radius=max_radius, accent=color)


def _wind_panel_rect():
    """Place le vent entre la carte P1 et le panneau DUEL."""
    player_right = 8 + 176
    duel_left = VIRTUAL_W // 2 - 53
    available = max(76, duel_left - player_right)
    width = max(76, min(142, available - 8))
    x = player_right + max(4, (available - width) // 2)
    return pygame.Rect(x, 10, width, 34)


def draw_wind_indicator(vsurf, font, wind_value, position=None):
    value = max(-WIND_MAX, min(WIND_MAX, int(round(wind_value))))
    panel = pygame.Rect(position) if position is not None else _wind_panel_rect()
    direction_color = (93, 211, 238) if value < 0 else (255, 190, 72)
    if value == 0:
        direction_color = (204, 194, 215)
    draw_panel(
        vsurf,
        panel,
        fill=HUD_BG_SOFT,
        border=HUD_BORDER,
        accent=direction_color,
        shadow=True,
    )

    label = render_text(font, "VENT", (200, 184, 209))
    value_text = render_text(font, f"{value:+d}", CREAM)
    compact = panel.width < 100
    side_pad = 6 if compact else 10
    value_pad = 5 if compact else 8
    vsurf.blit(label, (panel.x + side_pad, panel.y + 3))
    vsurf.blit(
        value_text,
        (panel.right - value_text.get_width() - value_pad, panel.y + 3),
    )

    line_y = panel.bottom - 8
    left = panel.x + (7 if compact else 12)
    right = panel.right - (6 if compact else 10)
    center_x = (left + right) // 2
    pygame.draw.line(vsurf, (93, 67, 103), (left, line_y), (right, line_y), 2)
    pygame.draw.rect(vsurf, (205, 178, 187), (center_x, line_y - 2, 1, 5))

    if value:
        strength = abs(value) / float(max(1, WIND_MAX))
        tip = center_x + int((right - center_x - 2) * strength) * (1 if value > 0 else -1)
        pygame.draw.line(vsurf, direction_color, (center_x, line_y), (tip, line_y), 3)
        sign = 1 if value > 0 else -1
        pygame.draw.polygon(
            vsurf,
            direction_color,
            [(tip, line_y), (tip - sign * 6, line_y - 4), (tip - sign * 6, line_y + 4)],
        )
    else:
        pygame.draw.rect(vsurf, direction_color, (center_x - 2, line_y - 2, 5, 5), 1)


def _active_player(city, players, banana_active, explicit):
    previous_flying = city._scene_banana_active
    if explicit is not None:
        city._hud_active = max(0, min(len(players) - 1, int(explicit)))
    else:
        raised = [index for index, player in enumerate(players) if player.state != "idle"]
        if len(raised) == 1:
            city._hud_active = raised[0]
        elif previous_flying and not banana_active and len(players) == 2:
            city._hud_active = 1 - city._hud_active
    city._scene_banana_active = bool(banana_active)
    return city._hud_active


def _draw_player_card(surface, player, index, active, font, font_small):
    width = 176
    x = 8 if index == 0 else VIRTUAL_W - width - 8
    rect = pygame.Rect(x, 7, width, 40)
    player_color = tuple(player.color[:3]) if hasattr(player, "color") else (210, 190, 220)
    accent = HUD_ACTIVE if active else player_color
    border = HUD_ACTIVE if active else HUD_BORDER
    draw_panel(surface, rect, fill=HUD_BG, border=border, accent=accent, shadow=True)

    tag = render_text(font_small, f"P{index + 1}", accent)
    surface.blit(tag, (rect.x + 10, rect.y + 3))

    name = clip_text(font, player.name, 112)
    name_img = render_text(font, name, CREAM if active else (226, 211, 224))
    surface.blit(name_img, (rect.x + 31, rect.y + 8))

    score = render_text(font, str(player.score), BANANA_YELLOW if active else WHITE)
    surface.blit(score, (rect.right - score.get_width() - 10, rect.y + 8))
    if active:
        pygame.draw.rect(surface, HUD_ACTIVE, (rect.x + 10, rect.bottom - 5, 13, 2))


def _draw_score_panel(surface, players, font, font_small):
    rect = pygame.Rect(VIRTUAL_W // 2 - 53, 6, 106, 41)
    draw_panel(surface, rect, fill=(16, 13, 34, 238), border=(184, 90, 114), shadow=True)
    label = render_text(font_small, "DUEL", (212, 154, 163))
    surface.blit(label, (rect.centerx - label.get_width() // 2, rect.y + 2))
    score = render_text(font, f"{players[0].score}  :  {players[1].score}", CREAM)
    surface.blit(score, (rect.centerx - score.get_width() // 2, rect.bottom - score.get_height() - 3))


def _point_xy(point):
    if hasattr(point, "x") and hasattr(point, "y"):
        return float(point.x), float(point.y)
    if point and hasattr(point[0], "x") and hasattr(point[0], "y"):
        return float(point[0].x), float(point[0].y)
    return float(point[0]), float(point[1])


def _update_internal_trail(city, active, position):
    if not active:
        city._banana_trail.clear()
        return city._banana_trail
    point = (float(position.x), float(position.y))
    if not city._banana_trail:
        city._banana_trail.append(point)
    else:
        old_x, old_y = city._banana_trail[-1]
        if math.hypot(point[0] - old_x, point[1] - old_y) >= 3.0:
            city._banana_trail.append(point)
            del city._banana_trail[:-18]
    return city._banana_trail


def _draw_banana_trail(surface, trail):
    if not trail:
        return
    points = list(trail)[-18:]
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    total = max(1, len(points) - 1)
    for index, point in enumerate(points):
        try:
            x, y = _point_xy(point)
        except (TypeError, ValueError, IndexError):
            continue
        age = index / float(total)
        alpha = int(35 + 160 * age)
        size = 1 + int(age * 2)
        color = (255, 129 + int(85 * age), 54, alpha)
        pygame.draw.rect(layer, color, (int(x) - size // 2, int(y) - size // 2, size, size))
    surface.blit(layer, (0, 0))


def _gorilla_render_pose(player, index, current, banana_active, banana_pos, scene_time):
    state = player.state
    reaction = (
        getattr(player, "reaction", "")
        if scene_time < getattr(player, "reaction_until", 0.0)
        else ""
    )
    jitter = 0
    bob = 0

    if reaction == "laugh":
        state = "leftup" if int(scene_time * 7) % 2 == 0 else "rightup"
        jitter = -2 if int(scene_time * 14) % 2 == 0 else 2
        bob = 4 if int(scene_time * 7) % 2 == 0 else 0
    elif reaction == "scared":
        state = "leftup" if int(scene_time * 12) % 2 == 0 else "rightup"
        jitter = -2 if int(scene_time * 24) % 2 == 0 else 2
    elif banana_active and index != current and state == "idle":
        distance = math.hypot(
            float(banana_pos.x) - float(player.pos.x),
            float(banana_pos.y) - float(player.pos.y - 34),
        )
        if distance < 145:
            state = "leftup" if banana_pos.x < player.pos.x else "rightup"
        if distance < 82:
            jitter = -2 if int(scene_time * 28) % 2 == 0 else 2
            reaction = "scared"
    elif state == "idle":
        # Les pieds restent fixes sur le toit : aucune fausse lévitation.
        bob = 0
        jitter = int(round(math.cos(scene_time * 1.4 + index * 2.1)))
        idle_cycle = (scene_time + index * 2.7) % 6.2
        if 0.0 < idle_cycle < 0.42:
            state = "leftup" if index == 0 else "rightup"
        elif 0.42 <= idle_cycle < 0.84:
            state = "rightup" if index == 0 else "leftup"

    return state, reaction, jitter, bob


def _draw_gorilla_reaction(surface, rect, reaction, blink, font=None):
    ink = (47, 28, 31)
    if blink:
        skin = (217, 145, 66)
        pygame.draw.rect(surface, skin, (rect.centerx - 10, rect.top + 18, 7, 4))
        pygame.draw.rect(surface, skin, (rect.centerx + 3, rect.top + 18, 7, 4))
        pygame.draw.line(
            surface,
            ink,
            (rect.centerx - 8, rect.top + 18),
            (rect.centerx - 4, rect.top + 18),
            2,
        )
        pygame.draw.line(
            surface,
            ink,
            (rect.centerx + 4, rect.top + 18),
            (rect.centerx + 8, rect.top + 18),
            2,
        )
    if reaction == "laugh":
        color = (255, 225, 119)
        mouth = pygame.Rect(rect.centerx - 7, rect.top + 28, 14, 9)
        pygame.draw.ellipse(surface, (47, 20, 26), mouth)
        pygame.draw.rect(
            surface,
            (250, 241, 205),
            (mouth.x + 3, mouth.y + 1, 8, 2),
        )
        pygame.draw.line(
            surface,
            color,
            (rect.left + 2, rect.top + 12),
            (rect.left - 5, rect.top + 5),
            3,
        )
        pygame.draw.line(
            surface,
            color,
            (rect.right - 2, rect.top + 12),
            (rect.right + 5, rect.top + 5),
            3,
        )
        if font is not None:
            laugh = render_text(font, "HA ! HA !", color)
            bubble = laugh.get_rect().inflate(10, 6)
            if rect.top < 105:
                bubble.center = (
                    rect.right + bubble.width // 2 + 7
                    if rect.centerx < VIRTUAL_W // 2
                    else rect.left - bubble.width // 2 - 7,
                    rect.top + 22,
                )
            else:
                bubble.midbottom = (rect.centerx, rect.top - 5)
            bubble.clamp_ip(surface.get_rect())
            pygame.draw.rect(surface, (15, 18, 35), bubble, border_radius=5)
            pygame.draw.rect(surface, color, bubble, 2, border_radius=5)
            surface.blit(laugh, laugh.get_rect(center=bubble.center))
    elif reaction == "scared":
        color = (139, 218, 250)
        pygame.draw.circle(surface, color, (rect.right + 2, rect.top + 5), 4)
        pygame.draw.line(
            surface,
            color,
            (rect.right + 2, rect.top + 8),
            (rect.right + 2, rect.top + 13),
            3,
        )
        if font is not None:
            alert = render_text(font, "!", (255, 225, 119))
            alert_rect = alert.get_rect(midbottom=(rect.centerx, rect.top - 4))
            if rect.top < 105:
                alert_rect.center = (
                    rect.right + 9
                    if rect.centerx < VIRTUAL_W // 2
                    else rect.left - 9,
                    rect.top + 10,
                )
            alert_rect.clamp_ip(surface.get_rect())
            surface.blit(alert, alert_rect)


def draw_scene(
    vsurf,
    spr,
    city: City,
    players,
    banana_active,
    banana_pos,
    sun_rect,
    font,
    font_small,
    status_message,
    wind_value,
    banana_angle_deg,
    active_player=None,
    banana_trail=None,
    scene_time=None,
    sun_expression=None,
):
    """Rendu complet. Tous les nouveaux arguments sont optionnels."""
    if scene_time is None:
        scene_time = pygame.time.get_ticks() / 1000.0

    city.draw_background(vsurf, scene_time, wind_value)

    expression = sun_expression
    if expression is None:
        expression = "blink" if int(scene_time * 2) % 17 == 0 else "smile"
        if banana_active:
            bx, by = float(banana_pos.x), float(banana_pos.y)
            if math.hypot(bx - sun_rect.centerx, by - sun_rect.centery) < 90:
                expression = "surprised"
    if city.show_sun:
        sun_image = spr.get_sun(expression) if hasattr(spr, "get_sun") else spr.sun
        vsurf.blit(sun_image, sun_image.get_rect(center=sun_rect.center))
    elif city.show_moon:
        _draw_moon(vsurf, sun_rect.center, expression)
    vsurf.blit(city.mask, (0, 0))
    city.draw_building_life(vsurf, scene_time)
    city.draw_damage_effects(vsurf, scene_time)
    city.draw_emergency_effects(vsurf, scene_time)
    city.draw_lightning_glow(vsurf, scene_time)

    current = _active_player(city, players, banana_active, active_player)

    # Gorilles, posés directement sur leur toit.
    for index, player in enumerate(players):
        render_state, reaction, jitter, bob = _gorilla_render_pose(
            player,
            index,
            current,
            banana_active,
            banana_pos,
            scene_time,
        )
        if hasattr(spr, "get_gorilla"):
            image = spr.get_gorilla(index, render_state)
        else:
            image = spr.gorilla_idle
            if render_state == "leftup":
                image = spr.gorilla_leftup
            elif render_state == "rightup":
                image = spr.gorilla_rightup
        rect = image.get_rect(
            midbottom=(
                int(player.pos.x) + jitter,
                int(player.pos.y) - bob,
            )
        )
        vsurf.blit(image, rect)
        blink = (
            render_state == "idle"
            and not reaction
            and (scene_time + index * 1.9) % 4.7 < 0.11
        )
        _draw_gorilla_reaction(vsurf, rect, reaction, blink, font_small)
        if index == current and not banana_active:
            marker_y = max(50, rect.top - 7)
            pygame.draw.polygon(
                vsurf,
                HUD_ACTIVE,
                [(rect.centerx - 4, marker_y), (rect.centerx + 4, marker_y), (rect.centerx, marker_y + 4)],
            )

    if banana_trail is None:
        banana_trail = _update_internal_trail(city, banana_active, banana_pos)
    _draw_banana_trail(vsurf, banana_trail)

    if banana_active:
        # Angles quantifies: rotation plus stable et franchement pixel.
        pixel_angle = round((banana_angle_deg % 360) / 15.0) * 15.0
        rotated = pygame.transform.rotate(spr.banana, pixel_angle)
        rect = rotated.get_rect(center=(int(banana_pos.x), int(banana_pos.y)))
        vsurf.blit(rotated, rect)

    city.draw_weather_foreground(vsurf, scene_time, wind_value)
    _draw_player_card(vsurf, players[0], 0, current == 0, font, font_small)
    _draw_player_card(vsurf, players[1], 1, current == 1, font, font_small)
    _draw_score_panel(vsurf, players, font, font_small)
    draw_wind_indicator(vsurf, font_small, wind_value)
    if status_message:
        draw_toast(vsurf, font_small, status_message)
