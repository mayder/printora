#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACT_DIR="${MUTATION_ARTIFACT_DIR:-${ROOT_DIR}/.artifacts/mutation}"
MIN_SCORE="${PRINTORA_MUTATION_MIN_SCORE:-60}"

mkdir -p "$ARTIFACT_DIR"
cd "$ROOT_DIR/backend"
uv run --extra dev mutmut run --max-children "${PRINTORA_MUTATION_WORKERS:-4}"
uv run --extra dev mutmut export-cicd-stats
cp mutants/mutmut-cicd-stats.json "$ARTIFACT_DIR/stats.json"
uv run --extra dev mutmut results > "$ARTIFACT_DIR/survivors.txt"

python3 - "$ARTIFACT_DIR/stats.json" "$MIN_SCORE" <<'PY'
import json
import sys

stats_path, minimum_text = sys.argv[1:]
stats = json.load(open(stats_path, encoding="utf-8"))
killed = int(stats["killed"])
survived = int(stats["survived"])
tested = killed + survived
score = (100.0 * killed / tested) if tested else 0.0
minimum = float(minimum_text)
print(
    f"mutation_score={score:.2f}% killed={killed} survived={survived} "
    f"no_tests={stats['no_tests']} minimum={minimum:.2f}%"
)
if score < minimum:
    raise SystemExit(
        f"Mutation score crítico {score:.2f}% abaixo do mínimo {minimum:.2f}%"
    )
PY
