from __future__ import annotations

from datetime import datetime
from pathlib import Path

import PySimpleGUI as sg

from foot_mesh_generator import generate_foot_mesh_from_skeleton
from foot_params import SLIDER_SPECS, FootParams
from foot_preview import cv2_image_to_png_bytes, draw_foot_preview_cv2
from foot_skeleton import calculate_foot_skeleton
from obj_exporter import export_obj
from presets import PRESETS, get_default_params


PARAM_KEYS = list(SLIDER_SPECS.keys())
PREVIEW_OPTIONS = {"上面プレビュー": "top", "側面プレビュー": "side", "両方表示": "both"}
PREVIEW_COLUMN_WIDTH = 790
CONTROL_COLUMN_WIDTH = 560
WINDOW_SIZE = (1380, 760)
APP_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = APP_ROOT / "output"
OBJ_FILE_PREFIX = "foot_base_mesh"
SLIDER_GROUPS = [
    ("基本形状", ["foot_length", "foot_width", "instep_height", "heel_width", "heel_size", "arch_height"]),
    ("長さ", ["toe_length", "big_toe_length"]),
    ("角度", ["toe_spread", "big_toe_angle", "ankle_angle", "ankle_pivot_angle"]),
    ("反り・曲げ", ["toe_curl", "toe_lift"]),
    ("出力形状", ["toe_thickness", "joint_sphere_scale", "malleolus_size", "instep_part_thickness"]),
]


def main() -> None:
    sg.theme("SystemDefault")
    params = get_default_params()
    skeleton = calculate_foot_skeleton(params)
    mesh_cache = None
    output_dir = _ensure_output_dir()

    layout = [
        [
            sg.Column(
                [
                    [sg.Image(data=_preview_bytes(skeleton, params), key="-PREVIEW-")],
                    [sg.HorizontalSeparator()],
                    *(_bottom_actions_layout(output_dir)),
                ],
                pad=(8, 8),
                size=(PREVIEW_COLUMN_WIDTH, 680),
                vertical_alignment="top",
            ),
            sg.Column(
                _slider_controls_layout(params),
                vertical_alignment="top",
                size=(CONTROL_COLUMN_WIDTH, 680),
                pad=(4, 8),
            ),
        ],
        [sg.Text("Ready", key="-STATUS-", size=(100, 1), text_color="#36556f")],
    ]
    window = sg.Window("Foot Base Mesh Generator", layout, finalize=True, resizable=True, size=WINDOW_SIZE)
    _bring_window_to_front(window)

    while True:
        event, values = window.read(timeout=80)
        if event in (sg.WIN_CLOSED, "Exit"):
            break

        try:
            if event in PRESETS:
                params = _merge_preserve_choices(PRESETS[event], values)
                _apply_params_to_window(window, params)
                skeleton = calculate_foot_skeleton(params)
                mesh_cache = None
                _update_preview(window, skeleton, params)
                window["-STATUS-"].update(f"{event} を適用しました")
            elif event == "-RESET-":
                params = get_default_params()
                _apply_params_to_window(window, params)
                skeleton = calculate_foot_skeleton(params)
                mesh_cache = None
                _update_preview(window, skeleton, params)
                window["-STATUS-"].update("リセットしました")
            elif event in PARAM_KEYS or event in ("-SIDE_RIGHT-", "-SIDE_LEFT-", "-PREVIEW_MODE-"):
                params = _params_from_values(values, params.toe_profile)
                skeleton = calculate_foot_skeleton(params)
                mesh_cache = None
                _update_preview(window, skeleton, params)
            elif event == "-EXPORT_OBJ-":
                params = _params_from_values(values, params.toe_profile)
                skeleton = calculate_foot_skeleton(params)
                mesh_cache = generate_foot_mesh_from_skeleton(skeleton, params)
                filepath = _next_output_path(output_dir)
                export_obj(*mesh_cache, filepath, params=params)
                window["-LAST_SAVE-"].update(f"前回保存: {filepath.name}")
                window["-STATUS-"].update(f"OBJ作成・保存完了: 頂点 {len(mesh_cache[0])}, 面 {len(mesh_cache[1])} / {filepath}")
        except Exception as exc:
            window["-STATUS-"].update(f"Error: {exc}")
            sg.popup_error("処理に失敗しました", str(exc))

    window.close()


def _bring_window_to_front(window: sg.Window) -> None:
    """Nudge Tk to show the window in front when launched from a macOS app bundle."""

    try:
        root = window.TKroot
        root.lift()
        root.attributes("-topmost", True)
        root.after(700, lambda: root.attributes("-topmost", False))
        root.focus_force()
    except Exception:
        pass


def _slider_controls_layout(params: FootParams) -> list[list[sg.Element]]:
    rows = [
        [sg.Text("足タイプ", font=("Helvetica", 13, "bold"))],
        [
            sg.Radio("右足", "SIDE", key="-SIDE_RIGHT-", default=params.side == "right", enable_events=True),
            sg.Radio("左足", "SIDE", key="-SIDE_LEFT-", default=params.side == "left", enable_events=True),
        ],
        [
            sg.Combo(
                list(PREVIEW_OPTIONS.keys()),
                default_value="両方表示",
                readonly=True,
                key="-PREVIEW_MODE-",
                enable_events=True,
                size=(18, 1),
            )
        ],
        [sg.HorizontalSeparator()],
    ]

    for group_title, keys in SLIDER_GROUPS:
        rows.append([sg.Text(group_title, font=("Helvetica", 11, "bold"), pad=(5, (4, 0)))])
        slider_cells = [_slider_cell(params, key) for key in keys]
        for left, right in _pairs(slider_cells):
            rows.append([left, right if right is not None else sg.Text("", size=(24, 1))])
        rows.append([sg.HorizontalSeparator(pad=(5, 2))])

    return rows


def _slider_cell(params: FootParams, key: str) -> sg.Column:
    label, min_value, max_value, resolution = SLIDER_SPECS[key]
    return sg.Column(
        [
            [sg.Text(label, size=(12, 1), pad=(0, 0)), sg.Text("", key=f"-VAL_{key}-", size=(5, 1), justification="right", pad=(0, 0))],
            [
                sg.Slider(
                    range=(min_value, max_value),
                    default_value=getattr(params, key),
                    resolution=resolution,
                    orientation="h",
                    size=(19, 10),
                    key=key,
                    enable_events=True,
                    pad=(0, 0),
                )
            ],
        ],
        pad=(5, 1),
        vertical_alignment="top",
    )


def _bottom_actions_layout(output_dir: Path) -> list[list[sg.Element]]:
    preset_rows = [[sg.Button(name, size=(12, 1), pad=(2, 1)) for name in row] for row in _chunks(list(PRESETS.keys()), 4)]
    return [
        [sg.Text("プリセット", font=("Helvetica", 12, "bold"), pad=(2, 2))],
        *preset_rows,
        [
            sg.Button("OBJ作成・保存", key="-EXPORT_OBJ-", size=(16, 1), button_color=("white", "#3d7f55"), pad=(2, 3)),
            sg.Button("リセット", key="-RESET-", size=(12, 1), pad=(2, 3)),
        ],
        [sg.Text(f"保存先: {output_dir}", key="-OUTPUT_DIR-", size=(100, 1), text_color="#36556f", pad=(2, (2, 0)))],
        [sg.Text("前回保存: なし", key="-LAST_SAVE-", size=(100, 1), text_color="#36556f", pad=(2, 0))],
    ]


def _preview_bytes(skeleton: dict, params: FootParams) -> bytes:
    return cv2_image_to_png_bytes(draw_foot_preview_cv2(skeleton, params))


def _update_preview(window: sg.Window, skeleton: dict, params: FootParams) -> None:
    window["-PREVIEW-"].update(data=_preview_bytes(skeleton, params))
    for key in PARAM_KEYS:
        value = getattr(params, key)
        window[f"-VAL_{key}-"].update(f"{value:.0f}")


def _params_from_values(values: dict, toe_profile: str = "standard") -> FootParams:
    preview_label = values.get("-PREVIEW_MODE-", "両方表示")
    side = "left" if values.get("-SIDE_LEFT-") else "right"
    data = {key: float(values[key]) for key in PARAM_KEYS}
    data["side"] = side
    data["preview_mode"] = PREVIEW_OPTIONS.get(preview_label, "both")
    data["toe_profile"] = toe_profile
    return FootParams(**data)


def _merge_preserve_choices(preset: FootParams, values: dict) -> FootParams:
    side = "left" if values.get("-SIDE_LEFT-") else "right"
    preview_label = values.get("-PREVIEW_MODE-", "両方表示")
    return preset.copy_with(side=side, preview_mode=PREVIEW_OPTIONS.get(preview_label, "both"))


def _apply_params_to_window(window: sg.Window, params: FootParams) -> None:
    for key in PARAM_KEYS:
        window[key].update(getattr(params, key))
    window["-SIDE_RIGHT-"].update(params.side == "right")
    window["-SIDE_LEFT-"].update(params.side == "left")
    label = next((k for k, v in PREVIEW_OPTIONS.items() if v == params.preview_mode), "両方表示")
    window["-PREVIEW_MODE-"].update(label)
    _update_preview(window, calculate_foot_skeleton(params), params)


def _chunks(items: list[str], size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _pairs(items: list[sg.Element]):
    for i in range(0, len(items), 2):
        right = items[i + 1] if i + 1 < len(items) else None
        yield items[i], right


def _ensure_output_dir() -> Path:
    """Create the app-local output directory used for automatic OBJ saves."""

    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_OUTPUT_DIR


def _next_output_path(output_dir: Path) -> Path:
    """Return a timestamped OBJ path without overwriting existing files."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = output_dir / f"{OBJ_FILE_PREFIX}_{timestamp}.obj"
    if not path.exists():
        return path
    for index in range(1, 1000):
        candidate = output_dir / f"{OBJ_FILE_PREFIX}_{timestamp}_{index:03d}.obj"
        if not candidate.exists():
            return candidate
    raise RuntimeError("保存ファイル名を作成できませんでした")


if __name__ == "__main__":
    main()
