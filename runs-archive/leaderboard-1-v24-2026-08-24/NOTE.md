# Leaderboard cohort 1 — re-judged under v2.4 (2026-08-24)

The same eleven agents' cell records (nine cohort-1 runs + the two
reference-run-2 models), re-judged by the **self-hosted Qwen3.6-35B-A3B
IQ4_XS** — v2.4-qualified on all seven axes, local and free — under the
v2.4 rubric questions. Nothing was re-run: the records are identical to
the v1.3-judged and v2.2/luna-judged archives
(`../leaderboard-1-v13judge-2026-08-23/`,
`../leaderboard-1-v2-2026-08-23/`); only the judge and the questions
changed.

**Two variables moved together, and this board cannot separate them.**
The previous edition was luna @ v2.2; this one is the self-hosted Qwen3.6
@ v2.4. Rank correlation with it is **0.72** (v1.3 → v2.2 was 0.45).
Attributing the movement to the rubric edit alone would be a claim this
run does not support; isolating it needs one more edition holding either
the judge or the question set fixed.

Measured deltas across the eleven agents (same cells, both boards):

| axis | agents up | down | mean delta |
|---|---|---|---|
| grounding | 5 | 1 | **+0.24** |
| wall-pricing | 1 | 5 | **−0.23** |
| object-hold | 2 | 3 | −0.06 |
| empty-measure | 0 | 2 | −0.06 |
| relief-page | 0 | 1 | −0.03 |
| handoff-verification | 0 | 0 | 0.00 |
| route-discipline | 0 | 0 | 0.00 (n/a for all but one agent) |

handoff-verification is one of the three axes v2.4 edited and it did not
move on a single agent — so the edit alone does not account for the two
axes that did.

Reproduce: `scripts/journeyman_rejudge.py SRC DEST --judge <url>
--judge-model <model>` per agent, then `scripts/journeyman_leaderboard.py`
over the resulting `report.json` files (notes sidecar:
`docs/research/journeyman-real-calibration/leaderboard-notes.json` in the
development monorepo). Cost: ~2 h of local GPU, $0.
