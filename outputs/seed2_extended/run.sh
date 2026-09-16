#!/bin/bash
cd "/Users/vincenzo/Desktop/Projects/Physics Sim Project/missile_guidance_sim"
export PYTHONPATH=src PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=.venv/bin/python
out=outputs/seed2_extended
for cp in 7 8 9 10; do
  [ -f $out/checkpoints/rl_checkpoint_0$cp.zip ] || \
    $PY scripts/run_evasive_checkpoint.py --checkpoint $cp --output-dir $out --seed 77000001 \
      --zem-t-go-max 10 --effort-weight 5 --precision-weight 50 \
      --finetune-log-std -2.0 --learning-rate 5e-5 --ent-coef 0 >> $out/launch.log 2>&1 || { echo "FAIL cp$cp"; exit 1; }
  $PY scripts/eval_checkpoint_large_heldout.py --model $out/checkpoints/rl_checkpoint_0$cp.zip --cases 300 --output $out/eval300_cp$cp.json >> $out/launch.log 2>&1
done
echo "SEED2_EXTENDED DONE"
