# action.py — visée moderne compatible Pygame et Pygbag
import asyncio
import math

import pygame

from browser_input import BrowserAimControls
from config import FPS, VIRTUAL_H, VIRTUAL_W
from movement import can_relocate
from ui import draw_center_text


MIN_ANGLE = 5.0
MAX_ANGLE = 85.0
MIN_POWER = 50.0
MAX_POWER = 400.0
DEFAULT_ANGLE = 45.0
DEFAULT_POWER = 180.0


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


def draw_center_text_shadow(surface, font, text, y, color, shadow=(0, 0, 0)):
    draw_center_text(surface, font, text, y + 2, color=shadow)
    draw_center_text(surface, font, text, y, color=color)


def get_remembered_shot(player):
    """Renvoie l'angle et la puissance mémorisés pour ce joueur."""
    angle = float(getattr(player, "last_angle", DEFAULT_ANGLE))
    power = float(getattr(player, "last_power", DEFAULT_POWER))
    return (
        _clamp(angle, MIN_ANGLE, MAX_ANGLE),
        _clamp(power, MIN_POWER, MAX_POWER),
    )


def remember_shot(player, angle, power):
    """Mémorise un tir validé et renvoie ses valeurs bornées."""
    angle = round(_clamp(float(angle), MIN_ANGLE, MAX_ANGLE), 1)
    power = round(_clamp(float(power), MIN_POWER, MAX_POWER), 1)
    player.last_angle = angle
    player.last_power = power
    return angle, power


def reset_shot_memory(players):
    """Réinitialise la visée d'une liste de joueurs."""
    for player in players:
        player.last_angle = DEFAULT_ANGLE
        player.last_power = DEFAULT_POWER


def _screen_to_virtual(game, position):
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
    if event.type in (
        pygame.MOUSEBUTTONDOWN,
        pygame.MOUSEBUTTONUP,
        pygame.MOUSEMOTION,
    ):
        return _screen_to_virtual(game, event.pos)
    if event.type in (pygame.FINGERDOWN, pygame.FINGERUP, pygame.FINGERMOTION):
        screen_w, screen_h = game.screen.get_size()
        return _screen_to_virtual(game, (event.x * screen_w, event.y * screen_h))
    return None


def _aim_rects():
    return {
        "panel": pygame.Rect(374, 220, 250, 166),
        "angle": pygame.Rect(394, 267, 210, 12),
        "power": pygame.Rect(394, 317, 210, 12),
        "move": pygame.Rect(394, 344, 96, 32),
        "fire": pygame.Rect(498, 344, 106, 32),
    }


def _value_from_slider(rect, x, minimum, maximum, step):
    ratio = _clamp((x - rect.left) / max(1, rect.width), 0.0, 1.0)
    value = minimum + ratio * (maximum - minimum)
    return round(value / step) * step


def _draw_slider(surface, font, label, value, rect, minimum, maximum, accent):
    label_image = font.render(label, True, (190, 214, 237))
    surface.blit(label_image, (rect.x, rect.y - 23))
    value_image = font.render(str(int(round(value))), True, (255, 239, 186))
    surface.blit(value_image, (rect.right - value_image.get_width(), rect.y - 23))

    pygame.draw.rect(surface, (16, 34, 61), rect, border_radius=6)
    fill_width = int((value - minimum) / (maximum - minimum) * rect.width)
    if fill_width > 0:
        pygame.draw.rect(
            surface,
            accent,
            (rect.x, rect.y, fill_width, rect.height),
            border_radius=6,
        )
    knob_x = rect.x + fill_width
    pygame.draw.circle(surface, (255, 255, 255), (knob_x, rect.centery), 7)
    pygame.draw.circle(surface, accent, (knob_x, rect.centery), 7, width=2)


def _draw_aim_guide(game, player, angle, power):
    try:
        image_height = game.spr.gorilla_idle.get_height()
        start = pygame.Vector2(player.pos.x, player.pos.y - image_height - 10)
    except (AttributeError, TypeError):
        return

    radians = math.radians(angle)
    direction = pygame.Vector2(math.cos(radians), -math.sin(radians))
    if len(getattr(game, "players", ())) > 1 and player is game.players[1]:
        direction.x *= -1

    length = 25.0 + (power - MIN_POWER) / (MAX_POWER - MIN_POWER) * 34.0
    for distance in range(12, int(length), 8):
        point = start + direction * distance
        if 0 <= point.x < VIRTUAL_W and 0 <= point.y < VIRTUAL_H:
            radius = 3 if distance < 28 else 2
            pygame.draw.circle(
                game.vsurf,
                (255, 218, 79),
                (int(point.x), int(point.y)),
                radius,
            )


def _draw_aim_panel(game, player, angle, power, pointer=None):
    surface = game.vsurf
    rects = _aim_rects()
    panel = rects["panel"]

    layer = pygame.Surface(panel.size, pygame.SRCALPHA)
    pygame.draw.rect(layer, (4, 15, 34, 230), layer.get_rect(), border_radius=13)
    pygame.draw.rect(
        layer,
        (77, 116, 164, 245),
        layer.get_rect(),
        width=1,
        border_radius=13,
    )
    surface.blit(layer, panel)

    title = game.font.render("RÉGLAGE DU TIR", True, (255, 211, 78))
    surface.blit(title, title.get_rect(center=(panel.centerx, panel.y + 20)))
    _draw_slider(
        surface,
        game.font_small,
        "ANGLE",
        angle,
        rects["angle"],
        MIN_ANGLE,
        MAX_ANGLE,
        (77, 176, 255),
    )
    _draw_slider(
        surface,
        game.font_small,
        "PUISSANCE",
        power,
        rects["power"],
        MIN_POWER,
        MAX_POWER,
        (255, 157, 54),
    )

    move = rects["move"]
    move_enabled = can_relocate(game, game.current_player)
    move_hovered = (
        move_enabled
        and pointer is not None
        and move.collidepoint(pointer)
    )
    pygame.draw.rect(surface, (15, 35, 55), move.move(0, 3), border_radius=8)
    pygame.draw.rect(
        surface,
        (103, 201, 235)
        if move_hovered
        else ((43, 128, 169) if move_enabled else (58, 65, 78)),
        move,
        border_radius=8,
    )
    move_text = game.font_small.render(
        "BOUGER" if move_enabled else "UTILISÉ",
        True,
        (239, 251, 255) if move_enabled else (157, 164, 177),
    )
    surface.blit(move_text, move_text.get_rect(center=move.center))

    fire = rects["fire"]
    hovered = pointer is not None and fire.collidepoint(pointer)
    pygame.draw.rect(surface, (119, 68, 2), fire.move(0, 3), border_radius=8)
    pygame.draw.rect(
        surface,
        (255, 224, 104) if hovered else (255, 190, 45),
        fire,
        border_radius=8,
    )
    fire_text = game.font.render("TIRER", True, (12, 29, 50))
    surface.blit(fire_text, fire_text.get_rect(center=fire.center))

    help_text = game.font_small.render(
        "Flèches : régler   •   B : bouger   •   Entrée : tirer",
        True,
        (226, 236, 246),
    )
    help_back = pygame.Surface((help_text.get_width() + 18, 23), pygame.SRCALPHA)
    pygame.draw.rect(help_back, (3, 13, 28, 195), help_back.get_rect(), border_radius=8)
    help_back.blit(help_text, (9, 4))
    surface.blit(help_back, help_back.get_rect(midbottom=(VIRTUAL_W // 2, VIRTUAL_H - 5)))


async def ask_angle_power(game, player):
    """Attend un tir humain.

    Retourne ``(angle, puissance)``. Échap renvoie ``None`` et pose
    ``game.menu_requested = True``. Une fermeture pose aussi
    ``game.quit_requested = True`` pour que la boucle principale distingue
    clairement les deux actions.
    """
    angle, power = get_remembered_shot(player)
    web_controls = BrowserAimControls()
    web_controls.show(
        angle,
        power,
        can_move=can_relocate(game, game.current_player),
    )
    active_slider = None
    pointer = None
    game.menu_requested = False

    def update_slider(name, position):
        nonlocal angle, power
        rects = _aim_rects()
        if position is None:
            return
        if name == "angle":
            angle = _value_from_slider(
                rects["angle"], position[0], MIN_ANGLE, MAX_ANGLE, 1.0
            )
        elif name == "power":
            power = _value_from_slider(
                rects["power"], position[0], MIN_POWER, MAX_POWER, 5.0
            )
        web_controls.set_values(angle, power)

    try:
        while True:
            if web_controls.available:
                values = web_controls.values()
                if values is not None:
                    angle = _clamp(values[0], MIN_ANGLE, MAX_ANGLE)
                    power = _clamp(values[1], MIN_POWER, MAX_POWER)
                if web_controls.cancelled():
                    game.menu_requested = True
                    return None
                if web_controls.move_requested():
                    if can_relocate(game, game.current_player):
                        _play_sound(game)
                        return "move"
                if web_controls.fired():
                    _play_sound(game)
                    return remember_shot(player, angle, power)

            pointer = _screen_to_virtual(game, pygame.mouse.get_pos())

            for event in pygame.event.get():
                # Les gestes tactiles arrivent aussi comme evenements souris
                # avec ``touch=True``. Les FINGER* sont deja geres ci-dessous.
                if (
                    event.type
                    in (
                        pygame.MOUSEBUTTONDOWN,
                        pygame.MOUSEBUTTONUP,
                        pygame.MOUSEMOTION,
                    )
                    and getattr(event, "touch", False)
                ):
                    continue
                if event.type == pygame.QUIT:
                    game.quit_requested = True
                    return None
                if event.type == pygame.VIDEORESIZE:
                    game.screen = pygame.display.get_surface()
                    continue
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game.menu_requested = True
                        return None
                    if event.key in (pygame.K_F11, pygame.K_f):
                        game.toggle_fullscreen()
                        continue
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                        _play_sound(game)
                        return remember_shot(player, angle, power)
                    if event.key == pygame.K_b:
                        if can_relocate(game, game.current_player):
                            _play_sound(game)
                            return "move"
                        continue
                    if event.key == pygame.K_m:
                        _toggle_sound(game)
                        continue

                    fine = not (event.mod & pygame.KMOD_SHIFT)
                    angle_step = 1.0 if fine else 5.0
                    power_step = 5.0 if fine else 25.0
                    changed = True
                    if event.key in (pygame.K_LEFT, pygame.K_q, pygame.K_a):
                        angle -= angle_step
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        angle += angle_step
                    elif event.key in (pygame.K_UP, pygame.K_z, pygame.K_w):
                        power += power_step
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        power -= power_step
                    elif event.key == pygame.K_r:
                        angle, power = DEFAULT_ANGLE, DEFAULT_POWER
                    else:
                        changed = False

                    if changed:
                        angle = _clamp(angle, MIN_ANGLE, MAX_ANGLE)
                        power = _clamp(power, MIN_POWER, MAX_POWER)
                        web_controls.set_values(angle, power)

                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                    position = _event_virtual_position(game, event)
                    if position is None:
                        continue
                    rects = _aim_rects()
                    for name in ("angle", "power"):
                        hitbox = rects[name].inflate(0, 22)
                        if hitbox.collidepoint(position):
                            active_slider = name
                            update_slider(name, position)
                            _play_sound(game)
                            break

                if event.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION):
                    if active_slider is not None:
                        update_slider(active_slider, _event_virtual_position(game, event))

                if event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
                    position = _event_virtual_position(game, event)
                    if active_slider is not None:
                        update_slider(active_slider, position)
                        active_slider = None
                    elif position is not None and _aim_rects()["fire"].collidepoint(position):
                        _play_sound(game)
                        return remember_shot(player, angle, power)
                    elif (
                        position is not None
                        and _aim_rects()["move"].collidepoint(position)
                        and can_relocate(game, game.current_player)
                    ):
                        _play_sound(game)
                        return "move"

            dt = min(0.05, game.clock.tick(FPS) / 1000.0)
            game.scene_time += dt
            game.draw_scene()
            _draw_aim_guide(game, player, angle, power)
            if not web_controls.available:
                _draw_aim_panel(game, player, angle, power, pointer)
            game.blit_scaled()
            pygame.display.flip()
            await asyncio.sleep(0)
    finally:
        web_controls.hide()
