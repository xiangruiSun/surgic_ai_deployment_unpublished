# Autonomous Suturing on the dVRK: from SurgicAI policies to a real PSM

> 📄 **Draft paper (prepared for publication, not yet peer reviewed):**
> [*Autonomous Suturing Task: From Hierarchical Policies in Simulation to a Guarded Needle-Handling Pipeline on a Real dVRK*](paper/surgical_rl_draft.pdf)
> — Xiangrui Sun, Jiaming Wen, Adnan Munawar\*, Anqi Liu\* (\*corresponding authors). Sources and figures in [`paper/`](paper/README.md).

This repository takes the reinforcement-learning suturing policies of
[SurgicAI](https://github.com/surgical-robotics-ai/SurgicAI) (NeurIPS 2024) and
runs them on a real da Vinci Research Kit PSM. It contains the real-robot
deployment, the grasp calibration, the simulation environments used to train
and retrain the policies, and the draft paper.

## The pipeline

```text
 PERCEPTION (real endoscope)                        separate repository, see below
   ECM RGB ─► Depth Anything V2 (sim-fine-tuned, metric) ─► depth
   RGB + mask + depth ─► FoundationPose ─► needle pose  ᶜT_N
   ArUco marker on the PSM shaft ─► hand-eye  ᴱT_C

 GRASP TARGET                                       deploy/surgicai_rl_deploy/calib/
   coarse:  ᴱT_C · ᶜT_N · T_grasp   (needle point 30° along the arc, not the mesh origin)
   fine:    + Bernstein residual field learned from taught grasps (affine → degree n)
   refuses outside the calibrated box, on a pose flip, or on changed conventions

 REAL-ROBOT SEQUENCE                                deploy/run_pipeline.py
   precheck (fail-closed) ─► stage ─► approach ─► descend 7 mm ─► settle ─► close jaw
        ─► observe ─► operator gate ─► lift 1.5 cm ─► transport (via point) ─► place ─► hold
   approach:  RL checkpoint (through the verified contract) or D2 SE(3) servo
   abort:     hold the last command, never open the jaw

 SIMULATION                                         src/SurgicAI/RL/ + SurgicAI fork
   AMBF + SRC ─► SurgicAI subtask envs ─► TD3+HER+BC policies ─► checkpoints
   hierarchical 5-stage chain replicated on ROS 2 / AMBF 3 (11/20 full sutures, paper: 52%)
```

The same `GraspLiftSequencer` drives both the real arm and the AMBF grasp-and-lift
environment, so what is rehearsed in simulation is the code that runs on the robot.

## Where things are

| Part | Location | Notes |
|---|---|---|
| Real-robot pipeline | [`deploy/`](deploy/) | ROS 2 entry points, phase machine, safety, tools; 588 tests with no ROS, robot or checkpoint |
| Full pipeline guide | [`deploy/README_GRASP_LIFT.md`](deploy/README_GRASP_LIFT.md) | stage → … → place, operator gate, safety envelope |
| Approach-only guide | [`deploy/README.md`](deploy/README.md) | `run_approach.py`, frame modes, contract |
| Grasp calibration | [`deploy/README_CALIBRATION.md`](deploy/README_CALIBRATION.md) | FoundationPose + hand-eye + Bernstein residual |
| Simulation / training | [`src/SurgicAI/RL/`](src/SurgicAI/RL/) | Approach and GraspLift envs, TD3/SAC/PPO(+BC,+HER), curriculum |
| Retraining plan | [`src/SurgicAI/RL/RETRAINING.md`](src/SurgicAI/RL/RETRAINING.md) | what retraining buys, and what it does not |
| Needle model | [`asset/`](asset/) | 20 mm, 135° needle STL used for pose estimation |
| Draft paper | [`paper/`](paper/) | PDF, LaTeX, figure script, rehearsal traces |
| Hierarchical replication | [xiangruiSun/SurgicAI @ `jin-hierarchical-repro`](https://github.com/xiangruiSun/SurgicAI/tree/jin-hierarchical-repro) | Jin Wu's 5-stage pipeline on ROS 2; needs the full SurgicAI tree and the old SRC |
| Perception (DA, FP) | [suturing-policy-sim2real](https://github.com/18244241528jm-cpu/suturing-policy-sim2real) | Depth Anything fine-tuning, FoundationPose, first-frame gate |

## Things you must know before running anything

These were each found the hard way. Every RL result taken before they were fixed
is void. Details are in the paper (Sec. V) and in `deploy/README_GRASP_LIFT.md`.

1. **Roll branch.** SurgicAI puts roll in **(−2π, 0]**, not SciPy's [−π, π].
   With the wrong branch the upstream Approach policy reproduces 0/25 of its own demonstrations.
2. **Action scale is 1.0 mm / 3°.** The environment metadata's 0.5 mm / 2° is
   the demonstrations' scale, not the policy's. The old 1.5 mm was wrong.
3. **Open-loop observation.** The network sees the integrated *command*, never
   `measured_cp`. Feeding it the measured pose drops Approach to 6/25 on a lagging arm.
4. **The trained goal is 7 mm short of the needle.** The `descend` phase covers
   the last 7 mm; the policy never learned it.
5. **Staging, not retraining.** The real task is outside the policy's trained
   support (0/400 placements). A computed staging move puts all 400/400 inside it.
6. **Deadband.** The PSM ignores small setpoints: 0.4 mm moved it not at all, and
   2 mm moved it 1.947 mm. Measure the deadband with `tools/poke_arm.py` and pass `--min-command-mm`.
7. **Jaw sign.** On the dVRK, a negative jaw angle means squeeze. There is no grasp sensor, so
   jaw evidence is logged with `grasp_verified=false` and the default gate is manual.
8. **QoS.** Subscriptions are BEST_EFFORT. A RELIABLE subscriber misses `jaw/measured_js`.

## Install

Deployment host: Ubuntu 22.04, ROS 2 Humble, Python 3.10.

```bash
git clone <this repository> surgical-rl
cd surgical-rl/deploy
python3 -m venv --system-site-packages .venv-deploy   # keeps rclpy visible
source .venv-deploy/bin/activate
pip install -r requirements-deploy.txt                 # CPU torch is enough
pip install pytest && python3 -m pytest tests -q       # expect 588 passed
```

Checkpoints are not in Git:

```bash
bash tools/fetch_upstream_checkpoints.sh     # upstream Approach + Place, SHA-256 verified
# R6 (r6_unified_single_goal_yaw15_seed1_final.zip) comes from the team; place it under models/rl/
```

Simulation and training need AMBF, the SRC and `requirements/simulation.txt`.
Install a CUDA PyTorch build first.

## Run the pipeline — in this order

All poses are **tool** poses in the frame `measured_cp` reports (`ECM`).

```bash
source /opt/ros/humble/setup.bash
cd deploy

# 0. Is the arm listening, and how big is its deadband?
python3 tools/poke_arm.py --arm /PSM1 --axis x --distance-mm 2 --execute

# 1. Empty-jaw baseline (EMPTY gripper; redo after any tool change)
python3 tools/calibrate_jaw.py --arm /PSM1 --out jaw_baseline.json --execute

# 2. Rehearse offline, including the failures
python3 tools/offline_grasp_lift.py \
  --start-pos <x y z> --start-quat <qx qy qz qw> \
  --grasp-pos <x y z> --suture-pos <x y z> --suture-quat <qx qy qz qw> --suture-confirmed \
  --controller d2 --grasp-standoff-mm 7 --lift-sign -1 --grasp-gate evidence \
  --lag 0.5 --noise-mm 0.2
#   also try: --empty-gripper, --drop-at-step N, --deadband-mm 1.0 --min-command-mm 1.2

# 3. Dry run on the robot (publishes nothing)
python3 run_pipeline.py --grasp-pos <x y z> --suture-pos <x y z> --suture-quat <q> \
  --jaw-baseline jaw_baseline.json --trace dryrun.jsonl

# 4. Empty-gripper rehearsal: same command + --execute --grasp-gate always, nothing under the jaws

# 5. Live, with a human on the gate and a hand on the e-stop
python3 run_pipeline.py --grasp-pos <x y z> --suture-pos <x y z> --suture-quat <q> \
  --suture-confirmed --controller d2 --interface move_cp --rate 2 \
  --lift-sign -1 --jaw-baseline jaw_baseline.json --min-command-mm <measured> \
  --grasp-gate manual --trace live.jsonl --execute
```

To use the RL policy on the approach leg, add `--controller rl --model <zip> --stage`.
To take the grasp target from vision instead of typing it, add
`--needle-pose <FoundationPose estimate> --grasp-calibration <model.json>`
(see `deploy/README_CALIBRATION.md`).

## Useful tools (`deploy/tools/`)

| Tool | Question it answers |
|---|---|
| `verify_contract.py` | Does our observation builder reproduce the checkpoint's stored observations? |
| `replay_demos.py --compare` | Does a checkpoint work through this loop, at which action scale? |
| `profile_checkpoint.py` | What support was the checkpoint trained on? |
| `workspace_spec.py` | Is the task inside the support, and what staging move fixes it? |
| `offline_grasp_lift.py` | Does the whole sequence complete on a lagging, noisy, deadbanded arm? |
| `poke_arm.py` | Does the arm move at all, and what is its deadband? |
| `residual_structure.py` | What should the grasp residual look like before collecting data? |
| `collect_grasp_calibration.py` / `fit_grasp_calibration.py` | Plan, audit and fit a calibration session |

## Status

| | |
|---|---|
| Hierarchy in simulation (ROS 2) | 11/20 full sutures; published result 52% |
| Upstream Approach through our loop | 45/50 of its own demos (published 96 ± 6%) |
| R6 through our loop | 46/50 at 1.0 mm / 3° |
| Full sequence, offline | completes at arm lag 0 / 0.5 / 0.7, final error 0.06–0.10 cm |
| Real robot | bring-up, dry runs, deadband found and handled. **No closed-loop grasp completed yet** |
| Grasp calibration | 10 hardware samples, none usable: eyeballed poses, plus a ~43 mm constant frame offset still to resolve |

## License

MIT for the code in this repository. AMBF, SRC, SurgicAI, FoundationPose, Depth
Anything, meshes and external checkpoints follow their own licenses.
