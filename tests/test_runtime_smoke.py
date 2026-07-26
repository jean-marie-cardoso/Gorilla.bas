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

        from graphics import _wind_panel_rect

        wind_panel = _wind_panel_rect()
        self.assertGreaterEqual(wind_panel.left, 184)
        self.assertLessEqual(wind_panel.right, 640 // 2 - 53)
        self.assertLess(wind_panel.top, 47)

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

    def test_city_styles_rooftop_objects_and_smoke(self):
        import random

        from graphics import CITY_STYLES

        rng = random.Random(1234)
        seen = set()
        roofs = set()
        for _ in range(70):
            self.game.city.generate(rng)
            seen.add(self.game.city.city_style_name)
            roofs.update(style["roof"] for style in self.game.city._styles)
            heights = [rect.height for rect in self.game.city.rects]
            self.assertGreaterEqual(max(heights) - min(heights), 42)

        self.assertEqual(set(CITY_STYLES), seen)
        self.assertTrue(
            {"billboard", "mansard", "neon", "solar", "dome", "dish"}
            .issubset(roofs)
        )

        self.explode_in_city(
            self.game.city,
            (320, 260),
            scene_time=2.0,
            strong=True,
        )
        self.assertTrue(self.game.city._smoke_plumes)
        self.assertTrue(self.game.city._debris_particles)
        self.assertGreater(
            self.game.city._smoke_plumes[-1]["duration"],
            6.0,
        )
        self.game.city.draw_damage_effects(self.game.vsurf, 2.5)

    def test_parachutists_fire_and_truck_stay_bounded(self):
        city = self.game.city
        building = city.rects[len(city.rects) // 2]
        for _ in range(5):
            launched = city.launch_parachutists(
                (building.centerx, building.top + 35),
                2.0,
                direction=1,
            )
            self.assertTrue(launched)
        self.assertGreaterEqual(len(city._parachutists), 2)
        self.assertLessEqual(len(city._parachutists), 8)
        for person in city._parachutists:
            source = city.rects[person["building_index"]]
            self.assertIn(
                int(person["x"]),
                (source.left + 3, source.right - 3),
            )
            self.assertGreaterEqual(person["y"], source.top + 26)
        before = len(city._parachutists)
        self.assertFalse(
            city.launch_parachutists((-100, 20), 2.0, direction=1)
        )
        self.assertEqual(before, len(city._parachutists))

        for offset in range(10):
            city.add_damage_effect(
                (320 + offset, 260),
                scene_time=2.0,
                strong=True,
            )
            if city._fires:
                break
        self.assertTrue(city._fires)
        self.assertLessEqual(len(city._fires), 2)
        self.assertIn("truck_start", city._fires[-1])
        self.assertNotIn("plane_start", city._fires[-1])
        for scene_time in (2.1, 3.0, 4.8, 7.5):
            city.draw_emergency_effects(self.game.vsurf, scene_time)

    def test_low_building_hit_collapses_to_rubble(self):
        city = self.game.city
        index = max(
            range(len(city.rects)),
            key=lambda item: city.rects[item].height,
        )
        original = city.rects[index].copy()
        high_impact = (original.centerx, original.top + 8)
        low_impact = (original.centerx, original.centery)
        self.assertFalse(city.should_collapse_at(high_impact))
        self.assertTrue(city.should_collapse_at(low_impact))

        collapse = city.collapse_building_at(low_impact, scene_time=1.0)
        self.assertIsNotNone(collapse)
        collapsed_index, old_rect, rubble = collapse
        self.assertEqual(index, collapsed_index)
        self.assertEqual(original, old_rect)
        self.assertLess(rubble.height, original.height)
        self.assertEqual(original.bottom, rubble.bottom)
        self.assertTrue(city._collapses)
        city.draw_emergency_effects(self.game.vsurf, 1.5)

    def test_second_building_hit_forces_collapse(self):
        city = self.game.city
        index = max(
            range(len(city.rects)),
            key=lambda item: city.rects[item].height,
        )
        original = city.rects[index].copy()
        high_impact = (original.centerx, original.top + 8)

        self.assertEqual(1, city.register_building_hit(high_impact))
        self.assertFalse(city.should_collapse_at(high_impact))
        self.assertEqual(2, city.register_building_hit(high_impact))
        self.assertTrue(city.should_collapse_at(high_impact))

        collapse = city.collapse_building_at(
            high_impact,
            scene_time=1.0,
        )
        self.assertIsNotNone(collapse)
        self.assertEqual(index, collapse[0])

    def test_descending_banana_warns_parachutists(self):
        building = self.game.city.rects[len(self.game.city.rects) // 2]
        self.game.banana_active = True
        self.game.banana_pos = pygame.Vector2(
            building.centerx,
            building.top - 55,
        )
        self.game.banana_vel = pygame.Vector2(0, 75)
        self.game._preview_building_impact()
        self.assertTrue(self.game._parachute_warning_for_shot)
        self.assertTrue(self.game.city._parachutists)

    def test_players_start_on_different_roof_levels(self):
        for _ in range(20):
            self.game.new_city()
            roof_gap = abs(
                self.game.players[0].pos.y
                - self.game.players[1].pos.y
            )
            self.assertGreaterEqual(roof_gap, 36)

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

    def test_city_intro_replay_and_storm_thunder(self):
        from main import WINNING_REPLAY_DURATION

        self.assertGreaterEqual(WINNING_REPLAY_DURATION, 2.5)
        old_clock = self.game.clock
        self.game.clock = type(
            "FastClock",
            (),
            {"tick": lambda _self, _fps: 240},
        )()
        try:
            self.game.city_intro_pending = True
            self.assertIsNone(asyncio.run(self.game.show_city_intro()))
            self.assertFalse(self.game.city_intro_pending)

            self.game.shot_path = [
                pygame.Vector2(80, 140),
                pygame.Vector2(320, 90),
                pygame.Vector2(560, 210),
            ]
            self.assertIsNone(asyncio.run(self.game.play_winning_replay()))
        finally:
            self.game.clock = old_clock

        calls = []
        self.game.sound = type(
            "RecordedSound",
            (),
            {"play": lambda _self, name: calls.append(name)},
        )()
        self.game.city.set_atmosphere("storm", __import__("random").Random(55))
        self.game.scene_time = 8.15
        self.game._last_thunder_cycle = -1
        self.game.draw_scene()
        self.game.draw_scene()
        self.assertEqual(["thunder"], calls)

    def test_idle_gorillas_keep_their_feet_on_the_roof(self):
        from graphics import _gorilla_render_pose

        player = self.game.players[0]
        for scene_time in (0.0, 1.3, 3.7, 8.2):
            _, _, _, bob = _gorilla_render_pose(
                player,
                0,
                0,
                False,
                pygame.Vector2(),
                scene_time,
            )
            self.assertEqual(0, bob)
        self.assertFalse(hasattr(player, "crowned"))

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
        self.assertIn(
            result,
            {"miss", "block", "collapse", "hit_p0", "hit_p1"},
        )

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
            {"click", "throw", "impact", "explosion", "thunder", "score", "victory"},
            set(self.game.sound.sounds),
        )


if __name__ == "__main__":
    unittest.main()
