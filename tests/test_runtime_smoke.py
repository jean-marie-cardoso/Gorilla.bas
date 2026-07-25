import asyncio
import os
from pathlib import Path
import sys
import unittest
from unittest import mock


os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

try:
    import pygame
except ImportError:
    pygame = None

GAME_DIR = Path(__file__).resolve().parents[1] / "game"
sys.path.insert(0, str(GAME_DIR))


@unittest.skipUnless(
    pygame is not None and hasattr(pygame, "Surface"),
    "pygame is not installed",
)
class RuntimeSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from action import ask_angle_power
        from graphics import draw_explosion_frame, explode_in_city
        from main import Game
        from menu import MODE_SOLO_AI, _draw_menu, run_menu

        cls.Game = Game
        cls.MODE_SOLO_AI = MODE_SOLO_AI
        cls.ask_angle_power = staticmethod(ask_angle_power)
        cls.draw_explosion_frame = staticmethod(draw_explosion_frame)
        cls.explode_in_city = staticmethod(explode_in_city)
        cls.draw_menu = staticmethod(_draw_menu)
        cls.run_menu = staticmethod(run_menu)

    def setUp(self):
        self.game = self.Game()
        pygame.event.clear()
        self.game.sound.muted = True
        self.game.rng.seed(17)
        self.game.new_city()

    def tearDown(self):
        pygame.event.clear()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_boot_assets_city_and_render(self):
        self.game.draw_scene()
        self.game.blit_scaled()
        self.assertEqual((640, 400), self.game.vsurf.get_size())
        self.assertGreaterEqual(len(self.game.city.rects), 13)
        self.assertEqual(68, self.game.spr.gorilla_idle.get_height())
        self.assertEqual(76, self.game.spr.sun.get_width())
        blue = self.game.spr.get_gorilla(0, "idle")
        sad = self.game.spr.get_gorilla(0, "sad")
        orange = self.game.spr.get_gorilla(1, "idle")
        self.assertEqual(blue.get_size(), orange.get_size())
        self.assertEqual(blue.get_size(), sad.get_size())
        self.assertNotEqual(
            pygame.image.tobytes(blue, "RGBA"),
            pygame.image.tobytes(sad, "RGBA"),
        )
        self.assertGreater(
            self.game.spr.banana.get_width(),
            self.game.spr.banana.get_height(),
        )
        self.assertNotEqual(
            pygame.image.tobytes(blue, "RGBA"),
            pygame.image.tobytes(orange, "RGBA"),
        )

    def test_all_random_atmospheres_render_and_control_wind(self):
        import random

        from graphics import ATMOSPHERES

        seen = set()
        previous = None
        for seed, name in enumerate(ATMOSPHERES):
            self.game.city.set_atmosphere(name, random.Random(seed))
            self.game.wind = self.game.city.choose_wind(random.Random(seed + 20))
            self.game.draw_scene()
            seen.add(self.game.city.atmosphere_name)
            if name == "sunny":
                self.assertLessEqual(abs(self.game.wind), 4)
            if name == "night":
                moon_center = self.game.vsurf.get_at(self.game.sun_rect.center)[:3]
                self.assertGreater(sum(moon_center), 600)
                moon_eye = self.game.vsurf.get_at(
                    (self.game.sun_rect.centerx - 7, self.game.sun_rect.centery - 3)
                )[:3]
                self.assertLess(sum(moon_eye), 300)
            if name == "storm":
                self.assertGreaterEqual(abs(self.game.wind), 7)

        self.assertEqual(set(ATMOSPHERES), seen)

        roof = self.game.city.rects[0]
        sample = (roof.centerx, roof.top + 5)
        self.game.city.set_atmosphere("sunny", random.Random(91))
        sunny_color = self.game.city.mask.get_at(sample)[:3]
        self.game.city.set_atmosphere("storm", random.Random(92))
        storm_color = self.game.city.mask.get_at(sample)[:3]
        self.assertGreater(sum(sunny_color), sum(storm_color))

        self.game.rng.seed(42)
        for _ in range(20):
            self.game.city.generate(self.game.rng)
            self.assertNotEqual(previous, self.game.city.atmosphere_name)
            previous = self.game.city.atmosphere_name

    def test_building_lights_keep_living_while_aiming(self):
        windows = self.game.city._living_windows
        self.assertGreater(len(windows), 10)
        self.assertTrue(any(window["silhouette"] for window in windows))

        window = windows[0]
        cycle_start = (-window["phase"]) % window["period"]
        on_time = cycle_start + window["period"] * 0.10
        off_time = cycle_start + window["period"] * 0.86
        self.assertTrue(
            self.game.city._living_window_is_on(window, on_time)
        )
        self.assertFalse(
            self.game.city._living_window_is_on(window, off_time)
        )

    def test_menu_and_aim_accept_keyboard(self):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        menu_result = asyncio.run(self.run_menu(self.game))
        self.assertEqual("start", menu_result)

        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        shot = asyncio.run(self.ask_angle_power(self.game, self.game.players[0]))
        self.assertEqual((45.0, 180.0), shot)

    def test_weather_time_keeps_moving_while_player_aims(self):
        start = self.game.scene_time
        old_clock = self.game.clock
        self.game.clock = type(
            "FastClock",
            (),
            {"tick": lambda _self, _fps: 25},
        )()
        event_batches = [
            [],
            [],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
        ]
        try:
            with mock.patch("pygame.event.get", side_effect=event_batches):
                shot = asyncio.run(
                    self.ask_angle_power(self.game, self.game.players[0])
                )
        finally:
            self.game.clock = old_clock

        self.assertEqual((45.0, 180.0), shot)
        self.assertGreaterEqual(self.game.scene_time - start, 0.05)

    def test_player_can_move_once_then_gets_move_back_in_new_city(self):
        from movement import (
            animate_relocation,
            choose_ai_relocation,
            relocation_targets,
            select_relocation_target,
        )

        player = self.game.players[0]
        targets = relocation_targets(self.game, 0)
        self.assertTrue(targets)

        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b))
        self.assertEqual(
            "move",
            asyncio.run(self.ask_angle_power(self.game, player)),
        )

        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        )
        target = asyncio.run(select_relocation_target(self.game, 0))
        self.assertIn(target, targets)

        old_clock = self.game.clock
        self.game.clock = type(
            "FastClock",
            (),
            {"tick": lambda _self, _fps: 50},
        )()
        try:
            self.assertIsNone(
                asyncio.run(animate_relocation(self.game, 0, target))
            )
        finally:
            self.game.clock = old_clock

        self.assertEqual(target, player.building_index)
        self.assertFalse(player.move_available)
        self.assertEqual([], relocation_targets(self.game, 0))

        self.game.new_city()
        self.assertTrue(player.move_available)

        ai_targets = relocation_targets(self.game, 1)
        self.assertTrue(ai_targets)
        old_rng = self.game.rng
        self.game.rng = type(
            "AlwaysMove",
            (),
            {"random": lambda _self: 0.0},
        )()
        try:
            self.assertIn(
                choose_ai_relocation(self.game, 1, 0),
                ai_targets,
            )
        finally:
            self.game.rng = old_rng

    def test_one_touch_increments_score_once(self):
        from menu import _menu_rects

        x, y = _menu_rects()["score_plus"].center
        pygame.event.post(
            pygame.event.Event(
                pygame.FINGERUP,
                x=x / 640.0,
                y=y / 400.0,
                finger_id=1,
                touch_id=1,
                dx=0,
                dy=0,
                pressure=0,
            )
        )
        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                pos=(x, y),
                button=1,
                touch=True,
            )
        )
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))

        self.assertEqual("start", asyncio.run(self.run_menu(self.game)))
        self.assertEqual(4, self.game.win_score)

    def test_one_touch_toggles_sound_once(self):
        from menu import _menu_rects

        self.game.sound.muted = False
        x, y = _menu_rects()["sound"].center
        pygame.event.post(
            pygame.event.Event(
                pygame.FINGERUP,
                x=x / 640.0,
                y=y / 400.0,
                finger_id=1,
                touch_id=1,
                dx=0,
                dy=0,
                pressure=0,
            )
        )
        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONUP,
                pos=(x, y),
                button=1,
                touch=True,
            )
        )
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))

        self.assertEqual("start", asyncio.run(self.run_menu(self.game)))
        self.assertTrue(self.game.sound.muted)

    def test_touch_slider_ignores_synthetic_mouse_duplicate(self):
        from action import _aim_rects

        calls = []
        self.game.sound = type(
            "RecordedSound",
            (),
            {
                "play": lambda _self, name: calls.append(name),
                "toggle": lambda _self: None,
            },
        )()
        x, y = _aim_rects()["angle"].center
        pygame.event.post(
            pygame.event.Event(
                pygame.FINGERDOWN,
                x=x / 640.0,
                y=y / 400.0,
                finger_id=1,
                touch_id=1,
                dx=0,
                dy=0,
                pressure=0,
            )
        )
        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                pos=(x, y),
                button=1,
                touch=True,
            )
        )
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))

        shot = asyncio.run(self.ask_angle_power(self.game, self.game.players[0]))
        self.assertEqual((45.0, 180.0), shot)
        self.assertEqual(["click", "click"], calls)

    def test_victory_keeps_synthetic_touch_mouse_support(self):
        self.game.players[0].score = self.game.win_score
        pygame.event.post(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                pos=(220, 270),
                button=1,
                touch=True,
            )
        )
        self.assertEqual("rematch", asyncio.run(self.game.show_victory(0)))

    def test_rematch_winner_wears_crown(self):
        self.game.reset_match(crowned_player=1)
        self.assertFalse(self.game.players[0].crowned)
        self.assertTrue(self.game.players[1].crowned)

        self.game.draw_scene()
        crowned = pygame.image.tobytes(self.game.vsurf, "RGBA")
        self.game.players[1].crowned = False
        self.game.draw_scene()
        plain = pygame.image.tobytes(self.game.vsurf, "RGBA")
        self.assertNotEqual(crowned, plain)

        self.game.reset_match()
        self.assertFalse(any(player.crowned for player in self.game.players))

    def test_projectile_resolves_and_effects_draw_at_edges(self):
        async def no_animation(*_args, **_kwargs):
            return None

        self.game.animate_explosion = no_animation
        self.game.fire_banana(self.game.players[0], 45, 180)

        async def resolve():
            for _ in range(900):
                result = await self.game.update_banana(1.0 / 60.0)
                if result is not None:
                    return result
            return None

        result = asyncio.run(resolve())
        self.assertIn(result, {"miss", "block", "hit_p0", "hit_p1"})

        for point in ((0, 0), (639, 399), (320, 200)):
            self.explode_in_city(self.game.city, point)
            self.draw_explosion_frame(self.game.vsurf, point, 0.5)

    def test_hit_gorilla_uses_sad_sprite(self):
        async def no_animation(*_args, **_kwargs):
            return None

        self.game.animate_explosion = no_animation
        self.game.current_player = 0
        self.game.other_player = 1
        self.game.banana_active = True
        self.game.banana_pos = pygame.Vector2(200, 100)
        self.game.banana_vel = pygame.Vector2(100, 0)

        hit = (0.1, 1, pygame.Vector2(self.game.players[1].pos.x, 100))
        with (
            mock.patch("main.first_segment_collision", return_value=None),
            mock.patch.object(self.game, "_first_player_hit", return_value=hit),
        ):
            result = asyncio.run(self.game.update_banana(1.0 / 60.0))

        self.assertEqual("hit_p1", result)
        self.assertEqual("sad", self.game.players[1].state)

    def test_menu_render_and_audio_bank(self):
        self.draw_menu(self.game, self.MODE_SOLO_AI, "hard", 9, (320, 200))
        self.assertTrue(self.game.sound.ensure_ready())
        self.assertEqual(
            {"click", "throw", "impact", "explosion", "score", "victory"},
            set(self.game.sound.sounds),
        )


if __name__ == "__main__":
    unittest.main()
