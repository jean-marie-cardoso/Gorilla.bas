# config.py — direction visuelle "QBASIC Deluxe"
# Resolution logique. Tous les dessins restent alignes sur cette grille.
VIRTUAL_W, VIRTUAL_H = 640, 400
FPS = 60

# Gameplay / physics
DEFAULT_GRAVITY = 220.0       # px/s^2 (vertical acceleration)
DEFAULT_WIN_SCORE = 3
WIND_MAX = 10                 # UI range [-10..+10]
WIND_ACCEL_PER_UNIT = 10       # px/s^2 horizontal accel per wind unit
EXPLOSION_RADIUS = 22

# Fonts
FONT_MAIN_SIZE = 18
FONT_SMALL_SIZE = 14
FONT_BIG_SIZE = 24
TEXT_COLOR = (255, 220, 128)

# Palette coucher de soleil. Ces constantes sont aussi utiles aux ecrans
# (intro, menu, victoire) qui veulent reprendre l'identite du jeu.
INK = (19, 15, 38)
INK_SOFT = (35, 25, 58)
CREAM = (255, 241, 201)
BANANA_YELLOW = (255, 216, 78)
SUN_ORANGE = (255, 139, 61)
CORAL = (238, 82, 83)
SKY_TOP = (12, 13, 47)
SKY_MIDDLE = (61, 35, 88)
SKY_HORIZON = (229, 91, 91)
SKY_GLOW = (255, 157, 79)
WINDOW_LIT = (255, 220, 117)
WINDOW_DARK = (38, 30, 68)

# UI
HUD_BG = (18, 15, 38, 226)
HUD_BG_SOFT = (31, 24, 55, 218)
HUD_BORDER = (117, 74, 130)
HUD_ACTIVE = BANANA_YELLOW
STATUS_BG = (18, 15, 38, 232)

# Sprites scaling targets
GORILLA_H_TARGET = 68
SUN_W_TARGET = 76
BANANA_H_TARGET = 16
USE_PROCEDURAL_PIXEL_SPRITES = False

# Banana rotation speed (deg/sec)
BANANA_ROT_SPEED = 360

# Assets
ASSETS_DIR = "assets"
SPRITES = {
    "gorilla_idle": "gorilla_idle_v2.png",
    "gorilla_leftup": "gorilla_leftup_v2.png",
    "gorilla_rightup": "gorilla_rightup_v2.png",
    "sun": "sun_v2.png",
    "sun_surprised": "sun_surprised_v2.png",
    "banana": "banana.png",
}
