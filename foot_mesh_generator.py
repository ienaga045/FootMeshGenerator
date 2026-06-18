from __future__ import annotations

import math

import numpy as np

from foot_params import FootParams


def generate_foot_mesh_from_skeleton(skeleton: dict, params: FootParams) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]], list[str]]:
    """Generate simple overlapping OBJ-ready parts from the shared skeleton."""

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    groups: list[str] = []

    _add_foot_body(vertices, faces, groups, params)
    _add_box_ellipsoid(vertices, faces, groups, (0, -params.foot_length * 0.37, params.heel_width * 0.10), (params.heel_width, params.foot_length * 0.22, params.heel_width * 0.30), params.mesh_resolution, "heel")
    _add_box_ellipsoid(vertices, faces, groups, tuple(skeleton["points"]["instep"]), (params.foot_width * 0.62, params.foot_length * 0.34, params.instep_height * 0.80), params.mesh_resolution, "instep")

    for toe in skeleton["toes"]:
        chain = [toe["base"], toe["mid"], toe["distal"], toe["tip"]]
        radii = [toe["radius"], toe["radius"] * 0.82, toe["radius"] * 0.64, toe["radius"] * 0.36]
        for a, b, ra, rb in zip(chain, chain[1:], radii, radii[1:]):
            _add_tapered_segment(vertices, faces, groups, a, b, ra, rb, max(8, int(params.mesh_resolution)), toe["name"])

    return vertices, faces, groups


def _add_foot_body(vertices, faces, groups, params: FootParams) -> None:
    ny = max(5, int(params.mesh_resolution))
    nx = max(6, int(params.mesh_resolution * 0.8))
    y_min = -params.foot_length * 0.43
    y_max = params.foot_length * 0.66
    center_x = 0.0
    top_indices = []
    bottom_indices = []

    for iy in range(ny + 1):
        t = iy / ny
        y = y_min + (y_max - y_min) * t
        width = _width_at_y(y, params)
        top_z = _height_at_y(y, params)
        bottom_z = _sole_z_at_y(y, params)
        row_top = []
        row_bottom = []
        for ix in range(nx + 1):
            u = ix / nx
            x = center_x + (u - 0.5) * width
            edge = abs(u - 0.5) * 2.0
            rounded_top = bottom_z + (top_z - bottom_z) * math.sqrt(max(0.0, 1.0 - edge * edge * 0.42))
            row_top.append(_append_vertex(vertices, (x, y, rounded_top)))
            row_bottom.append(_append_vertex(vertices, (x, y, bottom_z)))
        top_indices.append(row_top)
        bottom_indices.append(row_bottom)

    for grid, flip in [(top_indices, False), (bottom_indices, True)]:
        for iy in range(ny):
            for ix in range(nx):
                face = (grid[iy][ix], grid[iy][ix + 1], grid[iy + 1][ix + 1], grid[iy + 1][ix])
                if flip:
                    face = tuple(reversed(face))
                faces.append(face)
                groups.append("foot_body")

    for iy in range(ny):
        for ix in [0, nx]:
            face = (bottom_indices[iy][ix], bottom_indices[iy + 1][ix], top_indices[iy + 1][ix], top_indices[iy][ix])
            if ix == nx:
                face = tuple(reversed(face))
            faces.append(face)
            groups.append("foot_body")
    for iy in [0, ny]:
        for ix in range(nx):
            face = (bottom_indices[iy][ix], top_indices[iy][ix], top_indices[iy][ix + 1], bottom_indices[iy][ix + 1])
            if iy == ny:
                face = tuple(reversed(face))
            faces.append(face)
            groups.append("foot_body")


def _width_at_y(y: float, params: FootParams) -> float:
    length = params.foot_length
    heel_y = -length * 0.38
    ball_y = length * 0.46
    toe_y = length * 0.66
    if y < -length * 0.18:
        return np.interp(y, [heel_y, -length * 0.18], [params.heel_width, params.foot_width * 0.72])
    if y < ball_y:
        return np.interp(y, [-length * 0.18, ball_y], [params.foot_width * 0.72, params.foot_width])
    return np.interp(y, [ball_y, toe_y], [params.foot_width, params.foot_width * 0.76])


def _height_at_y(y: float, params: FootParams) -> float:
    length = params.foot_length
    instep_peak = math.exp(-((y - length * 0.03) / (length * 0.30)) ** 2) * params.instep_height
    ball = math.exp(-((y - length * 0.48) / (length * 0.16)) ** 2) * params.instep_height * 0.32
    heel = math.exp(-((y + length * 0.36) / (length * 0.15)) ** 2) * params.heel_width * 0.22
    return max(8.0, instep_peak + ball + heel)


def _sole_z_at_y(y: float, params: FootParams) -> float:
    length = params.foot_length
    arch_bump = math.exp(-((y + length * 0.04) / (length * 0.22)) ** 2) * params.arch_height * 0.26
    return arch_bump


def _add_tapered_segment(vertices, faces, groups, a, b, radius_a: float, radius_b: float, sides: int, group: str) -> None:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    axis = b - a
    length = float(np.linalg.norm(axis))
    if length < 0.001:
        return
    forward = axis / length
    ref = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(forward, ref))) > 0.92:
        ref = np.array([1.0, 0.0, 0.0])
    right = np.cross(forward, ref)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    rings = []
    for center, radius in [(a, radius_a), (b, radius_b)]:
        ring = []
        for i in range(sides):
            ang = math.tau * i / sides
            pos = center + right * math.cos(ang) * radius + up * math.sin(ang) * radius * 0.85
            ring.append(_append_vertex(vertices, pos))
        rings.append(ring)
    for i in range(sides):
        j = (i + 1) % sides
        faces.append((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))
        groups.append(group)
    faces.append(tuple(reversed(rings[0])))
    groups.append(group)
    faces.append(tuple(rings[1]))
    groups.append(group)


def _add_box_ellipsoid(vertices, faces, groups, center, size, resolution: int, group: str) -> None:
    cx, cy, cz = center
    sx, sy, sz = size
    stacks = max(4, int(resolution / 2))
    slices = max(8, int(resolution))
    grid = []
    for i in range(stacks + 1):
        phi = -math.pi / 2 + math.pi * i / stacks
        row = []
        for j in range(slices):
            theta = math.tau * j / slices
            x = cx + math.cos(phi) * math.cos(theta) * sx * 0.5
            y = cy + math.cos(phi) * math.sin(theta) * sy * 0.5
            z = cz + math.sin(phi) * sz * 0.5
            row.append(_append_vertex(vertices, (x, y, z)))
        grid.append(row)
    for i in range(stacks):
        for j in range(slices):
            faces.append((grid[i][j], grid[i][(j + 1) % slices], grid[i + 1][(j + 1) % slices], grid[i + 1][j]))
            groups.append(group)


def _append_vertex(vertices, v) -> int:
    vertices.append((float(v[0]), float(v[1]), float(v[2])))
    return len(vertices)
