import math
from pathlib import Path
import sys
import unittest


GAME_DIR = Path(__file__).resolve().parents[1] / "game"
sys.path.insert(0, str(GAME_DIR))

from physics import (  # noqa: E402
    ballistic_segments,
    first_segment_collision,
    segment_circle_intersection,
    step_ballistic,
)


class Vec:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def copy(self):
        return Vec(self.x, self.y)


class PhysicsTests(unittest.TestCase):
    def test_constant_acceleration_is_frame_rate_independent(self):
        start = Vec(10, 20)
        velocity = Vec(30, -40)
        one_step, one_velocity = step_ballistic(start, velocity, 200, 2, 10, 1.0)

        position = start
        current_velocity = velocity
        for _ in range(120):
            position, current_velocity = step_ballistic(
                position,
                current_velocity,
                200,
                2,
                10,
                1.0 / 120.0,
            )

        self.assertAlmostEqual(one_step.x, position.x, places=8)
        self.assertAlmostEqual(one_step.y, position.y, places=8)
        self.assertAlmostEqual(one_velocity.x, current_velocity.x, places=8)
        self.assertAlmostEqual(one_velocity.y, current_velocity.y, places=8)

    def test_fixed_segments_cover_full_duration(self):
        segments = list(
            ballistic_segments(Vec(0, 0), Vec(1, 0), 0, 0, 0, duration=0.1, fixed_dt=0.03)
        )
        self.assertEqual(4, len(segments))
        self.assertAlmostEqual(0.1, segments[-1][3])

    def test_segment_circle_catches_fast_projectile(self):
        hit = segment_circle_intersection(Vec(0, 0), Vec(100, 0), Vec(50, 0), 2)
        self.assertIsNotNone(hit)
        self.assertTrue(math.isclose(hit, 0.48))

    def test_first_segment_collision_catches_thin_wall(self):
        collision = first_segment_collision(
            Vec(0, 0),
            Vec(100, 0),
            lambda point: 50 <= point.x < 51,
        )
        self.assertIsNotNone(collision)
        point, fraction = collision
        self.assertEqual(50, point.x)
        self.assertEqual(0.5, fraction)


if __name__ == "__main__":
    unittest.main()
