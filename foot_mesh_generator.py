from __future__ import annotations

import math

import numpy as np

from foot_params import FootParams


MATERIAL_SEPARATOR = "__mat:"
MATERIAL_JOINT_SPHERE = "joint_sphere"
MATERIAL_BONE = "bone"
MATERIAL_SOFT_TISSUE = "soft_tissue"
SDIV_BODY_WIDTH_SCALE = 1.10
SDIV_BODY_HEIGHT_SCALE = 1.14
SDIV_BODY_SOLE_SCALE = 1.24
SDIV_BONE_THICKNESS_SCALE = 1.70
SDIV_SOFT_THICKNESS_SCALE = 1.55
SDIV_SPHERE_RADIUS_SCALE = 1.22
SDIV_BOX_SIZE_SCALE = np.array([1.12, 1.12, 1.18])
BOX_SEGMENT_MAX_FACE_SPAN = 56.0


def generate_foot_mesh_from_skeleton(skeleton: dict, params: FootParams) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]], list[str]]:
    """Generate simple overlapping OBJ-ready parts from the shared skeleton."""

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    groups: list[str] = []

    _add_foot_structure_blocks(vertices, faces, groups, skeleton, params)

    if params.foot_mode == "shoe":
        _add_toe_box_mesh(vertices, faces, groups, skeleton, params)
        return vertices, faces, groups

    for toe in skeleton["toes"]:
        chain = [toe["base"], toe["mid"], toe["distal"], toe["tip"]]
        radii = [toe["radius"], toe["radius"] * 0.82, toe["radius"] * 0.64, toe["radius"] * 0.42]
        for a, b, ra, rb in zip(chain, chain[1:], radii, radii[1:]):
            _add_box_segment(vertices, faces, groups, a, b, min(ra, rb) * 2.10, toe["name"])
        for center, radius in zip(chain, radii):
            _add_uv_sphere(vertices, faces, groups, center, radius * (params.joint_sphere_scale / 100.0), max(8, int(params.mesh_resolution)), toe["name"])

    return vertices, faces, groups


def _add_foot_structure_blocks(vertices, faces, groups, skeleton: dict, params: FootParams) -> None:
    """Build the foot as separated blocky bone/tendon masses instead of one slab."""

    pts = skeleton["points"]
    heel = np.asarray(pts["heel"], dtype=float)
    ankle = np.asarray(pts["ankle"], dtype=float)
    instep = np.asarray(pts["instep"], dtype=float)
    arch = np.asarray(pts["arch"], dtype=float)
    big_ball = np.asarray(pts["big_ball"], dtype=float)
    small_ball = np.asarray(pts["small_ball"], dtype=float)
    joint_scale = params.joint_sphere_scale / 100.0
    malleolus_scale = _malleolus_scale(params)
    instep_scale = _instep_part_scale(params)
    heel_scale = _heel_scale(params)

    _add_foot_skin_shell(vertices, faces, groups, skeleton, params)
    _add_flesh_masses(vertices, faces, groups, skeleton, params)
    _add_side_volume_masses(vertices, faces, groups, skeleton, params)
    _add_midfoot_fill_masses(vertices, faces, groups, skeleton, params)
    _add_ankle_achilles_masses(vertices, faces, groups, skeleton, params)

    _add_subdivided_box(
        vertices,
        faces,
        groups,
        tuple(heel),
        (params.heel_width * 0.92 * heel_scale, params.foot_length * 0.16 * (0.85 + heel_scale * 0.15), params.heel_width * 0.24 * heel_scale),
        (2, 3, 2),
        "heel",
    )
    _add_uv_sphere(vertices, faces, groups, heel, params.heel_width * 0.24 * joint_scale * heel_scale, max(8, int(params.mesh_resolution)), "heel")

    ankle_side = params.heel_width * 0.36 * (0.92 + malleolus_scale * 0.08)
    ankle_radius = params.heel_width * 0.18 * joint_scale * malleolus_scale
    for side in (-1.0, 1.0):
        malleolus = ankle + np.array([side * ankle_side, params.foot_length * 0.03, -params.instep_height * 0.10])
        _add_uv_sphere(vertices, faces, groups, malleolus, ankle_radius, max(8, int(params.mesh_resolution)), "ankle_joint")
        _add_box_segment(vertices, faces, groups, malleolus, instep, params.heel_width * 0.14 * max(malleolus_scale, instep_scale), "instep")

    _add_box_segment(vertices, faces, groups, heel, instep, params.heel_width * 0.24 * instep_scale * max(1.0, heel_scale * 0.92), "instep")
    _add_box_segment(vertices, faces, groups, heel, arch, params.heel_width * 0.14 * heel_scale, "foot_body")
    _add_box_segment(vertices, faces, groups, arch, big_ball, params.heel_width * 0.12, "foot_body")
    _add_box_segment(vertices, faces, groups, arch, small_ball, params.heel_width * 0.12, "foot_body")
    _add_uv_sphere(vertices, faces, groups, big_ball, params.foot_width * 0.13 * joint_scale, max(8, int(params.mesh_resolution)), "foot_body")
    _add_uv_sphere(vertices, faces, groups, small_ball, params.foot_width * 0.12 * joint_scale, max(8, int(params.mesh_resolution)), "foot_body")

    for index, toe in enumerate(skeleton["toes"]):
        base = np.asarray(toe["base"], dtype=float)
        metatarsal_root = instep + (base - instep) * 0.35
        metatarsal_root[2] = max(metatarsal_root[2], params.instep_height * 0.35)
        thickness = max(8.0, toe["radius"] * (1.58 if index == 0 else 1.36)) * instep_scale
        _add_box_segment(vertices, faces, groups, metatarsal_root, base, thickness, "foot_body")
        _add_box_segment(vertices, faces, groups, instep, metatarsal_root, thickness * 0.86, "instep")
        tendon_start = instep + (base - instep) * 0.18 + np.array([0.0, 0.0, params.instep_height * 0.08])
        tendon_end = base + np.array([0.0, -params.foot_length * 0.03, params.instep_height * 0.06])
        _add_box_segment(vertices, faces, groups, tendon_start, tendon_end, max(7.5, thickness * 0.68), "instep")

    if skeleton.get("toe_box"):
        _add_shoe_forefoot_fill(vertices, faces, groups, skeleton, params)
    else:
        _add_metatarsal_web_surfaces(vertices, faces, groups, skeleton, params)


def _add_foot_skin_shell(vertices, faces, groups, skeleton: dict, params: FootParams) -> None:
    """Create a coarse quad envelope for the non-toe foot body."""

    pts = skeleton["points"]
    heel = np.asarray(pts["heel"], dtype=float)
    arch = np.asarray(pts["arch"], dtype=float)
    instep = np.asarray(pts["instep"], dtype=float)
    big_ball = np.asarray(pts["big_ball"], dtype=float)
    small_ball = np.asarray(pts["small_ball"], dtype=float)
    mid_ball = (big_ball + small_ball) * 0.5
    toe_bases = [np.asarray(toe["base"], dtype=float) for toe in skeleton["toes"]]
    toe_box = skeleton.get("toe_box")
    if toe_bases:
        toe_root = np.mean(toe_bases, axis=0) + np.array([0.0, -params.foot_length * 0.04, -params.instep_height * 0.04])
    elif toe_box:
        toe_root = np.asarray(toe_box["back_center"], dtype=float) + np.array([0.0, -params.foot_length * 0.035, -params.instep_height * 0.06])
    else:
        toe_root = mid_ball + np.array([0.0, params.foot_length * 0.04, -params.instep_height * 0.08])
    heel_scale = _heel_scale(params)
    vamp_scale = max(0.70, params.vamp_volume / 100.0) if params.foot_mode == "shoe" else 1.0

    centers = [
        heel + np.array([0.0, -params.foot_length * 0.04, 0.0]),
        heel + np.array([0.0, params.foot_length * 0.06, params.heel_width * 0.04]),
        arch + np.array([0.0, params.foot_length * 0.02, -params.instep_height * 0.08]),
        instep + np.array([0.0, params.foot_length * 0.03, -params.instep_height * 0.08]),
        (instep + mid_ball) * 0.5 + np.array([0.0, -params.foot_length * 0.01, -params.instep_height * 0.10]),
        mid_ball + np.array([0.0, -params.foot_length * 0.02, -params.instep_height * 0.12]),
        toe_root,
    ]
    widths = [
        params.heel_width * 0.92 * heel_scale,
        params.heel_width * 1.08 * heel_scale,
        params.foot_width * 0.70,
        params.foot_width * 0.82,
        params.foot_width * 1.00,
        params.foot_width * 1.10,
        max(params.foot_width * 0.96, params.toe_box_width * 0.92) if toe_box else params.foot_width * 0.96,
    ]
    top_offsets = [
        params.heel_width * 0.22 * heel_scale,
        params.heel_width * 0.26 * heel_scale,
        params.instep_height * 0.38,
        params.instep_height * 0.84 * vamp_scale,
        params.instep_height * 0.58 * vamp_scale,
        params.instep_height * 0.34 * max(0.85, vamp_scale),
        params.instep_height * 0.18 * max(0.90, vamp_scale * 0.94),
    ]
    bottom_offsets = [
        params.heel_width * 0.16 * heel_scale,
        params.heel_width * 0.16 * heel_scale,
        params.instep_height * 0.18,
        params.instep_height * 0.16,
        params.instep_height * 0.16,
        params.instep_height * 0.18,
        params.instep_height * 0.16,
    ]
    centers, widths, top_offsets, bottom_offsets = _densify_skin_profile(centers, widths, top_offsets, bottom_offsets, steps=2)
    x_samples = [-0.50, -0.25, 0.0, 0.25, 0.50]

    top_grid = []
    bottom_grid = []
    for center, width, top_offset, bottom_offset in zip(centers, widths, top_offsets, bottom_offsets):
        width *= SDIV_BODY_WIDTH_SCALE
        top_offset *= SDIV_BODY_HEIGHT_SCALE
        bottom_offset *= SDIV_BODY_SOLE_SCALE
        top_row = []
        bottom_row = []
        for sample in x_samples:
            crown = 1.0 - abs(sample) * 0.42
            side_drop = abs(sample) * params.instep_height * 0.08
            x = center[0] + sample * width
            top_row.append(_append_vertex(vertices, (x, center[1], center[2] + top_offset * crown - side_drop)))
            bottom_row.append(_append_vertex(vertices, (x, center[1], center[2] - bottom_offset)))
        top_grid.append(top_row)
        bottom_grid.append(bottom_row)

    rows = len(top_grid)
    cols = len(x_samples)
    for r in range(rows - 1):
        for c in range(cols - 1):
            faces.append((top_grid[r][c], top_grid[r][c + 1], top_grid[r + 1][c + 1], top_grid[r + 1][c]))
            groups.append("foot_body")
            faces.append((bottom_grid[r][c], bottom_grid[r + 1][c], bottom_grid[r + 1][c + 1], bottom_grid[r][c + 1]))
            groups.append("foot_body")
    for r in range(rows - 1):
        faces.append((top_grid[r][0], top_grid[r + 1][0], bottom_grid[r + 1][0], bottom_grid[r][0]))
        groups.append("foot_body")
        faces.append((top_grid[r + 1][-1], top_grid[r][-1], bottom_grid[r][-1], bottom_grid[r + 1][-1]))
        groups.append("foot_body")
    for c in range(cols - 1):
        faces.append((top_grid[0][c + 1], top_grid[0][c], bottom_grid[0][c], bottom_grid[0][c + 1]))
        groups.append("foot_body")
        faces.append((top_grid[-1][c], top_grid[-1][c + 1], bottom_grid[-1][c + 1], bottom_grid[-1][c]))
        groups.append("foot_body")


def _densify_skin_profile(
    centers: list[np.ndarray],
    widths: list[float],
    top_offsets: list[float],
    bottom_offsets: list[float],
    steps: int,
) -> tuple[list[np.ndarray], list[float], list[float], list[float]]:
    """Insert support rows so the foot shell does not contain oversized SDiv faces."""

    steps = max(1, int(steps))
    dense_centers: list[np.ndarray] = []
    dense_widths: list[float] = []
    dense_top_offsets: list[float] = []
    dense_bottom_offsets: list[float] = []
    for i in range(len(centers) - 1):
        for step in range(steps):
            t = step / steps
            dense_centers.append(centers[i] * (1.0 - t) + centers[i + 1] * t)
            dense_widths.append(widths[i] * (1.0 - t) + widths[i + 1] * t)
            dense_top_offsets.append(top_offsets[i] * (1.0 - t) + top_offsets[i + 1] * t)
            dense_bottom_offsets.append(bottom_offsets[i] * (1.0 - t) + bottom_offsets[i + 1] * t)
    dense_centers.append(centers[-1])
    dense_widths.append(widths[-1])
    dense_top_offsets.append(top_offsets[-1])
    dense_bottom_offsets.append(bottom_offsets[-1])
    return dense_centers, dense_widths, dense_top_offsets, dense_bottom_offsets


def _skin_height_at(point: np.ndarray, params: FootParams) -> float:
    """Approximate soft-tissue height for the foot envelope."""

    y = float(point[1])
    x = abs(float(point[0]))
    length = params.foot_length
    instep = math.exp(-((y - length * 0.04) / (length * 0.30)) ** 2) * params.instep_height * 0.80
    forefoot = math.exp(-((y - length * 0.48) / (length * 0.18)) ** 2) * params.instep_height * 0.42
    heel = math.exp(-((y + length * 0.40) / (length * 0.14)) ** 2) * params.heel_width * 0.24 * _heel_scale(params)
    edge_falloff = max(0.72, 1.0 - x / max(params.foot_width, 1.0) * 0.30)
    return max(10.0, (instep + forefoot + heel) * edge_falloff)


def _skin_sole_offset_at(point: np.ndarray, params: FootParams) -> float:
    y = float(point[1])
    length = params.foot_length
    arch = math.exp(-((y + length * 0.04) / (length * 0.20)) ** 2) * params.arch_height * 0.18
    return max(8.0, params.instep_height * 0.12 + arch)


def _add_flesh_masses(vertices, faces, groups, skeleton: dict, params: FootParams) -> None:
    """Add separated low-poly flesh blocks so the base reads as a foot shape."""

    pts = skeleton["points"]
    heel = np.asarray(pts["heel"], dtype=float)
    instep = np.asarray(pts["instep"], dtype=float)
    arch = np.asarray(pts["arch"], dtype=float)
    big_ball = np.asarray(pts["big_ball"], dtype=float)
    small_ball = np.asarray(pts["small_ball"], dtype=float)
    side_sign = -1.0 if params.side == "right" else 1.0
    medial = side_sign
    lateral = -side_sign
    instep_scale = _instep_part_scale(params)
    heel_scale = _heel_scale(params)

    forefoot_center = (big_ball + small_ball) * 0.5 + np.array([0.0, params.foot_length * 0.015, -params.instep_height * 0.05])

    toe_bases = [np.asarray(toe["base"], dtype=float) for toe in skeleton["toes"]]
    for base in toe_bases:
        bridge_start = forefoot_center + (base - forefoot_center) * 0.25
        bridge_end = base + np.array([0.0, -params.foot_length * 0.025, -params.instep_height * 0.05])
        _add_box_segment(vertices, faces, groups, bridge_start, bridge_end, params.foot_width * 0.10 * instep_scale, "foot_body", material=MATERIAL_SOFT_TISSUE)
    toe_box = skeleton.get("toe_box")
    if not toe_bases and toe_box:
        back = np.asarray(toe_box["back_center"], dtype=float)
        outline = toe_box["top_outline"]
        left_back = np.asarray(outline[0], dtype=float)
        right_back = np.asarray(outline[-1], dtype=float)
        left_back[2] = back[2]
        right_back[2] = back[2]
        bridge_width = params.foot_width * 0.16 * instep_scale * max(0.85, params.vamp_volume / 100.0)
        _add_box_segment(vertices, faces, groups, forefoot_center, back, bridge_width, "foot_body", material=MATERIAL_SOFT_TISSUE)
        _add_box_segment(vertices, faces, groups, big_ball, left_back, bridge_width * 0.72, "foot_body", material=MATERIAL_SOFT_TISSUE)
        _add_box_segment(vertices, faces, groups, small_ball, right_back, bridge_width * 0.72, "foot_body", material=MATERIAL_SOFT_TISSUE)

    medial_heel = heel + np.array([medial * params.heel_width * 0.25 * heel_scale, params.foot_length * 0.08, params.heel_width * 0.08 * heel_scale])
    medial_ball = big_ball + np.array([medial * params.foot_width * 0.08, -params.foot_length * 0.06, -params.instep_height * 0.08])
    lateral_heel = heel + np.array([lateral * params.heel_width * 0.25 * heel_scale, params.foot_length * 0.08, params.heel_width * 0.08 * heel_scale])
    lateral_ball = small_ball + np.array([lateral * params.foot_width * 0.08, -params.foot_length * 0.06, -params.instep_height * 0.08])
    _add_box_segment(vertices, faces, groups, medial_heel, medial_ball, params.foot_width * 0.13 * instep_scale, "foot_body", material=MATERIAL_SOFT_TISSUE)
    _add_box_segment(vertices, faces, groups, lateral_heel, lateral_ball, params.foot_width * 0.14 * instep_scale, "foot_body", material=MATERIAL_SOFT_TISSUE)

    arch_pad = arch + np.array([0.0, params.foot_length * 0.05, params.arch_height * 0.16])
    heel_anchor = heel + np.array([0.0, params.foot_length * 0.03, params.heel_width * 0.06 * heel_scale])
    _add_box_segment(vertices, faces, groups, heel_anchor, arch_pad, params.foot_width * 0.11 * instep_scale * max(1.0, heel_scale * 0.86), "foot_body", material=MATERIAL_SOFT_TISSUE)


def _add_side_volume_masses(vertices, faces, groups, skeleton: dict, params: FootParams) -> None:
    """Add side-view bulk so the foot does not collapse into sparse struts."""

    pts = skeleton["points"]
    heel = np.asarray(pts["heel"], dtype=float)
    ankle = np.asarray(pts["ankle"], dtype=float)
    instep = np.asarray(pts["instep"], dtype=float)
    arch = np.asarray(pts["arch"], dtype=float)
    big_ball = np.asarray(pts["big_ball"], dtype=float)
    small_ball = np.asarray(pts["small_ball"], dtype=float)
    mid_ball = (big_ball + small_ball) * 0.5
    instep_scale = _instep_part_scale(params)
    heel_scale = _heel_scale(params)

    support_thickness = max(0.20, float(params.plantar_support_thickness) / 100.0)
    support_length = 0.0 if params.plantar_support_length <= 0 else min(1.20, max(0.02, float(params.plantar_support_length) / 100.0))
    if support_length > 0.0:
        plantar_rear = heel + np.array([0.0, params.foot_length * 0.08, -params.instep_height * 0.06 * heel_scale])
        plantar_front = mid_ball + np.array([0.0, -params.foot_length * 0.07, -params.instep_height * 0.05])
        plantar_arch = arch + np.array([0.0, params.foot_length * 0.04, params.arch_height * 0.18])
        plantar_start = plantar_arch + (plantar_rear - plantar_arch) * support_length
        plantar_end = plantar_arch + (plantar_front - plantar_arch) * support_length
        plantar_width = params.foot_width * 0.075 * instep_scale * support_thickness * max(1.0, heel_scale * 0.78)
        _add_box_segment(vertices, faces, groups, plantar_start, plantar_arch, plantar_width, "foot_body", material=MATERIAL_SOFT_TISSUE)
        _add_box_segment(vertices, faces, groups, plantar_arch, plantar_end, plantar_width * 0.92, "foot_body", material=MATERIAL_SOFT_TISSUE)

    dorsal_a = instep + np.array([0.0, params.foot_length * 0.02, params.instep_height * 0.04])
    dorsal_b = mid_ball + np.array([0.0, -params.foot_length * 0.02, params.instep_height * 0.12])
    vamp_scale = max(0.70, params.vamp_volume / 100.0) if params.foot_mode == "shoe" else 1.0
    _add_box_segment(vertices, faces, groups, dorsal_a, dorsal_b, params.foot_width * 0.16 * instep_scale * vamp_scale, "instep", material=MATERIAL_SOFT_TISSUE)

    achilles_a = heel + np.array([0.0, -params.foot_length * 0.04 * heel_scale, params.heel_width * 0.24 * heel_scale])
    achilles_b = ankle + np.array([0.0, params.foot_length * 0.02, -params.instep_height * 0.12])
    _add_box_segment(vertices, faces, groups, achilles_a, achilles_b, params.heel_width * 0.22 * heel_scale, "heel", material=MATERIAL_SOFT_TISSUE)

    for side in (-1.0, 1.0):
        rail_a = heel + np.array([side * params.heel_width * 0.38 * heel_scale, params.foot_length * 0.10, params.heel_width * 0.04 * heel_scale])
        rail_b = mid_ball + np.array([side * params.foot_width * 0.42, -params.foot_length * 0.02, -params.instep_height * 0.04])
        _add_box_segment(vertices, faces, groups, rail_a, rail_b, params.foot_width * 0.075 * instep_scale, "foot_body", material=MATERIAL_SOFT_TISSUE)


def _add_midfoot_fill_masses(vertices, faces, groups, skeleton: dict, params: FootParams) -> None:
    """Fill the midfoot volume with overlapping block masses for sculpting."""

    pts = skeleton["points"]
    heel = np.asarray(pts["heel"], dtype=float)
    ankle = np.asarray(pts["ankle"], dtype=float)
    instep = np.asarray(pts["instep"], dtype=float)
    arch = np.asarray(pts["arch"], dtype=float)
    big_ball = np.asarray(pts["big_ball"], dtype=float)
    small_ball = np.asarray(pts["small_ball"], dtype=float)
    mid_ball = (big_ball + small_ball) * 0.5

    length = params.foot_length
    width = params.foot_width
    instep_h = params.instep_height
    heel_w = params.heel_width * _heel_scale(params)
    instep_scale = _instep_part_scale(params)

    rear_dorsal = heel + np.array([0.0, length * 0.10, heel_w * 0.22])
    mid_dorsal = instep + np.array([0.0, length * 0.05, instep_h * 0.10])
    fore_dorsal = mid_ball + np.array([0.0, -length * 0.06, instep_h * 0.08])
    deep_core_a = heel + np.array([0.0, length * 0.08, heel_w * 0.12])
    deep_core_b = mid_ball + np.array([0.0, -length * 0.05, instep_h * 0.02])
    _add_box_segment(vertices, faces, groups, deep_core_a, deep_core_b, width * 0.30 * instep_scale, "foot_body", material=MATERIAL_SOFT_TISSUE)
    _add_box_segment(vertices, faces, groups, rear_dorsal, mid_dorsal, width * 0.24 * instep_scale, "instep", material=MATERIAL_SOFT_TISSUE)
    _add_box_segment(vertices, faces, groups, mid_dorsal, fore_dorsal, width * 0.22 * instep_scale, "instep", material=MATERIAL_SOFT_TISSUE)

    for side in (-1.0, 1.0):
        side_rear = heel + np.array([side * heel_w * 0.36, length * 0.08, heel_w * 0.12])
        side_mid = instep + np.array([side * width * 0.33, length * 0.05, -instep_h * 0.02])
        side_fore = mid_ball + np.array([side * width * 0.42, -length * 0.05, -instep_h * 0.05])
        _add_box_segment(vertices, faces, groups, side_rear, side_mid, width * 0.13 * instep_scale, "foot_body", material=MATERIAL_SOFT_TISSUE)
        _add_box_segment(vertices, faces, groups, side_mid, side_fore, width * 0.14 * instep_scale, "foot_body", material=MATERIAL_SOFT_TISSUE)

    for toe in skeleton["toes"]:
        base = np.asarray(toe["base"], dtype=float)
        root = mid_ball + (base - mid_ball) * 0.30 + np.array([0.0, -length * 0.035, -instep_h * 0.05])
        _add_box_segment(vertices, faces, groups, fore_dorsal, root, max(width * 0.12, toe["radius"] * 1.2) * instep_scale, "foot_body", material=MATERIAL_SOFT_TISSUE)
    toe_box = skeleton.get("toe_box")
    if not skeleton["toes"] and toe_box:
        back = np.asarray(toe_box["back_center"], dtype=float) + np.array([0.0, -length * 0.015, -instep_h * 0.05])
        front = np.asarray(toe_box["front_center"], dtype=float) + np.array([0.0, -length * 0.040, 0.0])
        vamp_scale = max(0.70, params.vamp_volume / 100.0)
        _add_box_segment(vertices, faces, groups, fore_dorsal, back, width * 0.18 * instep_scale * vamp_scale, "foot_body", material=MATERIAL_SOFT_TISSUE)
        _add_box_segment(vertices, faces, groups, back, front, width * 0.15 * instep_scale * vamp_scale, "toe_box", material=MATERIAL_SOFT_TISSUE)


def _add_ankle_achilles_masses(vertices, faces, groups, skeleton: dict, params: FootParams) -> None:
    """Add posterior ankle volume and a blocky Achilles tendon."""

    pts = skeleton["points"]
    heel = np.asarray(pts["heel"], dtype=float)
    ankle = np.asarray(pts["ankle"], dtype=float)
    instep = np.asarray(pts["instep"], dtype=float)
    arch = np.asarray(pts["arch"], dtype=float)

    length = params.foot_length
    width = params.foot_width
    heel_scale = _heel_scale(params)
    heel_w = params.heel_width * heel_scale
    instep_h = params.instep_height
    instep_scale = _instep_part_scale(params)
    malleolus_scale = _malleolus_scale(params)
    posterior = _normalized(heel - instep, np.array([0.0, -1.0, 0.0]))
    leg_axis = _normalized(ankle - heel, np.array([0.0, 0.0, 1.0]))

    heel_back = heel + posterior * length * 0.045 + leg_axis * heel_w * 0.13
    tendon_low = heel + posterior * length * 0.035 + leg_axis * heel_w * 0.30
    tendon_mid = heel + posterior * length * 0.030 + leg_axis * length * 0.34
    tendon_top = ankle + posterior * length * 0.028 + leg_axis * length * 0.075

    _add_box_segment(vertices, faces, groups, heel_back, tendon_low, heel_w * 0.26 * max(instep_scale, malleolus_scale * 0.92), "heel", material=MATERIAL_SOFT_TISSUE)
    _add_box_segment(vertices, faces, groups, tendon_low, tendon_mid, heel_w * 0.20 * instep_scale, "achilles_tendon", material=MATERIAL_SOFT_TISSUE)
    _add_box_segment(vertices, faces, groups, tendon_mid, tendon_top, heel_w * 0.18 * instep_scale, "achilles_tendon", material=MATERIAL_SOFT_TISSUE)

    ankle_core = (ankle + tendon_mid) * 0.5
    _add_box_segment(vertices, faces, groups, heel_back, ankle_core, heel_w * 0.28 * max(instep_scale, malleolus_scale * 0.95), "heel", material=MATERIAL_SOFT_TISSUE)
    _add_box_segment(vertices, faces, groups, ankle_core, instep, width * 0.18 * instep_scale, "instep", material=MATERIAL_SOFT_TISSUE)

    ankle_side = heel_w * 0.36 * (0.92 + malleolus_scale * 0.08)
    for side in (-1.0, 1.0):
        malleolus = ankle + np.array([side * ankle_side, length * 0.03, -instep_h * 0.10])
        heel_side = heel_back + np.array([side * heel_w * 0.30, 0.0, -heel_w * 0.02])
        ankle_side_pad = ankle_core + np.array([side * heel_w * 0.24, 0.0, -heel_w * 0.03])
        arch_side = arch + np.array([side * width * 0.22, length * 0.05, -instep_h * 0.05])
        _add_box_segment(vertices, faces, groups, heel_side, ankle_side_pad, heel_w * 0.22 * malleolus_scale, "heel", material=MATERIAL_SOFT_TISSUE)
        _add_box_segment(vertices, faces, groups, ankle_side_pad, malleolus, heel_w * 0.18 * malleolus_scale, "ankle_joint", material=MATERIAL_SOFT_TISSUE)
        _add_box_segment(vertices, faces, groups, ankle_side_pad, arch_side, width * 0.16 * instep_scale, "foot_body", material=MATERIAL_SOFT_TISSUE)


def _add_metatarsal_web_surfaces(vertices, faces, groups, skeleton: dict, params: FootParams) -> None:
    """Add filled polygon webs between metatarsal rays without adding cross bars."""

    pts = skeleton["points"]
    instep = np.asarray(pts["instep"], dtype=float)
    big_ball = np.asarray(pts["big_ball"], dtype=float)
    small_ball = np.asarray(pts["small_ball"], dtype=float)
    mid_ball = (big_ball + small_ball) * 0.5
    toes = skeleton["toes"]
    if len(toes) < 2:
        return
    length = params.foot_length
    width = params.foot_width
    instep_h = params.instep_height
    instep_scale = _instep_part_scale(params)
    patch_thickness = max(7.0, min(15.0, instep_h * 0.20)) * instep_scale

    rear_points = []
    mid_points = []
    front_points = []
    for toe in toes:
        base = np.asarray(toe["base"], dtype=float)
        rear = instep + (base - instep) * 0.22 + np.array([0.0, -length * 0.010, instep_h * 0.12])
        mid = instep + (base - instep) * 0.48 + np.array([0.0, -length * 0.010, instep_h * 0.07])
        front = base + np.array([0.0, -length * 0.045, instep_h * 0.045])
        rear_points.append(rear)
        mid_points.append(mid)
        front_points.append(front)

    for i in range(len(toes) - 1):
        _add_thick_loft_patch(
            vertices,
            faces,
            groups,
            rear_points[i],
            mid_points[i],
            mid_points[i + 1],
            rear_points[i + 1],
            u_steps=2,
            v_steps=2,
            thickness=patch_thickness * 0.95,
            crown=instep_h * 0.055,
            group="foot_body",
        )
        _add_thick_loft_patch(
            vertices,
            faces,
            groups,
            mid_points[i],
            front_points[i],
            front_points[i + 1],
            mid_points[i + 1],
            u_steps=3,
            v_steps=2,
            thickness=patch_thickness * 1.15,
            crown=instep_h * 0.045,
            group="foot_body",
        )

    medial_rear = instep + (big_ball - instep) * 0.30 + np.array([-width * 0.08, 0.0, instep_h * 0.06])
    lateral_rear = instep + (small_ball - instep) * 0.30 + np.array([width * 0.08, 0.0, instep_h * 0.04])
    medial_front = big_ball + np.array([-width * 0.10, -length * 0.08, instep_h * 0.02])
    lateral_front = small_ball + np.array([width * 0.10, -length * 0.08, instep_h * 0.02])
    _add_thick_loft_patch(
        vertices,
        faces,
        groups,
        medial_rear,
        medial_front,
        mid_ball + np.array([0.0, -length * 0.06, instep_h * 0.04]),
        instep + np.array([0.0, length * 0.01, instep_h * 0.08]),
        u_steps=3,
        v_steps=2,
        thickness=patch_thickness * 1.15,
        crown=instep_h * 0.05,
        group="foot_body",
    )
    _add_thick_loft_patch(
        vertices,
        faces,
        groups,
        instep + np.array([0.0, length * 0.01, instep_h * 0.08]),
        mid_ball + np.array([0.0, -length * 0.06, instep_h * 0.04]),
        lateral_front,
        lateral_rear,
        u_steps=3,
        v_steps=2,
        thickness=patch_thickness * 1.15,
        crown=instep_h * 0.05,
        group="foot_body",
    )


def _add_shoe_forefoot_fill(vertices, faces, groups, skeleton: dict, params: FootParams) -> None:
    """Fill the transition between the sculpt foot body and the unified toe box."""

    toe_box = skeleton.get("toe_box")
    if not toe_box:
        return

    pts = skeleton["points"]
    instep = np.asarray(pts["instep"], dtype=float)
    big_ball = np.asarray(pts["big_ball"], dtype=float)
    small_ball = np.asarray(pts["small_ball"], dtype=float)
    mid_ball = (big_ball + small_ball) * 0.5
    outline = toe_box["top_outline"]
    left_back = np.asarray(outline[0], dtype=float)
    right_back = np.asarray(outline[-1], dtype=float)
    back = np.asarray(toe_box["back_center"], dtype=float)
    left_back[2] = back[2] * 0.90
    right_back[2] = back[2] * 0.90

    length = params.foot_length
    width = params.foot_width
    instep_h = params.instep_height
    instep_scale = _instep_part_scale(params)
    vamp_scale = max(0.70, params.vamp_volume / 100.0)
    patch_thickness = max(9.0, instep_h * 0.22) * instep_scale * vamp_scale

    dorsal = mid_ball + np.array([0.0, -length * 0.03, instep_h * 0.10])
    rear = instep + (dorsal - instep) * 0.70 + np.array([0.0, -length * 0.02, instep_h * 0.06])
    _add_thick_loft_patch(
        vertices,
        faces,
        groups,
        big_ball + np.array([-width * 0.05, -length * 0.03, instep_h * 0.00]),
        left_back,
        back + np.array([0.0, 0.0, instep_h * 0.02]),
        rear,
        u_steps=2,
        v_steps=2,
        thickness=patch_thickness,
        crown=instep_h * 0.05,
        group="toe_box",
    )
    _add_thick_loft_patch(
        vertices,
        faces,
        groups,
        rear,
        back + np.array([0.0, 0.0, instep_h * 0.02]),
        right_back,
        small_ball + np.array([width * 0.05, -length * 0.03, instep_h * 0.00]),
        u_steps=2,
        v_steps=2,
        thickness=patch_thickness,
        crown=instep_h * 0.05,
        group="toe_box",
    )


def _add_toe_box_mesh(vertices, faces, groups, skeleton: dict, params: FootParams) -> None:
    """Add one low-poly rounded toe block for Shoe base mode."""

    toe_box = skeleton.get("toe_box")
    if not toe_box:
        return

    stations = toe_box["stations"]
    x_samples = [-1.0, -0.55, 0.0, 0.55, 1.0]
    top_grid = []
    bottom_grid = []
    for station_index, station in enumerate(stations):
        half_width = float(station["half_width"]) * (1.08 + 0.04 * toe_box["roundness"])
        y = float(station["y"])
        bottom_z = float(station["bottom_z"]) - max(0.0, params.sole_thickness) * 0.10
        top_z = float(station["top_z"])
        height = max(6.0, top_z - bottom_z)
        row_top = []
        row_bottom = []
        for sample in x_samples:
            edge = abs(sample)
            x = half_width * sample
            edge_drop = height * (0.13 + 0.06 * toe_box["roundness"]) * edge
            nose_drop = height * 0.08 * edge if station_index == len(stations) - 1 else 0.0
            row_top.append(_append_vertex(vertices, (x, y, top_z - edge_drop - nose_drop)))
            row_bottom.append(_append_vertex(vertices, (x, y, bottom_z - height * 0.025 * (1.0 - edge))))
        top_grid.append(row_top)
        bottom_grid.append(row_bottom)

    _append_grid_shell(faces, groups, top_grid, bottom_grid, "toe_box")


def _add_shoe_sole_wedge(vertices, faces, groups, skeleton: dict, params: FootParams) -> None:
    """Add a broad sole/heel wedge for Shoe base mode."""

    toe_box = skeleton.get("toe_box")
    sole = max(0.0, float(params.sole_thickness))
    heel_h = max(0.0, float(params.heel_height))
    if not toe_box or (sole < 0.1 and heel_h < 0.1):
        return

    pts = skeleton["points"]
    heel = np.asarray(pts["heel"], dtype=float)
    arch = np.asarray(pts["arch"], dtype=float)
    big_ball = np.asarray(pts["big_ball"], dtype=float)
    small_ball = np.asarray(pts["small_ball"], dtype=float)
    mid_ball = (big_ball + small_ball) * 0.5
    heel_scale = _heel_scale(params)
    stations = toe_box["stations"]
    sole_depth = max(2.0, sole)
    profile = [
        (heel[1] - params.foot_length * 0.05, params.heel_width * 0.48 * heel_scale, -sole_depth - heel_h, heel[2] + params.heel_width * 0.02),
        (heel[1] + params.foot_length * 0.07, params.heel_width * 0.56 * heel_scale, -sole_depth * 0.86 - heel_h * 0.62, heel[2] + params.heel_width * 0.04),
        (arch[1], params.foot_width * 0.42, -sole_depth * 0.60 - heel_h * 0.32, max(0.0, arch[2] * 0.16)),
        (mid_ball[1], params.foot_width * 0.54, -sole_depth * 0.46, max(0.0, mid_ball[2] * 0.06)),
        (stations[1]["y"], stations[1]["half_width"] * 1.02, float(stations[1]["bottom_z"]) - sole_depth * 0.38, float(stations[1]["bottom_z"]) + sole_depth * 0.10),
        (stations[-1]["y"], stations[-1]["half_width"] * 1.12, float(stations[-1]["bottom_z"]) - sole_depth * 0.28, float(stations[-1]["bottom_z"]) + sole_depth * 0.08),
    ]

    x_samples = [-1.0, -0.5, 0.0, 0.5, 1.0]
    top_grid = []
    bottom_grid = []
    for y, half_width, bottom_z, top_z in profile:
        row_top = []
        row_bottom = []
        for sample in x_samples:
            edge = abs(sample)
            x = half_width * sample
            row_top.append(_append_vertex(vertices, (x, y, top_z - edge * sole_depth * 0.08)))
            row_bottom.append(_append_vertex(vertices, (x, y, bottom_z - (1.0 - edge) * sole_depth * 0.06)))
        top_grid.append(row_top)
        bottom_grid.append(row_bottom)

    _append_grid_shell(faces, groups, top_grid, bottom_grid, "shoe_sole")


def _append_grid_shell(faces, groups, top_grid: list[list[int]], bottom_grid: list[list[int]], group: str) -> None:
    """Connect matching top/bottom grids into a closed low-poly shell."""

    rows = len(top_grid)
    cols = len(top_grid[0])
    for r in range(rows - 1):
        for c in range(cols - 1):
            faces.append((top_grid[r][c], top_grid[r][c + 1], top_grid[r + 1][c + 1], top_grid[r + 1][c]))
            groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))
            faces.append((bottom_grid[r][c], bottom_grid[r + 1][c], bottom_grid[r + 1][c + 1], bottom_grid[r][c + 1]))
            groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))
    for r in range(rows - 1):
        faces.append((top_grid[r][0], top_grid[r + 1][0], bottom_grid[r + 1][0], bottom_grid[r][0]))
        groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))
        faces.append((top_grid[r + 1][-1], top_grid[r][-1], bottom_grid[r][-1], bottom_grid[r + 1][-1]))
        groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))
    for c in range(cols - 1):
        faces.append((top_grid[0][c + 1], top_grid[0][c], bottom_grid[0][c], bottom_grid[0][c + 1]))
        groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))
        faces.append((top_grid[-1][c], top_grid[-1][c + 1], bottom_grid[-1][c + 1], bottom_grid[-1][c]))
        groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))


def _add_box_segment(vertices, faces, groups, a, b, thickness: float, group: str, material: str = MATERIAL_BONE) -> None:
    """Add an oriented rectangular block between two joints with lengthwise support cuts."""

    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    thickness *= _sdiv_thickness_scale(material)
    axis = b - a
    length = float(np.linalg.norm(axis))
    if length < 0.001:
        return
    forward = axis / length
    overlap = min(length * 0.34, max(thickness * 1.05, 5.0))
    a = a - forward * overlap
    b = b + forward * overlap
    axis = b - a
    length = float(np.linalg.norm(axis))
    forward = axis / length
    ref = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(forward, ref))) > 0.92:
        ref = np.array([1.0, 0.0, 0.0])
    right = np.cross(forward, ref)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    half = thickness * 0.5
    segment_count = _box_segment_divisions(length, thickness)
    ring_indices = []
    for i in range(segment_count + 1):
        center = a + forward * (length * i / segment_count)
        ring_indices.append(_append_box_ring(vertices, center, right, up, half))

    start = ring_indices[0]
    end = ring_indices[-1]
    for face in [(start[0], start[1], start[2], start[3]), (end[0], end[3], end[2], end[1])]:
        faces.append(face)
        groups.append(_group_with_material(group, material))

    for i in range(segment_count):
        current = ring_indices[i]
        nxt = ring_indices[i + 1]
        for side_index in range(4):
            face = (current[side_index], nxt[side_index], nxt[(side_index + 1) % 4], current[(side_index + 1) % 4])
            faces.append(face)
            groups.append(_group_with_material(group, material))


def _append_box_ring(vertices, center: np.ndarray, right: np.ndarray, up: np.ndarray, half: float) -> tuple[int, ...]:
    """Append a sparse rectangular ring so SDiv can round the block."""

    return tuple(
        _append_vertex(vertices, point)
        for point in [
            center - right * half - up * half,
            center + right * half - up * half,
            center + right * half + up * half,
            center - right * half + up * half,
        ]
    )


def _box_segment_divisions(length: float, thickness: float) -> int:
    """Choose enough cuts that SDiv does not treat long blocks as one giant face."""

    target_span = max(18.0, min(BOX_SEGMENT_MAX_FACE_SPAN, thickness * 1.15))
    return max(1, int(math.ceil(length / target_span)))


def _add_thick_loft_patch(
    vertices,
    faces,
    groups,
    p00,
    p10,
    p11,
    p01,
    u_steps: int,
    v_steps: int,
    thickness: float,
    crown: float,
    group: str,
) -> None:
    """Add a thickened quad patch that fills gaps between neighboring rays."""

    p00 = np.asarray(p00, dtype=float)
    p10 = np.asarray(p10, dtype=float)
    p11 = np.asarray(p11, dtype=float)
    p01 = np.asarray(p01, dtype=float)
    u_steps = max(1, int(u_steps))
    v_steps = max(1, int(v_steps))
    normal = np.cross(p10 - p00, p01 - p00)
    normal = _normalized(normal, np.array([0.0, 0.0, 1.0]))
    if normal[2] < 0.0:
        normal = -normal

    top_grid = []
    bottom_grid = []
    half = thickness * 0.5
    for v_index in range(v_steps + 1):
        v = v_index / v_steps
        top_row = []
        bottom_row = []
        for u_index in range(u_steps + 1):
            u = u_index / u_steps
            point = (
                (1.0 - u) * (1.0 - v) * p00
                + u * (1.0 - v) * p10
                + u * v * p11
                + (1.0 - u) * v * p01
            )
            point = point + np.array([0.0, 0.0, math.sin(math.pi * u) * math.sin(math.pi * v) * crown])
            top_row.append(_append_vertex(vertices, point + normal * half))
            bottom_row.append(_append_vertex(vertices, point - normal * half))
        top_grid.append(top_row)
        bottom_grid.append(bottom_row)

    for v_index in range(v_steps):
        for u_index in range(u_steps):
            faces.append((top_grid[v_index][u_index], top_grid[v_index][u_index + 1], top_grid[v_index + 1][u_index + 1], top_grid[v_index + 1][u_index]))
            groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))
            faces.append((bottom_grid[v_index][u_index], bottom_grid[v_index + 1][u_index], bottom_grid[v_index + 1][u_index + 1], bottom_grid[v_index][u_index + 1]))
            groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))

    for v_index in range(v_steps):
        faces.append((top_grid[v_index][0], top_grid[v_index + 1][0], bottom_grid[v_index + 1][0], bottom_grid[v_index][0]))
        groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))
        faces.append((top_grid[v_index + 1][-1], top_grid[v_index][-1], bottom_grid[v_index][-1], bottom_grid[v_index + 1][-1]))
        groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))
    for u_index in range(u_steps):
        faces.append((top_grid[0][u_index + 1], top_grid[0][u_index], bottom_grid[0][u_index], bottom_grid[0][u_index + 1]))
        groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))
        faces.append((top_grid[-1][u_index], top_grid[-1][u_index + 1], bottom_grid[-1][u_index + 1], bottom_grid[-1][u_index]))
        groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))


def _add_box(vertices, faces, groups, center, size, group: str) -> None:
    """Add a simple axis-aligned box for blocky sculpt base parts."""

    cx, cy, cz = center
    sx, sy, sz = _sdiv_box_size(size)
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    corners = [
        (cx - hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
    ]
    idx = [_append_vertex(vertices, corner) for corner in corners]
    for face in [
        (idx[0], idx[3], idx[2], idx[1]),
        (idx[4], idx[5], idx[6], idx[7]),
        (idx[0], idx[1], idx[5], idx[4]),
        (idx[1], idx[2], idx[6], idx[5]),
        (idx[2], idx[3], idx[7], idx[6]),
        (idx[3], idx[0], idx[4], idx[7]),
    ]:
        faces.append(face)
        groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))


def _add_subdivided_box(vertices, faces, groups, center, size, divisions, group: str) -> None:
    """Add a coarse quad box with visible subdivision density for base forms."""

    cx, cy, cz = center
    sx, sy, sz = _sdiv_box_size(size)
    nx, ny, nz = [max(1, int(value)) for value in divisions]
    x0, x1 = cx - sx * 0.5, cx + sx * 0.5
    y0, y1 = cy - sy * 0.5, cy + sy * 0.5
    z0, z1 = cz - sz * 0.5, cz + sz * 0.5

    def add_face_grid(origin, u_vec, v_vec, u_count: int, v_count: int, flip: bool = False) -> None:
        grid = []
        for iv in range(v_count + 1):
            row = []
            for iu in range(u_count + 1):
                pos = origin + u_vec * (iu / u_count) + v_vec * (iv / v_count)
                row.append(_append_vertex(vertices, pos))
            grid.append(row)
        for iv in range(v_count):
            for iu in range(u_count):
                face = (grid[iv][iu], grid[iv][iu + 1], grid[iv + 1][iu + 1], grid[iv + 1][iu])
                if flip:
                    face = tuple(reversed(face))
                faces.append(face)
                groups.append(_group_with_material(group, MATERIAL_SOFT_TISSUE))

    add_face_grid(np.array([x0, y0, z1]), np.array([sx, 0.0, 0.0]), np.array([0.0, sy, 0.0]), nx, ny)
    add_face_grid(np.array([x0, y1, z0]), np.array([sx, 0.0, 0.0]), np.array([0.0, -sy, 0.0]), nx, ny)
    add_face_grid(np.array([x0, y0, z0]), np.array([sx, 0.0, 0.0]), np.array([0.0, 0.0, sz]), nx, nz, flip=True)
    add_face_grid(np.array([x1, y0, z0]), np.array([0.0, sy, 0.0]), np.array([0.0, 0.0, sz]), ny, nz)
    add_face_grid(np.array([x0, y1, z0]), np.array([sx, 0.0, 0.0]), np.array([0.0, 0.0, sz]), nx, nz)
    add_face_grid(np.array([x0, y0, z0]), np.array([0.0, sy, 0.0]), np.array([0.0, 0.0, sz]), ny, nz, flip=True)


def _add_uv_sphere(vertices, faces, groups, center, radius: float, resolution: int, group: str) -> None:
    """Add a low-poly sphere for sculpt-friendly toe joints."""

    cx, cy, cz = np.asarray(center, dtype=float)
    radius *= SDIV_SPHERE_RADIUS_SCALE
    stacks = max(5, int(resolution * 0.65))
    slices = max(8, int(resolution))
    grid = []
    for i in range(stacks + 1):
        phi = -math.pi / 2 + math.pi * i / stacks
        row = []
        for j in range(slices):
            theta = math.tau * j / slices
            x = cx + math.cos(phi) * math.cos(theta) * radius
            y = cy + math.cos(phi) * math.sin(theta) * radius
            z = cz + math.sin(phi) * radius
            row.append(_append_vertex(vertices, (x, y, z)))
        grid.append(row)

    for i in range(stacks):
        for j in range(slices):
            faces.append((grid[i][j], grid[i][(j + 1) % slices], grid[i + 1][(j + 1) % slices], grid[i + 1][j]))
            groups.append(_group_with_material(group, MATERIAL_JOINT_SPHERE))


def _normalized(vector: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    length = float(np.linalg.norm(vector))
    if length < 0.001:
        return fallback.astype(float)
    return vector / length


def _sdiv_thickness_scale(material: str) -> float:
    if material == MATERIAL_BONE:
        return SDIV_BONE_THICKNESS_SCALE
    if material == MATERIAL_JOINT_SPHERE:
        return SDIV_SPHERE_RADIUS_SCALE
    return SDIV_SOFT_THICKNESS_SCALE


def _sdiv_box_size(size) -> np.ndarray:
    return np.asarray(size, dtype=float) * SDIV_BOX_SIZE_SCALE


def _malleolus_scale(params: FootParams) -> float:
    return max(0.35, float(params.malleolus_size) / 100.0)


def _instep_part_scale(params: FootParams) -> float:
    return max(0.35, float(params.instep_part_thickness) / 100.0)


def _heel_scale(params: FootParams) -> float:
    return max(0.35, float(params.heel_size) / 100.0)


def _group_with_material(group: str, material: str) -> str:
    return f"{group}{MATERIAL_SEPARATOR}{material}"


def _append_vertex(vertices, v) -> int:
    vertices.append((float(v[0]), float(v[1]), float(v[2])))
    return len(vertices)
