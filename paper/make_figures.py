"""Data figures for the draft paper.

Every number plotted here comes from one of three places, named per figure:
  * rehearsal runs produced by deploy/tools/offline_grasp_lift.py (runs/*.json)
  * a live computation with the deploy package (staging / support geometry)
  * measurements recorded in the repositories and project notes (quoted inline)
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)
# the deploy package of this repository (staging.py lives there)
DEPLOY = Path(os.environ.get("SURGICAI_DEPLOY", HERE.parent / "deploy"))
sys.path.insert(0, str(DEPLOY))

# reference palette, first three categorical slots + neutrals
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GRAY, DARK, MUTED, GRID = "#9a9893", "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Liberation Serif", "TeX Gyre Termes", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "axes.titlesize": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": DARK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.5,
    "axes.axisbelow": True,
    "legend.frameon": False,
    "lines.linewidth": 1.4,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})
COL = 3.45  # IEEE column width, inches


def save(fig, name):
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=200)
    plt.close(fig)
    print("wrote", name)


def bar_labels(ax, bars, fmt="{:.2f}", dy=0.015):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + dy, fmt.format(h),
                ha="center", va="bottom", fontsize=6, color=MUTED)


# ---------------------------------------------------------------------------
# Fig: hierarchical chain success. Paper Table 3 (n=100) vs our replication
# (SurgicAI jin-hierarchical-repro, RL/HIERARCHICAL_README.md, n=20, seed 10).
# ---------------------------------------------------------------------------
def fig_hierarchy():
    chains = ["Place", "Insert", "Regrasp", "Pullout"]
    flat = [0.64, 0.40, 0.24, 0.15]
    paper = [0.88, 0.72, 0.60, 0.52]
    ours = [0.90, 0.90, 0.90, 0.55]
    x = np.arange(len(chains))
    w = 0.26
    fig, ax = plt.subplots(figsize=(COL, 2.1))
    b1 = ax.bar(x - w, flat, w * 0.92, color=GRAY, label="Flat TD3+HER+BC [paper, n=100]")
    b2 = ax.bar(x, paper, w * 0.92, color=BLUE, label="Hierarchical [paper, n=100]")
    b3 = ax.bar(x + w, ours, w * 0.92, color=ORANGE, label="Hierarchical, ours (ROS 2, n=20)")
    for bs in (b1, b2, b3):
        bar_labels(ax, bs)
    ax.set_xticks(x, [f"Approach\n$\\rightarrow${c}" for c in chains])
    ax.set_ylabel("Chain success rate")
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.grid(axis="x", visible=False)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, handlelength=1.0,
              columnspacing=0.8, borderaxespad=0.2)
    save(fig, "hierarchy_chain")


# ---------------------------------------------------------------------------
# Fig: two contract defects measured by replaying R6 from its own 50
# demonstration starts (rpy-branch-defect note; commit 48a9b7a).
# ---------------------------------------------------------------------------
def fig_contract():
    fig, (a, b) = plt.subplots(1, 2, figsize=(COL * 2.0, 1.75),
                               gridspec_kw={"width_ratios": [1.25, 1]})
    labels = ["0.5 mm\n2°", "0.5 mm\n3°", "1.0 mm\n2°", "1.0 mm\n3°", "1.5 mm\n3°", "2.0 mm\n2°"]
    succ = [24, 23, 35, 46, 36, 10]
    colors = [GRAY, GRAY, GRAY, BLUE, ORANGE, GRAY]
    bars = a.bar(range(6), [s / 50 for s in succ], 0.7, color=colors)
    for bb, s in zip(bars, succ):
        a.text(bb.get_x() + bb.get_width() / 2, bb.get_height() + 0.02, f"{s}/50",
               ha="center", va="bottom", fontsize=6, color=MUTED)
    a.set_xticks(range(6), labels)
    a.set_ylim(0, 1.12)
    a.set_ylabel("Replay success (R6)")
    a.set_title("(a) Action scale: training value vs. value applied", loc="left")
    a.grid(axis="x", visible=False)
    a.annotate("training scale", xy=(3, 0.95), xytext=(1.2, 1.03), fontsize=6.5,
               color=DARK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    a.annotate("previously deployed", xy=(4, 0.75), xytext=(4.25, 0.95), fontsize=6.5,
               color=DARK, arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))

    track = [1.0, 0.5, 0.3]
    open_loop = [25, 25, 25]
    closed = [25, 21, 6]
    b.plot(track, [v / 25 for v in open_loop], "-o", color=BLUE, ms=4,
           label="obs = integrated command (training)")
    b.plot(track, [v / 25 for v in closed], "-s", color=ORANGE, ms=4,
           label="obs = measured pose")
    for t, v in zip(track, closed):
        b.text(t + 0.02, v / 25 - 0.13, f"{v}/25", ha="center", fontsize=6, color=ORANGE)
    b.set_xlim(1.05, 0.25)
    b.set_ylim(0, 1.12)
    b.set_xlabel("Arm tracking per cycle (1 = perfect)")
    b.set_ylabel("Replay success")
    b.set_title("(b) Observation source vs. arm lag (Approach)", loc="left")
    b.legend(loc="lower left", handlelength=1.4, bbox_to_anchor=(0.0, 0.08))
    fig.tight_layout(w_pad=1.5)
    save(fig, "contract_defects")


# ---------------------------------------------------------------------------
# Fig: workspace — computed live with deploy/surgicai_rl_deploy/staging.py
# on the recorded lcsr-dvrk-15 geometry and the ±3 mm / ±30° needle envelope.
# ---------------------------------------------------------------------------
def fig_workspace():
    from scipy.spatial.transform import Rotation
    from surgicai_rl_deploy.contract import CONTRACTS
    from surgicai_rl_deploy.frames import Pose
    from surgicai_rl_deploy.staging import stage_pose_for, support_report

    contract = CONTRACTS["approach_upstream"]
    q = [0.23319925218484056, 0.4267863636861243, -0.23588767438897446, 0.841325450478807]
    grasp = Pose.from_pos_quat([-0.050726357, 0.015332369, 0.049514053], q, 0.0)
    current = Pose.from_pos_quat([-0.05639860616831881, 0.03366166453830251,
                                  0.024455994074878362], q, 0.0)
    rng = np.random.default_rng(0)
    un, st = [], []
    n_un = n_st = 0
    for _ in range(400):
        off = np.array([rng.uniform(-0.003, 0.003), rng.uniform(-0.003, 0.003), 0.0])
        spin = Rotation.from_rotvec([0, 0, rng.uniform(-np.pi / 6, np.pi / 6)]).as_matrix()
        g = Pose(grasp.p + off, spin @ grasp.R, 0.0)
        r = support_report(current, g, contract)
        un.append((r["offset_tool_cm"][1], r["rotation_deg"]))
        n_un += r["in_support"]
        s = stage_pose_for(g, contract)
        r2 = support_report(s, g, contract)
        st.append((r2["offset_tool_cm"][1], r2["rotation_deg"]))
        n_st += r2["in_support"]
    un, st = np.array(un), np.array(st)
    lo, hi = contract.start_offset_tool_min, contract.start_offset_tool_max
    r0, r1 = contract.start_rot_deg_min, contract.start_rot_deg_max

    fig, ax = plt.subplots(figsize=(COL, 2.0))
    ax.add_patch(Rectangle((lo[1], r0), hi[1] - lo[1], r1 - r0, facecolor=BLUE,
                           alpha=0.12, edgecolor=BLUE, lw=1.0))
    ax.text(hi[1] - 0.05, r1 - 3, "demonstrated support\n(Approach TD3+HER+BC)",
            ha="right", va="top", fontsize=6.5, color=DARK)
    ax.scatter(un[:, 0], un[:, 1], s=6, color=ORANGE, alpha=0.6, lw=0,
               label=f"unstaged: {n_un}/400 in support")
    ax.scatter(st[:, 0], st[:, 1], s=26, color=BLUE, edgecolor="white", lw=0.8,
               marker="D", label=f"staged: {n_st}/400 in support", zorder=3)
    ax.set_xlabel("Start-to-goal offset, tool $y$ (cm)")
    ax.set_ylabel("Start-to-goal rotation (°)")
    ax.set_xlim(-1.4, 3.8)
    ax.set_ylim(-5, 105)
    ax.legend(loc="lower right", handletextpad=0.3)
    save(fig, "workspace_staging")
    return n_un, n_st


# ---------------------------------------------------------------------------
# Fig: deadband. Offline rehearsal with MockArm(deadband) reproducing the
# hardware stall on lcsr-dvrk-15 (commit 5fa329c).
# ---------------------------------------------------------------------------
def fig_deadband():
    runs = [("stideal", "ideal arm", GRAY, "-"),
            ("st0", "1.0 mm deadband, no command floor", ORANGE, "-"),
            ("st12", "1.0 mm deadband, 1.2 mm command floor", BLUE, "-")]
    fig, ax = plt.subplots(figsize=(COL, 1.8))
    for f, lab, c, ls in runs:
        t = json.load(open(RUNS / f"{f}.json"))["trace"]
        pts = [(x["i"], x["trans_err_cm"]) for x in t if x["phase"] == "stage"]
        i, e = np.array(pts).T
        ax.plot(i, e, ls, color=c, label=lab, lw=1.3 if f != "stideal" else 1.0)
    ax.axhline(0.2, color=MUTED, lw=0.6, ls=":")
    ax.text(5, 0.26, "staging tolerance (0.2 cm)", ha="left", fontsize=6, color=MUTED)
    ax.text(395, 0.95, "stalls; step budget\nends the run", ha="right", va="bottom",
            fontsize=6, color=ORANGE)
    ax.set_xlabel("Control cycle")
    ax.set_ylabel("Staging error (cm)")
    ax.set_xlim(0, 400)
    ax.set_ylim(0, 4.0)
    ax.legend(loc="upper right", handlelength=1.4, bbox_to_anchor=(1.0, 0.93))
    save(fig, "deadband")


# ---------------------------------------------------------------------------
# Fig: the whole real-robot sequence rehearsed offline (D2 servo, arm lag 0.5,
# 0.2 mm pose noise, 7 mm standoff) on the recorded operator poses.
# ---------------------------------------------------------------------------
PHASE_COLORS = {
    "approach": BLUE, "descend": "#4a3aa7", "settle": GRAY, "close": GRAY,
    "observe": GRAY, "lift": AQUA, "transport": ORANGE, "place": "#e34948",
    "hold": GRAY,
}


def fig_sequence():
    d = json.load(open(RUNS / "sl0.5.json"))
    t = d["trace"]
    plan = d["plan"]
    fig = plt.figure(figsize=(COL * 2.0, 2.05))
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    phases = [x["phase"] for x in t]
    P = np.array([x["measured_cm"] for x in t])
    for ph in dict.fromkeys(phases):
        idx = [k for k, p in enumerate(phases) if p == ph]
        seg = P[max(idx[0] - 1, 0): idx[-1] + 1]
        ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], color=PHASE_COLORS[ph], lw=1.4)
    pts = {"start": plan["start_cm"], "grasp": plan["grasp_cm"],
           "via": plan["via_cm"], "suture": plan["suture_cm"]}
    for k, v in pts.items():
        ax.scatter(*v, s=14, color=DARK, depthshade=False)
        ax.text(v[0], v[1], v[2] + 0.25, k, fontsize=6, color=DARK)
    ax.set_xlabel("x (cm)", labelpad=-8)
    ax.set_ylabel("y (cm)", labelpad=-8)
    ax.set_zlabel("z (cm)", labelpad=-9)
    ax.tick_params(pad=-3, labelsize=5.5)
    ax.view_init(elev=22, azim=-58)
    ax.set_title("(a) Tool path in the ECM frame", loc="left", pad=-2)

    b = fig.add_subplot(1, 2, 2)
    i = np.array([x["i"] for x in t])
    e = np.array([x["trans_err_cm"] for x in t])
    for ph in dict.fromkeys(phases):
        m = np.array([p == ph for p in phases])
        b.plot(i[m], e[m], ".", ms=2.2, color=PHASE_COLORS[ph], label=ph)
    b.set_yscale("log")
    b.set_xlabel("Control cycle")
    b.set_ylabel("Error to phase target (cm)")
    b.set_title("(b) Error to the current phase's target", loc="left")
    b.legend(loc="upper right", ncol=3, markerscale=3, handletextpad=0.1,
             columnspacing=0.6, fontsize=6)
    b.set_ylim(1e-2, 30)
    fig.tight_layout(w_pad=0.5)
    save(fig, "sequence_rehearsal")


# ---------------------------------------------------------------------------
# Fig: grasp calibration. (a) residual_structure.py output (derived from the
# dVRK DH parameters); (b) the ten first hardware samples (session30.json,
# recorded in the project note of 2026-09-23).
# ---------------------------------------------------------------------------
def fig_calibration():
    fig, (a, b) = plt.subplots(1, 2, figsize=(COL * 2.0, 1.9),
                               gridspec_kw={"width_ratios": [1.35, 1]})
    src = ["hand-eye\n1°+3.9 mm", "outer yaw\n1°", "outer pitch\n1°",
           "insertion\n1 mm", "depth bias\n$\\propto$ range$^2$", "lens\ndistortion"]
    raw = [3.42, 2.543, 2.551, 1.000, 0.53, 0.018]
    const = [0.287, 0.296, 0.297, 0.107, np.nan, np.nan]
    aff = [9e-15, 1e-5, 0.0160, 0.0101, 0.0091, 0.0081]
    x = np.arange(len(src))
    w = 0.27
    a.bar(x - w, raw, w * 0.92, color=GRAY, label="raw")
    a.bar(x, const, w * 0.92, color=ORANGE, label="after constant offset")
    a.bar(x + w, np.maximum(aff, 1e-4), w * 0.92, color=BLUE, label="after affine")
    a.axhline(0.43, color=DARK, lw=0.7, ls="--")
    a.text(4.6, 0.52, "grasp noise floor", ha="left", fontsize=6, color=DARK)
    a.set_yscale("log")
    a.set_ylim(1e-4, 300)
    a.set_xticks(x, src, fontsize=6)
    a.set_ylabel("Residual RMS (mm)")
    a.set_title("(a) Predicted residual structure", loc="left")
    a.grid(axis="x", visible=False)
    a.legend(loc="upper center", ncol=3, fontsize=6, handlelength=1.0,
             columnspacing=0.8, borderaxespad=0.1)
    a.text(0 + w, 1.3e-4, "0*", ha="center", fontsize=5.5, color=MUTED)
    a.text(1 + w, 1.3e-4, "0*", ha="center", fontsize=5.5, color=MUTED)

    res = np.array([
        (-14.7, 35.0, -0.7), (0.0, 47.3, -0.2), (2.6, 40.3, -7.0), (0.4, 41.7, 19.6),
        (-9.8, 37.6, 29.5), (2.7, 42.7, 19.8), (2.6, 34.8, 26.1), (-3.7, 32.6, 30.1),
        (-20.5, 36.4, 21.9), (-19.5, 39.4, 14.9)])
    rng = np.random.default_rng(3)
    for k, (ax_name, c) in enumerate(zip("xyz", [GRAY, BLUE, ORANGE])):
        jit = k + rng.uniform(-0.12, 0.12, len(res))
        b.scatter(jit, res[:, k], s=12, color=c, lw=0)
        m, s = res[:, k].mean(), res[:, k].std(ddof=0)
        b.plot([k - 0.28, k + 0.28], [m, m], color=DARK, lw=1.0)
        b.text(k + 0.3, m, f"{m:+.1f}\n±{s:.1f}", fontsize=6, color=DARK, va="center")
    b.axhline(0, color=MUTED, lw=0.6)
    b.set_xticks([0, 1, 2], ["$r_x$", "$r_y$", "$r_z$"])
    b.set_xlim(-0.5, 2.9)
    b.set_ylabel("Residual, gripper − needle (mm)")
    b.set_title("(b) First hardware samples (n=10)", loc="left")
    b.grid(axis="x", visible=False)
    fig.tight_layout(w_pad=1.2)
    save(fig, "calibration")


if __name__ == "__main__":
    fig_hierarchy()
    fig_contract()
    print("workspace in-support (unstaged, staged):", fig_workspace())
    fig_deadband()
    fig_sequence()
    fig_calibration()
