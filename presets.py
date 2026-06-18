from __future__ import annotations

from foot_params import FootParams


PRESETS = {
    "標準プリセット": FootParams(toe_profile="standard"),
    "幅広プリセット": FootParams(foot_width=118, heel_width=68, toe_spread=18, toe_profile="standard"),
    "甲高プリセット": FootParams(instep_height=68, arch_height=24, toe_profile="standard"),
    "扁平足気味プリセット": FootParams(arch_height=6, instep_height=42, toe_profile="standard"),
    "指長めプリセット": FootParams(toe_length=58, big_toe_length=62, toe_profile="standard"),
    "エジプト型": FootParams(big_toe_length=62, toe_length=50, big_toe_angle=4, toe_profile="egyptian"),
    "ギリシャ型": FootParams(big_toe_length=44, toe_length=58, big_toe_angle=2, toe_profile="greek"),
    "スクエア型": FootParams(big_toe_length=55, toe_length=54, toe_spread=8, toe_profile="square"),
}


def get_default_params() -> FootParams:
    return PRESETS["標準プリセット"].copy_with()
