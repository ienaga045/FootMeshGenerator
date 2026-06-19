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

    toes = []
    toe_lengths = _toe_lengths(params)
    toe_box = None
    if params.foot_mode == "shoe":
        toe_box = _calculate_toe_box(params, ball_y, toe_base_y)
    else:
        base_xs = np.array([-0.37, -0.18, 0.0, 0.18, 0.36]) * width
        base_zs = np.array([0.31, 0.28, 0.26, 0.24, 0.22]) * params.instep_height
        fan_offsets = np.array([-1.0, -0.4, 0.05, 0.45, 0.95]) * params.toe_spread

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

    outline = _calculate_shoe_outline(params, heel_y, toe_box) if toe_box else _calculate_outline(params, toe_base_y, heel_y)
    outline = [_pitch_for_tiptoe(point, pivot, params.ankle_pivot_angle) if point[1] < ball_y else point for point in outline]
    side_sole = _calculate_side_sole(params, heel_y, ball_y, toe_box)
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
        "toe_box": toe_box,
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


def _calculate_toe_box(params: FootParams, ball_y: float, toe_base_y: float) -> dict:
    """Calculate a unified toe-box block for shoe/boot base meshes."""

    length = params.foot_length
    roundness = min(1.0, max(0.0, params.toe_box_roundness / 100.0))
    sole = max(0.0, params.sole_thickness)
    vamp_scale = max(0.55, params.vamp_volume / 100.0)
    width = max(params.toe_box_width, params.foot_width * 0.58)
    height = max(8.0, params.toe_box_height)

    back_y = ball_y + length * 0.025
    shoulder_y = toe_base_y + length * 0.025
    front_y = length * (0.715 + 0.018 * roundness)
    nose_y = length * (0.735 + 0.040 * roundness)

    back_half = max(params.foot_width * 0.50, width * 0.50)
    shoulder_half = width * 0.52
    front_half = width * (0.42 - 0.08 * roundness)
    nose_half = width * (0.16 + 0.16 * (1.0 - roundness))

    base_z = max(0.0, sole * 0.20)
    lift = params.toe_box_lift
    stations = [
        {
            "y": back_y,
            "half_width": back_half,
            "bottom_z": base_z,
            "top_z": base_z + max(height * 1.06, params.instep_height * 0.42 * vamp_scale),
        },
        {
            "y": shoulder_y,
            "half_width": shoulder_half,
            "bottom_z": base_z + max(0.0, lift) * 0.10,
            "top_z": base_z + height * 1.08 + max(0.0, lift) * 0.18,
        },
        {
            "y": front_y,
            "half_width": front_half,
            "bottom_z": base_z + lift * 0.35,
            "top_z": base_z + height * 0.86 + lift * 0.52,
        },
        {
            "y": nose_y,
            "half_width": nose_half,
            "bottom_z": base_z + lift * 0.70,
            "top_z": base_z + height * 0.58 + lift,
        },
    ]

    for station in stations:
        station["bottom_z"] = max(-sole * 0.35, float(station["bottom_z"]))
        station["top_z"] = max(float(station["bottom_z"]) + height * 0.42, float(station["top_z"]))

    top_outline_specs = [
        (-back_half, back_y),
        (-shoulder_half, shoulder_y),
        (-front_half, front_y),
        (-nose_half, nose_y),
        (0.0, nose_y + length * 0.012 * roundness),
        (nose_half, nose_y),
        (front_half, front_y),
        (shoulder_half, shoulder_y),
        (back_half, back_y),
    ]
    top_outline = [np.array([_mirror_x(x, params), y, 0.0]) for x, y in top_outline_specs]

    side_profile = [
        np.array([0.0, stations[0]["y"], stations[0]["bottom_z"]]),
        np.array([0.0, stations[1]["y"], stations[1]["bottom_z"]]),
        np.array([0.0, stations[2]["y"], stations[2]["bottom_z"]]),
        np.array([0.0, stations[3]["y"], stations[3]["bottom_z"]]),
        np.array([0.0, stations[3]["y"], stations[3]["top_z"]]),
        np.array([0.0, stations[2]["y"], stations[2]["top_z"]]),
        np.array([0.0, stations[1]["y"], stations[1]["top_z"]]),
        np.array([0.0, stations[0]["y"], stations[0]["top_z"]]),
    ]

    return {
        "back_center": np.array([0.0, back_y, stations[0]["top_z"] * 0.45]),
        "front_center": np.array([0.0, front_y, stations[2]["top_z"] * 0.48]),
        "nose": np.array([0.0, nose_y, stations[3]["top_z"] * 0.45]),
        "top_outline": top_outline,
        "side_profile": side_profile,
        "stations": stations,
        "roundness": roundness,
        "width": width,
        "height": height,
        "sole_thickness": sole,
    }


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


def _calculate_shoe_outline(params: FootParams, heel_y: float, toe_box: dict) -> list[np.ndarray]:
    """Return a simplified outer foot outline with a continuous shoe toe box."""

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

    stations = toe_box["stations"]
    pts = [
        (-half * 0.62 * (0.95 + heel_scale * 0.05), -length * 0.25),
        (-half * 0.82, length * 0.08),
        (-half * 0.72, length * 0.34),
        (-stations[0]["half_width"], stations[0]["y"]),
        (-stations[1]["half_width"], stations[1]["y"]),
        (-stations[2]["half_width"], stations[2]["y"]),
        (-stations[3]["half_width"], stations[3]["y"]),
        (0.0, stations[3]["y"] + length * 0.012 * toe_box["roundness"]),
        (stations[3]["half_width"], stations[3]["y"]),
        (stations[2]["half_width"], stations[2]["y"]),
        (stations[1]["half_width"], stations[1]["y"]),
        (stations[0]["half_width"], stations[0]["y"]),
        (half * 0.78, length * 0.34),
        (half * 0.72, length * 0.04),
        (half * 0.56 * (0.95 + heel_scale * 0.05), -length * 0.25),
        *reversed(heel_arc),
    ]
    return [np.array([_mirror_x(float(x), params), float(y), 0.0]) for x, y in pts]


def _calculate_side_sole(params: FootParams, heel_y: float, ball_y: float, toe_box: dict | None = None) -> list[np.ndarray]:
    """Return a side-view sole guide that follows the shared tiptoe pivot."""

    length = params.foot_length
    heel_scale = max(0.35, params.heel_size / 100.0)
    heel_back_y = heel_y - params.heel_width * 0.24 * heel_scale
    if toe_box:
        toe_front_y = toe_box["stations"][-1]["y"]
        sole = max(0.0, params.sole_thickness)
        return [
            np.array([0.0, heel_back_y, -sole - params.heel_height]),
            np.array([0.0, heel_y + length * 0.06, -sole * 0.70 - params.heel_height * 0.65]),
            np.array([0.0, -length * 0.08, params.arch_height * 0.14 - sole * 0.42]),
            np.array([0.0, ball_y, 0.0]),
            np.array([0.0, toe_front_y, toe_box["stations"][-1]["bottom_z"]]),
        ]
    toe_front_y = length * 0.70
    return [
        np.array([0.0, heel_back_y, 0.0]),
        np.array([0.0, heel_y + length * 0.06, params.arch_height * 0.08]),
        np.array([0.0, -length * 0.08, params.arch_height * 0.30]),
        np.array([0.0, ball_y, 0.0]),
        np.array([0.0, toe_front_y, 0.0]),
    ]
