#!/usr/bin/env python3
"""Fine-tune the current baseline on saved play-mode rounds, then gate it.

Offline on purpose: visitors never change the live model. This script

1. loads the rounds saved by play mode (``api/play.py``) and holds out every
   4th one, which the candidate never trains on;
2. fine-tunes a copy of the current baseline with the same low-noise recipe
   that produced it (CP7-CP8), mixing replayed human rounds into the usual
   evasive training episodes;
3. scores baseline and candidate on the frozen held-out evasive cases and on
   the held-out human rounds, and prints whether the candidate may be
   promoted. It never edits ``CURRENT_RL_BASELINE.json``.

A replayed round is the pilot's recorded stick, not the pilot: it does not
react to a model that flies differently. Seeker delays are also redrawn, so
a replay is close to, not identical to, the round the visitor saw.

Stop it any time; rerun the same command to resume from the last block.

Usage:
    python scripts/retrain_from_rounds.py --name 2026-11-first
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import gymnasium as gym
import numpy as np
import torch
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

from guidance_sim.api import play
from guidance_sim.api.catalog import resolve_live_parameters
from guidance_sim.api.live_stream import _initial_condition_sampler
from guidance_sim.ml.policy_inference import load_baseline_pointer
from guidance_sim.physics.atmosphere import G0
from guidance_sim.physics.maneuvers import PlayerManeuver
from guidance_sim.rl.actions import action_dimension
from guidance_sim.rl.environment import InterceptionEnv
from guidance_sim.rl.evasive_scenarios import (
    build_held_out_cases,
    evasive_initial_conditions,
    evasive_maneuver_factory,
)
from guidance_sim.rl.training import (
    EvaluationCase,
    evaluate_policy,
    evasive_redesign_config,
)

BLOCK_TIMESTEPS = 20_480  # resume granularity; a multiple of n_steps * n_envs
MAX_FROZEN_MISS_M = 25.0  # every promoted checkpoint so far stays under this


def finetune_config():
    """The recipe that produced the current baseline's CP7-CP8."""

    return evasive_redesign_config(
        precision_weight=50.0, finetune_log_std=-2.0, learning_rate=5e-5, ent_coef=0.0
    )


def round_builders(record: dict):
    """(initial-condition sampler, maneuver factory) replaying one saved round."""

    sampler = _initial_condition_sampler(resolve_live_parameters(record["parameters"]))

    def maneuver(_rng: np.random.Generator) -> PlayerManeuver:
        return PlayerManeuver(
            record["max_g"] * G0, trace=record["inputs"], dt=record["dt_s"]
        )

    return sampler, maneuver


def round_cases(records: list[dict]) -> tuple[EvaluationCase, ...]:
    """Saved rounds as cases for the existing ``evaluate_policy`` loop."""

    cases = []
    for index, record in enumerate(records):
        sampler, maneuver = round_builders(record)

        def initial_conditions(_rng, sampler=sampler, seed=record["seed"]):
            return sampler(np.random.default_rng(seed))  # the round's own start

        _pursuer, target = initial_conditions(None)
        cases.append(
            EvaluationCase(
                name=f"round_{index:04d}_{record['outcome']}",
                target_position_m=tuple(float(v) for v in target.position),
                target_velocity_m_s=tuple(float(v) for v in target.velocity),
                maneuver="player",
                maneuver_builder=maneuver,
                initial_condition_builder=initial_conditions,
            )
        )
    return tuple(cases)


def mixed_samplers(records: list[dict], human_fraction: float):
    """Training episodes: a replayed human round with the given probability,
    otherwise the usual evasive episode.

    ``InterceptionEnv.reset`` calls the initial-condition sampler before the
    maneuver factory, so the first decides and the second follows it.
    """

    builders = [round_builders(record) for record in records]
    picked: list = [None]

    def initial_conditions(rng: np.random.Generator):
        human = bool(builders) and rng.random() < human_fraction
        picked[0] = builders[int(rng.integers(len(builders)))] if human else None
        return (picked[0][0] if human else evasive_initial_conditions)(rng)

    def maneuver(rng: np.random.Generator):
        return (picked[0][1] if picked[0] else evasive_maneuver_factory)(rng)

    return initial_conditions, maneuver


def split_rounds(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """(train, held out). Every 4th round is never trained on."""

    return (
        [r for i, r in enumerate(records) if i % 4 != 3],
        [r for i, r in enumerate(records) if i % 4 == 3],
    )


def make_vec_env(config, records: list[dict], human_fraction: float, seed: int):
    n_action = action_dimension(config.action_layout)

    def make_env() -> gym.Env:
        initial_conditions, maneuver = mixed_samplers(records, human_fraction)
        env = InterceptionEnv(
            config=config.simulation_config(),
            reward_config=config.reward_config(),
            initial_condition_sampler=initial_conditions,
            maneuver_factory=maneuver,
            action_layout=config.action_layout,
            use_target_turn_rate_obs=config.use_target_turn_rate_obs,
            tracking=config.tracking,
        )
        return gym.wrappers.RescaleAction(
            env,
            min_action=np.full(n_action, -1.0, dtype=np.float32),
            max_action=np.full(n_action, 1.0, dtype=np.float32),
        )

    vec_env = DummyVecEnv([make_env for _ in range(config.n_envs)])
    vec_env.seed(seed)
    return VecMonitor(vec_env)


def score(model, config, cases) -> dict:
    if not cases:
        return {"hits": 0, "cases": 0, "max_miss_m": 0.0, "hit_by_case": {}}
    summary = evaluate_policy(
        model,
        cases=cases,
        simulation_config=config.simulation_config(),
        action_layout=config.action_layout,
        use_target_turn_rate_obs=config.use_target_turn_rate_obs,
        tracking=config.tracking,
        reward_config=config.reward_config(),
    )
    return {
        "hits": summary.n_hits,
        "cases": summary.n_cases,
        "max_miss_m": max(case.miss_distance_m for case in summary.cases),
        "hit_by_case": {case.name: case.hit for case in summary.cases},
    }


def verdict(baseline: dict, candidate: dict) -> tuple[bool, list[str]]:
    """Promotion gate. Thresholds are fixed here; do not tune them to a result."""

    reasons = []
    if candidate["frozen"]["hits"] < baseline["frozen"]["hits"]:
        reasons.append("fewer hits than the baseline on the frozen evasive cases")
    if candidate["frozen"]["max_miss_m"] >= MAX_FROZEN_MISS_M:
        reasons.append(f"worst frozen miss is not under {MAX_FROZEN_MISS_M:g} m")
    if candidate["human_held_out"]["hits"] <= baseline["human_held_out"]["hits"]:
        reasons.append("does not catch more held-out human rounds than the baseline")
    return not reasons, reasons


def train(args, config, records: list[dict], baseline_path: Path, out: Path) -> Path:
    candidate_path = out / "candidate.zip"
    state_path = out / "state.json"
    done = json.loads(state_path.read_text())["timesteps"] if state_path.exists() else 0
    lr = config.learning_rate
    custom_objects = {
        "learning_rate": lr,
        "lr_schedule": lambda _progress: lr,
        "ent_coef": config.ent_coef,
    }
    while done < args.timesteps:
        vec_env = make_vec_env(config, records, args.human_fraction, args.seed + done)
        model = RecurrentPPO.load(
            candidate_path if done else baseline_path,
            env=vec_env,
            device="cpu",
            custom_objects=custom_objects,
        )
        if not done:
            with torch.no_grad():
                model.policy.log_std.fill_(config.finetune_log_std)
        model.set_random_seed(args.seed + done)
        started = time.monotonic()
        model.learn(total_timesteps=BLOCK_TIMESTEPS, reset_num_timesteps=False)
        vec_env.close()
        model.save(candidate_path)
        done += BLOCK_TIMESTEPS
        state_path.write_text(json.dumps({"timesteps": done}))
        print(
            f"trained {done}/{args.timesteps} steps "
            f"({BLOCK_TIMESTEPS / (time.monotonic() - started):.0f} steps/s)",
            flush=True,
        )
    return candidate_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="run folder under outputs/player_finetune/")
    parser.add_argument("--timesteps", type=int, default=204_800, help="one checkpoint's worth by default")
    parser.add_argument("--human-fraction", type=float, default=0.25)
    parser.add_argument("--min-rounds", type=int, default=40, help="refuse to train on fewer saved rounds")
    parser.add_argument("--eval-cases", type=int, default=300, help="frozen evasive cases; 300 matches the baseline's record")
    parser.add_argument("--seed", type=int, default=20_261_115)
    parser.add_argument("--threads", type=int, default=1, help="torch CPU threads; 1 is reproducible and laptop-friendly")
    args = parser.parse_args(argv)
    if args.timesteps % BLOCK_TIMESTEPS:
        parser.error(f"--timesteps must be a multiple of {BLOCK_TIMESTEPS}")

    records = play.load_rounds()
    if len(records) < args.min_rounds:
        print(f"Only {len(records)} saved rounds at {play.rounds_path()}; need {args.min_rounds}. Nothing trained.")
        return 1
    train_rounds, held_out_rounds = split_rounds(records)

    os.nice(10)
    torch.set_num_threads(args.threads)
    config = finetune_config()
    baseline_path = load_baseline_pointer().model_path
    out = play._REPO_ROOT / "outputs" / "player_finetune" / args.name
    out.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=play._REPO_ROOT
    ).stdout.strip()
    (out / "run.json").write_text(
        json.dumps({"argv": sys.argv, "git_commit": commit, "baseline": str(baseline_path),
                    "rounds": len(records), "train_rounds": len(train_rounds),
                    "held_out_rounds": len(held_out_rounds)}, indent=2) + "\n"
    )
    print(f"{len(records)} rounds: {len(train_rounds)} to train on, {len(held_out_rounds)} held out", flush=True)

    candidate_path = train(args, config, train_rounds, baseline_path, out)

    frozen_cases = build_held_out_cases(args.eval_cases)
    human_cases = round_cases(held_out_rounds)
    results = {}
    for label, path in (("baseline", baseline_path), ("candidate", candidate_path)):
        model = RecurrentPPO.load(path, device="cpu")
        results[label] = {
            "frozen": score(model, config, frozen_cases),
            "human_held_out": score(model, config, human_cases),
        }
        print(f"scored {label}", flush=True)
    eligible, reasons = verdict(results["baseline"], results["candidate"])
    (out / "report.json").write_text(
        json.dumps({"eligible": eligible, "reasons": reasons, **results}, indent=2) + "\n"
    )

    print(f"\n{'':10s} {'frozen evasive':>16s} {'worst miss':>11s} {'held-out human':>15s}")
    for label, result in results.items():
        frozen, human = result["frozen"], result["human_held_out"]
        print(
            f"{label:10s} {frozen['hits']:>11d}/{frozen['cases']:<4d} "
            f"{frozen['max_miss_m']:>9.1f} m {human['hits']:>10d}/{human['cases']:<4d}"
        )
    print("\nMay be promoted." if eligible else "\nNot promoted: " + "; ".join(reasons) + ".")
    print(f"Candidate and report: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
