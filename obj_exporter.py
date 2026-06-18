from __future__ import annotations

from pathlib import Path


def export_obj(vertices: list[tuple[float, float, float]], faces: list[tuple[int, ...]], groups: list[str], filepath: str | Path) -> None:
    """Write vertices and grouped 1-based faces to an OBJ file."""

    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("# Parametric foot base mesh\n")
        f.write("# Units are millimeter-like modeling units\n\n")
        for x, y, z in vertices:
            f.write(f"v {x:.5f} {y:.5f} {z:.5f}\n")
        f.write("\n")
        current_group = None
        for face, group in zip(faces, groups):
            if group != current_group:
                f.write(f"g {group}\n")
                current_group = group
            f.write("f " + " ".join(str(i) for i in face) + "\n")
