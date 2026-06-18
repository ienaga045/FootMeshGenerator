from __future__ import annotations

from pathlib import Path


OBJ_EXPORT_SCALE = 0.004
MATERIAL_SEPARATOR = "__mat:"
DEFAULT_MATERIAL = "soft_tissue"
MATERIAL_DEFS = {
    "joint_sphere": {
        "name": "joint_sphere",
        "ka": (0.44, 0.40, 0.34),
        "kd": (0.66, 0.61, 0.52),
        "ks": (0.18, 0.16, 0.14),
        "ns": 24,
    },
    "bone": {
        "name": "bone",
        "ka": (0.38, 0.22, 0.10),
        "kd": (0.68, 0.42, 0.20),
        "ks": (0.08, 0.06, 0.04),
        "ns": 10,
    },
    "soft_tissue": {
        "name": "soft_tissue",
        "ka": (0.47, 0.32, 0.18),
        "kd": (0.78, 0.55, 0.32),
        "ks": (0.08, 0.06, 0.04),
        "ns": 8,
    },
}


def export_obj(vertices: list[tuple[float, float, float]], faces: list[tuple[int, ...]], groups: list[str], filepath: str | Path, params: object | None = None) -> None:
    """Write vertices, grouped faces, and companion materials to an OBJ file."""

    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    mtl_path = path.with_suffix(".mtl")
    _write_mtl(mtl_path)
    with path.open("w", encoding="utf-8") as f:
        f.write("# Parametric foot base mesh\n")
        f.write(f"# Export scale: {OBJ_EXPORT_SCALE}\n\n")
        f.write(f"mtllib {mtl_path.name}\n\n")
        if params is not None and hasattr(params, "to_dict"):
            f.write("# Parameters\n")
            for key, value in params.to_dict().items():
                f.write(f"#   {key}: {value}\n")
            f.write("\n")
        for x, y, z in vertices:
            f.write(f"v {x * OBJ_EXPORT_SCALE:.5f} {y * OBJ_EXPORT_SCALE:.5f} {z * OBJ_EXPORT_SCALE:.5f}\n")
        f.write("\n")
        current_material = None
        f.write("o foot_base_mesh\n")
        f.write("g foot_base_mesh\n")
        for face, group in zip(faces, groups):
            _, material = _split_group_material(group)
            if material != current_material:
                f.write(f"usemtl {material}\n")
                current_material = material
            f.write("f " + " ".join(str(i) for i in face) + "\n")


def _split_group_material(group: str) -> tuple[str, str]:
    if MATERIAL_SEPARATOR in group:
        clean_group, material = group.split(MATERIAL_SEPARATOR, 1)
        if material in MATERIAL_DEFS:
            return clean_group, material
        return clean_group, DEFAULT_MATERIAL
    return group, DEFAULT_MATERIAL


def _write_mtl(path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write("# Materials for parametric foot base mesh\n\n")
        for material in MATERIAL_DEFS.values():
            f.write(f"newmtl {material['name']}\n")
            f.write(_rgb_line("Ka", material["ka"]))
            f.write(_rgb_line("Kd", material["kd"]))
            f.write(_rgb_line("Ks", material["ks"]))
            f.write(f"Ns {material['ns']}\n")
            f.write("d 1.0\n")
            f.write("illum 2\n\n")


def _rgb_line(label: str, values: tuple[float, float, float]) -> str:
    return f"{label} {values[0]:.4f} {values[1]:.4f} {values[2]:.4f}\n"
