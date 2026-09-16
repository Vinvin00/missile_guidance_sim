#!/bin/bash
# Fine-tune each CP6 parent for CP7-CP8 with/without the precision bonus, then 300-case eval.
cd "/Users/vincenzo/Desktop/Projects/Physics Sim Project/missile_guidance_sim"
export PYTHONPATH=src PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=.venv/bin/python
job() { # parent seed pw effort
  parent=$1 seed=$2 pw=$3 effort=$4
  out=outputs/precision_ft_lownoise/${parent}_pw${pw}
  mkdir -p $out/checkpoints
  src=outputs/evasive_zemtgo10_${parent}
  [ -f $out/checkpoints/rl_checkpoint_06.zip ] || { cp $src/checkpoints/rl_checkpoint_06.zip $out/checkpoints/; cp $src/rl_checkpoint_06.json $src/rl_checkpoint_06_eval.json $out/; }
  for cp in 7 8; do
    [ -f $out/checkpoints/rl_checkpoint_0$cp.zip ] || $PY scripts/run_evasive_checkpoint.py --checkpoint $cp --output-dir $out --seed $seed \
      --zem-t-go-max 10 --effort-weight $effort --precision-weight $pw --finetune-log-std -2.0 --learning-rate 5e-5 --ent-coef 0 >> $out/launch.log 2>&1 || { echo "FAIL $out cp$cp"; return; }
    [ -f $out/eval300_cp$cp.json ] || $PY scripts/eval_checkpoint_large_heldout.py --model $out/checkpoints/rl_checkpoint_0$cp.zip --cases 300 --output $out/eval300_cp$cp.json >> $out/launch.log 2>&1
    tail -1 $out/launch.log
  done
}
job seed2 77000001 50 5 &
job seed3 43500777 50 5 &
job seed4 61803399 50 5 &
job seed5 27182818 50 5 &
job seed6 31415926 50 5 &
job seed7 14142135 50 5 &
job effort8_seed2 77000001 50 8 &
job seed2 77000001 0 5 &
job seed4 61803399 0 5 &
job seed3 43500777 0 5 &
wait
echo ALL DONE
