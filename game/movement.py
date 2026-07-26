"""Déplacement unique d'un gorille vers un toit voisin."""

import asyncio
import math

import pygame

from config import FPS, HUD_ACTIVE, VIRTUAL_H, VIRTUAL_W
from ui import draw_panel, render_text


MIN_ROOF_WIDTH = 34
MAX_ROOF_SEARCH = 3


def _roof_is_safe(game, building_index):
    """Un toit doit être assez large et encore solide au centre."""
    rects = getattr(game.city, "rects", ())
    if not 0 <= building_index < len(rects):
        return False
    rect = rects[building_index]
    if rect.width < MIN_ROOF_WIDTH:
        return False

    sample_y = min(VIRTUAL_H - 1, rect.top + 3)
    offsets = (-12, -6, 0, 6, 12)
    solid = 0
    for offset in offsets:
        x = max(rect.left + 2, min(rect.right - 3, rect.centerx + offset))
        try:
            solid += game.city.mask.get_at((x, sample_y)).a > 0
        except (AttributeError, IndexError):
            return False
    return solid >= 4


def relocation_targets(game, player_index):
    """Renvoie au plus un toit sûr à gauche et un à droite."""
    players = getattr(game, "players", ())
    if not 0 <= player_index < len(players):
        return []
    player = players[player_index]
    if not getattr(player, "move_available", False):
        return []

    current = int(player.building_index)
    occupied = {
        int(other.building_index)
        for index, other in enumerate(players)
        if index != player_index
    }
    targets = []
    for direction in (-1, 1):
        for distance in range(1, MAX_ROOF_SEARCH + 1):
            candidate = current + direction * distance
            if not 0 <= candidate < len(game.city.rects):
                break
            if candidate not in occupied and _roof_is_safe(game, candidate):
                targets.append(candidate)
                break
    return targets


def can_relocate(game, player_index):
    return bool(relocation_targets(game, player_index))


def choose_ai_relocation(game, player_index, target_index):
    """L'IA préfère un toit plus haut, sans se coller à l'adversaire."""
    candidates = relocation_targets(game, player_index)
    if not candidates:
        return None

    shooter = game.players[player_index]
    opponent = game.players[target_index]
    def score(building_index):
        rect = game.city.rects[building_index]
        distance = abs(rect.centerx - opponent.pos.x)
        too_close = max(0.0, 150.0 - distance) * 1.5
        return -rect.top * 1.35 + min(distance, 430.0) * 0.08 - too_close

    best = max(candidates, key=score)
    improvement = score(best) - score(shooter.building_index)
    chance = {"easy": 0.16, "normal": 0.28, "hard": 0.42}.get(
        str(getattr(game, "ai_difficulty", "normal")).lower(),
        0.28,
    )
    if improvement >= 18.0 or game.rng.random() < chance:
        return best
    return None


def _choice_rect(game, building_index):
    rect = game.city.rects[building_index]
    marker_y = max(96, rect.top - 32)
    return pygame.Rect(rect.centerx - 28, marker_y - 20, 56, 48)


def draw_relocation_choices(game, targets, selected):
    """Dessine des boutons directement au-dessus des toits."""
    veil = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
    veil.fill((4, 9, 25, 55))
    game.vsurf.blit(veil, (0, 0))

    title_rect = pygame.Rect(VIRTUAL_W // 2 - 154, 54, 308, 38)
    draw_panel(
        game.vsurf,
        title_rect,
        fill=(7, 19, 42, 242),
        border=(120, 151, 191),
        accent=HUD_ACTIVE,
        shadow=True,
    )
    title = render_text(game.font, "CHOISIS UN TOIT", (255, 232, 151))
    game.vsurf.blit(title, title.get_rect(center=(title_rect.centerx, 67)))
    help_text = render_text(
        game.font_small,
        "Touchez un toit  •  Échap : annuler",
        (224, 235, 246),
    )
    game.vsurf.blit(help_text, help_text.get_rect(center=(title_rect.centerx, 82)))

    for position, building_index in enumerate(targets):
        rect = _choice_rect(game, building_index)
        active = position == selected
        color = (255, 211, 78) if active else (122, 218, 255)
        pygame.draw.circle(game.vsurf, (8, 20, 43), rect.center, 21)
        pygame.draw.circle(game.vsurf, color, rect.center, 21, 3)
        arrow = "<" if building_index < game.players[game.current_player].building_index else ">"
        image = render_text(game.font_big, arrow, color)
        game.vsurf.blit(image, image.get_rect(center=(rect.centerx, rect.centery - 1)))
        roof = game.city.rects[building_index]
        pygame.draw.line(
            game.vsurf,
            color,
            (roof.centerx - 13, roof.top - 3),
            (roof.centerx + 13, roof.top - 3),
            3,
        )


async def select_relocation_target(game, player_index):
    """Attend le choix clavier, souris ou tactile. None annule."""
    targets = relocation_targets(game, player_index)
    if not targets:
        return None
    selected = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.quit_requested = True
                return "quit"
            if game.is_resize_event(event):
                game.resize_display(event)
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_q):
                    selected = (selected - 1) % len(targets)
                    game.sound.play("click")
                    continue
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    selected = (selected + 1) % len(targets)
                    game.sound.play("click")
                    continue
                if event.key in (
                    pygame.K_RETURN,
                    pygame.K_KP_ENTER,
                    pygame.K_SPACE,
                ):
                    game.sound.play("click")
                    return targets[selected]

            action = game._handle_common_event(event)
            if action in ("quit", "menu"):
                return action

            if event.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION):
                position = _event_virtual_position(game, event)
                if position is not None:
                    for index, target in enumerate(targets):
                        if _choice_rect(game, target).collidepoint(position):
                            selected = index

            if event.type in (
                pygame.MOUSEBUTTONUP,
                pygame.FINGERUP,
            ):
                if getattr(event, "touch", False):
                    continue
                position = _event_virtual_position(game, event)
                if position is not None:
                    for index, target in enumerate(targets):
                        if _choice_rect(game, target).collidepoint(position):
                            game.sound.play("click")
                            return target

        dt = min(0.05, game.clock.tick(FPS) / 1000.0)
        game.scene_time += dt
        game.draw_scene()
        draw_relocation_choices(game, targets, selected)
        game.blit_scaled()
        pygame.display.flip()
        await asyncio.sleep(0)


def _event_virtual_position(game, event):
    if event.type in (
        pygame.MOUSEBUTTONUP,
        pygame.MOUSEMOTION,
    ):
        return game.screen_to_virtual(event.pos)
    if event.type in (pygame.FINGERUP, pygame.FINGERMOTION):
        screen_w, screen_h = game.screen.get_size()
        return game.screen_to_virtual((event.x * screen_w, event.y * screen_h))
    return None


async def animate_relocation(game, player_index, building_index):
    """Petit saut en arc. Le déplacement est consommé à l'atterrissage."""
    if building_index not in relocation_targets(game, player_index):
        return None

    player = game.players[player_index]
    start = player.pos.copy()
    target_rect = game.city.rects[building_index]
    destination = pygame.Vector2(target_rect.centerx, target_rect.top)
    duration = 0.58
    elapsed = 0.0
    player.move_available = False
    game.status_message = f"{player.name} change de toit !"
    game.sound.play("click")

    while elapsed < duration:
        for event in pygame.event.get():
            action = game._handle_common_event(event)
            if action in ("quit", "menu"):
                return action

        dt = min(0.05, game.clock.tick(FPS) / 1000.0)
        elapsed += dt
        game.scene_time += dt
        progress = min(1.0, elapsed / duration)
        eased = progress * progress * (3.0 - 2.0 * progress)
        player.pos = start.lerp(destination, eased)
        player.pos.y -= math.sin(progress * math.pi) * 46.0
        player.state = "leftup" if progress < 0.5 else "rightup"

        game.draw_scene()
        game.blit_scaled()
        pygame.display.flip()
        await asyncio.sleep(0)

    player.pos = destination
    player.building_index = building_index
    player.state = "idle"
    game.status_message = "Déplacement utilisé. À toi de tirer !"
    return None
