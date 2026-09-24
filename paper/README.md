# Draft paper — Autonomous Suturing Task

> **DRAFT, prepared for publication. Not peer reviewed.** Results, figures and
> text are preliminary and will change. Items marked in red in the PDF
> (`[...]`) are still open.

**[Read the PDF → `surgical_rl_draft.pdf`](surgical_rl_draft.pdf)**

*Autonomous Suturing Task: From Hierarchical Policies in Simulation to a Guarded
Needle-Handling Pipeline on a Real dVRK* — Xiangrui Sun‡, Jiaming Wen‡,
Adnan Munawar\*, Anqi Liu\* (‡equal contribution, co-first authors;
\*corresponding authors).

## What is in it

| Section | Where the work lives |
|---|---|
| Hierarchical SurgicAI pipeline re-run on ROS 2 / AMBF 3 (11/20 full sutures vs. 52% published) | `xiangruiSun/SurgicAI`, branch `jin-hierarchical-repro`, `RL/HIERARCHICAL_README.md` |
| Perception: sim-fine-tuned Depth Anything V2, FoundationPose, ArUco hand-eye | perception pipeline (Jiaming) |
| Deployment contract, the three defects, staging, phase machine, deadband | `deploy/` |
| Two-stage grasp calibration and first hardware samples | `deploy/surgicai_rl_deploy/calib/` |

## Files

```
surgical_rl_draft.pdf    the draft
surgical_rl_draft.tex    source (ieeeconf); needs colors.tex, ieeeconf.cls, figures/
figures/*.tikz           pipeline and phase-machine diagrams (drawn in LaTeX)
figures/*.pdf|png        data figures
make_figures.py          regenerates every data figure
runs/*.json              offline rehearsal traces used by the figures
```

## Rebuild

```bash
# figures (needs numpy, scipy, matplotlib; uses ../deploy)
python3 make_figures.py

# rehearsal traces, if you want to regenerate runs/ too (run from ../deploy)
python3 tools/offline_grasp_lift.py \
  --start-pos -0.05639860616831881 0.03366166453830251 0.024455994074878362 \
  --start-quat 0.23319925218484056 0.4267863636861243 -0.23588767438897446 0.841325450478807 \
  --grasp-pos -0.050726357 0.015332369 0.049514053 \
  --suture-pos -0.040 0.005 0.040 --suture-quat 0 0 0 1 --suture-confirmed \
  --controller d2 --lift-sign -1 --grasp-gate evidence --grasp-standoff-mm 7 \
  --noise-mm 0.2 --seed 1 --lag 0.5 --json-out sl0.5.json
#   deadband runs: add --stage --contract approach_upstream --deadband-mm 1.0
#   --descend-success-trans-cm 0.2 [--min-command-mm 1.2]

# paper
pdflatex surgical_rl_draft.tex && pdflatex surgical_rl_draft.tex
```
