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


def _draw_crown(surface, center_x, bottom_y):
    """Petite couronne pixel, lisible sur tous les gorilles."""
    dark = (75, 43, 28)
    gold = (255, 193, 45)
    shine = (255, 231, 112)
    points = [
        (center_x - 10, bottom_y - 2),
        (center_x - 9, bottom_y - 11),
        (center_x - 4, bottom_y - 7),
        (center_x, bottom_y - 13),
        (center_x + 4, bottom_y - 7),
        (center_x + 9, bottom_y - 11),
        (center_x + 10, bottom_y - 2),
    ]
    pygame.draw.polygon(surface, dark, points)
    inner = [(x, y + 2) for x, y in points]
    pygame.draw.polygon(surface, gold, inner)
    pygame.draw.rect(surface, dark, (center_x - 10, bottom_y - 3, 20, 5))
    pygame.draw.rect(surface, gold, (center_x - 8, bottom_y - 2, 16, 3))
    pygame.draw.rect(surface, shine, (center_x - 6, bottom_y - 1, 3, 1))


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
        "count": (14, 18),
        "height": (90, 248),
        "roofs": ("antenna", "tank", "billboard", "lip"),
        "trim": (0, 1, 2),
        "tint": (54, 66, 91),
        "tint_amount": 0.08,
    },
    "paris": {
        "label": "PARIS",
        "count": (15, 20),
        "height": (72, 190),
        "roofs": ("mansard", "chimney", "mansard", "lip"),
        "trim": (1, 1, 0),
        "tint": (122, 91, 91),
        "tint_amount": 0.16,
    },
    "tokyo": {
        "label": "TOKYO",
        "count": (14, 19),
        "height": (86, 232),
        "roofs": ("neon", "antenna", "billboard", "tank"),
        "trim": (0, 2, 2),
        "tint": (83, 55, 112),
        "tint_amount": 0.13,
    },
    "seaside": {
        "label": "BORD DE MER",
        "count": (12, 17),
        "height": (58, 158),
        "roofs": ("solar", "chimney", "lip", "tank"),
        "trim": (0, 1, 1),
        "tint": (145, 126, 118),
        "tint_amount": 0.22,
    },
    "future": {
        "label": "NÉO-CITY",
        "count": (13, 18),
        "height": (92, 242),
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
        self._stuck_bananas = []
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
        self._stuck_bananas.clear()
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
        for _ in widths:
            height = rng.randint(*city_settings["height"])
            if previous is not None and abs(height - previous) < 18:
                low, high = city_settings["height"]
                height = max(low, min(high, height + rng.choice((-28, 28))))
            heights.append(height)
            previous = height

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
                    "roof": rng.choice(city_settings["roofs"]),
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

    def add_damage_effect(self, center, scene_time, strong=False):
        cx, cy = int(center[0]), int(center[1])
        self._smoke_plumes.append(
            {
                "x": cx,
                "y": cy,
                "start": float(scene_time),
                "duration": 3.2 if strong else 2.4,
                "seed": (cx * 31 + cy * 17) % 97,
            }
        )
        self._smoke_plumes = self._smoke_plumes[-6:]

    def draw_damage_effects(self, surface, scene_time):
        """Fumée légère après impact, dessinée sans asset."""
        if not self._smoke_plumes:
            return
        alive = []
        layer = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        for plume in self._smoke_plumes:
            age = scene_time - plume["start"]
            if age < 0 or age >= plume["duration"]:
                continue
            alive.append(plume)
            progress = age / plume["duration"]
            alpha = int(145 * (1.0 - progress))
            for index in range(5):
                phase = plume["seed"] + index * 1.7
                x = plume["x"] + math.sin(age * 1.5 + phase) * (4 + index)
                y = plume["y"] - age * (11 + index * 2) - index * 4
                radius = 4 + index + int(progress * 4)
                pygame.draw.circle(
                    layer,
                    (44, 39, 56, max(0, alpha - index * 12)),
                    (int(x), int(y)),
                    radius,
                )
        self._smoke_plumes = alive
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
            pygame.draw.rect(self._far_layer, (*base, 150), (0, 305, VIRTUAL_W, 50))
            for yy in range(309, 352, 8):
                pygame.draw.line(
                    self._far_layer,
                    (*light, 70),
                    (0, yy),
                    (VIRTUAL_W, yy),
                    1,
                )

        x = -8
        index = 0
        while x < VIRTUAL_W:
            width = rng.randint(18, 42)
            height = rng.randint(42, 122)
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

        landmark_x = int(VIRTUAL_W * 0.52)
        if self.city_style_name == "seaside":
            pygame.draw.rect(
                self._far_layer,
                (*base, 205),
                (0, 326, VIRTUAL_W, 28),
            )
            for yy in range(330, 353, 7):
                pygame.draw.line(
                    self._far_layer,
                    (*light, 105),
                    (0, yy),
                    (VIRTUAL_W, yy),
                    2,
                )
        if self.city_style_name == "paris":
            pygame.draw.line(
                self._far_layer,
                (*shadow, 235),
                (landmark_x, 210),
                (landmark_x - 25, 354),
                4,
            )
            pygame.draw.line(
                self._far_layer,
                (*shadow, 235),
                (landmark_x, 210),
                (landmark_x + 25, 354),
                4,
            )
            for yy, width in ((255, 16), (298, 28), (338, 42)):
                pygame.draw.line(
                    self._far_layer,
                    (*shadow, 235),
                    (landmark_x - width // 2, yy),
                    (landmark_x + width // 2, yy),
                    3,
                )
        elif self.city_style_name == "tokyo":
            pygame.draw.polygon(
                self._far_layer,
                (*shadow, 235),
                [
                    (landmark_x, 198),
                    (landmark_x - 13, 354),
                    (landmark_x + 13, 354),
                ],
            )
            for yy in range(230, 340, 22):
                pygame.draw.line(
                    self._far_layer,
                    (*light, 125),
                    (landmark_x - 7, yy),
                    (landmark_x + 7, yy),
                    2,
                )
        elif self.city_style_name == "future":
            pygame.draw.ellipse(
                self._far_layer,
                (*base, 230),
                (landmark_x - 48, 282, 96, 72),
            )
            pygame.draw.arc(
                self._far_layer,
                (*light, 135),
                (landmark_x - 48, 282, 96, 72),
                math.pi,
                math.tau,
                3,
            )
        elif self.city_style_name == "seaside":
            pygame.draw.circle(
                self._far_layer,
                (*shadow, 205),
                (landmark_x, 291),
                28,
                3,
            )
            for angle in range(0, 360, 45):
                radians = math.radians(angle)
                pygame.draw.line(
                    self._far_layer,
                    (*shadow, 190),
                    (landmark_x, 291),
                    (
                        landmark_x + int(math.cos(radians) * 27),
                        291 + int(math.sin(radians) * 27),
                    ),
                    1,
                )
        else:
            pygame.draw.rect(
                self._far_layer,
                (*shadow, 225),
                (landmark_x - 5, 205, 10, 149),
            )
            pygame.draw.polygon(
                self._far_layer,
                (*shadow, 225),
                [(landmark_x, 168), (landmark_x - 5, 205), (landmark_x + 5, 205)],
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
    radius = EXPLOSION_RADIUS
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
                elif distance <= radius + 3:
                    city.mask.set_at((x, y), (31, 20, 43, 255))
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


def draw_wind_indicator(vsurf, font, wind_value, position=None):
    value = max(-WIND_MAX, min(WIND_MAX, int(round(wind_value))))
    panel = pygame.Rect(position or (8, 53, 142, 32))
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
    vsurf.blit(label, (panel.x + 10, panel.y + 3))
    vsurf.blit(value_text, (panel.right - value_text.get_width() - 8, panel.y + 3))

    line_y = panel.bottom - 8
    left = panel.x + 12
    right = panel.right - 10
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
        state = "leftup" if int(scene_time * 9) % 2 == 0 else "rightup"
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
        bob = 1 if math.sin(scene_time * 3.2 + index * 1.7) > 0.72 else 0

    return state, reaction, jitter, bob


def _draw_gorilla_reaction(surface, rect, reaction, blink):
    ink = (47, 28, 31)
    if blink:
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
        pygame.draw.line(surface, color, (rect.left + 2, rect.top + 12), (rect.left - 3, rect.top + 8), 2)
        pygame.draw.line(surface, color, (rect.right - 2, rect.top + 12), (rect.right + 3, rect.top + 8), 2)
    elif reaction == "scared":
        color = (139, 218, 250)
        pygame.draw.line(surface, color, (rect.right - 1, rect.top + 9), (rect.right + 2, rect.top + 3), 2)


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
    city.draw_lightning_glow(vsurf, scene_time)

    current = _active_player(city, players, banana_active, active_player)

    # Ombre et gorilles.
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
        shadow_width = max(12, rect.w - 12)
        pygame.draw.rect(
            vsurf,
            (26, 17, 38),
            (rect.centerx - shadow_width // 2, int(player.pos.y) - 2, shadow_width, 3),
        )
        if getattr(player, "crowned", False):
            # Dessinée derrière les cheveux : la couronne paraît portée.
            _draw_crown(vsurf, rect.centerx, rect.top + 10)
        vsurf.blit(image, rect)
        blink = (
            render_state == "idle"
            and not reaction
            and (scene_time + index * 1.9) % 4.7 < 0.11
        )
        _draw_gorilla_reaction(vsurf, rect, reaction, blink)
        if index == current and not banana_active:
            marker_y = max(50, rect.top - (20 if getattr(player, "crowned", False) else 7))
            pygame.draw.polygon(
                vsurf,
                HUD_ACTIVE,
                [(rect.centerx - 4, marker_y), (rect.centerx + 4, marker_y), (rect.centerx, marker_y + 4)],
            )

    stuck_alive = []
    for stuck in city._stuck_bananas:
        if scene_time >= stuck["expires"]:
            continue
        stuck_alive.append(stuck)
        rotated = pygame.transform.rotate(spr.banana, stuck["angle"])
        vsurf.blit(
            rotated,
            rotated.get_rect(center=(stuck["x"], stuck["y"])),
        )
    city._stuck_bananas = stuck_alive

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
