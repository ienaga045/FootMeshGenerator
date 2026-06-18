from __future__ import annotations

from dataclasses import asdict, dataclass, replace


@dataclass
class FootParams:
    """GUI, preview, and OBJ generation parameters in millimeter-like units."""

    foot_length: float = 250.0
    foot_width: float = 95.0
    instep_height: float = 48.0
    heel_width: float = 58.0
    arch_height: float = 18.0
    toe_length: float = 42.0
    big_toe_length: float = 48.0
    toe_spread: float = 12.0
    toe_curl: float = 8.0
    toe_lift: float = 6.0
    big_toe_angle: float = 5.0
    ankle_angle: float = 0.0
    mesh_resolution: int = 10
    side: str = "right"
    preview_mode: str = "both"
    toe_profile: str = "standard"

    def copy_with(self, **changes: object) -> "FootParams":
        return replace(self, **changes)

    def to_dict(self) -> dict:
        return asdict(self)


SLIDER_SPECS = {
    "foot_length": ("足長", 180, 320, 1),
    "foot_width": ("足幅", 60, 140, 1),
    "instep_height": ("甲の高さ", 20, 90, 1),
    "heel_width": ("かかとの幅", 35, 95, 1),
    "arch_height": ("土踏まずの高さ", 0, 45, 1),
    "toe_length": ("指の長さ", 25, 75, 1),
    "big_toe_length": ("親指の長さ", 25, 85, 1),
    "toe_spread": ("指の開き", 0, 30, 1),
    "toe_curl": ("指の曲げ", -20, 35, 1),
    "toe_lift": ("指の反り", -15, 30, 1),
    "big_toe_angle": ("親指角度", -25, 25, 1),
    "ankle_angle": ("足首角度", -25, 25, 1),
    "mesh_resolution": ("メッシュ解像度", 6, 20, 1),
}
