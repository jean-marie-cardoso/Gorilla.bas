import asyncio
import os
from pathlib import Path
import sys
import unittest


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

    def test_menu_and_aim_accept_keyboard(self):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        menu_result = asyncio.run(self.run_menu(self.game))
        self.assertEqual("start", menu_result)

        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        shot = asyncio.run(self.ask_angle_power(self.game, self.game.players[0]))
        self.assertEqual((45.0, 180.0), shot)

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

    def test_menu_render_and_audio_bank(self):
        self.draw_menu(self.game, self.MODE_SOLO_AI, "hard", 9, (320, 200))
        self.assertTrue(self.game.sound.ensure_ready())
        self.assertEqual(
            {"click", "throw", "impact", "explosion", "score", "victory"},
            set(self.game.sound.sounds),
        )


if __name__ == "__main__":
    unittest.main()
