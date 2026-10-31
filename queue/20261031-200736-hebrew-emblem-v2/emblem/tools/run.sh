#!/bin/bash
# run.sh VARIANT DRAFT [tune.json]  -> renders and compares
set -e
V=$1; D=$2; TUNE=$3
E=/home/claude/build/days/2026-11-01/emblem
cd /home/claude/work/funkbox
export FUNK_GL_BACKEND=egl FUNK_INPUTS=/home/claude/build/days FUNK_OUT=/home/claude/build/days
python3 /home/claude/build/tools/gen.py $E $V $D $TUNE >/dev/null
case $V in a) REF=A-faithful;; b) REF=B-idf-gold;; c) REF=C-hybrid;; esac
python -m funkbox poster render $E/emblem-$V-draft$D.poster.json --name emblem-$V-draft$D --out $E/renders --formats png,svg 2>&1 | tail -3
python -m funkbox poster compare $E/renders/emblem-$V-draft$D.png /home/claude/build/days/2026-11-01/refs/$REF.png --name compare-$V-draft$D --out $E/compare 2>&1 | tail -40
