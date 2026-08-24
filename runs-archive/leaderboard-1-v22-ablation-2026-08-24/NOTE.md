# Ablation — same judge, older questions (2026-08-24)

The v2.4 board changed two things at once against its predecessor: the
judge (`openai/gpt-5.6-luna` → the self-hosted Qwen3.6) *and* the rubric
(v2.2 → v2.4). This third edition holds the judge fixed and rolls the
questions back to v2.2 — the same text the luna board used, checked out
of git rather than retyped — so the 2×2 has three of its four cells:

| | v2.2 questions | v2.4 questions |
|---|---|---|
| judge: luna | `../leaderboard-1-v2-2026-08-23/` | — |
| judge: self-hosted Qwen3.6 | **this archive** | `../leaderboard-1-v24-2026-08-24/` |

Predictions were frozen before the run. Result, over the eleven agents:

| axis | rubric effect (same judge) | judge effect (same questions) |
|---|---|---|
| **wall-pricing** | **−0.40** (7/10 agents changed) | +0.17 (4/10) |
| **grounding** | −0.06 (4/11) | **+0.31** (5/11) |
| handoff-verification | 0.00 (0/10) | 0.00 (0/10) |
| object-hold | −0.00 (6/11 changed) | −0.06 (2/11) |
| empty-measure | −0.03 (3/11) | −0.03 (1/11) |
| relief-page | 0.00 (0/10) | −0.03 (1/10) |

**The two axes that moved have different causes.** The wall-pricing
collapse is the rubric: v2.4 asks for the filed-report marker, and under
the same judge the older question keeps the old scores — clearest on
`moonshotai/kimi-k2`, which reads 1.00 under luna@v2.2, 1.00 under
Qwen@v2.2, and 0.00 under Qwen@v2.4. The grounding rise is the judge:
the rubric barely moves it, the judge swap accounts for almost all of it.

**Noise is axis-dependent, and one control says so.** handoff-verification
did not change on a single agent in either comparison — the null control
held. object-hold changed on 6 of 11 agents while its mean stayed at zero:
direction-free churn, i.e. real single-draw noise on that axis (verdicts
are one draw per cell; judge draws carry no seed). Both findings above are
larger and one-directional, well outside that churn — but a per-axis noise
band has still not been measured, and neither number should be read as
tighter than "much bigger than the churn we can see."
