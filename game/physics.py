"""Physique du projectile et collisions continues.

Les fonctions restent independantes de Pygame pour etre testables facilement.
Elles acceptent les ``Vector2`` de Pygame, ou tout objet equivalent avec
``x``, ``y`` et ``copy()``.
"""

import math

from config import VIRTUAL_H, VIRTUAL_W


FIXED_TIMESTEP = 1.0 / 120.0
MAX_SIMULATION_TIME = 7.0


def _copy_vector(value):
    copier = getattr(value, "copy", None)
    if copier is not None:
        return copier()
    return type(value)(value)


def _point_like(reference, x, y):
    point = _copy_vector(reference)
    point.x = x
    point.y = y
    return point


def step_ballistic(pos, vel, gravity, wind, wind_accel_per_unit, dt):
    """Avance un projectile avec une acceleration constante.

    L'integration analytique evite que la trajectoire change selon le nombre
    d'images par seconde.
    """

    if dt < 0:
        raise ValueError("dt must be positive")

    pos = _copy_vector(pos)
    vel = _copy_vector(vel)
    ax = float(wind) * float(wind_accel_per_unit)
    ay = float(gravity)

    pos.x += vel.x * dt + 0.5 * ax * dt * dt
    pos.y += vel.y * dt + 0.5 * ay * dt * dt
    vel.x += ax * dt
    vel.y += ay * dt
    return pos, vel


def ballistic_segments(
    pos,
    vel,
    gravity,
    wind,
    wind_accel_per_unit,
    duration=MAX_SIMULATION_TIME,
    fixed_dt=FIXED_TIMESTEP,
):
    """Produit des segments de trajectoire avec un pas fixe."""

    if duration < 0:
        raise ValueError("duration must be positive")
    if fixed_dt <= 0:
        raise ValueError("fixed_dt must be greater than zero")

    current_pos = _copy_vector(pos)
    current_vel = _copy_vector(vel)
    elapsed = 0.0

    while elapsed < duration:
        dt = min(fixed_dt, duration - elapsed)
        next_pos, next_vel = step_ballistic(
            current_pos,
            current_vel,
            gravity,
            wind,
            wind_accel_per_unit,
            dt,
        )
        elapsed += dt
        yield current_pos, next_pos, next_vel, elapsed
        current_pos = next_pos
        current_vel = next_vel


def segment_circle_intersection(start, end, center, radius):
    """Retourne le premier temps d'impact [0..1], sinon ``None``."""

    if radius < 0:
        raise ValueError("radius must be positive")

    dx = end.x - start.x
    dy = end.y - start.y
    fx = start.x - center.x
    fy = start.y - center.y
    a = dx * dx + dy * dy

    if a == 0:
        return 0.0 if fx * fx + fy * fy <= radius * radius else None

    b = 2.0 * (fx * dx + fy * dy)
    c = fx * fx + fy * fy - radius * radius
    discriminant = b * b - 4.0 * a * c
    if discriminant < 0:
        return None

    root = math.sqrt(discriminant)
    for value in ((-b - root) / (2.0 * a), (-b + root) / (2.0 * a)):
        if 0.0 <= value <= 1.0:
            return value
    return None


def first_segment_collision(start, end, is_solid, max_spacing=1.0):
    """Echantillonne tout un segment et retourne ``(point, t)`` au premier mur."""

    if max_spacing <= 0:
        raise ValueError("max_spacing must be greater than zero")

    dx = end.x - start.x
    dy = end.y - start.y
    length = math.hypot(dx, dy)
    samples = max(1, int(math.ceil(length / max_spacing)))

    for index in range(1, samples + 1):
        t = index / samples
        point = _point_like(start, start.x + dx * t, start.y + dy * t)
        if is_solid(point):
            return point, t
    return None


def out_of_bounds(pos):
    return pos.x < -80 or pos.x > VIRTUAL_W + 80 or pos.y > VIRTUAL_H + 80 or pos.y < -300
