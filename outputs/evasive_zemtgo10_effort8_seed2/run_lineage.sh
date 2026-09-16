#!/bin/bash
set -u
cd "/Users/vincenzo/Desktop/Projects/Physics Sim Project/missile_guidance_sim" || exit 1
OUT="outputs/evasive_zemtgo10_effort8_seed2"
PY="./.venv/bin/python"
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
LOG="$OUT/launch.log"
{
  echo "===== START lineage $(date) ====="
  echo "Config: zem_t_go_max_s=10 effort_weight=8 seed=77000001"
} >> "$LOG"
for cp in 1 2 3 4 5; do
  echo "===== START CP${cp} $(date) =====" >> "$LOG"
  if ! "$PY" scripts/run_evasive_checkpoint.py \
      --checkpoint "$cp" \
      --output-dir "$OUT" \
      --effort-weight 8 \
      --zem-t-go-max 10 \
      --seed 77000001 \
      >> "$LOG" 2>&1; then
    ec=$?
    echo "===== FAIL CP${cp} $(date) exit=$ec =====" >> "$LOG"
    exit "$ec"
  fi
  echo "===== DONE CP${cp} $(date) =====" >> "$LOG"
  if grep -q "STOP CONDITION" <(tail -n 30 "$LOG"); then
    echo "NOTE: STOP CONDITION printed at CP${cp}; continuing planned CP1-CP5." >> "$LOG"
  fi
done
echo "===== LINEAGE COMPLETE $(date) =====" >> "$LOG"
