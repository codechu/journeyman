# The judge registry

<p align="center"><img src="../assets/judges.jpg" alt="A guild master seals one examiner's certificate under lantern light; a long row of unsealed certificates waits in shadow, and a lens is turned on the examiner's own scale." width="100%"></p>

Journeyman grades agents with two layers: deterministic event-metrics
computed by the scene itself, and a **judge** — a model that reads the
transcript and scores what cannot be counted. A judge's verdicts are only
worth what the judge can see, so no model is trusted as `--judge` on
reputation: it sits an exam first.

This page is the public registry: how the badge is earned, who holds it,
and — just as important — who was examined and did not.

## The exam

```
journeyman qualify --set journeyman/calibration/v1_real.json \
    --judge <endpoint> --judge-model <model> --repeats 3
```

- **The set** (shipped in the package, currently revision **v1.3, 59
  cases**) is distilled from real reference-run transcripts of third-party
  models — not synthetic vignettes. Every case was labelled blind by a
  three-labeller panel (≥2/3 agreement required; splits discarded), grey
  cases went to a human adjudicator, and the contested tail was probed
  with a cross-family panel (three non-Claude labellers): 6 of 9 decidable
  cases agreed; the two that split 2-1 in *every* panel are flagged
  `cross_family_contested` in the set rather than hidden.
- **The bar:** accuracy ≥ 0.8 on every axis, each case decided by a
  3-repeat majority vote. Miss one axis, no badge.
- **The badge** is per model *and* per route: a quantized local build and
  a cloud deployment of the same weights are examined separately.

## Qualified judges

| judge | route | exam | result | cost per exam |
|---|---|---|---|---|
| **Qwen3.6-35B-A3B** | self-hosted, GGUF IQ4_XS (llama.cpp) | v1.3, 6/6 axes, mean 0.96 | **QUALIFIED** (2026-08-20) | free, ~35 min |
| **Qwen3.6-35B-A3B** | cloud, OpenRouter `qwen/qwen3.6-35b-a3b` | v1.3, 6/6 axes, mean 0.95 (empty-measure 0.82, grounding 0.88, rest 1.0) | **QUALIFIED** (2026-08-20) | ~$0.25, ~25 min |

The same open-weights model holds the badge on both routes, so there are
two ways to run a qualified judge: **host it yourself for free, or rent
it for about a quarter per exam.** The local row is a recipe, not our
machine — any llama.cpp host with the IQ4_XS build reproduces it.

**Historical:** GLM-5.2 qualified on set revision v1.1 (mean 0.98) and
fell one axis short on a draw when re-examined on v1.3. The v1.1 badge
stands as a historical record; re-rolling exams until one passes would
turn the badge into a lottery, so it was not re-run.

**Hors concours:** Claude Sonnet 5 (`claude-sonnet-5`; model id
receipt-verified across all 75 exam agents' transcripts) sat the v1.3
exam (2026-08-22) and passed every axis — empty-measure 17/17 in single
draws, the only perfect empty-measure score ever recorded, object-hold
0.88 by majority-of-three. It passed, and it earns that said plainly.
It is listed outside the badge registry for a structural reason, not a
performance one: the calibration labels were authored by blind Sonnet
panels running the **same model id** (`claude-sonnet-5`, verified from
the labelling sessions' transcripts), so the pass cannot distinguish
judging skill from self-agreement — the exam's ground truth is, in
part, its own voice. (The
run still carried one honest signal: on one contested case Sonnet's
majority went *against* its own family's label — the family prime is
not a mirror.) A Claude-family badge would require a calibration set
labelled outside the family; that gate stays open.

## Examined and not qualified

Twenty-plus configurations sat the exam or its screening gate
(empty-measure + wall-pricing first, hardest cases first). That most
fail **is the finding**: judging process-quality is not proportional to
model size or price.

Full exams (all axes sat, or eliminated mid-exam when an axis could
mathematically no longer reach 0.8):

| judge | exam | what felled it |
|---|---|---|
| GPT-OSS-120B | v1.1 & v1.3 | empty-measure — best attempt 5/6 with em 0.67; on v1.3, em 0.64 |
| GPT-5.6-Luna | v1.3 | empty-measure 0.43 — every other axis 1.0 |
| Grok-4.3 | v1.3 | wall-pricing 0.0 (early exit; em 0.67 at the time) |
| DeepSeek chat | v1.1 | 3/6 — em 0.44, wall-pricing 0.50, route 0.78 |
| Qwen3-235B | v1.1 | 3/6 — em 0.56, relief-page 0.56 (size bought nothing) |
| Gemini Flash Lite | v1.1 | 0/6 — no axis at threshold |

Screening eliminations (the funnel: empty-measure + wall-pricing
subset, hardest cases first, mathematical early exit — a failing
candidate costs cents):

| judge | screen result |
|---|---|
| Llama-4 Maverick | em 0.56 · wp 0.38 |
| MiniMax | em 0.67 · wp 0.75 |
| Mistral Small | em 0.44 · wp 0.38 |
| GPT-OSS-20B | em 0.56 · wp 0.88 |
| Qwen3-30B | em 0.44 · wp 0.38 |
| Gemini Flash | em 0.50 (early exit) |
| GLM-4.6 | em 0.50 (early exit; wp 1.0 — the family transfer did not carry the em muscle) |
| Kimi K2 | em 0.67 (early exit) |
| Gemini 2.5 Pro | em 0.67 (early exit) |
- The discriminating axis is **empty-measure** — noticing that work has
  stopped yielding information. No examined model other than the badge
  holders read it at threshold.

## Named limits

Disclosed, not denied:

- The ground-truth labels come from a single labeller family plus one
  human adjudicator. The cross-family probe above dissolved most of the
  family-bias concern, but two irreducible micro-cases remain flagged,
  and one divergence is editorial by design (a closing report that
  elevates an unsupported story into an action item is `mixed` here,
  even where average models read it leniently).
- **Claude-family models are permanently ineligible as judges** — they
  are the labeller family; qualifying them would grade the labellers
  with their own pen.
- The premium tier ($1-12+/M) was deliberately not examined: the goal
  was a free-or-cheap qualified judge, and that exists. The gate stays
  open — hardest-first ordering eliminates a failing candidate for
  under a dollar if the question ever matters.

## Qualify your own

Any OpenAI-compatible endpoint can sit the exam with the command above.
If your judge clears 0.8 on all axes, it is qualified in the only sense
this project recognizes: measured, on labelled cases, with the records
kept. Exam records behind this page (per-axis accuracies, misses, dates)
are archived by the maintainers as decision-record JSONs; the summary
here is transcribed from them.
