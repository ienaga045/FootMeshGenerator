from __future__ import annotations

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


def main() -> None:
    sg.theme("SystemDefault")
    params = get_default_params()
    skeleton = calculate_foot_skeleton(params)
    mesh_cache = None

    layout = [
        [
            sg.Column([[sg.Image(data=_preview_bytes(skeleton, params), key="-PREVIEW-")]], pad=(8, 8)),
            sg.Column(_controls_layout(params), vertical_alignment="top", scrollable=True, size=(430, 620), expand_y=True),
        ],
        [sg.Text("Ready", key="-STATUS-", size=(100, 1), text_color="#36556f")],
    ]
    window = sg.Window("Foot Base Mesh Generator", layout, finalize=True, resizable=True)

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
            elif event == "-MAKE_MODEL-":
                params = _params_from_values(values, params.toe_profile)
                skeleton = calculate_foot_skeleton(params)
                mesh_cache = generate_foot_mesh_from_skeleton(skeleton, params)
                window["-STATUS-"].update(f"モデル作成完了: 頂点 {len(mesh_cache[0])}, 面 {len(mesh_cache[1])}")
            elif event == "-EXPORT_OBJ-":
                params = _params_from_values(values, params.toe_profile)
                skeleton = calculate_foot_skeleton(params)
                if mesh_cache is None:
                    mesh_cache = generate_foot_mesh_from_skeleton(skeleton, params)
                filepath = sg.popup_get_file(
                    "OBJ保存先を選択",
                    save_as=True,
                    default_extension=".obj",
                    file_types=(("OBJ files", "*.obj"),),
                    default_path=str(Path.cwd() / "foot_base_mesh.obj"),
                )
                if filepath:
                    export_obj(*mesh_cache, filepath)
                    window["-STATUS-"].update(f"OBJ出力完了: {filepath}")
        except Exception as exc:
            window["-STATUS-"].update(f"Error: {exc}")
            sg.popup_error("処理に失敗しました", str(exc))

    window.close()


def _controls_layout(params: FootParams) -> list[list[sg.Element]]:
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

    for key, (label, min_value, max_value, resolution) in SLIDER_SPECS.items():
        rows.append([sg.Text(label, size=(14, 1)), sg.Text("", key=f"-VAL_{key}-", size=(6, 1))])
        rows.append(
            [
                sg.Slider(
                    range=(min_value, max_value),
                    default_value=getattr(params, key),
                    resolution=resolution,
                    orientation="h",
                    size=(32, 16),
                    key=key,
                    enable_events=True,
                )
            ]
        )

    preset_buttons = [[sg.Button(name, size=(14, 1)) for name in row] for row in _chunks(list(PRESETS.keys()), 2)]
    rows.extend(
        [
            [sg.HorizontalSeparator()],
            [sg.Text("プリセット", font=("Helvetica", 13, "bold"))],
            *preset_buttons,
            [sg.HorizontalSeparator()],
            [sg.Button("モデル作成", key="-MAKE_MODEL-", button_color=("white", "#2f6f9f")), sg.Button("OBJ出力", key="-EXPORT_OBJ-", button_color=("white", "#3d7f55")), sg.Button("リセット", key="-RESET-")],
        ]
    )
    return rows


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
    data["mesh_resolution"] = int(data["mesh_resolution"])
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


if __name__ == "__main__":
    main()
