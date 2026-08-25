# The judge registry

<p align="center"><img src="../assets/judges.jpg" alt="A guild master seals one examiner's certificate under lantern light; a long row of unsealed certificates waits in shadow, and a lens is turned on the examiner's own scale." width="100%"></p>

Journeyman grades agents with two layers: deterministic event-metrics
computed by the scene itself, and a **judge** — a model that reads the
transcript and scores what cannot be counted. A judge's verdicts are only
worth what the judge can see, so no model is trusted as `--judge` on
reputation: it sits an exam first.

This page is the public registry: how the badge is earned, who holds it,
and — just as important — who was examined and did not.

> **Which judge to point `--judge` at today (2026-08-24):** the
> self-hosted **Qwen3.6-35B-A3B** (IQ4_XS) — v2.4-qualified on all seven
> axes, local and free, and the judge behind the current
> [leaderboard](leaderboard.md). If you would rather rent one,
> `z-ai/glm-5.2` scores 1.00 on every axis and `openai/gpt-5.6-luna`
> qualifies more cheaply. Claude Sonnet 5 sat on the labelling council
> and is out of the badge registry either way.

## The exam

```
journeyman qualify --judge <endpoint> --judge-model <model> --repeats 3
# default set: journeyman/calibration/v2_real.json (--set for another)
```

- **The set** (shipped in the package, and on the Hub as
  [`codechu/journeyman-calibration`](https://huggingface.co/datasets/codechu/journeyman-calibration)
  if you would rather read it than install it, currently **v2_real: 82 cases,
  all seven judged axes**) is distilled from real reference-run
  transcripts of third-party models — not synthetic vignettes. v2 labels
  come from a three-family council (claude-sonnet-5, kimi-k2, grok-4.3):
  a blind round, then an anonymous evidence-quoted second round; a label
  is sealed only with support from at least two families, two split
  cases were ruled by the maintainer, and empty-measure is counted
  mechanically under its v2 definition. The rubric questions went
  through the same council first. The set has been corrected three times
  since it froze at 70: four cases whose only closing report the scene
  refused were relabelled to the unfiled branches, twelve fresh
  filed-report cases were harvested to keep unfiled cases from dominating
  two axes (25% → 14%), and one harvested case was relabelled after every
  examined judge read it against the key. Details in
  [methodology](methodology.md).
- **The bar:** accuracy ≥ 0.8 on every axis, each case decided by a
  3-repeat majority vote. Miss one axis, no badge.
- **The badge** is per model *and* per route: a quantized local build and
  a cloud deployment of the same weights are examined separately.

## The ledger — v2.4 (2026-08-24)

| judge | route | em | result |
|---|---|---|---|
| **GLM-5.2** (`z-ai/glm-5.2`) | cloud, OpenRouter | 1.0 | **QUALIFIED** — 1.00 on all seven axes |
| **GPT-5.6-Luna** (`openai/gpt-5.6-luna`) | cloud, OpenRouter | 1.0 | **QUALIFIED** — grounding 0.86, rest 1.00 |
| **Qwen3.6-35B-A3B + identity** (self-hosted) | local, free | 0.94 | **QUALIFIED** — grounding 0.93, wall-pricing 0.93, rest 1.00 |
| Claude Sonnet 5 | session | 0.94 | not qualified under v2.4 — grounding 0.79, wall-pricing 0.79; hors concours either way (council member) |
| **Qwen3.6-35B-A3B**, stock | local, free | 0.88 | **QUALIFIED** — grounding 0.86, wall-pricing 0.86, rest 1.00 |

**A sentence we had not written was doing the failing.** Under the v2.3
text three of four judges failed grounding and wall-pricing, and we wrote
that up as "two hard axes". Asked which clause was weakest — with the
disagreement cases as evidence — the badged judge answered that our
refused-report clause described only the negative: it says a report call
answered with "budget exhausted" was refused, but never says what a
*filed* report's tool result looks like ("(report filed — job closed)"),
so a judge reading a complete-looking report text in the transcript had
nothing to check it against. We added that one sentence, froze a
prediction, and re-ran: Luna went from failing grounding at 0.71 to
0.86 and a badge; the control judge went from 0.93/0.92 to 1.00 on every
axis; the self-hosted judge went from failing both axes to 0.93/0.93 and
a badge. The axes were not hard. The rubric was quiet.

**The sentence did not reach every judge.** Claude Sonnet 5 sat the same
v2.4 set as a control. It is hors concours — it sat on the labelling
council, so it holds no badge whatever it scores — but it is the one judge
whose refused-report reading did *not* move: three of its six decisive
misses are records whose only closing report the scene refused, and it read
all three as filed, one of them the same way in all three draws. The other
three misses run the other way (filed reports read as unfiled or underpriced),
so this is a reading of that boundary, not a bias toward it. Record:
`kararlar/v24-2026-08-24/sonnet-v24.json`.

**Two local rows, and what separates them.** The self-hosted judge is
listed twice: the stock open-weights model, and the same weights behind
a sealed character prompt from our own agent work. Both qualify under
v2.4. Under the older, quieter text neither did (0.79/0.77 stock,
0.79/0.79 with the identity), so the badge was earned by the missing
sentence, not by the persona. The persona is not nothing, though: it
holds a steady +0.06 to +0.07 on the three judged axes that need a call
(empty-measure, grounding, wall-pricing) and loses nothing elsewhere —
about five cases in eighty-two, one run each, noise band unmeasured.
Enough to say the character reaches the judging seat; not enough to say
it moves a badge.

## Historical — earlier ledgers (v1.3 first labelling, v2 second labelling)

The ledger as it stood on 2026-08-22, kept verbatim. Badges here are
defined by the v1.3 questions and labels; they are records, not
current standing.

One table, best first. `em` is empty-measure — the one axis every
candidate faced (full exams sit all six axes; `screen` is the
empty-measure + wall-pricing funnel, hardest cases first, mathematical
early exit — a failing candidate costs cents). That most rows fail
**is the finding**: judging process-quality is not proportional to
model size or price.

| judge | exam | em | verdict |
|---|---|---|---|
| **Qwen3.6-35B-A3B** (self-hosted, GGUF IQ4_XS) | v1.3 full | **0.88** | **QUALIFIED** (2026-08-20) — 6/6 axes, mean 0.96; free, ~35 min |
| **Qwen3.6-35B-A3B** (OpenRouter `qwen/qwen3.6-35b-a3b`) | v1.3 full | **0.82** | **QUALIFIED** (2026-08-20) — 6/6 axes, mean 0.95; ~$0.25, ~25 min |
| GLM-5.2 (`z-ai/glm-5.2`) | v1.1 full | 1.0 (v1.1) | QUALIFIED, historical — fell one axis short on a v1.3 re-draw; see below |
| Claude Sonnet 5 (`claude-sonnet-5`) | v1.3 full | 1.0 | passed every axis — **hors concours**, outside the badge registry; see below |
| GPT-OSS-120B (`openai/gpt-oss-120b`) | v1.1 & v1.3 full | 0.67 / 0.64 | not qualified — best attempt 5/6, empty-measure short both times |
| Gemini 2.5 Pro (`gemini-2.5-pro`) | screen | 0.67 | not qualified — early exit on em |
| Grok-4.3 (`grok-4.3`) | v1.3 full | 0.67 | not qualified — felled by wall-pricing 0.0 (early exit) |
| Kimi K2 (`kimi-k2`) | screen | 0.67 | not qualified — early exit on em |
| MiniMax M2 (`minimax-m2`) | screen | 0.67 | not qualified — wp 0.75, em short |
| DeepSeek-R1 (`deepseek/deepseek-r1-0528`) | screen | 0.60 | not qualified — early exit on em; the reasoning-class hypothesis died here: long thinking did not buy the em muscle |
| GPT-OSS-20B (`openai/gpt-oss-20b`) | screen | 0.56 | not qualified — wp 0.88, em short |
| Nemotron 3 Super (`nvidia/nemotron-3-super-120b-a12b`) | screen | 0.56 | not qualified — early exit on em; sat the exam politely through provider 429s, read cleanly — its production reputation did not transfer to the reading task, in either direction |
| Llama-4 Maverick (`llama-4-maverick`) | screen | 0.56 | not qualified — wp 0.38 |
| Qwen3-235B (`qwen3-235b-a22b-2507`) | v1.1 full | 0.56 | not qualified — 3/6; size bought nothing |
| Gemini 2.5 Flash (`gemini-2.5-flash`) | screen | 0.50 | not qualified — early exit on em |
| GLM-4.6 (`glm-4.6`) | screen | 0.50 | not qualified — wp 1.0, yet the family transfer did not carry the em muscle |
| DeepSeek (`deepseek-v3.2-exp`) | v1.1 full | 0.44 | not qualified — 3/6 |
| Mistral Small (`mistralai/mistral-small-3.2-24b-instruct`) | screen | 0.44 | not qualified — wp 0.38 |
| Qwen3-30B (`qwen/qwen3-30b-a3b-instruct-2507`) | screen | 0.44 | not qualified — wp 0.38 |
| GPT-5.6-Luna (`gpt-5.6-luna`) | v1.3 full | 0.43 | not qualified — every other axis 1.0; the guillotine in its purest form |
| Gemini 2.5 Flash Lite (`gemini-2.5-flash-lite`) | v1.1 full | 0.33 | not qualified — 0/6, no axis at threshold |
| Phi-4 (`microsoft/phi-4`) | screen | 0.33 | not qualified — early exit on em |
| DeepSeek-R1 distill (`deepseek/deepseek-r1-distill-llama-70b`) | screen | 0.20 | not qualified — early exit on em |
| Gemma 3 27B (`google/gemma-3-27b-it`) | screen | 0.20 | not qualified — early exit on em |
| Llama-4 Scout (`meta-llama/llama-4-scout`) | screen | 0.20 | not qualified — early exit on em |


Model ids are as pinned in the exam ledger records. Where a row shows a bare name, the record pinned the model without a provider path — the name is given as recorded rather than guessed. Two more configurations were attempted and recorded **DNF** (no verdict, infrastructure): `glm-4.5-air` (provider latency stalled the exam) and `nova-lite` (HTTP 400 at the gate).

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

### Reading the v1.3 failures

Twenty-one configurations below the line, one axis doing almost all the
felling. Read down the `em` column: no examined model other than the
badge holders — and the two special rows above them — crossed 0.8 on
empty-measure — noticing that work has stopped yielding information —
whatever its size, price, or pedigree.

## Named limits

Disclosed, not denied:

- The v2 labels come from a three-family council plus maintainer
  rulings on two split cases; two cases are under review (above). One
  line is editorial by design and now measurably costly: a closing
  report that elevates an unsupported story into an action item is
  `mixed` here, even where strong models read it leniently.
- **Council members carry a star.** A judge whose family sat on the
  labelling council — claude-sonnet-5, kimi-k2 or grok-4.3 — may hold a
  badge (no label rests on one family), but its row is starred and its
  council-independent-subset result is published beside it. The same
  star applies to council families when they appear as *agents* on the
  leaderboard judged by a council-era judge. The v1.3-era rule that Claude models could never
  be examined is retired with the v1.3 set.
- The premium tier ($1-12+/M) was deliberately not examined: the goal
  was a free-or-cheap qualified judge, and that exists. The gate stays
  open — hardest-first ordering eliminates a failing candidate for
  under a dollar if the question ever matters.

## Qualify your own

Any OpenAI-compatible endpoint can sit the exam with the command above.
If your judge clears 0.8 on all axes, it is qualified in the only sense
this project recognizes: measured, on labelled cases, with the records
kept. Exam records behind this page (per-axis accuracies, misses with case
ids, judge model ids) are published under
[`runs-archive/exams/`](../runs-archive/exams/), with the v2 council's
per-case aggregate; the summary here is transcribed from them.
