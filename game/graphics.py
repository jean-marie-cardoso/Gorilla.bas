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
    INK,
    SKY_GLOW,
    SKY_HORIZON,
    SKY_MIDDLE,
    SKY_TOP,
    SUN_ORANGE,
    VIRTUAL_H,
    VIRTUAL_W,
    WINDOW_DARK,
    WINDOW_LIT,
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


def _lerp_color(a, b, amount):
    amount = max(0.0, min(1.0, amount))
    return tuple(int(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def _make_sky():
    sky = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    horizon_y = int(VIRTUAL_H * 0.68)
    for y in range(VIRTUAL_H):
        # Pas de 3 pixels: le degrade reste doux mais garde un grain retro.
        sample_y = (y // 3) * 3
        if sample_y <= horizon_y:
            t = sample_y / float(horizon_y)
            if t < 0.58:
                color = _lerp_color(SKY_TOP, SKY_MIDDLE, t / 0.58)
            else:
                color = _lerp_color(SKY_MIDDLE, SKY_HORIZON, (t - 0.58) / 0.42)
        else:
            t = (sample_y - horizon_y) / float(VIRTUAL_H - horizon_y)
            color = _lerp_color(SKY_HORIZON, SKY_GLOW, min(1.0, t * 0.72))
        pygame.draw.line(sky, color, (0, y), (VIRTUAL_W, y))

    # Quelques lignes de trame discretes pres de l'horizon.
    for y in range(174, 246, 8):
        color = (*_lerp_color(SKY_MIDDLE, SKY_GLOW, (y - 174) / 110.0),)
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
        self._sky = _make_sky()
        self._far_layer = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        self._styles = []
        self._stars = []
        self._clouds = []
        self._banana_trail = []
        self._scene_banana_active = False
        self._hud_active = 0
        self._generation = 0

    def generate(self, rng: random.Random):
        self._generation += 1
        self._banana_trail.clear()

        count = rng.randint(13, 17)
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
            height = rng.randint(72, 238)
            if previous is not None and abs(height - previous) < 18:
                height = max(72, min(238, height + rng.choice((-28, 28))))
            heights.append(height)
            previous = height

        self.rects.clear()
        self._styles.clear()
        for index, (width, height) in enumerate(zip(widths, heights)):
            top = VIRTUAL_H - height
            rect = pygame.Rect(x, top, width, height)
            self.rects.append(rect)
            columns = max(1, (width - 10) // 10)
            rows = max(1, (height - 16) // 12)
            windows = []
            for row in range(rows):
                line = []
                for column in range(columns):
                    chance = rng.random()
                    if chance < 0.44:
                        state = 1
                    elif chance < 0.51:
                        state = 2
                    else:
                        state = 0
                    # Une petite repetition donne une facade moins chaotique.
                    if row and column and rng.random() < 0.22:
                        state = windows[row - 1][column - 1]
                    line.append(state)
                windows.append(line)
            self._styles.append(
                {
                    "color": BUILDING_COLORS[index % len(BUILDING_COLORS)]
                    if rng.random() < 0.52
                    else rng.choice(BUILDING_COLORS),
                    "roof": rng.choice(("lip", "antenna", "chimney", "tank")),
                    "windows": windows,
                    "trim": rng.randint(0, 2),
                }
            )
            x += width

        self._stars = [
            (
                rng.randint(5, VIRTUAL_W - 6),
                rng.randint(8, 190),
                rng.randint(0, 3),
                rng.choice((1, 1, 1, 2)),
            )
            for _ in range(54)
        ]

        self._clouds = []
        for _ in range(4):
            width = rng.randint(42, 82)
            height = rng.randint(10, 18)
            cloud = _make_cloud(width, height, (121, 91, 145, rng.randint(32, 60)))
            self._clouds.append(
                {
                    "x": rng.uniform(-width, VIRTUAL_W),
                    "y": rng.randint(66, 184),
                    "speed": rng.uniform(1.0, 3.2),
                    "surface": cloud,
                }
            )

        self._build_far_layer(rng)
        self.rebuild_mask()

    def _build_far_layer(self, rng):
        self._far_layer.fill((0, 0, 0, 0))
        x = -8
        index = 0
        while x < VIRTUAL_W:
            width = rng.randint(18, 42)
            height = rng.randint(42, 122)
            bottom = 356
            rect = pygame.Rect(x, bottom - height, width, height)
            color = (35 + index % 3 * 5, 25, 64 + index % 4 * 4, 220)
            pygame.draw.rect(self._far_layer, color, rect)
            pygame.draw.rect(
                self._far_layer,
                (22, 18, 47, 210),
                (rect.right - 3, rect.top, 3, rect.h),
            )
            if index % 4 == 0:
                pygame.draw.rect(
                    self._far_layer,
                    (30, 21, 55, 220),
                    (rect.centerx - 1, rect.top - 10, 2, 10),
                )
            for yy in range(rect.top + 9, rect.bottom - 5, 13):
                for xx in range(rect.left + 6, rect.right - 4, 9):
                    if rng.random() < 0.16:
                        pygame.draw.rect(
                            self._far_layer,
                            (231, 133, 95, 85),
                            (xx, yy, 3, 4),
                        )
            x += width + rng.randint(2, 7)
            index += 1
        pygame.draw.rect(self._far_layer, (25, 20, 51, 235), (0, 354, VIRTUAL_W, 46))

    def draw_background(self, surface, scene_time=None):
        if scene_time is None:
            scene_time = pygame.time.get_ticks() / 1000.0
        surface.blit(self._sky, (0, 0))

        # Etoiles: seulement deux niveaux de lumiere, donc aucun flou.
        for x, y, phase, size in self._stars:
            bright = int(scene_time * 2.0 + phase) % 4 == 0
            color = (255, 235, 177) if bright else (157, 142, 183)
            pygame.draw.rect(surface, color, (x, y, size, size))
            if bright and size == 2:
                pygame.draw.rect(surface, (220, 183, 174), (x - 1, y, 4, 1))

        for cloud in self._clouds:
            image = cloud["surface"]
            span = VIRTUAL_W + image.get_width() * 2
            x = (cloud["x"] + scene_time * cloud["speed"]) % span - image.get_width()
            surface.blit(image, (int(x), cloud["y"]))

        surface.blit(self._far_layer, (0, 0))

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

    def _draw_building(self, rect, style, index):
        color = style["color"]
        outline = (24, 17, 43, 255)
        shadow = _lerp_color(color, INK, 0.36)
        highlight = _lerp_color(color, SKY_HORIZON, 0.18)

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
                pygame.draw.rect(self.mask, (*WINDOW_DARK, 255), (xx, yy, 5, 7))
                if state == 1:
                    pygame.draw.rect(self.mask, (*WINDOW_LIT, 255), (xx + 1, yy + 1, 3, 5))
                    pygame.draw.rect(self.mask, (255, 242, 171, 255), (xx + 1, yy + 1, 3, 1))
                elif state == 2:
                    pygame.draw.rect(self.mask, (225, 103, 98, 255), (xx + 1, yy + 1, 3, 5))


def explode_in_city(city: City, center):
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
    for index in range(14):
        angle = index * (math.tau / 14.0) + (index % 3) * 0.11
        distance = max_radius * progress * (0.55 + (index % 5) * 0.09)
        px = int(cx + math.cos(angle) * distance)
        py = int(cy + math.sin(angle) * distance + progress * progress * 12)
        size = 3 if index % 4 == 0 else 2
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

    city.draw_background(vsurf, scene_time)

    expression = sun_expression
    if expression is None:
        expression = "blink" if int(scene_time * 2) % 17 == 0 else "smile"
        if banana_active:
            bx, by = float(banana_pos.x), float(banana_pos.y)
            if math.hypot(bx - sun_rect.centerx, by - sun_rect.centery) < 90:
                expression = "surprised"
    sun_image = spr.get_sun(expression) if hasattr(spr, "get_sun") else spr.sun
    vsurf.blit(sun_image, sun_image.get_rect(center=sun_rect.center))
    vsurf.blit(city.mask, (0, 0))

    current = _active_player(city, players, banana_active, active_player)

    # Ombre et gorilles.
    for index, player in enumerate(players):
        image = spr.gorilla_idle
        if player.state == "leftup":
            image = spr.gorilla_leftup
        elif player.state == "rightup":
            image = spr.gorilla_rightup
        rect = image.get_rect(midbottom=(int(player.pos.x), int(player.pos.y)))
        shadow_width = max(12, rect.w - 12)
        pygame.draw.rect(
            vsurf,
            (26, 17, 38),
            (rect.centerx - shadow_width // 2, int(player.pos.y) - 2, shadow_width, 3),
        )
        vsurf.blit(image, rect)
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

    _draw_player_card(vsurf, players[0], 0, current == 0, font, font_small)
    _draw_player_card(vsurf, players[1], 1, current == 1, font, font_small)
    _draw_score_panel(vsurf, players, font, font_small)
    draw_wind_indicator(vsurf, font_small, wind_value)

    if status_message:
        draw_toast(vsurf, font_small, status_message)
