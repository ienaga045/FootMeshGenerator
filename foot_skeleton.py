from __future__ import annotations

import math

import numpy as np

from foot_params import FootParams


TOE_NAMES = ["toe_1_big", "toe_2", "toe_3", "toe_4", "toe_5"]


def _mirror_x(x: float, params: FootParams) -> float:
    return -x if params.side == "left" else x


def _toe_lengths(params: FootParams) -> list[float]:
    base = params.toe_length
    if params.toe_profile == "egyptian":
        return [params.big_toe_length, base * 0.92, base * 0.82, base * 0.72, base * 0.62]
    if params.toe_profile == "greek":
        return [params.big_toe_length * 0.95, base * 1.12, base, base * 0.86, base * 0.70]
    if params.toe_profile == "square":
        return [params.big_toe_length, base * 1.00, base * 0.98, base * 0.86, base * 0.72]
    return [params.big_toe_length, base * 1.03, base, base * 0.86, base * 0.68]


def calculate_foot_skeleton(params: FootParams) -> dict:
    """Calculate one shared 3D skeleton used by preview and mesh generation.

    Coordinate system: X is foot width, Y is heel-to-toe length, Z is height.
    The ankle is near negative Y, toe tips are positive Y.
    """

    length = params.foot_length
    width = params.foot_width
    toe_base_y = length * 0.62
    ball_y = length * 0.50
    heel_y = -length * 0.42
    ankle_y = -length * 0.52

    ankle_angle = math.radians(params.ankle_angle)
    ankle = np.array([0.0, ankle_y, params.instep_height + 18.0 + math.sin(ankle_angle) * 18.0])
    heel = np.array([0.0, heel_y, params.heel_width * 0.08])
    instep = np.array([0.0, length * 0.05, params.instep_height])
    arch = np.array([_mirror_x(-width * 0.18, params), -length * 0.05, params.arch_height])
    big_ball = np.array([_mirror_x(-width * 0.36, params), ball_y, params.instep_height * 0.35])
    small_ball = np.array([_mirror_x(width * 0.40, params), ball_y * 0.98, params.instep_height * 0.28])

    base_xs = np.array([-0.37, -0.18, 0.0, 0.18, 0.36]) * width
    base_zs = np.array([0.31, 0.28, 0.26, 0.24, 0.22]) * params.instep_height
    toe_lengths = _toe_lengths(params)
    fan_offsets = np.array([-1.0, -0.4, 0.05, 0.45, 0.95]) * params.toe_spread

    toes = []
    for i, name in enumerate(TOE_NAMES):
        base = np.array([_mirror_x(float(base_xs[i]), params), toe_base_y - abs(base_xs[i]) * 0.08, float(base_zs[i])])
        lateral_angle = fan_offsets[i] + (params.big_toe_angle if i == 0 else 0.0)
        if params.side == "left":
            lateral_angle *= -1.0
        lateral = math.radians(lateral_angle)
        curl = math.radians(params.toe_curl)
        lift = math.radians(params.toe_lift)
        total_len = toe_lengths[i]

        seg1_len = total_len * 0.48
        seg2_len = total_len * 0.32
        seg3_len = total_len * 0.20

        dir1 = np.array([math.sin(lateral), math.cos(lateral), math.sin(lift)]) * seg1_len
        dir2 = np.array([math.sin(lateral), math.cos(lateral + curl * 0.25), math.sin(lift - curl * 0.30)]) * seg2_len
        dir3 = np.array([math.sin(lateral), math.cos(lateral + curl * 0.50), math.sin(lift - curl * 0.55)]) * seg3_len

        mid = base + dir1
        distal = mid + dir2
        tip = distal + dir3
        toes.append(
            {
                "name": name,
                "base": base,
                "mid": mid,
                "distal": distal,
                "tip": tip,
                "length": total_len,
                "radius": max(6.0, width * (0.085 if i == 0 else 0.065 - i * 0.004)),
            }
        )

    outline = _calculate_outline(params, toe_base_y, heel_y)
    return {
        "points": {
            "ankle": ankle,
            "heel": heel,
            "instep": instep,
            "arch": arch,
            "big_ball": big_ball,
            "small_ball": small_ball,
        },
        "toes": toes,
        "outline": outline,
        "toe_lengths": toe_lengths,
    }


def _calculate_outline(params: FootParams, toe_base_y: float, heel_y: float) -> list[np.ndarray]:
    width = params.foot_width
    length = params.foot_length
    half = width * 0.5
    pts = [
        (-params.heel_width * 0.46, heel_y),
        (-half * 0.62, -length * 0.25),
        (-half * 0.82, length * 0.08),
        (-half * 0.70, length * 0.36),
        (-half * 0.48, toe_base_y),
        (-half * 0.12, length * 0.72),
        (half * 0.20, length * 0.72),
        (half * 0.52, toe_base_y),
        (half * 0.76, length * 0.34),
        (half * 0.72, length * 0.04),
        (half * 0.56, -length * 0.25),
        (params.heel_width * 0.46, heel_y),
    ]
    return [np.array([_mirror_x(x, params), y, 0.0]) for x, y in pts]
