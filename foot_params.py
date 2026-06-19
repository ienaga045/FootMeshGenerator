from __future__ import annotations

from dataclasses import asdict, dataclass, replace


@dataclass
class FootParams:
    """GUI, preview, and OBJ generation parameters in millimeter-like units."""

    foot_length: float = 250.0
    foot_width: float = 95.0
    instep_height: float = 48.0
    heel_width: float = 58.0
    heel_size: float = 100.0
    arch_height: float = 18.0
    toe_length: float = 42.0
    big_toe_length: float = 48.0
    toe_thickness: float = 100.0
    joint_sphere_scale: float = 100.0
    malleolus_size: float = 100.0
    instep_part_thickness: float = 100.0
    plantar_support_length: float = 55.0
    plantar_support_thickness: float = 45.0
    toe_box_width: float = 96.0
    toe_box_height: float = 32.0
    toe_box_roundness: float = 55.0
    toe_box_lift: float = 6.0
    sole_thickness: float = 8.0
    heel_height: float = 0.0
    vamp_volume: float = 100.0
    toe_spread: float = 12.0
    toe_curl: float = 8.0
    toe_lift: float = 6.0
    big_toe_angle: float = 5.0
    ankle_angle: float = 0.0
    ankle_pivot_angle: float = 0.0
    mesh_resolution: int = 10
    side: str = "right"
    preview_mode: str = "both"
    foot_mode: str = "barefoot"
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
    "heel_size": ("かかとの大きさ", 50, 220, 5),
    "arch_height": ("土踏まずの高さ", 0, 45, 1),
    "toe_length": ("指の長さ", 25, 75, 1),
    "big_toe_length": ("親指の長さ", 25, 85, 1),
    "toe_thickness": ("指の太さ", 50, 180, 5),
    "joint_sphere_scale": ("球体の大きさ", 50, 180, 5),
    "malleolus_size": ("くるぶしの大きさ", 50, 220, 5),
    "instep_part_thickness": ("甲パーツ厚み", 60, 240, 5),
    "plantar_support_length": ("足裏芯の長さ", 20, 120, 5),
    "plantar_support_thickness": ("足裏芯の太さ", 20, 130, 5),
    "toe_box_width": ("つま先幅", 50, 150, 1),
    "toe_box_height": ("つま先高さ", 12, 70, 1),
    "toe_box_roundness": ("つま先丸み", 0, 100, 5),
    "toe_box_lift": ("つま先反り", -10, 35, 1),
    "sole_thickness": ("靴底厚み", 0, 35, 1),
    "heel_height": ("かかと高さ", 0, 55, 1),
    "vamp_volume": ("甲の盛り", 60, 180, 5),
    "toe_spread": ("指の開き", 0, 30, 1),
    "toe_curl": ("指の曲げ", -20, 35, 1),
    "toe_lift": ("指の反り", -45, 30, 1),
    "big_toe_angle": ("親指角度", -25, 25, 1),
    "ankle_angle": ("足首角度", -25, 25, 1),
    "ankle_pivot_angle": ("くるぶし回転", -20, 65, 1),
}
