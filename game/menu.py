# menu.py — menu Pygame compatible ordinateur, tactile et Pygbag
import asyncio

import pygame

from config import FPS, VIRTUAL_H, VIRTUAL_W
from sprites import resource_path


MODE_SOLO_AI = "solo_ai"
MODE_TWO_PLAYERS = "two_players"
MODE_TRAINING = "solo_target"

DIFFICULTY_EASY = "easy"
DIFFICULTY_NORMAL = "normal"
DIFFICULTY_HARD = "hard"

MENU_START = "start"
MENU_QUIT = "quit"

MIN_WIN_SCORE = 1
MAX_WIN_SCORE = 9
BASE_CONTENT_W = 640

MODE_OPTIONS = (
    (MODE_SOLO_AI, "SOLO IA", "Affronte l'ordinateur"),
    (MODE_TWO_PLAYERS, "2 JOUEURS", "Jouez à tour de rôle"),
    (MODE_TRAINING, "ENTRAÎNEMENT", "Vise une cible immobile"),
)

DIFFICULTY_OPTIONS = (
    (DIFFICULTY_EASY, "FACILE"),
    (DIFFICULTY_NORMAL, "NORMAL"),
    (DIFFICULTY_HARD, "DIFFICILE"),
)


def _clamp(value, low, high):
    return max(low, min(high, value))


def _play_sound(game, name="click"):
    sound = getattr(game, "sound", None)
    play = getattr(sound, "play", None)
    if callable(play):
        play(name)


def _toggle_sound(game):
    sound = getattr(game, "sound", None)
    toggle = getattr(sound, "toggle", None)
    if callable(toggle):
        toggle()


def _screen_to_virtual(game, position):
    """Convertit un clic écran vers la surface virtuelle du jeu."""
    converter = getattr(game, "screen_to_virtual", None)
    if callable(converter):
        converted = converter(position)
        return None if converted is None else tuple(converted)

    viewport = getattr(game, "viewport_rect", None)
    if viewport is not None:
        rect = pygame.Rect(viewport)
        if not rect.collidepoint(position):
            return None
        return (
            (position[0] - rect.x) * VIRTUAL_W / max(1, rect.width),
            (position[1] - rect.y) * VIRTUAL_H / max(1, rect.height),
        )

    screen_w, screen_h = game.screen.get_size()
    return (
        position[0] * VIRTUAL_W / max(1, screen_w),
        position[1] * VIRTUAL_H / max(1, screen_h),
    )


def _event_virtual_position(game, event):
    if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
        return _screen_to_virtual(game, event.pos)
    if event.type in (pygame.FINGERDOWN, pygame.FINGERUP):
        screen_w, screen_h = game.screen.get_size()
        return _screen_to_virtual(game, (event.x * screen_w, event.y * screen_h))
    return None


def _draw_center(surface, font, text, rect, color):
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(center=rect.center))


def _draw_panel(surface, rect, color=(5, 18, 39, 225), border=(61, 96, 145)):
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, color, layer.get_rect(), border_radius=12)
    pygame.draw.rect(layer, border, layer.get_rect(), width=1, border_radius=12)
    surface.blit(layer, rect)


def _draw_button(surface, font, rect, label, selected=False, hovered=False, disabled=False):
    if disabled:
        fill = (26, 42, 64)
        border = (50, 67, 88)
        text_color = (109, 124, 143)
    elif selected:
        fill = (45, 86, 133)
        border = (255, 205, 75)
        text_color = (255, 242, 199)
    elif hovered:
        fill = (31, 61, 99)
        border = (105, 154, 211)
        text_color = (255, 255, 255)
    else:
        fill = (20, 43, 74)
        border = (64, 99, 142)
        text_color = (220, 232, 245)

    pygame.draw.rect(surface, fill, rect, border_radius=9)
    pygame.draw.rect(surface, border, rect, width=2 if selected else 1, border_radius=9)
    _draw_center(surface, font, label, rect, text_color)


def draw_menu_background(game):
    """Dessine le fond partagé par l'intro et le menu."""
    surface = game.vsurf
    background = getattr(game, "_menu_background", None)
    if background is None:
        background = getattr(getattr(game, "spr", None), "menu_background", None)
        try:
            if background is None:
                background = pygame.image.load(
                    resource_path("assets/menu_background.png")
                ).convert()
            if background.get_height() != VIRTUAL_H:
                target_width = round(
                    background.get_width() * VIRTUAL_H / background.get_height()
                )
                background = pygame.transform.smoothscale(
                    background, (target_width, VIRTUAL_H)
                )
            if background.get_width() < VIRTUAL_W:
                expanded = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
                offset = (VIRTUAL_W - background.get_width()) // 2
                expanded.blit(background, (offset, 0))
                if offset:
                    side_width = min(offset, background.get_width() // 3)
                    left = background.subsurface((0, 0, side_width, VIRTUAL_H))
                    right = background.subsurface(
                        (background.get_width() - side_width, 0, side_width, VIRTUAL_H)
                    )
                    expanded.blit(
                        pygame.transform.flip(left, True, False),
                        (offset - side_width, 0),
                    )
                    expanded.blit(
                        pygame.transform.flip(right, True, False),
                        (offset + background.get_width(), 0),
                    )
                background = expanded
        except (OSError, pygame.error):
            background = False
        game._menu_background = background

    if background:
        surface.blit(background, (0, 0))
        shade = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        shade.fill((2, 11, 28, 46))
        surface.blit(shade, (0, 0))
        return

    top = (10, 29, 62)
    bottom = (24, 105, 151)
    for y in range(0, VIRTUAL_H, 4):
        amount = y / VIRTUAL_H
        color = tuple(int(top[i] + (bottom[i] - top[i]) * amount) for i in range(3))
        pygame.draw.rect(surface, color, (0, y, VIRTUAL_W, 4))

    for x, y in ((58, 39), (104, 67), (157, 31), (465, 47), (539, 28), (587, 72)):
        pygame.draw.circle(surface, (178, 221, 238), (x, y), 1)

    skyline = (
        (0, 344, 58, 56),
        (52, 330, 70, 70),
        (114, 350, 54, 50),
        (158, 320, 78, 80),
        (228, 342, 62, 58),
        (281, 325, 75, 75),
        (348, 348, 51, 52),
        (391, 314, 84, 86),
        (467, 338, 69, 62),
        (527, 322, 72, 78),
        (592, 347, 48, 53),
    )
    for rect in skyline:
        pygame.draw.rect(surface, (7, 20, 38), rect)


def _normalise_mode(value):
    aliases = {
        "solo": MODE_SOLO_AI,
        "ia": MODE_SOLO_AI,
        "two": MODE_TWO_PLAYERS,
        "2": MODE_TWO_PLAYERS,
        "training": MODE_TRAINING,
        "target": MODE_TRAINING,
        "entrainement": MODE_TRAINING,
    }
    value = aliases.get(str(value or "").lower(), value)
    valid = {item[0] for item in MODE_OPTIONS}
    return value if value in valid else MODE_SOLO_AI


def _normalise_difficulty(value):
    aliases = {
        "facile": DIFFICULTY_EASY,
        "moyen": DIFFICULTY_NORMAL,
        "normale": DIFFICULTY_NORMAL,
        "difficile": DIFFICULTY_HARD,
    }
    value = aliases.get(str(value or "").lower(), value)
    valid = {item[0] for item in DIFFICULTY_OPTIONS}
    return value if value in valid else DIFFICULTY_NORMAL


def get_menu_selection(game):
    """Renvoie ``(mode, difficulté, score)`` avec des valeurs sûres."""
    mode = _normalise_mode(getattr(game, "game_mode", MODE_SOLO_AI))
    difficulty = _normalise_difficulty(getattr(game, "ai_difficulty", DIFFICULTY_NORMAL))
    try:
        score = int(getattr(game, "win_score", 3))
    except (TypeError, ValueError):
        score = 3
    score = int(_clamp(score, MIN_WIN_SCORE, MAX_WIN_SCORE))
    return mode, difficulty, score


def apply_menu_selection(game, mode, difficulty, score, reset_match=True):
    """Applique le choix du menu au ``Game``.

    ``main.py`` peut appeler cette petite API sans connaître les détails du
    menu. Par défaut, une pression sur JOUER démarre une nouvelle partie.
    """
    mode = _normalise_mode(mode)
    difficulty = _normalise_difficulty(difficulty)
    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 3
    score = int(_clamp(score, MIN_WIN_SCORE, MAX_WIN_SCORE))

    game.game_mode = mode
    game.ai_difficulty = difficulty
    game.win_score = score

    if len(getattr(game, "players", ())) >= 2:
        if mode == MODE_SOLO_AI:
            game.players[0].name = "Joueur"
            game.players[1].name = "IA"
        elif mode == MODE_TRAINING:
            game.players[0].name = "Joueur"
            game.players[1].name = "Cible"
        else:
            game.players[0].name = "Joueur 1"
            game.players[1].name = "Joueur 2"

        if reset_match:
            for player in game.players:
                player.score = 0
                player.state = "idle"

    if reset_match:
        game.current_player = 0
        game.other_player = 1
        game.ai_shots_taken = 0
        game.status_message = ""

    return mode, difficulty, score


def _menu_rects():
    offset = max(0, (VIRTUAL_W - BASE_CONTENT_W) // 2)
    mode_rects = [
        pygame.Rect(offset + 44 + index * 184, 94, 172, 62)
        for index in range(len(MODE_OPTIONS))
    ]
    difficulty_rects = [
        pygame.Rect(offset + 251 + index * 104, 195, 94, 34)
        for index in range(len(DIFFICULTY_OPTIONS))
    ]
    return {
        "modes": mode_rects,
        "difficulties": difficulty_rects,
        "score_minus": pygame.Rect(offset + 313, 246, 38, 34),
        "score_plus": pygame.Rect(offset + 409, 246, 38, 34),
        "sound": pygame.Rect(offset + 568, 14, 54, 30),
        "play": pygame.Rect(offset + 190, 310, 260, 56),
    }


def _draw_menu(game, mode, difficulty, score, pointer):
    draw_menu_background(game)
    surface = game.vsurf
    rects = _menu_rects()
    offset = max(0, (VIRTUAL_W - BASE_CONTENT_W) // 2)

    title_back = pygame.Surface((390, 72), pygame.SRCALPHA)
    pygame.draw.rect(title_back, (4, 15, 34, 185), title_back.get_rect(), border_radius=15)
    surface.blit(title_back, (offset + 125, 5))

    title = game.font_big.render("GORILLAS", True, (255, 211, 78))
    surface.blit(title, title.get_rect(center=(VIRTUAL_W // 2, 31)))
    subtitle = game.font_small.render(
        "Choisis, règle si besoin, puis lance la banane.",
        True,
        (207, 228, 244),
    )
    surface.blit(subtitle, subtitle.get_rect(center=(VIRTUAL_W // 2, 59)))

    sound = getattr(game, "sound", None)
    muted = bool(getattr(sound, "muted", False))
    _draw_button(
        surface,
        game.font_small,
        rects["sound"],
        "MUET" if muted else "SON",
        selected=not muted,
        hovered=pointer is not None and rects["sound"].collidepoint(pointer),
        disabled=sound is None,
    )

    for index, (option, label, description) in enumerate(MODE_OPTIONS):
        rect = rects["modes"][index]
        _draw_button(
            surface,
            game.font_small,
            rect,
            label,
            selected=mode == option,
            hovered=pointer is not None and rect.collidepoint(pointer),
        )
        if mode == option:
            info = game.font_small.render(description, True, (255, 235, 168))
            surface.blit(info, info.get_rect(center=(VIRTUAL_W // 2, 174)))

    settings_rect = pygame.Rect(offset + 124, 184, 392, 108)
    _draw_panel(surface, settings_rect)

    difficulty_label = game.font_small.render("DIFFICULTÉ IA", True, (181, 206, 230))
    surface.blit(difficulty_label, (offset + 145, 204))
    difficulty_disabled = mode != MODE_SOLO_AI
    for index, (option, label) in enumerate(DIFFICULTY_OPTIONS):
        rect = rects["difficulties"][index]
        _draw_button(
            surface,
            game.font_small,
            rect,
            label,
            selected=difficulty == option and not difficulty_disabled,
            hovered=(
                not difficulty_disabled
                and pointer is not None
                and rect.collidepoint(pointer)
            ),
            disabled=difficulty_disabled,
        )

    score_label = game.font_small.render("POINTS POUR GAGNER", True, (181, 206, 230))
    surface.blit(score_label, (offset + 145, 255))
    for key, label in (("score_minus", "−"), ("score_plus", "+")):
        rect = rects[key]
        _draw_button(
            surface,
            game.font,
            rect,
            label,
            hovered=pointer is not None and rect.collidepoint(pointer),
        )
    score_image = game.font_big.render(str(score), True, (255, 216, 86))
    surface.blit(score_image, score_image.get_rect(center=(offset + 380, 263)))

    play = rects["play"]
    hovered = pointer is not None and play.collidepoint(pointer)
    shadow = play.move(0, 4)
    pygame.draw.rect(surface, (116, 70, 3), shadow, border_radius=13)
    pygame.draw.rect(
        surface,
        (255, 222, 98) if hovered else (255, 194, 48),
        play,
        border_radius=13,
    )
    pygame.draw.rect(surface, (255, 238, 166), play, width=2, border_radius=13)
    _draw_center(surface, game.font_big, "JOUER", play, (17, 32, 52))

    hint = game.font_small.render(
        "Entrée : jouer   •   1 / 2 / 3 : mode   •   Échap : quitter",
        True,
        (162, 190, 213),
    )
    surface.blit(hint, hint.get_rect(center=(VIRTUAL_W // 2, 385)))


async def run_menu(game):
    """Affiche le menu principal.

    Retourne ``MENU_START`` après JOUER et ``MENU_QUIT`` après Échap/fermeture.
    Le mode, la difficulté et le score sont déjà appliqués au jeu au retour.
    """
    first_open = not hasattr(game, "ai_difficulty")
    mode, difficulty, score = get_menu_selection(game)
    if first_open and mode == MODE_TWO_PLAYERS:
        mode = MODE_SOLO_AI

    pointer = None
    while True:
        mouse_position = pygame.mouse.get_pos()
        pointer = _screen_to_virtual(game, mouse_position)

        for event in pygame.event.get():
            # SDL emet souvent FINGERUP puis un MOUSEBUTTONUP synthetique.
            # Le gerer deux fois double le score et annule le bouton muet.
            if (
                event.type == pygame.MOUSEBUTTONUP
                and getattr(event, "touch", False)
            ):
                continue
            if event.type == pygame.QUIT:
                game.quit_requested = True
                return MENU_QUIT
            if event.type == pygame.VIDEORESIZE:
                game.screen = pygame.display.get_surface()
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game.quit_requested = True
                    return MENU_QUIT
                if event.key in (pygame.K_F11, pygame.K_f):
                    game.toggle_fullscreen()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    _play_sound(game)
                    apply_menu_selection(game, mode, difficulty, score)
                    return MENU_START
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    mode = MODE_SOLO_AI
                    _play_sound(game)
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    mode = MODE_TWO_PLAYERS
                    _play_sound(game)
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    mode = MODE_TRAINING
                    _play_sound(game)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS, pygame.K_LEFT):
                    score = max(MIN_WIN_SCORE, score - 1)
                    _play_sound(game)
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS, pygame.K_RIGHT):
                    score = min(MAX_WIN_SCORE, score + 1)
                    _play_sound(game)
                elif event.key == pygame.K_d and mode == MODE_SOLO_AI:
                    values = [item[0] for item in DIFFICULTY_OPTIONS]
                    difficulty = values[(values.index(difficulty) + 1) % len(values)]
                    _play_sound(game)
                elif event.key == pygame.K_m:
                    _toggle_sound(game)

            if event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
                position = _event_virtual_position(game, event)
                if position is None:
                    continue
                rects = _menu_rects()
                for index, rect in enumerate(rects["modes"]):
                    if rect.collidepoint(position):
                        mode = MODE_OPTIONS[index][0]
                        _play_sound(game)
                        break
                else:
                    if rects["score_minus"].collidepoint(position):
                        score = max(MIN_WIN_SCORE, score - 1)
                        _play_sound(game)
                    elif rects["score_plus"].collidepoint(position):
                        score = min(MAX_WIN_SCORE, score + 1)
                        _play_sound(game)
                    elif rects["sound"].collidepoint(position):
                        _toggle_sound(game)
                    elif rects["play"].collidepoint(position):
                        _play_sound(game)
                        apply_menu_selection(game, mode, difficulty, score)
                        return MENU_START
                    elif mode == MODE_SOLO_AI:
                        for index, rect in enumerate(rects["difficulties"]):
                            if rect.collidepoint(position):
                                difficulty = DIFFICULTY_OPTIONS[index][0]
                                _play_sound(game)
                                break

        _draw_menu(game, mode, difficulty, score, pointer)
        game.blit_scaled()
        pygame.display.flip()
        game.clock.tick(FPS)
        await asyncio.sleep(0)
