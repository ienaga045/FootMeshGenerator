from __future__ import annotations

from pathlib import Path


OBJ_EXPORT_SCALE = 0.004
MATERIAL_SEPARATOR = "__mat:"
DEFAULT_MATERIAL = "soft_tissue"
MATERIAL_VERTEX_COLORS = {
    "soft_tissue": (0.78, 0.55, 0.32),
    "bone": (0.68, 0.42, 0.20),
    "joint_sphere": (0.66, 0.61, 0.52),
}


def export_obj(vertices: list[tuple[float, float, float]], faces: list[tuple[int, ...]], groups: list[str], filepath: str | Path, params: object | None = None) -> None:
    """Write one Nomad/ZBrush-friendly OBJ object with vertex colors."""

    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    vertex_colors = _calculate_vertex_colors(len(vertices), faces, groups)
    with path.open("w", encoding="utf-8") as f:
        f.write("# Parametric foot base mesh\n")
        f.write("# Single object export for Nomad/ZBrush import; colors are written as OBJ vertex colors\n")
        f.write(f"# Export scale: {OBJ_EXPORT_SCALE}\n\n")
        if params is not None and hasattr(params, "to_dict"):
            f.write("# Parameters\n")
            for key, value in params.to_dict().items():
                f.write(f"#   {key}: {value}\n")
            f.write("\n")
        for (x, y, z), (r, g, b) in zip(vertices, vertex_colors):
            f.write(f"v {x * OBJ_EXPORT_SCALE:.5f} {y * OBJ_EXPORT_SCALE:.5f} {z * OBJ_EXPORT_SCALE:.5f} {r:.4f} {g:.4f} {b:.4f}\n")
        f.write("\n")
        f.write("o foot_base_mesh\n")
        f.write("g foot_base_mesh\n")
        for face in faces:
            f.write("f " + " ".join(str(i) for i in face) + "\n")


def _calculate_vertex_colors(vertex_count: int, faces: list[tuple[int, ...]], groups: list[str]) -> list[tuple[float, float, float]]:
    """Average face material colors onto vertices without emitting OBJ material splits."""

    sums = [[0.0, 0.0, 0.0] for _ in range(vertex_count)]
    counts = [0 for _ in range(vertex_count)]
    for face, group in zip(faces, groups):
        color = MATERIAL_VERTEX_COLORS[_material_from_group(group)]
        for vertex_index in face:
            idx = vertex_index - 1
            if 0 <= idx < vertex_count:
                sums[idx][0] += color[0]
                sums[idx][1] += color[1]
                sums[idx][2] += color[2]
                counts[idx] += 1

    default = MATERIAL_VERTEX_COLORS[DEFAULT_MATERIAL]
    colors = []
    for total, count in zip(sums, counts):
        if count:
            colors.append((total[0] / count, total[1] / count, total[2] / count))
        else:
            colors.append(default)
    return colors


def _material_from_group(group: str) -> str:
    if MATERIAL_SEPARATOR in group:
        material = group.split(MATERIAL_SEPARATOR, 1)[1]
        if material in MATERIAL_VERTEX_COLORS:
            return material
    return DEFAULT_MATERIAL
