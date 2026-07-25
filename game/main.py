"""Gorillas — version web « QBASIC Deluxe »."""

import asyncio
import inspect
import math
import random

import pygame
from pygame.math import Vector2

from action import ask_angle_power
from ai import choose_ai_shot
from audio import SoundBank
from config import *
from graphics import (
    City,
    draw_explosion_frame,
    draw_scene,
    explode_in_city,
)
from intro import show_intro
from menu import run_menu
from movement import (
    animate_relocation,
    choose_ai_relocation,
    select_relocation_target,
)
from physics import (
    first_segment_collision,
    out_of_bounds,
    segment_circle_intersection,
    step_ballistic,
)
from sprites import Sprites


WINNING_REPLAY_DURATION = 2.8


class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.building_index = 0
        self.pos = Vector2(0, 0)
        self.score = 0
        self.state = "idle"
        self.last_angle = 45.0
        self.last_power = 180.0
        self.move_available = True
        self.reaction = ""
        self.reaction_until = 0.0


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Gorillas — QBASIC Deluxe")

        # Le web choisit une surface virtuelle au ratio réel du téléphone.
        self.screen = pygame.display.set_mode(
            (VIRTUAL_W, VIRTUAL_H),
            pygame.RESIZABLE,
        )
        self.clock = pygame.time.Clock()
        self.fullscreen = False
        self._render_rect = pygame.Rect(0, 0, VIRTUAL_W, VIRTUAL_H)

        self.vsurf = pygame.Surface((VIRTUAL_W, VIRTUAL_H)).convert_alpha()
        self.font = pygame.font.Font(None, FONT_MAIN_SIZE + 4)
        self.font_small = pygame.font.Font(None, FONT_SMALL_SIZE + 3)
        self.font_big = pygame.font.Font(None, FONT_BIG_SIZE + 12)

        self.spr = Sprites()
        self.sound = SoundBank()
        self.rng = random.Random()

        self.players = [
            Player("Joueur 1", (126, 220, 255)),
            Player("Joueur 2", (255, 193, 74)),
        ]
        self.current_player = 0
        self.other_player = 1
        self.game_mode = "solo_ai"
        self.ai_difficulty = "normal"
        self.ai_shots_taken = 0

        self.city = City()
        self.sun_rect = self.spr.sun.get_rect(center=(VIRTUAL_W // 2, 78))

        self.banana_active = False
        self.banana_pos = Vector2()
        self.banana_vel = Vector2()
        self.banana_angle = 0.0
        self.banana_trail = []

        self.gravity = DEFAULT_GRAVITY
        self.wind = 0
        self.win_score = DEFAULT_WIN_SCORE

        self.status_message = ""
        self.scene_time = 0.0
        self.sun_expression = "happy"
        self.quit_requested = False

        self._ignore_self_timer = 0.0
        self._ignore_self_index = None
        self._throw_pose_timer = 0.0
        self.shot_path = []
        self._shot_min_distances = [float("inf"), float("inf")]
        self.city_intro_pending = False
        self._last_thunder_cycle = -1

    def toggle_fullscreen(self):
        # En web, le conteneur HTML gère la taille. En natif, F/F11 fonctionne.
        self.fullscreen = not self.fullscreen
        flags = pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE
        size = (0, 0) if self.fullscreen else (VIRTUAL_W, VIRTUAL_H)
        try:
            self.screen = pygame.display.set_mode(size, flags)
        except pygame.error:
            self.fullscreen = False
            self.screen = pygame.display.set_mode(
                (VIRTUAL_W, VIRTUAL_H),
                pygame.RESIZABLE,
            )

    def blit_scaled(self, shake=(0, 0)):
        """Agrandit sans déformer le monde logique."""
        screen_w, screen_h = self.screen.get_size()
        if screen_w <= 0 or screen_h <= 0:
            return

        scale = min(screen_w / VIRTUAL_W, screen_h / VIRTUAL_H)
        target_w = max(1, round(VIRTUAL_W * scale))
        target_h = max(1, round(VIRTUAL_H * scale))
        left = (screen_w - target_w) // 2 + int(shake[0])
        top = (screen_h - target_h) // 2 + int(shake[1])

        self.screen.fill((5, 8, 24))
        if (target_w, target_h) == (VIRTUAL_W, VIRTUAL_H):
            scaled = self.vsurf
        else:
            # Le lissage conserve les courbes et surtout le texte lisible sur
            # les écrans Retina, même avec un facteur non entier.
            scaled = pygame.transform.smoothscale(
                self.vsurf,
                (target_w, target_h),
            )
        self.screen.blit(scaled, (left, top))
        self._render_rect = pygame.Rect(left, top, target_w, target_h)

    def screen_to_virtual(self, pos):
        if not self._render_rect.collidepoint(pos):
            return None
        x = (pos[0] - self._render_rect.x) * VIRTUAL_W / self._render_rect.w
        y = (pos[1] - self._render_rect.y) * VIRTUAL_H / self._render_rect.h
        return int(x), int(y)

    def new_city(self):
        self.city.generate(self.rng)
        left_high = max(1, len(self.city.rects) // 3)
        right_low = max(
            len(self.city.rects) // 3 * 2,
            left_high + 1,
        )
        left_candidates = list(range(1, left_high + 1))
        right_candidates = list(range(right_low, len(self.city.rects) - 1))
        roof_pairs = [
            (left, right)
            for left in left_candidates
            for right in right_candidates
        ]
        varied_pairs = [
            pair
            for pair in roof_pairs
            if abs(
                self.city.rects[pair[0]].top
                - self.city.rects[pair[1]].top
            )
            >= 36
        ]
        if varied_pairs:
            left_idx, right_idx = self.rng.choice(varied_pairs)
        else:
            left_idx, right_idx = max(
                roof_pairs,
                key=lambda pair: abs(
                    self.city.rects[pair[0]].top
                    - self.city.rects[pair[1]].top
                ),
            )
        self.players[0].building_index = left_idx
        self.players[1].building_index = right_idx
        for player in self.players:
            building = self.city.rects[player.building_index]
            player.pos = Vector2(building.centerx, building.top)
            player.state = "idle"
            player.move_available = True
            player.reaction = ""
            player.reaction_until = 0.0
        self.wind = self.city.choose_wind(self.rng)
        self.banana_active = False
        self.banana_trail.clear()
        self.shot_path.clear()
        self.sun_expression = "happy"
        self.city_intro_pending = True
        self._last_thunder_cycle = -1

    def reset_match(self):
        for player in self.players:
            player.score = 0
            player.last_angle = 45.0
            player.last_power = 180.0
            player.state = "idle"
            player.move_available = True
        self.current_player = 0
        self.other_player = 1
        self.ai_shots_taken = 0
        self.status_message = ""
        self.new_city()

    def is_solo_target_mode(self):
        return self.game_mode == "solo_target"

    def is_solo_ai_mode(self):
        return self.game_mode == "solo_ai"

    def is_ai_turn(self):
        return self.is_solo_ai_mode() and self.current_player == 1

    def draw_scene(self):
        if self.city.storm_flash_active(self.scene_time):
            cycle = int(self.scene_time // 8.0)
            if cycle != self._last_thunder_cycle:
                self._last_thunder_cycle = cycle
                self.sound.play("thunder")
        draw_scene(
            self.vsurf,
            self.spr,
            self.city,
            self.players,
            self.banana_active,
            self.banana_pos,
            self.sun_rect,
            self.font,
            self.font_small,
            self.status_message,
            self.wind,
            self.banana_angle,
            active_player=self.current_player,
            banana_trail=self.banana_trail,
            scene_time=self.scene_time,
            sun_expression=self.sun_expression,
        )

    def _set_reaction(self, player_index, reaction, duration=1.0):
        if not 0 <= player_index < len(self.players):
            return
        player = self.players[player_index]
        player.reaction = reaction
        player.reaction_until = self.scene_time + duration

    async def show_reaction_pause(self, duration=1.25):
        """Laisse le temps de voir rire ou paniquer le gorille."""
        elapsed = 0.0
        while elapsed < duration:
            for event in pygame.event.get():
                action = self._handle_common_event(event)
                if action in ("quit", "menu"):
                    return action
            dt = min(0.05, self.clock.tick(FPS) / 1000.0)
            elapsed += dt
            self.scene_time += dt
            self.draw_scene()
            self.blit_scaled()
            pygame.display.flip()
            await asyncio.sleep(0)
        return None

    def _vibrate(self, pattern):
        try:
            import platform

            window = getattr(platform, "window", None)
            if window is None:
                return
            values = (
                [max(0, int(value)) for value in pattern]
                if isinstance(pattern, (tuple, list))
                else [max(0, int(pattern))]
            )
            window.eval(
                "navigator.vibrate && navigator.vibrate(%s)"
                % repr(values)
            )
        except Exception:
            pass

    def _handle_common_event(self, event):
        if event.type == pygame.QUIT:
            self.quit_requested = True
            return "quit"
        if event.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.get_surface()
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_F11, pygame.K_f):
                self.toggle_fullscreen()
            elif event.key == pygame.K_m:
                self.sound.toggle()
            elif event.key == pygame.K_ESCAPE:
                return "menu"
        return None

    async def wait_for_ai_shot(self):
        old_status = self.status_message
        self.status_message = "L'IA réfléchit..."
        elapsed = 0.0
        while elapsed < 0.62:
            for event in pygame.event.get():
                action = self._handle_common_event(event)
                if action in ("quit", "menu"):
                    return None

            dt = min(0.05, self.clock.tick(FPS) / 1000.0)
            elapsed += dt
            self.scene_time += dt
            self.draw_scene()
            self.blit_scaled()
            pygame.display.flip()
            await asyncio.sleep(0)

        result = choose_ai_shot(
            self,
            self.current_player,
            self.other_player,
        )
        if inspect.isawaitable(result):
            result = await result
        self.status_message = old_status
        return result

    async def show_city_intro(self):
        """Travelling lent et lisible au début de chaque ville."""
        if not self.city_intro_pending:
            return None
        duration = 2.6
        elapsed = 0.0
        while elapsed < duration:
            for event in pygame.event.get():
                action = self._handle_common_event(event)
                if action in ("quit", "menu"):
                    return action
                if event.type in (
                    pygame.KEYDOWN,
                    pygame.MOUSEBUTTONDOWN,
                    pygame.FINGERDOWN,
                ):
                    elapsed = duration

            dt = min(0.05, self.clock.tick(FPS) / 1000.0)
            elapsed += dt
            self.scene_time += dt
            progress = min(1.0, elapsed / duration)
            travel = progress * progress * (3.0 - 2.0 * progress)
            self.draw_scene()

            source = self.vsurf.copy()
            zoom = 1.02 + math.sin(progress * math.pi) * 0.07
            crop_w = max(1, int(VIRTUAL_W / zoom))
            crop_h = max(1, int(VIRTUAL_H / zoom))
            camera_x = (
                self.players[0].pos.x * (1.0 - travel)
                + self.players[1].pos.x * travel
            )
            camera_y = 215
            crop_x = max(0, min(VIRTUAL_W - crop_w, int(camera_x - crop_w / 2)))
            crop_y = max(0, min(VIRTUAL_H - crop_h, int(camera_y - crop_h / 2)))
            crop = source.subsurface((crop_x, crop_y, crop_w, crop_h))
            self.vsurf.blit(
                pygame.transform.scale(crop, (VIRTUAL_W, VIRTUAL_H)),
                (0, 0),
            )

            shade = pygame.Surface((VIRTUAL_W, 78), pygame.SRCALPHA)
            shade.fill((3, 10, 24, 208))
            self.vsurf.blit(shade, (0, VIRTUAL_H // 2 - 39))
            title = self.font_big.render(
                self.city.city_style_label,
                True,
                (255, 218, 91),
            )
            subtitle = self.font_small.render(
                self.city.city_style_tagline,
                True,
                (225, 236, 246),
            )
            self.vsurf.blit(
                title,
                title.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2 - 10)),
            )
            self.vsurf.blit(
                subtitle,
                subtitle.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2 + 18)),
            )
            self.blit_scaled()
            pygame.display.flip()
            await asyncio.sleep(0)

        self.city_intro_pending = False
        return None

    async def play_winning_replay(self):
        """Rejoue lentement la trajectoire, puis garde l'impact à l'écran."""
        if len(self.shot_path) < 2:
            return None
        duration = WINNING_REPLAY_DURATION
        flight_end = 0.62
        explosion_end = 0.82
        elapsed = 0.0
        impact = Vector2(self.shot_path[-1])
        while elapsed < duration:
            for event in pygame.event.get():
                action = self._handle_common_event(event)
                if action in ("quit", "menu"):
                    return action

            dt = min(0.04, self.clock.tick(FPS) / 1000.0)
            elapsed += dt
            self.scene_time += dt
            progress = min(1.0, elapsed / duration)
            raw_path_progress = min(1.0, progress / flight_end)
            path_progress = (
                raw_path_progress
                * raw_path_progress
                * (3.0 - 2.0 * raw_path_progress)
            )
            path_index = min(
                len(self.shot_path) - 1,
                int(path_progress * (len(self.shot_path) - 1)),
            )
            banana = Vector2(self.shot_path[path_index])

            self.draw_scene()
            _trail = self.shot_path[max(0, path_index - 22):path_index + 1]
            for index, point in enumerate(_trail):
                size = 1 + int(index / max(1, len(_trail) - 1) * 2)
                pygame.draw.rect(
                    self.vsurf,
                    (255, 185, 61),
                    (int(point.x) - size // 2, int(point.y) - size // 2, size, size),
                )
            if progress <= flight_end:
                angle = round((progress * 720) / 15.0) * 15.0
                image = pygame.transform.rotate(self.spr.banana, angle)
                self.vsurf.blit(
                    image,
                    image.get_rect(center=(int(banana.x), int(banana.y))),
                )
            if progress > flight_end:
                explosion_progress = min(
                    0.72,
                    (progress - flight_end)
                    / max(0.01, explosion_end - flight_end),
                )
                draw_explosion_frame(
                    self.vsurf,
                    impact,
                    explosion_progress,
                    max_radius=52,
                )

            zoom = 1.0 + max(0.0, progress - 0.40) * 0.55
            if zoom > 1.0:
                source = self.vsurf.copy()
                crop_w = max(1, int(VIRTUAL_W / zoom))
                crop_h = max(1, int(VIRTUAL_H / zoom))
                crop_x = max(0, min(VIRTUAL_W - crop_w, int(impact.x - crop_w / 2)))
                crop_y = max(0, min(VIRTUAL_H - crop_h, int(impact.y - crop_h / 2)))
                crop = source.subsurface((crop_x, crop_y, crop_w, crop_h))
                self.vsurf.blit(
                    pygame.transform.scale(crop, (VIRTUAL_W, VIRTUAL_H)),
                    (0, 0),
                )

            label_text = "IMPACT !" if progress >= explosion_end else "RALENTI"
            label = self.font_small.render(
                label_text,
                True,
                (255, 226, 112),
            )
            self.vsurf.blit(label, label.get_rect(center=(VIRTUAL_W // 2, 66)))
            self.blit_scaled()
            pygame.display.flip()
            await asyncio.sleep(0)
        return None

    def fire_banana(self, player, angle_deg, power):
        angle_deg = max(5.0, min(85.0, float(angle_deg)))
        power = max(50.0, min(400.0, float(power)))
        player.last_angle = angle_deg
        player.last_power = power

        angle = math.radians(angle_deg)
        velocity_x = math.cos(angle) * power
        velocity_y = math.sin(angle) * power
        if player is self.players[1]:
            velocity_x = -velocity_x

        image_height = self.spr.gorilla_idle.get_height()
        start = Vector2(player.pos.x, player.pos.y - image_height - 10)
        self.banana_pos = start.copy()
        self.banana_vel = Vector2(velocity_x, -velocity_y)
        self.banana_active = True
        self.banana_angle = 0.0
        self.banana_trail = [start.copy()]
        self.shot_path = [start.copy()]
        self._shot_min_distances = [float("inf"), float("inf")]
        player.state = "leftup" if player is self.players[0] else "rightup"
        self._throw_pose_timer = 0.28
        self._ignore_self_index = self.current_player
        self._ignore_self_timer = 0.22
        self.status_message = ""
        self.sound.play("throw")
        self._vibrate(14)

    async def animate_explosion(self, x, y, strong=False):
        self.sound.play("explosion" if strong else "impact")
        self._vibrate((35, 22, 70) if strong else 24)
        elapsed = 0.0
        duration = 0.48 if strong else 0.34
        shake_strength = 5 if strong else 3

        while elapsed < duration:
            for event in pygame.event.get():
                action = self._handle_common_event(event)
                if action in ("quit", "menu"):
                    return action

            dt = min(0.04, self.clock.tick(FPS) / 1000.0)
            elapsed += dt
            self.scene_time += dt
            progress = min(1.0, elapsed / duration)

            self.draw_scene()
            draw_explosion_frame(
                self.vsurf,
                (int(x), int(y)),
                progress,
                max_radius=50 if strong else 38,
            )
            decay = 1.0 - progress
            shake = (
                self.rng.randint(-shake_strength, shake_strength) * decay,
                self.rng.randint(-shake_strength, shake_strength) * decay,
            )
            self.blit_scaled(shake)
            pygame.display.flip()
            await asyncio.sleep(0)
        return None

    def _solid_at(self, point):
        x, y = int(point.x), int(point.y)
        if not (0 <= x < VIRTUAL_W and 0 <= y < VIRTUAL_H):
            return False
        return self.city.mask.get_at((x, y)).a > 0

    def _first_player_hit(self, start, end):
        result = None
        for index, player in enumerate(self.players):
            if (
                self._ignore_self_index is not None
                and index == self._ignore_self_index
            ):
                continue
            center = Vector2(
                player.pos.x,
                player.pos.y - self.spr.gorilla_idle.get_height() // 2,
            )
            hit_t = segment_circle_intersection(
                start,
                end,
                center,
                30,
            )
            if hit_t is not None and (result is None or hit_t < result[0]):
                result = (hit_t, index, center)
        return result

    async def update_banana(self, dt):
        if not self.banana_active:
            return None

        dt = max(0.0, min(float(dt), 0.05))
        substeps = max(1, math.ceil(dt / (1.0 / 120.0)))
        step_dt = dt / substeps

        for _ in range(substeps):
            previous = self.banana_pos.copy()
            self.banana_pos, self.banana_vel = step_ballistic(
                self.banana_pos,
                self.banana_vel,
                self.gravity,
                self.wind,
                WIND_ACCEL_PER_UNIT,
                step_dt,
            )
            self.banana_angle = (
                self.banana_angle + BANANA_ROT_SPEED * step_dt
            ) % 360
            if (
                not self.shot_path
                or self.shot_path[-1].distance_to(self.banana_pos) >= 2.5
            ):
                self.shot_path.append(self.banana_pos.copy())
                self.shot_path = self.shot_path[-700:]

            for index, player in enumerate(self.players):
                if index == self.current_player:
                    continue
                center = Vector2(
                    player.pos.x,
                    player.pos.y - self.spr.gorilla_idle.get_height() // 2,
                )
                self._shot_min_distances[index] = min(
                    self._shot_min_distances[index],
                    self.banana_pos.distance_to(center),
                )

            if (
                not self.banana_trail
                or self.banana_trail[-1].distance_to(self.banana_pos) >= 5
            ):
                self.banana_trail.append(self.banana_pos.copy())
                self.banana_trail = self.banana_trail[-7:]

            if self._throw_pose_timer > 0:
                self._throw_pose_timer -= step_dt
                if self._throw_pose_timer <= 0:
                    self.players[self.current_player].state = "idle"

            if self._ignore_self_timer > 0:
                self._ignore_self_timer -= step_dt
                if self._ignore_self_timer <= 0:
                    self._ignore_self_index = None

            building_hit = first_segment_collision(
                previous,
                self.banana_pos,
                self._solid_at,
                max_spacing=1.5,
            )
            player_hit = self._first_player_hit(previous, self.banana_pos)

            building_t = building_hit[1] if building_hit is not None else None
            player_t = player_hit[0] if player_hit is not None else None

            if player_hit is not None and (
                building_t is None or player_t <= building_t
            ):
                _, hit_index, center = player_hit
                self.banana_active = False
                self.players[self.current_player].state = "idle"
                self.players[hit_index].state = "sad"
                explode_in_city(
                    self.city,
                    (int(center.x), int(self.players[hit_index].pos.y)),
                    scene_time=self.scene_time,
                    strong=True,
                )
                self.shot_path.append(center.copy())
                animation_action = await self.animate_explosion(
                    center.x,
                    center.y,
                    strong=True,
                )
                if animation_action:
                    return animation_action
                return f"hit_p{hit_index}"

            if building_hit is not None:
                impact, _ = building_hit
                self.banana_active = False
                self.players[self.current_player].state = "idle"
                explode_in_city(
                    self.city,
                    (int(impact.x), int(impact.y)),
                    scene_time=self.scene_time,
                )
                self.shot_path.append(Vector2(impact))
                target = self.other_player
                if self._shot_min_distances[target] < 78:
                    self._set_reaction(target, "scared", 2.0)
                else:
                    self._set_reaction(target, "laugh", 2.0)
                animation_action = await self.animate_explosion(
                    impact.x,
                    impact.y,
                )
                if animation_action:
                    return animation_action
                return "block"

            if out_of_bounds(self.banana_pos):
                self.banana_active = False
                self.players[self.current_player].state = "idle"
                target = self.other_player
                if self._shot_min_distances[target] < 78:
                    self._set_reaction(target, "scared", 2.0)
                else:
                    self._set_reaction(target, "laugh", 2.0)
                return "miss"

            self.sun_expression = (
                "surprised"
                if self.banana_pos.distance_to(Vector2(self.sun_rect.center)) < 72
                else "happy"
            )
        return None

    async def celebrate_point(self, winner):
        self.sound.play("score")
        elapsed = 0.0
        while elapsed < 0.75:
            for event in pygame.event.get():
                action = self._handle_common_event(event)
                if action in ("quit", "menu"):
                    return action
            dt = min(0.05, self.clock.tick(FPS) / 1000.0)
            elapsed += dt
            self.scene_time += dt
            frame = int(elapsed * 9)
            self.players[winner].state = (
                "leftup" if frame % 2 == 0 else "rightup"
            )
            self.draw_scene()
            self.blit_scaled()
            pygame.display.flip()
            await asyncio.sleep(0)
        self.players[winner].state = "idle"
        return None

    def _draw_victory_button(self, rect, label, selected=False):
        color = (255, 191, 61) if selected else (31, 35, 70)
        border = (255, 224, 153) if selected else (105, 112, 164)
        pygame.draw.rect(self.vsurf, color, rect, border_radius=7)
        pygame.draw.rect(self.vsurf, border, rect, 2, border_radius=7)
        text_color = (19, 22, 47) if selected else (247, 240, 222)
        text = self.font.render(label, True, text_color)
        self.vsurf.blit(text, text.get_rect(center=rect.center))

    async def show_victory(self, winner):
        self.sound.play("victory")
        selected = 0
        content_x = max(0, (VIRTUAL_W - 640) // 2)
        rematch = pygame.Rect(160 + content_x, 252, 145, 44)
        menu = pygame.Rect(335 + content_x, 252, 145, 44)
        elapsed = 0.0
        confetti = [
            (
                self.rng.randrange(VIRTUAL_W),
                self.rng.randrange(VIRTUAL_H),
                self.rng.choice(
                    (
                        (255, 191, 61),
                        (120, 220, 255),
                        (255, 99, 146),
                        (238, 235, 215),
                    )
                ),
                self.rng.randrange(18, 42),
            )
            for _ in range(46)
        ]

        while True:
            for event in pygame.event.get():
                action = self._handle_common_event(event)
                if action == "quit":
                    return "quit"
                if action == "menu":
                    return "menu"
                if event.type == pygame.KEYDOWN:
                    if event.key in (
                        pygame.K_LEFT,
                        pygame.K_RIGHT,
                        pygame.K_TAB,
                    ):
                        selected = 1 - selected
                        self.sound.play("click")
                    elif event.key in (
                        pygame.K_RETURN,
                        pygame.K_KP_ENTER,
                        pygame.K_SPACE,
                    ):
                        self.sound.play("click")
                        return "rematch" if selected == 0 else "menu"
                elif event.type == pygame.MOUSEMOTION:
                    pos = self.screen_to_virtual(event.pos)
                    if pos is not None:
                        if rematch.collidepoint(pos):
                            selected = 0
                        elif menu.collidepoint(pos):
                            selected = 1
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = self.screen_to_virtual(event.pos)
                    if pos is not None and rematch.collidepoint(pos):
                        self.sound.play("click")
                        return "rematch"
                    if pos is not None and menu.collidepoint(pos):
                        self.sound.play("click")
                        return "menu"

            dt = min(0.05, self.clock.tick(FPS) / 1000.0)
            elapsed += dt
            self.scene_time += dt
            self.draw_scene()
            veil = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
            veil.fill((5, 8, 28, 205))
            self.vsurf.blit(veil, (0, 0))

            for x, y, color, speed in confetti:
                cy = int((y + elapsed * speed) % VIRTUAL_H)
                pygame.draw.rect(self.vsurf, color, (x, cy, 3, 5))

            title = (
                f"{self.players[winner].name} gagne !"
                if not self.is_solo_target_mode()
                else f"{self.win_score} cibles touchées !"
            )
            title_image = self.font_big.render(title, True, (255, 210, 83))
            self.vsurf.blit(
                title_image,
                title_image.get_rect(center=(VIRTUAL_W // 2, 150)),
            )
            subtitle = self.font.render(
                f"Score final : {self.players[0].score} - {self.players[1].score}",
                True,
                (239, 238, 225),
            )
            self.vsurf.blit(
                subtitle,
                subtitle.get_rect(center=(VIRTUAL_W // 2, 197)),
            )
            self._draw_victory_button(
                rematch,
                "REVANCHE",
                selected == 0,
            )
            self._draw_victory_button(
                menu,
                "MENU",
                selected == 1,
            )
            self.blit_scaled()
            pygame.display.flip()
            await asyncio.sleep(0)

    def _switch_turn(self):
        if self.is_solo_target_mode():
            self.current_player = 0
            self.other_player = 1
        else:
            self.current_player, self.other_player = (
                self.other_player,
                self.current_player,
            )

    async def run_match(self):
        self.reset_match()
        while not self.quit_requested:
            for event in pygame.event.get():
                action = self._handle_common_event(event)
                if action == "quit":
                    return "quit"
                if action == "menu":
                    return "menu"
                if (
                    event.type == pygame.KEYDOWN
                    and event.key == pygame.K_r
                    and not self.banana_active
                ):
                    self.new_city()

            if self.city_intro_pending:
                intro_action = await self.show_city_intro()
                if intro_action in ("quit", "menu"):
                    return intro_action

            if not self.banana_active:
                if self.is_ai_turn():
                    move_target = choose_ai_relocation(
                        self,
                        self.current_player,
                        self.other_player,
                    )
                    if move_target is not None:
                        move_action = await animate_relocation(
                            self,
                            self.current_player,
                            move_target,
                        )
                        if move_action in ("quit", "menu"):
                            return move_action
                    angle_power = await self.wait_for_ai_shot()
                else:
                    angle_power = await ask_angle_power(
                        self,
                        self.players[self.current_player],
                    )
                if angle_power is None:
                    return "quit" if self.quit_requested else "menu"
                if angle_power == "move":
                    move_target = await select_relocation_target(
                        self,
                        self.current_player,
                    )
                    if move_target in ("quit", "menu"):
                        return move_target
                    if move_target is not None:
                        move_action = await animate_relocation(
                            self,
                            self.current_player,
                            move_target,
                        )
                        if move_action in ("quit", "menu"):
                            return move_action
                    continue
                angle, power = angle_power
                self.fire_banana(
                    self.players[self.current_player],
                    angle,
                    power,
                )

            dt = min(0.05, self.clock.tick(FPS) / 1000.0)
            self.scene_time += dt
            result = await self.update_banana(dt)

            if result in ("quit", "menu"):
                return result

            shot_resolved = result in ("miss", "block")
            if result == "miss":
                self.status_message = "La banane disparaît dans la nuit..."
            elif result == "block":
                self.status_message = "L'immeuble a pris cher !"
            elif result in ("hit_p0", "hit_p1"):
                hit_index = 0 if result == "hit_p0" else 1
                if self.is_solo_target_mode():
                    if hit_index == 1:
                        winner = 0
                        self.players[winner].score += 1
                        self.status_message = "Cible touchée !"
                    else:
                        winner = 1
                        self.status_message = "Oups, retour à l'envoyeur !"
                else:
                    winner = 1 - hit_index
                    self.players[winner].score += 1
                    self.status_message = (
                        f"Point pour {self.players[winner].name} !"
                    )

                has_won = self.players[winner].score >= self.win_score and (
                    not self.is_solo_target_mode() or winner == 0
                )
                if has_won:
                    replay_action = await self.play_winning_replay()
                    if replay_action:
                        return replay_action

                celebration_action = await self.celebrate_point(winner)
                if celebration_action:
                    return celebration_action

                if has_won:
                    victory_action = await self.show_victory(winner)
                    if victory_action != "rematch":
                        return victory_action
                    self.reset_match()
                    continue

                shot_resolved = True

            if shot_resolved:
                if result in ("miss", "block"):
                    reaction_action = await self.show_reaction_pause(1.35)
                    if reaction_action:
                        return reaction_action
                self._switch_turn()
                if result in ("hit_p0", "hit_p1"):
                    self.new_city()

            self.draw_scene()
            self.blit_scaled()
            pygame.display.flip()
            await asyncio.sleep(0)
        return "quit"

    async def run(self):
        if not await show_intro(self):
            pygame.quit()
            return

        while not self.quit_requested:
            menu_action = await run_menu(self)
            if menu_action != "start":
                break
            match_action = await self.run_match()
            if match_action == "quit":
                break

        pygame.quit()


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
