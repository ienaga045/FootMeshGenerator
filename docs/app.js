const OBJ_EXPORT_SCALE = 0.004;
const TOE_NAMES = ["toe_1_big", "toe_2", "toe_3", "toe_4", "toe_5"];
const MATERIAL_SEPARATOR = "__mat:";
const MATERIAL_COLORS = {
  soft_tissue: [0.78, 0.55, 0.32],
  bone: [0.68, 0.42, 0.20],
  joint_sphere: [0.66, 0.61, 0.52],
};

const DEFAULT_PARAMS = {
  foot_length: 250,
  foot_width: 95,
  instep_height: 48,
  heel_width: 58,
  heel_size: 100,
  arch_height: 18,
  toe_length: 42,
  big_toe_length: 48,
  toe_thickness: 100,
  joint_sphere_scale: 100,
  malleolus_size: 100,
  instep_part_thickness: 100,
  plantar_support_length: 55,
  plantar_support_thickness: 45,
  toe_box_width: 96,
  toe_box_height: 32,
  toe_box_roundness: 55,
  toe_box_lift: 6,
  sole_thickness: 8,
  heel_height: 0,
  vamp_volume: 100,
  toe_spread: 12,
  toe_curl: 8,
  toe_lift: 6,
  big_toe_angle: 5,
  ankle_angle: 0,
  ankle_pivot_angle: 0,
  mesh_resolution: 10,
  side: "right",
  preview_mode: "both",
  foot_mode: "barefoot",
  toe_profile: "standard",
};

const SLIDER_SPECS = {
  foot_length: ["足長", 180, 320, 1],
  foot_width: ["足幅", 60, 140, 1],
  instep_height: ["甲の高さ", 20, 90, 1],
  heel_width: ["かかとの幅", 35, 95, 1],
  heel_size: ["かかとの大きさ", 50, 220, 5],
  arch_height: ["土踏まずの高さ", 0, 45, 1],
  toe_length: ["指の長さ", 25, 75, 1],
  big_toe_length: ["親指の長さ", 25, 85, 1],
  toe_thickness: ["指の太さ", 50, 180, 5],
  joint_sphere_scale: ["球体の大きさ", 50, 180, 5],
  malleolus_size: ["くるぶしの大きさ", 50, 220, 5],
  instep_part_thickness: ["甲パーツ厚み", 60, 240, 5],
  plantar_support_length: ["足裏芯の長さ", 20, 120, 5],
  plantar_support_thickness: ["足裏芯の太さ", 20, 130, 5],
  toe_box_width: ["つま先幅", 50, 150, 1],
  toe_box_height: ["つま先高さ", 12, 70, 1],
  toe_box_roundness: ["つま先丸み", 0, 100, 5],
  toe_box_lift: ["つま先反り", -10, 35, 1],
  sole_thickness: ["靴底厚み", 0, 35, 1],
  heel_height: ["かかと高さ", 0, 55, 1],
  vamp_volume: ["甲の盛り", 60, 180, 5],
  toe_spread: ["指の開き", 0, 30, 1],
  toe_curl: ["指の曲げ", -20, 35, 1],
  toe_lift: ["指の反り", -45, 30, 1],
  big_toe_angle: ["親指角度", -25, 25, 1],
  ankle_angle: ["足首角度", -25, 25, 1],
  ankle_pivot_angle: ["くるぶし回転", -20, 65, 1],
};

const SLIDER_GROUPS = [
  ["basic", "基本形状", ["foot_length", "foot_width", "instep_height", "heel_width", "heel_size", "arch_height"], "both"],
  ["shoe", "靴用", ["toe_box_width", "toe_box_height", "toe_box_roundness", "toe_box_lift", "sole_thickness", "heel_height", "vamp_volume"], "shoe"],
  ["toeLength", "足指長さ", ["toe_length", "big_toe_length"], "barefoot"],
  ["toeAngle", "足指角度", ["toe_spread", "big_toe_angle"], "barefoot"],
  ["ankle", "足首", ["ankle_angle", "ankle_pivot_angle"], "both"],
  ["toePose", "足指反り・曲げ", ["toe_curl", "toe_lift"], "barefoot"],
  ["output", "出力形状", ["toe_thickness", "joint_sphere_scale", "malleolus_size", "instep_part_thickness"], "both"],
  ["sole", "足裏", ["plantar_support_length", "plantar_support_thickness"], "both"],
];

const PRESETS = {
  標準: { toe_profile: "standard" },
  幅広: { foot_width: 118, heel_width: 68, toe_spread: 18, toe_profile: "standard" },
  甲高: { instep_height: 68, arch_height: 24, toe_profile: "standard" },
  扁平足気味: { arch_height: 6, instep_height: 42, toe_profile: "standard" },
  指長め: { toe_length: 58, big_toe_length: 62, toe_profile: "standard" },
  エジプト型: { big_toe_length: 62, toe_length: 50, big_toe_angle: 4, toe_profile: "egyptian" },
  ギリシャ型: { big_toe_length: 44, toe_length: 58, big_toe_angle: 2, toe_profile: "greek" },
  スクエア型: { big_toe_length: 55, toe_length: 54, toe_spread: 8, toe_profile: "square" },
};

let params = loadParams();

const canvas = document.getElementById("preview");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("status");
const sliderGroupsEl = document.getElementById("sliderGroups");

init();

function init() {
  buildPresetButtons();
  buildSliders();
  bindStaticControls();
  applyParamsToControls();
  render();
}

function buildPresetButtons() {
  const target = document.getElementById("presetButtons");
  for (const [label, preset] of Object.entries(PRESETS)) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", () => {
      params = { ...DEFAULT_PARAMS, ...preset, side: params.side, preview_mode: params.preview_mode, foot_mode: params.foot_mode };
      applyParamsToControls();
      render(`${label}を適用しました`);
    });
    target.append(button);
  }
}

function buildSliders() {
  for (const [groupId, title, keys, mode] of SLIDER_GROUPS) {
    const group = document.createElement("section");
    group.className = "slider-group";
    group.dataset.mode = mode;
    group.id = `group-${groupId}`;

    const heading = document.createElement("h2");
    heading.textContent = title;
    group.append(heading);

    for (const key of keys) {
      const [label, min, max, step] = SLIDER_SPECS[key];
      const row = document.createElement("label");
      row.className = "slider-row";
      row.innerHTML = `
        <span class="slider-label"><span>${label}</span><output id="out-${key}"></output></span>
        <input id="slider-${key}" type="range" min="${min}" max="${max}" step="${step}">
      `;
      const input = row.querySelector("input");
      input.addEventListener("input", () => {
        params[key] = Number(input.value);
        document.getElementById(`out-${key}`).value = String(Math.round(params[key]));
        render();
      });
      group.append(row);
    }
    sliderGroupsEl.append(group);
  }
}

function bindStaticControls() {
  for (const radio of document.querySelectorAll('input[name="footMode"]')) {
    radio.addEventListener("change", () => {
      params.foot_mode = radio.value;
      updateModeVisibility();
      render();
    });
  }
  for (const radio of document.querySelectorAll('input[name="side"]')) {
    radio.addEventListener("change", () => {
      params.side = radio.value;
      render();
    });
  }
  document.getElementById("previewMode").addEventListener("change", (event) => {
    params.preview_mode = event.target.value;
    render();
  });
  document.getElementById("resetParams").addEventListener("click", () => {
    params = { ...DEFAULT_PARAMS };
    applyParamsToControls();
    render("リセットしました");
  });
  document.getElementById("downloadObj").addEventListener("click", () => {
    const skeleton = calculateFootSkeleton(params);
    const mesh = generateFootMeshFromSkeleton(skeleton, params);
    const obj = exportObj(mesh.vertices, mesh.faces, mesh.groups, params);
    const filename = `foot_base_mesh_${timestamp()}.obj`;
    downloadText(obj, filename);
    render(`OBJを作成しました: ${filename}`);
  });
}

function applyParamsToControls() {
  for (const key of Object.keys(SLIDER_SPECS)) {
    const input = document.getElementById(`slider-${key}`);
    const output = document.getElementById(`out-${key}`);
    input.value = String(params[key]);
    output.value = String(Math.round(params[key]));
  }
  document.querySelector(`input[name="footMode"][value="${params.foot_mode}"]`).checked = true;
  document.querySelector(`input[name="side"][value="${params.side}"]`).checked = true;
  document.getElementById("previewMode").value = params.preview_mode;
  updateModeVisibility();
}

function updateModeVisibility() {
  for (const group of sliderGroupsEl.querySelectorAll(".slider-group")) {
    const mode = group.dataset.mode;
    group.classList.toggle("is-hidden", !(mode === "both" || mode === params.foot_mode));
  }
}

function render(message = "Ready") {
  const skeleton = calculateFootSkeleton(params);
  drawPreview(ctx, canvas, skeleton, params);
  statusEl.textContent = message;
  localStorage.setItem("footBaseMeshWebParams", JSON.stringify(params));
}

function loadParams() {
  try {
    const saved = JSON.parse(localStorage.getItem("footBaseMeshWebParams") || "{}");
    return { ...DEFAULT_PARAMS, ...saved };
  } catch {
    return { ...DEFAULT_PARAMS };
  }
}

function calculateFootSkeleton(p) {
  const length = p.foot_length;
  const width = p.foot_width;
  const heelScale = Math.max(0.35, p.heel_size / 100);
  const toeBaseY = length * 0.62;
  const ballY = length * 0.5;
  const heelY = -length * 0.42;
  const ankleY = -length * 0.52;
  const ankleAngle = deg(p.ankle_angle);

  let ankle = v(0, ankleY, p.instep_height + 18 + Math.sin(ankleAngle) * 18);
  let heel = v(0, heelY, p.heel_width * 0.08 * heelScale);
  let instep = v(0, length * 0.05, p.instep_height);
  let arch = v(mirrorX(-width * 0.18, p), -length * 0.05, p.arch_height);
  const bigBall = v(mirrorX(-width * 0.36, p), ballY, p.instep_height * 0.35);
  const smallBall = v(mirrorX(width * 0.4, p), ballY * 0.98, p.instep_height * 0.28);
  const pivot = v(0, ballY, p.instep_height * 0.2);

  ankle = pitchForTiptoe(ankle, pivot, p.ankle_pivot_angle);
  heel = pitchForTiptoe(heel, pivot, p.ankle_pivot_angle);
  instep = pitchForTiptoe(instep, pivot, p.ankle_pivot_angle);
  arch = pitchForTiptoe(arch, pivot, p.ankle_pivot_angle);

  const toes = [];
  const toeLengths = toeLengthsFor(p);
  let toeBox = null;
  if (p.foot_mode === "shoe") {
    toeBox = calculateToeBox(p, ballY, toeBaseY);
  } else {
    const baseXs = [-0.37, -0.18, 0, 0.18, 0.36].map((x) => x * width);
    const baseZs = [0.31, 0.28, 0.26, 0.24, 0.22].map((z) => z * p.instep_height);
    const fanOffsets = [-1, -0.4, 0.05, 0.45, 0.95].map((x) => x * p.toe_spread);
    for (let i = 0; i < TOE_NAMES.length; i++) {
      const base = v(mirrorX(baseXs[i], p), toeBaseY - Math.abs(baseXs[i]) * 0.08, baseZs[i]);
      let lateralAngle = fanOffsets[i] + (i === 0 ? p.big_toe_angle : 0);
      if (p.side === "left") lateralAngle *= -1;
      const lateral = deg(lateralAngle);
      const curl = deg(p.toe_curl);
      const lift = deg(p.toe_lift);
      const totalLen = toeLengths[i];
      const seg1Len = totalLen * 0.44;
      const seg2Len = totalLen * 0.34;
      const seg3Len = totalLen * 0.22;
      const curlSteps = [0, -curl * 0.78, -curl * 1.55];
      const liftSteps = [lift, lift + curlSteps[1], lift + curlSteps[2]];
      const mid = add(base, mul(toeDirection(lateral, liftSteps[0]), seg1Len));
      const distal = add(mid, mul(toeDirection(lateral, liftSteps[1]), seg2Len));
      const tip = add(distal, mul(toeDirection(lateral, liftSteps[2]), seg3Len));
      const radius = Math.max(6, width * (i === 0 ? 0.085 : 0.065 - i * 0.004)) * (p.toe_thickness / 100);
      toes.push({ name: TOE_NAMES[i], base, mid, distal, tip, length: totalLen, radius });
    }
  }

  let outline = toeBox ? calculateShoeOutline(p, heelY, toeBox) : calculateOutline(p, toeBaseY, heelY);
  outline = outline.map((point) => (point.y < ballY ? pitchForTiptoe(point, pivot, p.ankle_pivot_angle) : point));
  let sideSole = calculateSideSole(p, heelY, ballY, toeBox);
  sideSole = sideSole.map((point) => (point.y < ballY ? pitchForTiptoe(point, pivot, p.ankle_pivot_angle) : point));

  return {
    points: { ankle, heel, instep, arch, big_ball: bigBall, small_ball: smallBall },
    toes,
    toe_box: toeBox,
    outline,
    side_sole: sideSole,
    toe_lengths: toeLengths,
  };
}

function calculateToeBox(p, ballY, toeBaseY) {
  const length = p.foot_length;
  const roundness = clamp(p.toe_box_roundness / 100, 0, 1);
  const sole = Math.max(0, p.sole_thickness);
  const vampScale = Math.max(0.55, p.vamp_volume / 100);
  const width = Math.max(p.toe_box_width, p.foot_width * 0.58);
  const height = Math.max(8, p.toe_box_height);
  const backY = ballY + length * 0.025;
  const shoulderY = toeBaseY + length * 0.025;
  const frontY = length * (0.715 + 0.018 * roundness);
  const noseY = length * (0.735 + 0.04 * roundness);
  const backHalf = Math.max(p.foot_width * 0.5, width * 0.5);
  const shoulderHalf = width * 0.52;
  const frontHalf = width * (0.42 - 0.08 * roundness);
  const noseHalf = width * (0.16 + 0.16 * (1 - roundness));
  const baseZ = Math.max(0, sole * 0.2);
  const lift = p.toe_box_lift;
  const stations = [
    { y: backY, half_width: backHalf, bottom_z: baseZ, top_z: baseZ + Math.max(height * 1.06, p.instep_height * 0.42 * vampScale) },
    { y: shoulderY, half_width: shoulderHalf, bottom_z: baseZ + Math.max(0, lift) * 0.1, top_z: baseZ + height * 1.08 + Math.max(0, lift) * 0.18 },
    { y: frontY, half_width: frontHalf, bottom_z: baseZ + lift * 0.35, top_z: baseZ + height * 0.86 + lift * 0.52 },
    { y: noseY, half_width: noseHalf, bottom_z: baseZ + lift * 0.7, top_z: baseZ + height * 0.58 + lift },
  ];
  for (const station of stations) {
    station.bottom_z = Math.max(-sole * 0.35, station.bottom_z);
    station.top_z = Math.max(station.bottom_z + height * 0.42, station.top_z);
  }
  const specs = [
    [-backHalf, backY],
    [-shoulderHalf, shoulderY],
    [-frontHalf, frontY],
    [-noseHalf, noseY],
    [0, noseY + length * 0.012 * roundness],
    [noseHalf, noseY],
    [frontHalf, frontY],
    [shoulderHalf, shoulderY],
    [backHalf, backY],
  ];
  return {
    back_center: v(0, backY, stations[0].top_z * 0.45),
    front_center: v(0, frontY, stations[2].top_z * 0.48),
    nose: v(0, noseY, stations[3].top_z * 0.45),
    top_outline: specs.map(([x, y]) => v(mirrorX(x, p), y, 0)),
    side_profile: [
      v(0, stations[0].y, stations[0].bottom_z),
      v(0, stations[1].y, stations[1].bottom_z),
      v(0, stations[2].y, stations[2].bottom_z),
      v(0, stations[3].y, stations[3].bottom_z),
      v(0, stations[3].y, stations[3].top_z),
      v(0, stations[2].y, stations[2].top_z),
      v(0, stations[1].y, stations[1].top_z),
      v(0, stations[0].y, stations[0].top_z),
    ],
    stations,
    roundness,
    width,
    height,
    sole_thickness: sole,
  };
}

function calculateOutline(p, toeBaseY, heelY) {
  const width = p.foot_width;
  const length = p.foot_length;
  const heelScale = Math.max(0.35, p.heel_size / 100);
  const half = width * 0.5;
  const heelHalf = p.heel_width * 0.46 * heelScale;
  const heelBackY = heelY - p.heel_width * 0.22 * heelScale;
  const heelArc = [];
  for (let i = 0; i < 7; i++) {
    const theta = Math.PI - (Math.PI * i) / 6;
    heelArc.push([Math.cos(theta) * heelHalf, heelY - Math.sin(theta) * (heelY - heelBackY)]);
  }
  const pts = [
    [-half * 0.62 * (0.95 + heelScale * 0.05), -length * 0.25],
    [-half * 0.82, length * 0.08],
    [-half * 0.7, length * 0.36],
    [-half * 0.48, toeBaseY],
    [-half * 0.12, length * 0.72],
    [half * 0.2, length * 0.72],
    [half * 0.52, toeBaseY],
    [half * 0.76, length * 0.34],
    [half * 0.72, length * 0.04],
    [half * 0.56 * (0.95 + heelScale * 0.05), -length * 0.25],
    ...heelArc.reverse(),
  ];
  return pts.map(([x, y]) => v(mirrorX(x, p), y, 0));
}

function calculateShoeOutline(p, heelY, toeBox) {
  const width = p.foot_width;
  const length = p.foot_length;
  const heelScale = Math.max(0.35, p.heel_size / 100);
  const half = width * 0.5;
  const heelHalf = p.heel_width * 0.46 * heelScale;
  const heelBackY = heelY - p.heel_width * 0.22 * heelScale;
  const heelArc = [];
  for (let i = 0; i < 7; i++) {
    const theta = Math.PI - (Math.PI * i) / 6;
    heelArc.push([Math.cos(theta) * heelHalf, heelY - Math.sin(theta) * (heelY - heelBackY)]);
  }
  const s = toeBox.stations;
  const pts = [
    [-half * 0.62 * (0.95 + heelScale * 0.05), -length * 0.25],
    [-half * 0.82, length * 0.08],
    [-half * 0.72, length * 0.34],
    [-s[0].half_width, s[0].y],
    [-s[1].half_width, s[1].y],
    [-s[2].half_width, s[2].y],
    [-s[3].half_width, s[3].y],
    [0, s[3].y + length * 0.012 * toeBox.roundness],
    [s[3].half_width, s[3].y],
    [s[2].half_width, s[2].y],
    [s[1].half_width, s[1].y],
    [s[0].half_width, s[0].y],
    [half * 0.78, length * 0.34],
    [half * 0.72, length * 0.04],
    [half * 0.56 * (0.95 + heelScale * 0.05), -length * 0.25],
    ...heelArc.reverse(),
  ];
  return pts.map(([x, y]) => v(mirrorX(x, p), y, 0));
}

function calculateSideSole(p, heelY, ballY, toeBox) {
  const length = p.foot_length;
  const heelScale = Math.max(0.35, p.heel_size / 100);
  const heelBackY = heelY - p.heel_width * 0.24 * heelScale;
  if (toeBox) {
    const lastStation = toeBox.stations[toeBox.stations.length - 1];
    const toeFrontY = lastStation.y;
    const sole = Math.max(0, p.sole_thickness);
    return [
      v(0, heelBackY, -sole - p.heel_height),
      v(0, heelY + length * 0.06, -sole * 0.7 - p.heel_height * 0.65),
      v(0, -length * 0.08, p.arch_height * 0.14 - sole * 0.42),
      v(0, ballY, 0),
      v(0, toeFrontY, lastStation.bottom_z),
    ];
  }
  return [
    v(0, heelBackY, 0),
    v(0, heelY + length * 0.06, p.arch_height * 0.08),
    v(0, -length * 0.08, p.arch_height * 0.3),
    v(0, ballY, 0),
    v(0, length * 0.7, 0),
  ];
}

function drawPreview(context, canvasEl, skeleton, p) {
  const width = canvasEl.width;
  const height = canvasEl.height;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#fbfaf9";
  context.fillRect(0, 0, width, height);

  if (p.preview_mode === "top") {
    drawTopView(context, skeleton, p, [0, 0, width, height], "Top View");
  } else if (p.preview_mode === "side") {
    drawSideView(context, skeleton, p, [0, 0, width, height], "Side View");
  } else {
    const topH = Math.round(height * 0.62);
    drawTopView(context, skeleton, p, [0, 0, width, topH], "Top View");
    line2d(context, [28, topH], [width - 28, topH], "#d2d6dc", 1);
    drawSideView(context, skeleton, p, [0, topH, width, height - topH], "Side View");
  }
}

function drawTopView(context, skeleton, p, rect, title) {
  const [x0, y0, w, h] = rect;
  const bounds = topBounds(skeleton);
  const project = (point) => projectXY(point, bounds, [x0 + 34, y0 + 34, w - 68, h - 64]);
  titleText(context, title, x0 + 22, y0 + 28);
  fillPolyline(context, skeleton.outline.map(project), "#e8eef3", "#b6cad8", 2);

  const pts = skeleton.points;
  const toeBox = skeleton.toe_box;
  if (toeBox) {
    fillPolyline(context, toeBox.top_outline.map(project), "#dbe8f0", "#5c7c94", 2);
  }
  drawBone(context, project(pts.heel), project(pts.ankle));
  drawBone(context, project(pts.heel), project(pts.instep));
  drawBone(context, project(pts.instep), project(pts.big_ball));
  drawBone(context, project(pts.instep), project(pts.small_ball));
  drawBone(context, project(pts.big_ball), project(pts.small_ball));

  if (toeBox) {
    drawBone(context, project(pts.big_ball), project(toeBox.top_outline[0]), 3);
    drawBone(context, project(pts.small_ball), project(toeBox.top_outline[toeBox.top_outline.length - 1]), 3);
    drawBone(context, project(pts.instep), project(toeBox.back_center), 3);
    drawBone(context, project(toeBox.back_center), project(toeBox.nose), 3);
  }
  for (const toe of skeleton.toes) {
    const chain = [toe.base, toe.mid, toe.distal, toe.tip];
    const thick = clamp(toe.radius * 0.42, 2, 8);
    for (let i = 0; i < chain.length - 1; i++) drawBone(context, project(chain[i]), project(chain[i + 1]), thick);
    drawBone(context, project(toe.name === "toe_1_big" ? pts.big_ball : pts.small_ball), project(toe.base), 2, "#5c7082");
  }

  for (const key of ["ankle", "heel", "instep", "big_ball", "small_ball", "arch"]) {
    joint(context, project(pts[key]), 5, "#3072a4");
  }
  for (const toe of skeleton.toes) {
    const radius = clamp(toe.radius * p.joint_sphere_scale / 100 * 0.45, 4, 10);
    for (const key of ["base", "mid", "distal"]) joint(context, project(toe[key]), radius, "#238469");
    joint(context, project(toe.tip), Math.max(5, radius), "#c85840");
  }
  if (toeBox) {
    for (const point of [toeBox.top_outline[1], toeBox.top_outline[3], toeBox.top_outline[5], toeBox.top_outline[7]]) {
      joint(context, project(point), 4, "#238469");
    }
    joint(context, project(toeBox.nose), 6, "#c85840");
  }
  labelText(context, `${toeBox ? "SHOE" : "BAREFOOT"}  ${p.side.toUpperCase()}  L:${p.foot_length}  W:${p.foot_width}`, x0 + 22, y0 + h - 18);
}

function drawSideView(context, skeleton, p, rect, title) {
  const [x0, y0, w, h] = rect;
  const bounds = sideBounds(skeleton, p);
  const project = (point) => projectYZ(point, bounds, [x0 + 34, y0 + 36, w - 68, h - 68]);
  titleText(context, title, x0 + 22, y0 + 28);
  const pts = skeleton.points;
  const toeBox = skeleton.toe_box;
  if (skeleton.side_sole.length >= 2) polyline(context, skeleton.side_sole.map(project), "#becbd4", 2);
  polyline(context, [pts.heel, pts.instep, pts.ankle].map(project), "#b6cad8", 2);
  if (toeBox) fillPolyline(context, toeBox.side_profile.map(project), "#dbe8f0", "#5c7c94", 2);

  drawBone(context, project(pts.heel), project(pts.instep));
  drawBone(context, project(pts.instep), project(pts.ankle));
  drawBone(context, project(pts.instep), project(pts.big_ball));
  if (toeBox) {
    drawBone(context, project(pts.big_ball), project(toeBox.back_center), 3);
    drawBone(context, project(toeBox.back_center), project(toeBox.front_center), 3);
    drawBone(context, project(toeBox.front_center), project(toeBox.nose), 3);
  } else if (skeleton.toes.length) {
    drawBone(context, project(pts.big_ball), project(skeleton.toes[0].base));
  }

  for (const toe of skeleton.toes) {
    const chain = [toe.base, toe.mid, toe.distal, toe.tip];
    const thick = clamp(toe.radius * 0.42, 2, 8);
    for (let i = 0; i < chain.length - 1; i++) drawBone(context, project(chain[i]), project(chain[i + 1]), thick);
    const radius = clamp(toe.radius * p.joint_sphere_scale / 100 * 0.45, 4, 10);
    for (const key of ["base", "mid", "distal"]) joint(context, project(toe[key]), radius, "#238469");
    joint(context, project(toe.tip), Math.max(5, radius), "#c85840");
  }
  if (toeBox) {
    joint(context, project(toeBox.back_center), 5, "#238469");
    joint(context, project(toeBox.front_center), 5, "#238469");
    joint(context, project(toeBox.nose), 6, "#c85840");
  }
  for (const key of ["ankle", "heel", "instep", "arch", "big_ball"]) joint(context, project(pts[key]), 5, "#3072a4");
  const label = toeBox
    ? `Instep:${p.instep_height}  ToeBox:${p.toe_box_height}  Lift:${p.toe_box_lift}  Sole:${p.sole_thickness}  Pivot:${p.ankle_pivot_angle}`
    : `Instep:${p.instep_height}  Arch:${p.arch_height}  Lift:${p.toe_lift}  Curl:${p.toe_curl}  Pivot:${p.ankle_pivot_angle}`;
  labelText(context, label, x0 + 22, y0 + h - 18);
}

function generateFootMeshFromSkeleton(skeleton, p) {
  const mesh = { vertices: [], faces: [], groups: [] };
  addFootBody(mesh, skeleton, p);
  if (p.foot_mode === "shoe") {
    addShoeSole(mesh, skeleton, p);
    addToeBoxMesh(mesh, skeleton, p);
  } else {
    for (const toe of skeleton.toes) {
      const chain = [toe.base, toe.mid, toe.distal, toe.tip];
      const radii = [toe.radius, toe.radius * 0.82, toe.radius * 0.64, toe.radius * 0.42];
      for (let i = 0; i < chain.length - 1; i++) addBoxSegment(mesh, chain[i], chain[i + 1], Math.min(radii[i], radii[i + 1]) * 2.1, toe.name, "bone");
      for (let i = 0; i < chain.length; i++) addUvSphere(mesh, chain[i], radii[i] * (p.joint_sphere_scale / 100), p.mesh_resolution, toe.name, "joint_sphere");
    }
  }
  return mesh;
}

function addFootBody(mesh, skeleton, p) {
  const pts = skeleton.points;
  const heel = pts.heel;
  const instep = pts.instep;
  const arch = pts.arch;
  const bigBall = pts.big_ball;
  const smallBall = pts.small_ball;
  const midBall = mul(add(bigBall, smallBall), 0.5);
  const heelScale = Math.max(0.35, p.heel_size / 100);
  const instepScale = Math.max(0.35, p.instep_part_thickness / 100);
  const jointScale = p.joint_sphere_scale / 100;

  addBodyShell(mesh, skeleton, p);
  addFleshMasses(mesh, skeleton, p);
  addSideVolumeMasses(mesh, skeleton, p);
  addMidfootFillMasses(mesh, skeleton, p);
  addAnkleAchillesMasses(mesh, skeleton, p);
  addSubdividedBox(
    mesh,
    heel,
    v(p.heel_width * 0.92 * heelScale, p.foot_length * 0.16 * (0.85 + heelScale * 0.15), p.heel_width * 0.24 * heelScale),
    [2, 3, 2],
    "heel",
    "soft_tissue",
  );
  addUvSphere(mesh, heel, p.heel_width * 0.24 * jointScale * heelScale, p.mesh_resolution, "heel", "joint_sphere");
  addUvSphere(mesh, bigBall, p.foot_width * 0.13 * jointScale, p.mesh_resolution, "foot_body", "joint_sphere");
  addUvSphere(mesh, smallBall, p.foot_width * 0.12 * jointScale, p.mesh_resolution, "foot_body", "joint_sphere");
  addBoxSegment(mesh, heel, instep, p.heel_width * 0.24 * instepScale, "instep", "bone");
  addBoxSegment(mesh, heel, arch, p.heel_width * 0.14 * heelScale, "foot_body", "bone");
  addBoxSegment(mesh, arch, bigBall, p.heel_width * 0.12, "foot_body", "bone");
  addBoxSegment(mesh, arch, smallBall, p.heel_width * 0.12, "foot_body", "bone");
  addBoxSegment(mesh, add(heel, v(0, -p.foot_length * 0.03, p.heel_width * 0.25)), add(pts.ankle, v(0, p.foot_length * 0.02, -p.instep_height * 0.12)), p.heel_width * 0.22 * heelScale, "achilles_tendon", "soft_tissue");
  for (const side of [-1, 1]) {
    const malleolus = add(pts.ankle, v(side * p.heel_width * 0.36, p.foot_length * 0.03, -p.instep_height * 0.1));
    addUvSphere(mesh, malleolus, p.heel_width * 0.18 * jointScale * Math.max(0.35, p.malleolus_size / 100), p.mesh_resolution, "ankle_joint", "joint_sphere");
    addBoxSegment(mesh, malleolus, instep, p.heel_width * 0.14 * instepScale, "instep", "bone");
  }
  if (skeleton.toe_box) {
    addBoxSegment(mesh, midBall, skeleton.toe_box.back_center, p.foot_width * 0.18 * instepScale * Math.max(0.7, p.vamp_volume / 100), "toe_box", "soft_tissue");
  } else {
    skeleton.toes.forEach((toe, index) => {
      const root0 = add(instep, mul(sub(toe.base, instep), 0.35));
      const root = v(root0.x, root0.y, Math.max(root0.z, p.instep_height * 0.35));
      const thickness = Math.max(8, toe.radius * (index === 0 ? 1.58 : 1.36)) * instepScale;
      const tendonStart = add(add(instep, mul(sub(toe.base, instep), 0.18)), v(0, 0, p.instep_height * 0.08));
      const tendonEnd = add(toe.base, v(0, -p.foot_length * 0.03, p.instep_height * 0.06));
      addBoxSegment(mesh, root, toe.base, thickness, "foot_body", "bone");
      addBoxSegment(mesh, instep, root, thickness * 0.86, "instep", "bone");
      addBoxSegment(mesh, tendonStart, tendonEnd, Math.max(7.5, thickness * 0.68), "instep", "bone");
    });
    addMetatarsalWebs(mesh, skeleton, p);
  }
}

function addBodyShell(mesh, skeleton, p) {
  const pts = skeleton.points;
  const heel = pts.heel;
  const arch = pts.arch;
  const instep = pts.instep;
  const bigBall = pts.big_ball;
  const smallBall = pts.small_ball;
  const midBall = mul(add(bigBall, smallBall), 0.5);
  const heelScale = Math.max(0.35, p.heel_size / 100);
  const toeRoot = skeleton.toe_box
    ? add(skeleton.toe_box.back_center, v(0, -p.foot_length * 0.035, -p.instep_height * 0.06))
    : add(avg(skeleton.toes.map((toe) => toe.base)), v(0, -p.foot_length * 0.04, -p.instep_height * 0.04));
  const vampScale = p.foot_mode === "shoe" ? Math.max(0.7, p.vamp_volume / 100) : 1;
  const centers = [
    add(heel, v(0, -p.foot_length * 0.04, 0)),
    add(heel, v(0, p.foot_length * 0.06, p.heel_width * 0.04)),
    add(arch, v(0, p.foot_length * 0.02, -p.instep_height * 0.08)),
    add(instep, v(0, p.foot_length * 0.03, -p.instep_height * 0.08)),
    add(mul(add(instep, midBall), 0.5), v(0, -p.foot_length * 0.01, -p.instep_height * 0.1)),
    add(midBall, v(0, -p.foot_length * 0.02, -p.instep_height * 0.12)),
    toeRoot,
  ];
  const widths = [
    p.heel_width * 0.92 * heelScale,
    p.heel_width * 1.08 * heelScale,
    p.foot_width * 0.7,
    p.foot_width * 0.82,
    p.foot_width,
    p.foot_width * 1.1,
    skeleton.toe_box ? Math.max(p.foot_width * 0.96, p.toe_box_width * 0.92) : p.foot_width * 0.96,
  ];
  const topOffsets = [
    p.heel_width * 0.22 * heelScale,
    p.heel_width * 0.26 * heelScale,
    p.instep_height * 0.38,
    p.instep_height * 0.84 * vampScale,
    p.instep_height * 0.58 * vampScale,
    p.instep_height * 0.34 * Math.max(0.85, vampScale),
    p.instep_height * 0.18 * Math.max(0.9, vampScale * 0.94),
  ];
  const bottomOffsets = [
    p.heel_width * 0.16 * heelScale,
    p.heel_width * 0.16 * heelScale,
    p.instep_height * 0.18,
    p.instep_height * 0.16,
    p.instep_height * 0.16,
    p.instep_height * 0.18,
    p.instep_height * 0.16,
  ];
  const profile = densifyProfile(centers, widths, topOffsets, bottomOffsets, 2);
  const xSamples = [-0.5, -0.25, 0, 0.25, 0.5];
  const top = [];
  const bottom = [];
  profile.centers.forEach((center, i) => {
    const width = profile.widths[i] * 1.1;
    const topOffset = profile.topOffsets[i] * 1.14;
    const bottomOffset = profile.bottomOffsets[i] * 1.24;
    const topRow = [];
    const bottomRow = [];
    for (const sample of xSamples) {
      const crown = 1 - Math.abs(sample) * 0.42;
      const sideDrop = Math.abs(sample) * p.instep_height * 0.08;
      topRow.push(addVertex(mesh, v(center.x + sample * width, center.y, center.z + topOffset * crown - sideDrop)));
      bottomRow.push(addVertex(mesh, v(center.x + sample * width, center.y, center.z - bottomOffset)));
    }
    top.push(topRow);
    bottom.push(bottomRow);
  });
  appendGridShell(mesh, top, bottom, "foot_body", "soft_tissue");
}

function densifyProfile(centers, widths, topOffsets, bottomOffsets, steps) {
  const dense = { centers: [], widths: [], topOffsets: [], bottomOffsets: [] };
  for (let i = 0; i < centers.length - 1; i++) {
    for (let step = 0; step < steps; step++) {
      const t = step / steps;
      dense.centers.push(lerpVec(centers[i], centers[i + 1], t));
      dense.widths.push(lerp(widths[i], widths[i + 1], t));
      dense.topOffsets.push(lerp(topOffsets[i], topOffsets[i + 1], t));
      dense.bottomOffsets.push(lerp(bottomOffsets[i], bottomOffsets[i + 1], t));
    }
  }
  dense.centers.push(centers[centers.length - 1]);
  dense.widths.push(widths[widths.length - 1]);
  dense.topOffsets.push(topOffsets[topOffsets.length - 1]);
  dense.bottomOffsets.push(bottomOffsets[bottomOffsets.length - 1]);
  return dense;
}

function addFleshMasses(mesh, skeleton, p) {
  const pts = skeleton.points;
  const heel = pts.heel;
  const instep = pts.instep;
  const arch = pts.arch;
  const bigBall = pts.big_ball;
  const smallBall = pts.small_ball;
  const sideSign = p.side === "right" ? -1 : 1;
  const medial = sideSign;
  const lateral = -sideSign;
  const instepScale = Math.max(0.35, p.instep_part_thickness / 100);
  const heelScale = Math.max(0.35, p.heel_size / 100);
  const forefootCenter = add(mul(add(bigBall, smallBall), 0.5), v(0, p.foot_length * 0.015, -p.instep_height * 0.05));

  if (skeleton.toes.length) {
    for (const toe of skeleton.toes) {
      const bridgeStart = add(forefootCenter, mul(sub(toe.base, forefootCenter), 0.25));
      const bridgeEnd = add(toe.base, v(0, -p.foot_length * 0.025, -p.instep_height * 0.05));
      addBoxSegment(mesh, bridgeStart, bridgeEnd, p.foot_width * 0.1 * instepScale, "foot_body", "soft_tissue");
    }
  } else if (skeleton.toe_box) {
    const back = skeleton.toe_box.back_center;
    const outline = skeleton.toe_box.top_outline;
    const leftBack = v(outline[0].x, outline[0].y, back.z);
    const rightBack = v(outline[outline.length - 1].x, outline[outline.length - 1].y, back.z);
    const bridgeWidth = p.foot_width * 0.16 * instepScale * Math.max(0.85, p.vamp_volume / 100);
    addBoxSegment(mesh, forefootCenter, back, bridgeWidth, "foot_body", "soft_tissue");
    addBoxSegment(mesh, bigBall, leftBack, bridgeWidth * 0.72, "foot_body", "soft_tissue");
    addBoxSegment(mesh, smallBall, rightBack, bridgeWidth * 0.72, "foot_body", "soft_tissue");
  }

  const medialHeel = add(heel, v(medial * p.heel_width * 0.25 * heelScale, p.foot_length * 0.08, p.heel_width * 0.08 * heelScale));
  const medialBall = add(bigBall, v(medial * p.foot_width * 0.08, -p.foot_length * 0.06, -p.instep_height * 0.08));
  const lateralHeel = add(heel, v(lateral * p.heel_width * 0.25 * heelScale, p.foot_length * 0.08, p.heel_width * 0.08 * heelScale));
  const lateralBall = add(smallBall, v(lateral * p.foot_width * 0.08, -p.foot_length * 0.06, -p.instep_height * 0.08));
  addBoxSegment(mesh, medialHeel, medialBall, p.foot_width * 0.13 * instepScale, "foot_body", "soft_tissue");
  addBoxSegment(mesh, lateralHeel, lateralBall, p.foot_width * 0.14 * instepScale, "foot_body", "soft_tissue");

  const archPad = add(arch, v(0, p.foot_length * 0.05, p.arch_height * 0.16));
  const heelAnchor = add(heel, v(0, p.foot_length * 0.03, p.heel_width * 0.06 * heelScale));
  addBoxSegment(mesh, heelAnchor, archPad, p.foot_width * 0.11 * instepScale * Math.max(1, heelScale * 0.86), "foot_body", "soft_tissue");
}

function addSideVolumeMasses(mesh, skeleton, p) {
  const pts = skeleton.points;
  const heel = pts.heel;
  const arch = pts.arch;
  const bigBall = pts.big_ball;
  const smallBall = pts.small_ball;
  const midBall = mul(add(bigBall, smallBall), 0.5);
  const instepScale = Math.max(0.35, p.instep_part_thickness / 100);
  const heelScale = Math.max(0.35, p.heel_size / 100);
  const supportLength = Math.max(0.2, p.plantar_support_length / 100);
  const supportThickness = Math.max(0.2, p.plantar_support_thickness / 100);
  const plantarRear = add(heel, v(0, p.foot_length * 0.08, -p.instep_height * 0.06 * heelScale));
  const plantarFront = add(midBall, v(0, -p.foot_length * 0.07, -p.instep_height * 0.05));
  const plantarArch = add(arch, v(0, p.foot_length * 0.04, p.arch_height * 0.18));
  const plantarStart = add(plantarArch, mul(sub(plantarRear, plantarArch), supportLength));
  const plantarEnd = add(plantarArch, mul(sub(plantarFront, plantarArch), supportLength));
  const plantarWidth = p.foot_width * 0.075 * instepScale * supportThickness * Math.max(1, heelScale * 0.78);
  addBoxSegment(mesh, plantarStart, plantarArch, plantarWidth, "foot_body", "soft_tissue");
  addBoxSegment(mesh, plantarArch, plantarEnd, plantarWidth * 0.92, "foot_body", "soft_tissue");

  const dorsalA = add(pts.instep, v(0, p.foot_length * 0.02, p.instep_height * 0.04));
  const dorsalB = add(midBall, v(0, -p.foot_length * 0.02, p.instep_height * 0.12));
  const vampScale = p.foot_mode === "shoe" ? Math.max(0.7, p.vamp_volume / 100) : 1;
  addBoxSegment(mesh, dorsalA, dorsalB, p.foot_width * 0.16 * instepScale * vampScale, "instep", "soft_tissue");

  for (const side of [-1, 1]) {
    const railA = add(heel, v(side * p.heel_width * 0.38 * heelScale, p.foot_length * 0.1, p.heel_width * 0.04 * heelScale));
    const railB = add(midBall, v(side * p.foot_width * 0.42, -p.foot_length * 0.02, -p.instep_height * 0.04));
    addBoxSegment(mesh, railA, railB, p.foot_width * 0.075 * instepScale, "foot_body", "soft_tissue");
  }
}

function addMidfootFillMasses(mesh, skeleton, p) {
  const pts = skeleton.points;
  const heel = pts.heel;
  const instep = pts.instep;
  const bigBall = pts.big_ball;
  const smallBall = pts.small_ball;
  const midBall = mul(add(bigBall, smallBall), 0.5);
  const length = p.foot_length;
  const width = p.foot_width;
  const instepH = p.instep_height;
  const heelW = p.heel_width * Math.max(0.35, p.heel_size / 100);
  const instepScale = Math.max(0.35, p.instep_part_thickness / 100);
  const rearDorsal = add(heel, v(0, length * 0.1, heelW * 0.22));
  const midDorsal = add(instep, v(0, length * 0.05, instepH * 0.1));
  const foreDorsal = add(midBall, v(0, -length * 0.06, instepH * 0.08));
  const deepCoreA = add(heel, v(0, length * 0.08, heelW * 0.12));
  const deepCoreB = add(midBall, v(0, -length * 0.05, instepH * 0.02));
  addBoxSegment(mesh, deepCoreA, deepCoreB, width * 0.3 * instepScale, "foot_body", "soft_tissue");
  addBoxSegment(mesh, rearDorsal, midDorsal, width * 0.24 * instepScale, "instep", "soft_tissue");
  addBoxSegment(mesh, midDorsal, foreDorsal, width * 0.22 * instepScale, "instep", "soft_tissue");

  for (const side of [-1, 1]) {
    const sideRear = add(heel, v(side * heelW * 0.36, length * 0.08, heelW * 0.12));
    const sideMid = add(instep, v(side * width * 0.33, length * 0.05, -instepH * 0.02));
    const sideFore = add(midBall, v(side * width * 0.42, -length * 0.05, -instepH * 0.05));
    addBoxSegment(mesh, sideRear, sideMid, width * 0.13 * instepScale, "foot_body", "soft_tissue");
    addBoxSegment(mesh, sideMid, sideFore, width * 0.14 * instepScale, "foot_body", "soft_tissue");
  }

  if (skeleton.toe_box) {
    const back = add(skeleton.toe_box.back_center, v(0, -length * 0.015, -instepH * 0.05));
    const front = add(skeleton.toe_box.front_center, v(0, -length * 0.04, 0));
    const vampScale = Math.max(0.7, p.vamp_volume / 100);
    addBoxSegment(mesh, foreDorsal, back, width * 0.18 * instepScale * vampScale, "foot_body", "soft_tissue");
    addBoxSegment(mesh, back, front, width * 0.15 * instepScale * vampScale, "toe_box", "soft_tissue");
  } else {
    for (const toe of skeleton.toes) {
      const root = add(midBall, add(mul(sub(toe.base, midBall), 0.3), v(0, -length * 0.035, -instepH * 0.05)));
      addBoxSegment(mesh, foreDorsal, root, Math.max(width * 0.12, toe.radius * 1.2) * instepScale, "foot_body", "soft_tissue");
    }
  }
}

function addAnkleAchillesMasses(mesh, skeleton, p) {
  const pts = skeleton.points;
  const heel = pts.heel;
  const ankle = pts.ankle;
  const instep = pts.instep;
  const arch = pts.arch;
  const length = p.foot_length;
  const width = p.foot_width;
  const heelScale = Math.max(0.35, p.heel_size / 100);
  const heelW = p.heel_width * heelScale;
  const instepScale = Math.max(0.35, p.instep_part_thickness / 100);
  const malleolusScale = Math.max(0.35, p.malleolus_size / 100);
  const posterior = normalize(sub(heel, instep), v(0, -1, 0));
  const legAxis = normalize(sub(ankle, heel), v(0, 0, 1));
  const heelBack = add(add(heel, mul(posterior, length * 0.045)), mul(legAxis, heelW * 0.13));
  const tendonLow = add(add(heel, mul(posterior, length * 0.035)), mul(legAxis, heelW * 0.3));
  const tendonMid = add(add(heel, mul(posterior, length * 0.03)), mul(legAxis, length * 0.34));
  const tendonTop = add(add(ankle, mul(posterior, length * 0.028)), mul(legAxis, length * 0.075));
  addBoxSegment(mesh, heelBack, tendonLow, heelW * 0.26 * Math.max(instepScale, malleolusScale * 0.92), "heel", "soft_tissue");
  addBoxSegment(mesh, tendonLow, tendonMid, heelW * 0.2 * instepScale, "achilles_tendon", "soft_tissue");
  addBoxSegment(mesh, tendonMid, tendonTop, heelW * 0.18 * instepScale, "achilles_tendon", "soft_tissue");
  const ankleCore = mul(add(ankle, tendonMid), 0.5);
  addBoxSegment(mesh, heelBack, ankleCore, heelW * 0.28 * Math.max(instepScale, malleolusScale * 0.95), "heel", "soft_tissue");
  addBoxSegment(mesh, ankleCore, instep, width * 0.18 * instepScale, "instep", "soft_tissue");
  const ankleSide = heelW * 0.36 * (0.92 + malleolusScale * 0.08);
  for (const side of [-1, 1]) {
    const malleolus = add(ankle, v(side * ankleSide, length * 0.03, -p.instep_height * 0.1));
    const heelSide = add(heelBack, v(side * heelW * 0.3, 0, -heelW * 0.02));
    const ankleSidePad = add(ankleCore, v(side * heelW * 0.24, 0, -heelW * 0.03));
    const archSide = add(arch, v(side * width * 0.22, length * 0.05, -p.instep_height * 0.05));
    addBoxSegment(mesh, heelSide, ankleSidePad, heelW * 0.22 * malleolusScale, "heel", "soft_tissue");
    addBoxSegment(mesh, ankleSidePad, malleolus, heelW * 0.18 * malleolusScale, "ankle_joint", "soft_tissue");
    addBoxSegment(mesh, ankleSidePad, archSide, width * 0.16 * instepScale, "foot_body", "soft_tissue");
  }
}

function addMetatarsalWebs(mesh, skeleton, p) {
  const toes = skeleton.toes;
  if (toes.length < 2) return;
  const pts = skeleton.points;
  const instep = pts.instep;
  const bigBall = pts.big_ball;
  const smallBall = pts.small_ball;
  const midBall = mul(add(bigBall, smallBall), 0.5);
  const length = p.foot_length;
  const width = p.foot_width;
  const instepH = p.instep_height;
  const instepScale = Math.max(0.35, p.instep_part_thickness / 100);
  const patchThickness = Math.max(7, Math.min(15, instepH * 0.2)) * instepScale;
  const rearPoints = [];
  const midPoints = [];
  const frontPoints = [];
  for (const toe of toes) {
    rearPoints.push(add(add(instep, mul(sub(toe.base, instep), 0.22)), v(0, -length * 0.01, instepH * 0.12)));
    midPoints.push(add(add(instep, mul(sub(toe.base, instep), 0.48)), v(0, -length * 0.01, instepH * 0.07)));
    frontPoints.push(add(toe.base, v(0, -length * 0.045, instepH * 0.045)));
  }
  for (let i = 0; i < toes.length - 1; i++) {
    addThickLoftPatch(mesh, rearPoints[i], midPoints[i], midPoints[i + 1], rearPoints[i + 1], 2, 2, patchThickness * 0.95, instepH * 0.055, "foot_body");
    addThickLoftPatch(mesh, midPoints[i], frontPoints[i], frontPoints[i + 1], midPoints[i + 1], 3, 2, patchThickness * 1.15, instepH * 0.045, "foot_body");
  }
  addThickLoftPatch(
    mesh,
    add(instep, add(mul(sub(bigBall, instep), 0.3), v(-width * 0.08, 0, instepH * 0.06))),
    add(bigBall, v(-width * 0.1, -length * 0.08, instepH * 0.02)),
    add(midBall, v(0, -length * 0.06, instepH * 0.04)),
    add(instep, v(0, length * 0.01, instepH * 0.08)),
    3,
    2,
    patchThickness * 1.15,
    instepH * 0.05,
    "foot_body",
  );
  addThickLoftPatch(
    mesh,
    add(instep, v(0, length * 0.01, instepH * 0.08)),
    add(midBall, v(0, -length * 0.06, instepH * 0.04)),
    add(smallBall, v(width * 0.1, -length * 0.08, instepH * 0.02)),
    add(instep, add(mul(sub(smallBall, instep), 0.3), v(width * 0.08, 0, instepH * 0.04))),
    3,
    2,
    patchThickness * 1.15,
    instepH * 0.05,
    "foot_body",
  );
}

function addToeBoxMesh(mesh, skeleton, p) {
  const toeBox = skeleton.toe_box;
  if (!toeBox) return;
  const xSamples = [-1, -0.55, 0, 0.55, 1];
  const top = [];
  const bottom = [];
  toeBox.stations.forEach((station, stationIndex) => {
    const halfWidth = station.half_width * (1.08 + 0.04 * toeBox.roundness);
    const bottomZ = station.bottom_z - Math.max(0, p.sole_thickness) * 0.1;
    const height = Math.max(6, station.top_z - bottomZ);
    const topRow = [];
    const bottomRow = [];
    for (const sample of xSamples) {
      const edge = Math.abs(sample);
      const x = halfWidth * sample;
      const edgeDrop = height * (0.13 + 0.06 * toeBox.roundness) * edge;
      const noseDrop = stationIndex === toeBox.stations.length - 1 ? height * 0.08 * edge : 0;
      topRow.push(addVertex(mesh, v(x, station.y, station.top_z - edgeDrop - noseDrop)));
      bottomRow.push(addVertex(mesh, v(x, station.y, bottomZ - height * 0.025 * (1 - edge))));
    }
    top.push(topRow);
    bottom.push(bottomRow);
  });
  appendGridShell(mesh, top, bottom, "toe_box", "soft_tissue");
}

function addShoeSole(mesh, skeleton, p) {
  const toeBox = skeleton.toe_box;
  if (!toeBox || (p.sole_thickness < 0.1 && p.heel_height < 0.1)) return;
  const pts = skeleton.points;
  const heelScale = Math.max(0.35, p.heel_size / 100);
  const sole = Math.max(2, p.sole_thickness);
  const midBall = mul(add(pts.big_ball, pts.small_ball), 0.5);
  const s = toeBox.stations;
  const lastStation = s[s.length - 1];
  const profile = [
    [pts.heel.y - p.foot_length * 0.05, p.heel_width * 0.48 * heelScale, -sole - p.heel_height, pts.heel.z + p.heel_width * 0.02],
    [pts.arch.y, p.foot_width * 0.42, -sole * 0.6 - p.heel_height * 0.32, Math.max(0, pts.arch.z * 0.16)],
    [midBall.y, p.foot_width * 0.54, -sole * 0.46, Math.max(0, midBall.z * 0.06)],
    [s[1].y, s[1].half_width * 1.02, s[1].bottom_z - sole * 0.38, s[1].bottom_z + sole * 0.1],
    [lastStation.y, lastStation.half_width * 1.12, lastStation.bottom_z - sole * 0.28, lastStation.bottom_z + sole * 0.08],
  ];
  const xSamples = [-1, -0.5, 0, 0.5, 1];
  const top = [];
  const bottom = [];
  for (const [y, halfWidth, bottomZ, topZ] of profile) {
    const topRow = [];
    const bottomRow = [];
    for (const sample of xSamples) {
      const edge = Math.abs(sample);
      topRow.push(addVertex(mesh, v(halfWidth * sample, y, topZ - edge * sole * 0.08)));
      bottomRow.push(addVertex(mesh, v(halfWidth * sample, y, bottomZ - (1 - edge) * sole * 0.06)));
    }
    top.push(topRow);
    bottom.push(bottomRow);
  }
  appendGridShell(mesh, top, bottom, "shoe_sole", "soft_tissue");
}

function addBoxSegment(mesh, a, b, thickness, group, material = "bone") {
  thickness *= material === "bone" ? 1.7 : 1.55;
  let axis = sub(b, a);
  let length = norm(axis);
  if (length < 0.001) return;
  const forward0 = mul(axis, 1 / length);
  const overlap = Math.min(length * 0.34, Math.max(thickness * 1.05, 5));
  a = sub(a, mul(forward0, overlap));
  b = add(b, mul(forward0, overlap));
  axis = sub(b, a);
  length = norm(axis);
  const forward = mul(axis, 1 / length);
  let ref = v(0, 0, 1);
  if (Math.abs(dot(forward, ref)) > 0.92) ref = v(1, 0, 0);
  const right = normalize(cross(forward, ref));
  const up = cross(right, forward);
  const half = thickness * 0.5;
  const segments = Math.max(1, Math.ceil(length / Math.max(18, Math.min(56, thickness * 1.15))));
  const rings = [];
  for (let i = 0; i <= segments; i++) {
    const center = add(a, mul(forward, (length * i) / segments));
    rings.push([
      addVertex(mesh, sub(sub(center, mul(right, half)), mul(up, half))),
      addVertex(mesh, add(sub(center, mul(up, half)), mul(right, half))),
      addVertex(mesh, add(add(center, mul(right, half)), mul(up, half))),
      addVertex(mesh, add(sub(center, mul(right, half)), mul(up, half))),
    ]);
  }
  pushFace(mesh, [rings[0][0], rings[0][1], rings[0][2], rings[0][3]], group, material);
  const end = rings[rings.length - 1];
  pushFace(mesh, [end[0], end[3], end[2], end[1]], group, material);
  for (let i = 0; i < segments; i++) {
    for (let side = 0; side < 4; side++) {
      pushFace(mesh, [rings[i][side], rings[i + 1][side], rings[i + 1][(side + 1) % 4], rings[i][(side + 1) % 4]], group, material);
    }
  }
}

function addUvSphere(mesh, center, radius, resolution, group, material = "joint_sphere") {
  radius *= 1.22;
  const stacks = Math.max(5, Math.floor(resolution * 0.65));
  const slices = Math.max(8, Math.floor(resolution));
  const grid = [];
  for (let i = 0; i <= stacks; i++) {
    const phi = -Math.PI / 2 + (Math.PI * i) / stacks;
    const row = [];
    for (let j = 0; j < slices; j++) {
      const theta = (Math.PI * 2 * j) / slices;
      row.push(addVertex(mesh, v(center.x + Math.cos(phi) * Math.cos(theta) * radius, center.y + Math.cos(phi) * Math.sin(theta) * radius, center.z + Math.sin(phi) * radius)));
    }
    grid.push(row);
  }
  for (let i = 0; i < stacks; i++) {
    for (let j = 0; j < slices; j++) {
      pushFace(mesh, [grid[i][j], grid[i][(j + 1) % slices], grid[i + 1][(j + 1) % slices], grid[i + 1][j]], group, material);
    }
  }
}

function addThickLoftPatch(mesh, p00, p10, p11, p01, uSteps, vSteps, thickness, crown, group) {
  const normal0 = normalize(cross(sub(p10, p00), sub(p01, p00)), v(0, 0, 1));
  const normal = normal0.z < 0 ? mul(normal0, -1) : normal0;
  const top = [];
  const bottom = [];
  for (let u = 0; u <= uSteps; u++) {
    const tu = u / uSteps;
    const left = lerpVec(p00, p10, tu);
    const right = lerpVec(p01, p11, tu);
    const topRow = [];
    const bottomRow = [];
    for (let vv = 0; vv <= vSteps; vv++) {
      const tv = vv / vSteps;
      const base = lerpVec(left, right, tv);
      const arch = Math.sin(Math.PI * tu) * Math.sin(Math.PI * tv) * crown;
      const center = add(base, mul(normal, arch));
      topRow.push(addVertex(mesh, add(center, mul(normal, thickness * 0.5))));
      bottomRow.push(addVertex(mesh, sub(center, mul(normal, thickness * 0.5))));
    }
    top.push(topRow);
    bottom.push(bottomRow);
  }
  appendGridShell(mesh, top, bottom, group, "soft_tissue");
}

function addSubdividedBox(mesh, center, size, divisions, group, material = "soft_tissue") {
  const sx = size.x * 1.12;
  const sy = size.y * 1.12;
  const sz = size.z * 1.18;
  const nx = Math.max(1, divisions[0]);
  const ny = Math.max(1, divisions[1]);
  const nz = Math.max(1, divisions[2]);
  const x0 = center.x - sx * 0.5;
  const y0 = center.y - sy * 0.5;
  const z0 = center.z - sz * 0.5;
  const x1 = center.x + sx * 0.5;
  const y1 = center.y + sy * 0.5;
  const z1 = center.z + sz * 0.5;

  addBoxFaceGrid(mesh, v(x0, y0, z1), v(sx, 0, 0), v(0, sy, 0), nx, ny, group, material, false);
  addBoxFaceGrid(mesh, v(x0, y0, z0), v(0, sy, 0), v(sx, 0, 0), ny, nx, group, material, false);
  addBoxFaceGrid(mesh, v(x0, y0, z0), v(sx, 0, 0), v(0, 0, sz), nx, nz, group, material, false);
  addBoxFaceGrid(mesh, v(x0, y1, z0), v(0, 0, sz), v(sx, 0, 0), nz, nx, group, material, false);
  addBoxFaceGrid(mesh, v(x0, y0, z0), v(0, 0, sz), v(0, sy, 0), nz, ny, group, material, false);
  addBoxFaceGrid(mesh, v(x1, y0, z0), v(0, sy, 0), v(0, 0, sz), ny, nz, group, material, false);
}

function addBoxFaceGrid(mesh, origin, uVec, vVec, uCount, vCount, group, material, flip) {
  const grid = [];
  for (let u = 0; u <= uCount; u++) {
    const row = [];
    for (let vv = 0; vv <= vCount; vv++) {
      row.push(addVertex(mesh, add(add(origin, mul(uVec, u / uCount)), mul(vVec, vv / vCount))));
    }
    grid.push(row);
  }
  for (let u = 0; u < uCount; u++) {
    for (let vv = 0; vv < vCount; vv++) {
      const face = [grid[u][vv], grid[u + 1][vv], grid[u + 1][vv + 1], grid[u][vv + 1]];
      pushFace(mesh, flip ? face.reverse() : face, group, material);
    }
  }
}

function appendGridShell(mesh, top, bottom, group, material) {
  const rows = top.length;
  const cols = top[0].length;
  for (let r = 0; r < rows - 1; r++) {
    for (let c = 0; c < cols - 1; c++) {
      pushFace(mesh, [top[r][c], top[r][c + 1], top[r + 1][c + 1], top[r + 1][c]], group, material);
      pushFace(mesh, [bottom[r][c], bottom[r + 1][c], bottom[r + 1][c + 1], bottom[r][c + 1]], group, material);
    }
  }
  for (let r = 0; r < rows - 1; r++) {
    pushFace(mesh, [top[r][0], top[r + 1][0], bottom[r + 1][0], bottom[r][0]], group, material);
    pushFace(mesh, [top[r + 1][cols - 1], top[r][cols - 1], bottom[r][cols - 1], bottom[r + 1][cols - 1]], group, material);
  }
  for (let c = 0; c < cols - 1; c++) {
    pushFace(mesh, [top[0][c + 1], top[0][c], bottom[0][c], bottom[0][c + 1]], group, material);
    pushFace(mesh, [top[rows - 1][c], top[rows - 1][c + 1], bottom[rows - 1][c + 1], bottom[rows - 1][c]], group, material);
  }
}

function exportObj(vertices, faces, groups, p) {
  const colors = calculateVertexColors(vertices.length, faces, groups);
  const lines = [
    "# Parametric foot base mesh - GitHub Pages JavaScript edition",
    "# Single object export; colors are OBJ vertex colors",
    `# Export scale: ${OBJ_EXPORT_SCALE}`,
    "",
  ];
  for (const [key, value] of Object.entries(p)) lines.push(`#   ${key}: ${value}`);
  lines.push("");
  for (let i = 0; i < vertices.length; i++) {
    const point = vertices[i];
    const color = colors[i];
    lines.push(`v ${(point.x * OBJ_EXPORT_SCALE).toFixed(5)} ${(point.y * OBJ_EXPORT_SCALE).toFixed(5)} ${(point.z * OBJ_EXPORT_SCALE).toFixed(5)} ${color[0].toFixed(4)} ${color[1].toFixed(4)} ${color[2].toFixed(4)}`);
  }
  lines.push("", "o foot_base_mesh", `g ${p.foot_mode === "shoe" ? "toe_box" : "foot_base_mesh"}`);
  for (const face of faces) lines.push(`f ${face.join(" ")}`);
  return `${lines.join("\n")}\n`;
}

function calculateVertexColors(vertexCount, faces, groups) {
  const sums = Array.from({ length: vertexCount }, () => [0, 0, 0]);
  const counts = Array.from({ length: vertexCount }, () => 0);
  faces.forEach((face, index) => {
    const color = MATERIAL_COLORS[materialFromGroup(groups[index])] || MATERIAL_COLORS.soft_tissue;
    for (const vertexIndex of face) {
      const idx = vertexIndex - 1;
      sums[idx][0] += color[0];
      sums[idx][1] += color[1];
      sums[idx][2] += color[2];
      counts[idx] += 1;
    }
  });
  return sums.map((sum, i) => (counts[i] ? sum.map((value) => value / counts[i]) : MATERIAL_COLORS.soft_tissue));
}

function materialFromGroup(group) {
  return group.includes(MATERIAL_SEPARATOR) ? group.split(MATERIAL_SEPARATOR)[1] : "soft_tissue";
}

function pushFace(mesh, face, group, material) {
  mesh.faces.push(face);
  mesh.groups.push(`${group}${MATERIAL_SEPARATOR}${material}`);
}

function addVertex(mesh, point) {
  mesh.vertices.push(point);
  return mesh.vertices.length;
}

function topBounds(skeleton) {
  const values = [...Object.values(skeleton.points), ...skeleton.outline];
  for (const toe of skeleton.toes) values.push(toe.base, toe.mid, toe.distal, toe.tip);
  if (skeleton.toe_box) values.push(...skeleton.toe_box.top_outline, skeleton.toe_box.back_center, skeleton.toe_box.front_center, skeleton.toe_box.nose);
  return bounds(values, "x", "y");
}

function sideBounds(skeleton, p) {
  const values = [...Object.values(skeleton.points), ...skeleton.side_sole];
  for (const toe of skeleton.toes) values.push(toe.base, toe.mid, toe.distal, toe.tip);
  if (skeleton.toe_box) values.push(...skeleton.toe_box.side_profile, skeleton.toe_box.back_center, skeleton.toe_box.front_center, skeleton.toe_box.nose);
  const b = bounds(values, "y", "z");
  b.minB = Math.min(b.minB, -8);
  b.maxB = Math.max(b.maxB, p.instep_height + 16);
  return b;
}

function bounds(values, axisA, axisB) {
  return {
    minA: Math.min(...values.map((point) => point[axisA])),
    maxA: Math.max(...values.map((point) => point[axisA])),
    minB: Math.min(...values.map((point) => point[axisB])),
    maxB: Math.max(...values.map((point) => point[axisB])),
  };
}

function projectXY(point, b, rect) {
  const [x0, y0, w, h] = rect;
  const scale = Math.min(w / Math.max(b.maxA - b.minA, 1), h / Math.max(b.maxB - b.minB, 1));
  const cx = x0 + w / 2;
  const cy = y0 + h / 2;
  const mx = (b.minA + b.maxA) / 2;
  const my = (b.minB + b.maxB) / 2;
  return [cx + (point.x - mx) * scale, cy - (point.y - my) * scale];
}

function projectYZ(point, b, rect) {
  const [x0, y0, w, h] = rect;
  const scale = Math.min(w / Math.max(b.maxA - b.minA, 1), h / Math.max(b.maxB - b.minB, 1));
  const cx = x0 + w / 2;
  const cy = y0 + h / 2;
  const my = (b.minA + b.maxA) / 2;
  const mz = (b.minB + b.maxB) / 2;
  return [cx + (point.y - my) * scale, cy - (point.z - mz) * scale];
}

function fillPolyline(context, points, fill, stroke, width) {
  if (!points.length) return;
  context.beginPath();
  context.moveTo(points[0][0], points[0][1]);
  for (const point of points.slice(1)) context.lineTo(point[0], point[1]);
  context.closePath();
  context.fillStyle = fill;
  context.fill();
  context.strokeStyle = stroke;
  context.lineWidth = width;
  context.stroke();
}

function polyline(context, points, stroke, width) {
  if (points.length < 2) return;
  context.beginPath();
  context.moveTo(points[0][0], points[0][1]);
  for (const point of points.slice(1)) context.lineTo(point[0], point[1]);
  context.strokeStyle = stroke;
  context.lineWidth = width;
  context.stroke();
}

function drawBone(context, a, b, width = 2, color = "#546778") {
  line2d(context, a, b, color, width);
}

function line2d(context, a, b, color, width) {
  context.beginPath();
  context.moveTo(a[0], a[1]);
  context.lineTo(b[0], b[1]);
  context.strokeStyle = color;
  context.lineWidth = width;
  context.lineCap = "round";
  context.stroke();
}

function joint(context, point, radius, color) {
  context.beginPath();
  context.arc(point[0], point[1], radius + 2, 0, Math.PI * 2);
  context.fillStyle = "#fbfdff";
  context.fill();
  context.beginPath();
  context.arc(point[0], point[1], radius, 0, Math.PI * 2);
  context.fillStyle = color;
  context.fill();
}

function titleText(context, text, x, y) {
  context.fillStyle = "#3e4856";
  context.font = "22px -apple-system, BlinkMacSystemFont, sans-serif";
  context.fillText(text, x, y);
}

function labelText(context, text, x, y) {
  context.fillStyle = "#4e5a66";
  context.font = "15px -apple-system, BlinkMacSystemFont, sans-serif";
  context.fillText(text, x, y);
}

function downloadText(text, filename) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function timestamp() {
  const now = new Date();
  const pad = (value) => String(value).padStart(2, "0");
  return `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
}

function toeLengthsFor(p) {
  const base = p.toe_length;
  if (p.toe_profile === "egyptian") return [p.big_toe_length, base * 0.92, base * 0.82, base * 0.72, base * 0.62];
  if (p.toe_profile === "greek") return [p.big_toe_length * 0.95, base * 1.12, base, base * 0.86, base * 0.7];
  if (p.toe_profile === "square") return [p.big_toe_length, base, base * 0.98, base * 0.86, base * 0.72];
  return [p.big_toe_length, base * 1.03, base, base * 0.86, base * 0.68];
}

function toeDirection(lateralAngle, pitchAngle) {
  const forward = Math.cos(pitchAngle);
  return v(Math.sin(lateralAngle) * forward, Math.cos(lateralAngle) * forward, Math.sin(pitchAngle));
}

function pitchForTiptoe(point, pivot, angleDegrees) {
  if (Math.abs(angleDegrees) < 0.001) return point;
  const angle = deg(angleDegrees);
  const dy = point.y - pivot.y;
  const dz = point.z - pivot.z;
  return v(point.x, pivot.y + dy * Math.cos(angle) + dz * Math.sin(angle), pivot.z - dy * Math.sin(angle) + dz * Math.cos(angle));
}

function mirrorX(x, p) {
  return p.side === "left" ? -x : x;
}

function v(x, y, z) {
  return { x, y, z };
}

function add(a, b) {
  return v(a.x + b.x, a.y + b.y, a.z + b.z);
}

function sub(a, b) {
  return v(a.x - b.x, a.y - b.y, a.z - b.z);
}

function mul(a, scalar) {
  return v(a.x * scalar, a.y * scalar, a.z * scalar);
}

function avg(points) {
  if (!points.length) return v(0, 0, 0);
  return mul(points.reduce((total, point) => add(total, point), v(0, 0, 0)), 1 / points.length);
}

function dot(a, b) {
  return a.x * b.x + a.y * b.y + a.z * b.z;
}

function cross(a, b) {
  return v(a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x);
}

function norm(a) {
  return Math.hypot(a.x, a.y, a.z);
}

function normalize(a, fallback = v(0, 0, 1)) {
  const length = norm(a);
  return length < 0.001 ? fallback : mul(a, 1 / length);
}

function deg(value) {
  return (value * Math.PI) / 180;
}

function lerp(a, b, t) {
  return a * (1 - t) + b * t;
}

function lerpVec(a, b, t) {
  return v(lerp(a.x, b.x, t), lerp(a.y, b.y, t), lerp(a.z, b.z, t));
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}
