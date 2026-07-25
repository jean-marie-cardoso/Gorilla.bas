"""Adversaire autonome avec trois niveaux de difficulte."""

import math

from pygame.math import Vector2

from config import VIRTUAL_H, VIRTUAL_W, WIND_ACCEL_PER_UNIT
from physics import (
    FIXED_TIMESTEP,
    MAX_SIMULATION_TIME,
    ballistic_segments,
    first_segment_collision,
    out_of_bounds,
    segment_circle_intersection,
)


AI_PROFILES = {
    "easy": {
        "rank": (24, 72),
        "angle_spread": 15.0,
        "power_spread": 0.24,
        "mistake_chance": 0.55,
    },
    "normal": {
        "rank": (6, 34),
        "angle_spread": 9.0,
        "power_spread": 0.15,
        "mistake_chance": 0.28,
    },
    "hard": {
        "rank": (0, 8),
        "angle_spread": 3.0,
        "power_spread": 0.05,
        "mistake_chance": 0.08,
    },
}


def _shot_start(game, shooter):
    img_h = game.spr.gorilla_idle.get_height()
    return Vector2(shooter.pos.x, shooter.pos.y - img_h - 10)


def _shot_velocity(shooter, right_player, angle_deg, power):
    ang = math.radians(angle_deg)
    vx = math.cos(ang) * power
    vy = math.sin(ang) * power
    if shooter is right_player:
        vx = -vx
    return Vector2(vx, -vy)


def _solid_city_point(game, point):
    x, y = int(point.x), int(point.y)
    if not (0 <= x < VIRTUAL_W and 0 <= y < VIRTUAL_H):
        return False
    try:
        return game.city.mask.get_at((x, y)).a > 0
    except IndexError:
        return False


def _distance_to_segment(point, start, end):
    dx = end.x - start.x
    dy = end.y - start.y
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return point.distance_to(start)
    t = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared
    t = max(0.0, min(1.0, t))
    nearest = Vector2(start.x + dx * t, start.y + dy * t)
    return point.distance_to(nearest)


def _simulate_shot(game, shooter_idx, target_idx, angle_deg, power):
    """Note un tir avec les memes equations que le jeu.

    La collision porte sur tout le segment. Une banane rapide ne traverse donc
    ni un immeuble fin, ni le gorille entre deux images.
    """

    shooter = game.players[shooter_idx]
    target = game.players[target_idx]
    target_center = Vector2(
        target.pos.x,
        target.pos.y - game.spr.gorilla_idle.get_height() // 2,
    )
    pos = _shot_start(game, shooter)
    vel = _shot_velocity(shooter, game.players[1], angle_deg, power)
    best_distance = float("inf")

    for previous, current, _velocity, _elapsed in ballistic_segments(
        pos,
        vel,
        game.gravity,
        game.wind,
        WIND_ACCEL_PER_UNIT,
        duration=MAX_SIMULATION_TIME,
        fixed_dt=FIXED_TIMESTEP,
    ):
        best_distance = min(best_distance, _distance_to_segment(target_center, previous, current))

        target_hit = segment_circle_intersection(previous, current, target_center, 30.0)
        building_hit = first_segment_collision(
            previous,
            current,
            lambda point: _solid_city_point(game, point),
        )

        if target_hit is not None and (
            building_hit is None or target_hit <= building_hit[1]
        ):
            return 0.0

        if building_hit is not None:
            return best_distance + 35.0

        if out_of_bounds(current):
            break

    return best_distance


def _difficulty_profile(game):
    difficulty = str(getattr(game, "ai_difficulty", "normal")).strip().lower()
    return AI_PROFILES.get(difficulty, AI_PROFILES["normal"])


def choose_ai_shot(game, shooter_idx=1, target_idx=0):
    shots_taken = getattr(game, "ai_shots_taken", 0)
    game.ai_shots_taken = shots_taken + 1

    candidates = []
    for angle in range(24, 79, 4):
        for power in range(90, 361, 12):
            score = _simulate_shot(game, shooter_idx, target_idx, angle, power)
            candidates.append((score, angle, power))

    if not candidates:
        return 45.0, 180.0

    candidates.sort(key=lambda item: item[0])
    profile = _difficulty_profile(game)
    min_rank, max_rank = profile["rank"]

    # L'IA apprend legerement pendant la partie, sans devenir parfaite.
    experience = min(shots_taken, 4)
    min_rank = max(0, min_rank - experience * 2)
    max_rank = max(min_rank + 1, max_rank - experience * 3)
    min_rank = min(min_rank, len(candidates) - 1)
    max_rank = min(max_rank, len(candidates))
    _, angle, power = game.rng.choice(candidates[min_rank:max_rank])

    learning = 1.0 - experience * 0.08
    angle_spread = profile["angle_spread"] * learning
    power_spread = profile["power_spread"] * learning
    angle_error = game.rng.uniform(-angle_spread, angle_spread)
    power_error = game.rng.uniform(-power_spread, power_spread)

    if game.rng.random() < profile["mistake_chance"]:
        angle_error += game.rng.choice((-1, 1)) * game.rng.uniform(3.0, max(3.0, angle_spread))
        power_error += game.rng.choice((-1, 1)) * game.rng.uniform(0.03, max(0.03, power_spread))

    angle = max(12.0, min(84.0, angle + angle_error))
    power = max(55.0, min(390.0, power * (1.0 + power_error)))
    return angle, power
