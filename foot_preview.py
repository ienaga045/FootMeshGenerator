from __future__ import annotations

import cv2
import numpy as np

from foot_params import FootParams


def draw_foot_preview_cv2(skeleton: dict, params: FootParams, size: tuple[int, int] = (740, 520)) -> np.ndarray:
    """Draw a stick-like OpenCV preview and return a BGR image."""

    width, height = size
    canvas = np.full((height, width, 3), (245, 247, 250), dtype=np.uint8)

    if params.preview_mode == "top":
        _draw_top_view(canvas, skeleton, params, (0, 0, width, height), "Top View")
    elif params.preview_mode == "side":
        _draw_side_view(canvas, skeleton, params, (0, 0, width, height), "Side View")
    else:
        top_h = int(height * 0.62)
        _draw_top_view(canvas, skeleton, params, (0, 0, width, top_h), "Top View")
        cv2.line(canvas, (24, top_h), (width - 24, top_h), (210, 214, 220), 1)
        _draw_side_view(canvas, skeleton, params, (0, top_h, width, height - top_h), "Side View")
    return canvas


def cv2_image_to_png_bytes(image: np.ndarray) -> bytes:
    ok, data = cv2.imencode(".png", image)
    if not ok:
        raise RuntimeError("OpenCV PNG encoding failed")
    return data.tobytes()


def _draw_top_view(canvas: np.ndarray, skeleton: dict, params: FootParams, rect: tuple[int, int, int, int], title: str) -> None:
    x0, y0, w, h = rect
    bounds = _top_bounds(skeleton)

    def p(v):
        return _project_xy(v, bounds, (x0 + 32, y0 + 30, w - 64, h - 58))

    cv2.putText(canvas, title, (x0 + 18, y0 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (62, 72, 86), 1, cv2.LINE_AA)
    outline = np.array([p(v) for v in skeleton["outline"]], dtype=np.int32)
    cv2.polylines(canvas, [outline], True, (182, 202, 216), 2, cv2.LINE_AA)
    cv2.fillPoly(canvas, [outline], (230, 238, 243))

    pts = skeleton["points"]
    _line(canvas, p(pts["heel"]), p(pts["ankle"]))
    _line(canvas, p(pts["heel"]), p(pts["instep"]))
    _line(canvas, p(pts["instep"]), p(pts["big_ball"]))
    _line(canvas, p(pts["instep"]), p(pts["small_ball"]))
    _line(canvas, p(pts["big_ball"]), p(pts["small_ball"]))
    for toe in skeleton["toes"]:
        chain = [toe["base"], toe["mid"], toe["distal"], toe["tip"]]
        toe_line_width = max(2, min(8, int(toe["radius"] * 0.42)))
        for a, b in zip(chain, chain[1:]):
            _line(canvas, p(a), p(b), (70, 92, 112), toe_line_width)
        _line(canvas, p(pts["big_ball" if toe["name"] == "toe_1_big" else "small_ball"]), p(toe["base"]), (92, 112, 130), 2)

    for key in ["ankle", "heel", "instep", "big_ball", "small_ball", "arch"]:
        _joint(canvas, p(pts[key]), 5, (48, 114, 164))
    for toe in skeleton["toes"]:
        joint_radius = max(4, min(10, int(toe["radius"] * params.joint_sphere_scale / 100.0 * 0.45)))
        for key in ["base", "mid", "distal"]:
            _joint(canvas, p(toe[key]), joint_radius, (35, 132, 105))
        _joint(canvas, p(toe["tip"]), max(5, joint_radius), (200, 88, 64))

    label = f"{params.side.upper()}  L:{params.foot_length:.0f}  W:{params.foot_width:.0f}"
    cv2.putText(canvas, label, (x0 + 18, y0 + h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (78, 88, 102), 1, cv2.LINE_AA)


def _draw_side_view(canvas: np.ndarray, skeleton: dict, params: FootParams, rect: tuple[int, int, int, int], title: str) -> None:
    x0, y0, w, h = rect
    bounds = _side_bounds(skeleton, params)

    def p(v):
        return _project_yz(v, bounds, (x0 + 32, y0 + 32, w - 64, h - 60))

    cv2.putText(canvas, title, (x0 + 18, y0 + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (62, 72, 86), 1, cv2.LINE_AA)
    pts = skeleton["points"]
    sole = skeleton.get("side_sole", [])
    upper = [pts["heel"], pts["instep"], pts["ankle"]]
    if len(sole) >= 2:
        cv2.polylines(canvas, [np.array([p(v) for v in sole], dtype=np.int32)], False, (190, 204, 212), 2, cv2.LINE_AA)
    cv2.polylines(canvas, [np.array([p(v) for v in upper], dtype=np.int32)], False, (182, 202, 216), 2, cv2.LINE_AA)

    _line(canvas, p(pts["heel"]), p(pts["instep"]))
    _line(canvas, p(pts["instep"]), p(pts["ankle"]))
    _line(canvas, p(pts["instep"]), p(pts["big_ball"]))
    _line(canvas, p(pts["big_ball"]), p(skeleton["toes"][0]["base"]))
    for toe in skeleton["toes"]:
        chain = [toe["base"], toe["mid"], toe["distal"], toe["tip"]]
        toe_line_width = max(2, min(8, int(toe["radius"] * 0.42)))
        for a, b in zip(chain, chain[1:]):
            _line(canvas, p(a), p(b), (70, 92, 112), toe_line_width)
        joint_radius = max(4, min(10, int(toe["radius"] * params.joint_sphere_scale / 100.0 * 0.45)))
        for key in ["base", "mid", "distal"]:
            _joint(canvas, p(toe[key]), joint_radius, (35, 132, 105))
        _joint(canvas, p(toe["tip"]), max(5, joint_radius), (200, 88, 64))

    for key in ["ankle", "heel", "instep", "arch", "big_ball"]:
        _joint(canvas, p(pts[key]), 5, (48, 114, 164))
    label = f"Instep:{params.instep_height:.0f}  Arch:{params.arch_height:.0f}  Lift:{params.toe_lift:.0f}  Curl:{params.toe_curl:.0f}  Pivot:{params.ankle_pivot_angle:.0f}"
    cv2.putText(canvas, label, (x0 + 18, y0 + h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (78, 88, 102), 1, cv2.LINE_AA)


def _line(canvas, a, b, color=(84, 103, 120), thickness=2):
    cv2.line(canvas, a, b, color, thickness, cv2.LINE_AA)


def _joint(canvas, p, radius, color):
    cv2.circle(canvas, p, radius + 2, (250, 252, 254), -1, cv2.LINE_AA)
    cv2.circle(canvas, p, radius, color, -1, cv2.LINE_AA)


def _top_bounds(skeleton: dict) -> tuple[float, float, float, float]:
    values = list(skeleton["points"].values()) + skeleton["outline"]
    for toe in skeleton["toes"]:
        values.extend([toe["base"], toe["mid"], toe["distal"], toe["tip"]])
    arr = np.array(values)
    return float(arr[:, 0].min()), float(arr[:, 0].max()), float(arr[:, 1].min()), float(arr[:, 1].max())


def _side_bounds(skeleton: dict, params: FootParams) -> tuple[float, float, float, float]:
    values = list(skeleton["points"].values()) + list(skeleton.get("side_sole", []))
    for toe in skeleton["toes"]:
        values.extend([toe["base"], toe["mid"], toe["distal"], toe["tip"]])
    arr = np.array(values)
    return float(arr[:, 1].min()), float(arr[:, 1].max()), -8.0, max(float(arr[:, 2].max()), params.instep_height) + 16.0


def _project_xy(v, bounds, rect):
    min_x, max_x, min_y, max_y = bounds
    x0, y0, w, h = rect
    scale = min(w / max(max_x - min_x, 1.0), h / max(max_y - min_y, 1.0))
    cx = x0 + w / 2.0
    cy = y0 + h / 2.0
    mx = (min_x + max_x) / 2.0
    my = (min_y + max_y) / 2.0
    return int(cx + (v[0] - mx) * scale), int(cy - (v[1] - my) * scale)


def _project_yz(v, bounds, rect):
    min_y, max_y, min_z, max_z = bounds
    x0, y0, w, h = rect
    scale = min(w / max(max_y - min_y, 1.0), h / max(max_z - min_z, 1.0))
    cx = x0 + w / 2.0
    cy = y0 + h / 2.0
    my = (min_y + max_y) / 2.0
    mz = (min_z + max_z) / 2.0
    return int(cx + (v[1] - my) * scale), int(cy - (v[2] - mz) * scale)
