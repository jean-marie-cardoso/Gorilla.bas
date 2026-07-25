# sprites.py — sprites nets, compatibles PyInstaller + Pygbag
import os
import sys

import pygame

from config import (
    ASSETS_DIR,
    BANANA_H_TARGET,
    GORILLA_H_TARGET,
    SPRITES,
    SUN_W_TARGET,
    USE_PROCEDURAL_PIXEL_SPRITES,
)


def resource_path(relative_path):
    """Chemin compatible PyInstaller, execution locale et Pygbag."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def _load(path):
    return pygame.image.load(path).convert_alpha()


def _scale_to_height(img, h):
    """Mise a l'echelle nearest-neighbour pour garder des pixels francs."""
    if img.get_height() == 0:
        return img
    scale = h / img.get_height()
    width = max(1, int(round(img.get_width() * scale)))
    return pygame.transform.scale(img, (width, int(h)))


def _scale_to_width(img, w):
    if img.get_width() == 0:
        return img
    scale = w / img.get_width()
    height = max(1, int(round(img.get_height() * scale)))
    return pygame.transform.scale(img, (int(w), height))


def _finish_pixel_sprite(surface, target_height=None, target_width=None):
    if target_height is not None:
        return _scale_to_height(surface, target_height)
    if target_width is not None:
        return _scale_to_width(surface, target_width)
    return surface


def _orange_team_variant(source):
    """Recolore seulement le maillot bleu et remplace 1 par 2."""
    result = source.copy()
    blue_points = []
    width, height = result.get_size()

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = result.get_at((x, y))
            if (
                alpha > 40
                and blue > 70
                and blue > red * 1.18
                and blue > green * 1.08
            ):
                blue_points.append((x, y))

    if not blue_points:
        return result

    left = min(point[0] for point in blue_points)
    right = max(point[0] for point in blue_points)
    top = min(point[1] for point in blue_points)
    bottom = max(point[1] for point in blue_points)

    # Ombres et reflets du maillot restent identiques, seule la teinte change.
    for y in range(top, bottom + 1):
        for x in range(left, right + 1):
            red, green, blue, alpha = result.get_at((x, y))
            if (
                alpha > 20
                and blue > 38
                and blue > red * 1.06
                and blue > green * 1.03
            ):
                strength = max(red, green, blue) / 255.0
                result.set_at(
                    (x, y),
                    (
                        min(255, int(255 * strength)),
                        min(255, int(104 * strength)),
                        min(255, int(22 * strength)),
                        alpha,
                    ),
                )

    # Efface le numéro 1 sans toucher aux dents, situées plus haut.
    number_top = top + max(1, (bottom - top) // 3)
    center_x = (left + right) // 2
    for y in range(number_top, bottom + 1):
        for x in range(max(left, center_x - 5), min(right, center_x + 5) + 1):
            red, green, blue, alpha = result.get_at((x, y))
            if alpha > 80 and min(red, green, blue) > 135 and max(red, green, blue) - min(red, green, blue) < 55:
                result.set_at((x, y), (238, 91, 16, alpha))

    # Petit 2 en pixels, net même sur téléphone.
    pattern = ("111", "001", "001", "111", "100", "100", "111")
    start_x = center_x - 1
    start_y = number_top + max(0, (bottom - number_top - len(pattern)) // 2)
    for row, line in enumerate(pattern):
        for column, pixel in enumerate(line):
            if pixel == "1":
                result.set_at(
                    (start_x + column, start_y + row),
                    (255, 250, 235, 255),
                )
    return result


def _make_gorilla(pose="idle"):
    """Petit gorille 26x28 dessine sur une vraie grille de pixels."""
    surf = pygame.Surface((26, 28), pygame.SRCALPHA)
    outline = (22, 14, 34)
    fur_dark = (62, 30, 58)
    fur = (105, 49, 69)
    fur_light = (143, 69, 74)
    skin = (242, 154, 65)
    skin_light = (255, 205, 101)
    eye = (18, 13, 31)

    # Bras derriere le corps.
    if pose == "leftup":
        pygame.draw.polygon(
            surf, outline, [(6, 18), (2, 18), (0, 5), (2, 1), (6, 2), (8, 14)]
        )
        pygame.draw.polygon(
            surf, fur, [(5, 17), (3, 17), (2, 6), (3, 3), (5, 4), (7, 15)]
        )
        pygame.draw.rect(surf, outline, (0, 0, 6, 5))
        pygame.draw.rect(surf, skin_light, (1, 1, 4, 3))
    else:
        pygame.draw.rect(surf, outline, (2, 9, 6, 15))
        pygame.draw.rect(surf, fur, (3, 10, 4, 12))
        pygame.draw.rect(surf, outline, (1, 20, 7, 6))
        pygame.draw.rect(surf, skin_light, (2, 21, 5, 4))

    if pose == "rightup":
        pygame.draw.polygon(
            surf, outline, [(20, 18), (24, 18), (26, 5), (24, 1), (20, 2), (18, 14)]
        )
        pygame.draw.polygon(
            surf, fur, [(21, 17), (23, 17), (24, 6), (23, 3), (21, 4), (19, 15)]
        )
        pygame.draw.rect(surf, outline, (20, 0, 6, 5))
        pygame.draw.rect(surf, skin_light, (21, 1, 4, 3))
    else:
        pygame.draw.rect(surf, outline, (18, 9, 6, 15))
        pygame.draw.rect(surf, fur, (19, 10, 4, 12))
        pygame.draw.rect(surf, outline, (18, 20, 7, 6))
        pygame.draw.rect(surf, skin_light, (19, 21, 5, 4))

    # Jambes, pieds, torse.
    pygame.draw.rect(surf, outline, (5, 18, 7, 8))
    pygame.draw.rect(surf, outline, (14, 18, 7, 8))
    pygame.draw.rect(surf, fur_dark, (6, 19, 5, 6))
    pygame.draw.rect(surf, fur_dark, (15, 19, 5, 6))
    pygame.draw.rect(surf, outline, (3, 24, 9, 4))
    pygame.draw.rect(surf, outline, (14, 24, 9, 4))
    pygame.draw.rect(surf, skin, (4, 25, 7, 2))
    pygame.draw.rect(surf, skin, (15, 25, 7, 2))

    pygame.draw.rect(surf, outline, (5, 7, 16, 16))
    pygame.draw.rect(surf, fur, (6, 8, 14, 13))
    pygame.draw.rect(surf, fur_light, (7, 9, 12, 3))
    pygame.draw.rect(surf, outline, (8, 11, 10, 10))
    pygame.draw.rect(surf, skin, (9, 12, 8, 8))
    pygame.draw.rect(surf, skin_light, (10, 12, 6, 5))

    # Tete et visage lisibles meme a petite taille.
    pygame.draw.rect(surf, outline, (5, 3, 4, 5))
    pygame.draw.rect(surf, outline, (17, 3, 4, 5))
    pygame.draw.rect(surf, skin, (6, 4, 3, 3))
    pygame.draw.rect(surf, skin, (17, 4, 3, 3))
    pygame.draw.rect(surf, outline, (7, 0, 12, 11))
    pygame.draw.rect(surf, fur_dark, (8, 1, 10, 3))
    pygame.draw.rect(surf, skin_light, (8, 4, 10, 6))
    pygame.draw.rect(surf, eye, (10, 5, 2, 2))
    pygame.draw.rect(surf, eye, (15, 5, 2, 2))
    pygame.draw.rect(surf, skin, (10, 7, 6, 3))
    pygame.draw.rect(surf, eye, (11, 8, 4, 1))

    return _finish_pixel_sprite(surf, target_height=GORILLA_H_TARGET)


def _make_sun(expression="smile"):
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)
    ray = (255, 136, 48)
    edge = (210, 64, 63)
    face = (255, 215, 74)
    glow = (255, 174, 60)
    ink = (55, 26, 51)

    # Rayons carres, silhouette arcade.
    for rect in (
        (14, 0, 4, 5),
        (14, 27, 4, 5),
        (0, 14, 5, 4),
        (27, 14, 5, 4),
        (4, 4, 4, 4),
        (24, 4, 4, 4),
        (4, 24, 4, 4),
        (24, 24, 4, 4),
    ):
        pygame.draw.rect(surf, ray, rect)

    pygame.draw.circle(surf, edge, (16, 16), 12)
    pygame.draw.circle(surf, glow, (16, 16), 10)
    pygame.draw.circle(surf, face, (14, 13), 8)

    if expression == "surprised":
        pygame.draw.rect(surf, ink, (10, 12, 2, 3))
        pygame.draw.rect(surf, ink, (20, 12, 2, 3))
        pygame.draw.circle(surf, ink, (16, 20), 3)
        pygame.draw.circle(surf, face, (16, 20), 1)
    elif expression == "blink":
        pygame.draw.rect(surf, ink, (10, 14, 3, 1))
        pygame.draw.rect(surf, ink, (19, 14, 3, 1))
        pygame.draw.rect(surf, ink, (13, 20, 6, 1))
    else:
        pygame.draw.rect(surf, ink, (10, 12, 2, 3))
        pygame.draw.rect(surf, ink, (20, 12, 2, 3))
        pygame.draw.line(surf, ink, (12, 19), (14, 21), 1)
        pygame.draw.line(surf, ink, (14, 21), (18, 21), 1)
        pygame.draw.line(surf, ink, (18, 21), (20, 19), 1)

    return _finish_pixel_sprite(surf, target_width=SUN_W_TARGET)


def _make_banana():
    surf = pygame.Surface((16, 10), pygame.SRCALPHA)
    outline = (41, 24, 43)
    peel = (255, 214, 58)
    light = (255, 241, 139)
    shade = (235, 139, 40)
    pygame.draw.polygon(
        surf,
        outline,
        [(0, 1), (5, 1), (6, 5), (9, 7), (12, 6), (14, 2), (16, 3),
         (14, 8), (9, 10), (5, 8), (3, 4), (0, 3)],
    )
    pygame.draw.polygon(
        surf,
        peel,
        [(2, 2), (4, 2), (6, 6), (9, 8), (12, 7), (14, 4),
         (13, 7), (9, 9), (5, 7), (3, 3), (2, 3)],
    )
    pygame.draw.line(surf, light, (4, 3), (7, 7), 1)
    pygame.draw.line(surf, shade, (7, 8), (12, 7), 1)
    return _finish_pixel_sprite(surf, target_height=BANANA_H_TARGET)


class Sprites:
    def __init__(self):
        self.menu_background = None
        menu_path = resource_path(os.path.join(ASSETS_DIR, "menu_background.png"))
        try:
            self.menu_background = _load(menu_path)
        except (FileNotFoundError, pygame.error):
            # Le menu sait alors utiliser son fond procedural.
            pass

        if USE_PROCEDURAL_PIXEL_SPRITES:
            self.gorilla_idle = _make_gorilla("idle")
            self.gorilla_leftup = _make_gorilla("leftup")
            self.gorilla_rightup = _make_gorilla("rightup")
            self.sun_frames = {
                "smile": _make_sun("smile"),
                "surprised": _make_sun("surprised"),
                "blink": _make_sun("blink"),
            }
            self.sun = self.sun_frames["smile"]
            self.banana = _make_banana()
            self._build_gorilla_teams()
            return

        base = ASSETS_DIR
        self.gorilla_idle = _load(resource_path(os.path.join(base, SPRITES["gorilla_idle"])))
        self.gorilla_leftup = _load(resource_path(os.path.join(base, SPRITES["gorilla_leftup"])))
        self.gorilla_rightup = _load(resource_path(os.path.join(base, SPRITES["gorilla_rightup"])))
        self.sun = _load(resource_path(os.path.join(base, SPRITES["sun"])))
        try:
            sun_surprised = _load(
                resource_path(os.path.join(base, SPRITES["sun_surprised"]))
            )
        except (KeyError, FileNotFoundError, pygame.error):
            sun_surprised = self.sun
        self.banana = _load(resource_path(os.path.join(base, SPRITES["banana"])))

        self.gorilla_idle = _scale_to_height(self.gorilla_idle, GORILLA_H_TARGET)
        target_size = self.gorilla_idle.get_size()
        self.gorilla_leftup = pygame.transform.scale(self.gorilla_leftup, target_size)
        self.gorilla_rightup = pygame.transform.scale(self.gorilla_rightup, target_size)
        self.sun = _scale_to_width(self.sun, SUN_W_TARGET)
        self.sun_frames = {
            "smile": self.sun,
            "surprised": pygame.transform.scale(
                sun_surprised,
                self.sun.get_size(),
            ),
            "blink": self.sun,
        }
        self.banana = _scale_to_height(self.banana, BANANA_H_TARGET)
        self._build_gorilla_teams()

    def _build_gorilla_teams(self):
        blue = {
            "idle": self.gorilla_idle,
            "leftup": self.gorilla_leftup,
            "rightup": self.gorilla_rightup,
        }
        orange = {
            state: _orange_team_variant(image)
            for state, image in blue.items()
        }
        self.gorilla_teams = (blue, orange)

    def get_gorilla(self, player_index=0, state="idle"):
        team = self.gorilla_teams[int(player_index) % len(self.gorilla_teams)]
        return team.get(state, team["idle"])

    def get_sun(self, expression="smile"):
        aliases = {
            "happy": "smile",
            "neutral": "smile",
            "surprise": "surprised",
            "shocked": "surprised",
            "worried": "surprised",
            "closed": "blink",
        }
        expression = aliases.get(expression, expression)
        return self.sun_frames.get(expression, self.sun)
