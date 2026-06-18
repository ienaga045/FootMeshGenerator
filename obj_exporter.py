from __future__ import annotations

from pathlib import Path


OBJ_EXPORT_SCALE = 0.004


def export_obj(vertices: list[tuple[float, float, float]], faces: list[tuple[int, ...]], groups: list[str], filepath: str | Path, params: object | None = None) -> None:
    """Write one Nomad/ZBrush-friendly OBJ object without material splits."""

    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("# Parametric foot base mesh\n")
        f.write("# Single object export for Nomad/ZBrush import\n")
        f.write(f"# Export scale: {OBJ_EXPORT_SCALE}\n\n")
        if params is not None and hasattr(params, "to_dict"):
            f.write("# Parameters\n")
            for key, value in params.to_dict().items():
                f.write(f"#   {key}: {value}\n")
            f.write("\n")
        for x, y, z in vertices:
            f.write(f"v {x * OBJ_EXPORT_SCALE:.5f} {y * OBJ_EXPORT_SCALE:.5f} {z * OBJ_EXPORT_SCALE:.5f}\n")
        f.write("\n")
        f.write("o foot_base_mesh\n")
        f.write("g foot_base_mesh\n")
        for face in faces:
            f.write("f " + " ".join(str(i) for i in face) + "\n")
