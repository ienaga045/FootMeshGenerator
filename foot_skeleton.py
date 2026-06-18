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
    heel_scale = max(0.35, params.heel_size / 100.0)
    toe_base_y = length * 0.62
    ball_y = length * 0.50
    heel_y = -length * 0.42
    ankle_y = -length * 0.52

    ankle_angle = math.radians(params.ankle_angle)
    ankle = np.array([0.0, ankle_y, params.instep_height + 18.0 + math.sin(ankle_angle) * 18.0])
    heel = np.array([0.0, heel_y, params.heel_width * 0.08 * heel_scale])
    instep = np.array([0.0, length * 0.05, params.instep_height])
    arch = np.array([_mirror_x(-width * 0.18, params), -length * 0.05, params.arch_height])
    big_ball = np.array([_mirror_x(-width * 0.36, params), ball_y, params.instep_height * 0.35])
    small_ball = np.array([_mirror_x(width * 0.40, params), ball_y * 0.98, params.instep_height * 0.28])
    pivot = np.array([0.0, ball_y, params.instep_height * 0.20])

    ankle = _pitch_for_tiptoe(ankle, pivot, params.ankle_pivot_angle)
    heel = _pitch_for_tiptoe(heel, pivot, params.ankle_pivot_angle)
    instep = _pitch_for_tiptoe(instep, pivot, params.ankle_pivot_angle)
    arch = _pitch_for_tiptoe(arch, pivot, params.ankle_pivot_angle)

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

        seg1_len = total_len * 0.44
        seg2_len = total_len * 0.34
        seg3_len = total_len * 0.22

        curl_steps = [0.0, -curl * 0.78, -curl * 1.55]
        lift_steps = [lift, lift + curl_steps[1], lift + curl_steps[2]]

        dir1 = _toe_direction(lateral, lift_steps[0]) * seg1_len
        dir2 = _toe_direction(lateral, lift_steps[1]) * seg2_len
        dir3 = _toe_direction(lateral, lift_steps[2]) * seg3_len

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
                "radius": max(6.0, width * (0.085 if i == 0 else 0.065 - i * 0.004)) * (params.toe_thickness / 100.0),
            }
        )

    outline = _calculate_outline(params, toe_base_y, heel_y)
    outline = [_pitch_for_tiptoe(point, pivot, params.ankle_pivot_angle) if point[1] < ball_y else point for point in outline]
    side_sole = _calculate_side_sole(params, heel_y, ball_y)
    side_sole = [_pitch_for_tiptoe(point, pivot, params.ankle_pivot_angle) if point[1] < ball_y else point for point in side_sole]
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
        "side_sole": side_sole,
        "toe_lengths": toe_lengths,
    }


def _toe_direction(lateral_angle: float, pitch_angle: float) -> np.ndarray:
    """Return a toe segment direction from top-view spread and side-view pitch."""

    forward = math.cos(pitch_angle)
    return np.array(
        [
            math.sin(lateral_angle) * forward,
            math.cos(lateral_angle) * forward,
            math.sin(pitch_angle),
        ]
    )


def _pitch_for_tiptoe(point: np.ndarray, pivot: np.ndarray, angle_degrees: float) -> np.ndarray:
    """Rotate rear-foot points around the ball area for tiptoe-like poses."""

    if abs(angle_degrees) < 0.001:
        return point
    angle = math.radians(angle_degrees)
    dy = point[1] - pivot[1]
    dz = point[2] - pivot[2]
    y = pivot[1] + dy * math.cos(angle) + dz * math.sin(angle)
    z = pivot[2] - dy * math.sin(angle) + dz * math.cos(angle)
    return np.array([point[0], y, z])


def _calculate_outline(params: FootParams, toe_base_y: float, heel_y: float) -> list[np.ndarray]:
    width = params.foot_width
    length = params.foot_length
    heel_scale = max(0.35, params.heel_size / 100.0)
    half = width * 0.5
    heel_half = params.heel_width * 0.46 * heel_scale
    heel_back_y = heel_y - params.heel_width * 0.22 * heel_scale
    heel_arc = []
    for i in range(7):
        theta = math.pi - math.pi * i / 6.0
        x = math.cos(theta) * heel_half
        y = heel_y - math.sin(theta) * (heel_y - heel_back_y)
        heel_arc.append((x, y))

    pts = [
        (-half * 0.62 * (0.95 + heel_scale * 0.05), -length * 0.25),
        (-half * 0.82, length * 0.08),
        (-half * 0.70, length * 0.36),
        (-half * 0.48, toe_base_y),
        (-half * 0.12, length * 0.72),
        (half * 0.20, length * 0.72),
        (half * 0.52, toe_base_y),
        (half * 0.76, length * 0.34),
        (half * 0.72, length * 0.04),
        (half * 0.56 * (0.95 + heel_scale * 0.05), -length * 0.25),
        *reversed(heel_arc),
    ]
    return [np.array([_mirror_x(x, params), y, 0.0]) for x, y in pts]


def _calculate_side_sole(params: FootParams, heel_y: float, ball_y: float) -> list[np.ndarray]:
    """Return a side-view sole guide that follows the shared tiptoe pivot."""

    length = params.foot_length
    heel_scale = max(0.35, params.heel_size / 100.0)
    heel_back_y = heel_y - params.heel_width * 0.24 * heel_scale
    toe_front_y = length * 0.70
    return [
        np.array([0.0, heel_back_y, 0.0]),
        np.array([0.0, heel_y + length * 0.06, params.arch_height * 0.08]),
        np.array([0.0, -length * 0.08, params.arch_height * 0.30]),
        np.array([0.0, ball_y, 0.0]),
        np.array([0.0, toe_front_y, 0.0]),
    ]
