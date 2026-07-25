import math
from pathlib import Path
import random
import sys
import types
import unittest


try:
    import pygame
    from pygame.math import Vector2
except ImportError:
    class Vector2:
        def __init__(self, x=0, y=0):
            if hasattr(x, "x"):
                self.x = float(x.x)
                self.y = float(x.y)
            else:
                self.x = float(x)
                self.y = float(y)

        def copy(self):
            return Vector2(self.x, self.y)

        def distance_to(self, other):
            return math.hypot(self.x - other.x, self.y - other.y)

    pygame = types.ModuleType("pygame")
    pygame_math = types.ModuleType("pygame.math")
    pygame_math.Vector2 = Vector2
    pygame.math = pygame_math
    sys.modules["pygame"] = pygame
    sys.modules["pygame.math"] = pygame_math

GAME_DIR = Path(__file__).resolve().parents[1] / "game"
sys.path.insert(0, str(GAME_DIR))

from ai import AI_PROFILES, _difficulty_profile, choose_ai_shot  # noqa: E402


class Image:
    def get_height(self):
        return 56


class Pixel:
    a = 0


class Mask:
    def get_at(self, _position):
        return Pixel()


class Player:
    def __init__(self, x):
        self.pos = Vector2(x, 300)


class FakeGame:
    def __init__(self, difficulty="normal"):
        self.players = [Player(100), Player(540)]
        self.spr = types.SimpleNamespace(gorilla_idle=Image())
        self.city = types.SimpleNamespace(mask=Mask())
        self.gravity = 220
        self.wind = 0
        self.rng = random.Random(7)
        self.ai_difficulty = difficulty
        self.ai_shots_taken = 0


class AiTests(unittest.TestCase):
    def test_profiles_and_fallback(self):
        self.assertEqual({"easy", "normal", "hard"}, set(AI_PROFILES))
        game = FakeGame("inconnu")
        self.assertIs(AI_PROFILES["normal"], _difficulty_profile(game))

    def test_choose_ai_shot_is_sync_and_bounded(self):
        game = FakeGame("normal")
        angle, power = choose_ai_shot(game)
        self.assertGreaterEqual(angle, 12)
        self.assertLessEqual(angle, 84)
        self.assertGreaterEqual(power, 55)
        self.assertLessEqual(power, 390)
        self.assertEqual(1, game.ai_shots_taken)


if __name__ == "__main__":
    unittest.main()
