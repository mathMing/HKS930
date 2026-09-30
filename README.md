# HKS930 · ARC-Bench Agent

Octos-based ARC-Bench submission source for the GitHub-style ERP and Spreadsheet tasks. This repository contains the V3 agent adapter and its local test harness, not generated applications or the full upstream Octos Rust repository.

## Layout

- `arc/main.py`, `arc/verify_node.py`, `arc/octos_stdio.py`: platform entry, per-requirement acceptance, and Octos runtime connection.
- `arc/arc-policy.toml`, `arc/prompts/`, `arc/template/`: execution policy, model instructions, and generic web starter.
- `arc/public-tests/`, `arc/tests/`, `arc/tasks/`: public browser examples, adapter unit tests, and local benchmark fixtures.
- `arcbench-hackathon-requirements/`: the two competition requirement YAML files.

## Offline checks and packaging

From the repository root, install `arc/requirements.txt`, then run:

```sh
python -m unittest discover -s arc/tests -t arc
python arc/contest-local.py --check
sh arc/pack.sh
```

`arc/pack.sh` builds the submission ZIP with `main.py` at its root and enforces the 1,360-line Python limit. It does not include credentials, local results, or the unit tests. Local model runs require a separately configured API key and an Octos binary; never commit either credential or generated output. See `arc/README.md` for development details.

The Playwright results are local mirror tests, not official ARC-Bench scores. V3 records sanitized acceptance outcomes in `.arc/check-results.jsonl` and stops on confirmed infrastructure failures.

The Octos runtime is fetched from the release pinned by `arc-runtime-lock.json`; upstream source is at [octos-org/octos-arc](https://github.com/octos-org/octos-arc).
