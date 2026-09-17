#!/usr/bin/env python3
"""Detached RL training babysitter. Survives shell teardown (double-fork)."""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/Users/vincenzo/Desktop/Projects/Physics Sim Project/missile_guidance_sim")
QUEUE_DIR = ROOT / "outputs" / "train_queue"
LOG = QUEUE_DIR / "babysit.log"
PIDFILE = QUEUE_DIR / "babysit.pid"
PYTHON = str(ROOT / ".venv" / "bin" / "python")
SCRIPT = str(ROOT / "scripts" / "run_evasive_checkpoint.py")
EVAL_SCRIPT = str(ROOT / "scripts" / "eval_checkpoint_large_heldout.py")

BASE_EXTRA = ["--zem-t-go-max", "10", "--effort-weight", "5"]
PREC_EXTRA = BASE_EXTRA + [
    "--precision-weight", "50",
    "--finetune-log-std", "-2.0",
    "--learning-rate", "5e-5",
    "--ent-coef", "0",
]
EFFORT8_BASE = ["--zem-t-go-max", "10", "--effort-weight", "8"]
EFFORT8_PREC = EFFORT8_BASE + [
    "--precision-weight", "50",
    "--finetune-log-std", "-2.0",
    "--learning-rate", "5e-5",
    "--ent-coef", "0",
]

# Large held-out evals first (skip if output json already exists)
EVAL_JOBS = [
    # seed2_extended CP10 already evaluated; keep list empty unless a missing eval is queued
]

# Ordered training: (outdir relative, seed, start_cp, end_cp, extra_cli, largeeval_after)
# largeeval_after: if True, run 300-case eval after each finished CP in this job
# seed4/effort8_seed2/seed5 CP7-8 done; continue seed8 recipe with fresh seeds
JOBS = [
    # seed17/seed18 complete; continue seed8 recipe with fresh seeds
    ("outputs/evasive_zemtgo10_seed19", 3316624790, 1, 6, BASE_EXTRA, False),
    ("outputs/evasive_zemtgo10_seed19", 3316624790, 7, 8, PREC_EXTRA, True),
    ("outputs/evasive_zemtgo10_seed20", 3605551275, 1, 6, BASE_EXTRA, False),
    ("outputs/evasive_zemtgo10_seed20", 3605551275, 7, 8, PREC_EXTRA, True),
]


def log(msg: str) -> None:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    line = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    with LOG.open("a") as f:
        f.write(line + "\n")
        f.flush()


def highest_checkpoint(outdir: Path) -> int:
    ck = outdir / "checkpoints"
    if not ck.is_dir():
        return 0
    best = 0
    for p in ck.glob("rl_checkpoint_*.zip"):
        try:
            n = int(p.stem.split("_")[-1])
        except ValueError:
            continue
        best = max(best, n)
    return best


def any_heavy_job_running() -> bool:
    try:
        out = subprocess.check_output(["ps", "aux"], text=True)
    except Exception:
        return False
    for line in out.splitlines():
        if "grep" in line:
            continue
        if "run_evasive_checkpoint.py" in line:
            return True
        if "eval_checkpoint_large_heldout.py" in line:
            return True
        if "for i in 1 2 3 4 5 6" in line and "run_evasive_checkpoint" in line:
            return True
    return False


def train_running(outdir: Path) -> bool:
    needle = outdir.name
    try:
        out = subprocess.check_output(["ps", "aux"], text=True)
    except Exception:
        return False
    for line in out.splitlines():
        if "run_evasive_checkpoint.py" in line and needle in line and "grep" not in line:
            return True
    return False


def run_eval(model_rel: str, output_rel: str) -> int:
    model = ROOT / model_rel
    output = ROOT / output_rel
    if output.is_file():
        log(f"skip eval exists {output.name}")
        return 0
    if not model.is_file():
        log(f"ABORT eval missing model {model}")
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    launch = QUEUE_DIR / "largeeval.log"
    cmd = [
        PYTHON, EVAL_SCRIPT,
        "--model", str(model),
        "--cases", "300",
        "--output", str(output),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["PYTHONUNBUFFERED"] = "1"
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    log(f"START eval {model.name} -> {output.name}")
    with launch.open("a") as lf:
        lf.write(f"\n==== {time.strftime('%Y-%m-%d %H:%M:%S')} {' '.join(cmd)} ====\n")
        lf.flush()
        proc = subprocess.Popen(cmd, cwd=str(ROOT), env=env, stdout=lf, stderr=subprocess.STDOUT)
        rc = proc.wait()
    if rc == 0 and output.is_file():
        try:
            d = json.loads(output.read_text())
            line = (
                f"{model_rel}: {d.get('n_hits')}/{d.get('n_cases')} hits "
                f"({100.0 * float(d.get('hit_rate', 0)):.1f}%), median miss "
                f"{float(d.get('median_miss_distance_m', 0)):.1f} m -> {output_rel}\n"
            )
            with launch.open("a") as lf:
                lf.write(line)
            log(line.strip())
        except Exception as e:
            log(f"eval summary append failed: {e!r}")
    log(f"DONE eval {output.name} rc={rc}")
    return rc


def run_checkpoint(outdir: Path, seed: int, cp: int, extra: list[str]) -> int:
    outdir.mkdir(parents=True, exist_ok=True)
    launch = outdir / "launch.log"
    cmd = [
        PYTHON, SCRIPT,
        "--checkpoint", str(cp),
        "--output-dir", str(outdir),
        "--seed", str(seed),
        *extra,
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["PYTHONUNBUFFERED"] = "1"
    env["OMP_NUM_THREADS"] = "1"
    env["MKL_NUM_THREADS"] = "1"
    log(f"START cp={cp} out={outdir.name} seed={seed} cmd={' '.join(cmd)}")
    with launch.open("a") as lf:
        lf.write(f"\n==== babysit CP{cp} {time.strftime('%Y-%m-%d %H:%M:%S')} ====\n")
        lf.flush()
        proc = subprocess.Popen(cmd, cwd=str(ROOT), env=env, stdout=lf, stderr=subprocess.STDOUT)
        rc = proc.wait()
    log(f"DONE cp={cp} out={outdir.name} rc={rc}")
    return rc


def process_jobs() -> None:
    os.chdir(ROOT)
    if any_heavy_job_running():
        log("wait: another trainer/eval is already running")
        return

    for model_rel, output_rel in EVAL_JOBS:
        if any_heavy_job_running():
            log("wait: heavy job appeared mid-eval queue")
            return
        rc = run_eval(model_rel, output_rel)
        if rc != 0:
            log(f"ABORT eval {output_rel} rc={rc}; will retry later")
            return

    for rel, seed, start_cp, end_cp, extra, largeeval_after in JOBS:
        outdir = ROOT / rel
        while train_running(outdir) or any_heavy_job_running():
            log(f"wait: external job owns {outdir.name}")
            time.sleep(60)
        done = highest_checkpoint(outdir)
        next_cp = max(start_cp, done + 1)
        if next_cp > end_cp:
            # Still may need largeevals for existing CPs
            if largeeval_after:
                for cp in range(start_cp, end_cp + 1):
                    model_rel = f"{rel}/checkpoints/rl_checkpoint_{cp:02d}.zip"
                    output_rel = f"{rel}/eval300_cp{cp}.json"
                    if (ROOT / model_rel).is_file() and not (ROOT / output_rel).is_file():
                        rc = run_eval(model_rel, output_rel)
                        if rc != 0:
                            return
            log(f"skip complete {outdir.name} through CP{done}")
            continue
        for cp in range(next_cp, end_cp + 1):
            if train_running(outdir) or any_heavy_job_running():
                log(f"yield {outdir.name} to external job")
                return
            done = highest_checkpoint(outdir)
            if cp <= done:
                log(f"skip already have CP{cp} in {outdir.name}")
            else:
                rc = run_checkpoint(outdir, seed, cp, extra)
                if rc != 0:
                    log(f"ABORT {outdir.name} CP{cp} rc={rc}; will retry later")
                    return
            if largeeval_after:
                model_rel = f"{rel}/checkpoints/rl_checkpoint_{cp:02d}.zip"
                output_rel = f"{rel}/eval300_cp{cp}.json"
                rc = run_eval(model_rel, output_rel)
                if rc != 0:
                    return


def daemonize() -> None:
    if os.fork() > 0:
        sys.exit(0)
    os.setsid()
    if os.fork() > 0:
        sys.exit(0)
    sys.stdin.close()
    log_f = open(LOG, "a", buffering=1)
    os.dup2(log_f.fileno(), 1)
    os.dup2(log_f.fileno(), 2)


def main() -> None:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    if "--foreground" not in sys.argv:
        daemonize()
    PIDFILE.write_text(str(os.getpid()))
    log(f"babysit online pid={os.getpid()} queue=seed19+seed20_seed8_recipe")
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    while True:
        try:
            process_jobs()
        except Exception as e:
            log(f"error: {e!r}")
        time.sleep(90)


if __name__ == "__main__":
    main()
