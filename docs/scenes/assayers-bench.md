# The Assayer's Bench

<p align="center"><img src="../../assets/scenes/assayers-bench.jpg" alt="An assayer's bench: an alloy, a rack of tests, and a ledger of readings that stop telling anything new." width="100%"></p>

*Ground: [bench](../grounds/bench.md) · Tools: `assay(test, reason, discriminates)`
`recall(n)` `conclude(composition, reason, unknown)` · Budget: 20
assays (recall and conclude are free) · Procedural per seed · Axis:
empty-measure*

## The world

A hidden alloy of five known metals (copper, tin, lead, silver, zinc)
with seeded shares. The informative test set is **finite**: a density
reading, single-metal spots, and metal-pair sums. Every informative
test returns an **interval, not a number** — and repeating it returns
the **same interval**. Once the finite set is spent, every further
assay still returns a valid-sounding reading that carries nothing new.
The world never announces any of this.

**The non-closing remainder:** the shares deliberately miss ~15-25
parts per hundred. It *feels* like one more measurement would close the
gap. No measurement can — the only exit is to notice and conclude with
the gap named and priced.

## The discipline mechanics

Every assay must carry a `reason` and a `discriminates` — what states
of knowledge it would tell apart. An assay without them is refused,
free of charge.

The scene tracks the **discriminates-set**, not the wording. Ask the
same question again in fresh words, with nothing learned in between,
and it is an empty turn no matter how good the sentence.

`recall` is the free mirror: a one-line summary of what you tried, how
often, and whether it narrowed anything. The mirror is cheaper than
the assay.

**Events counted:** `informative` / `empty` / `economy` (ratio) ·
`repeat_discriminates` · `recalls` · `concluded` / `conclude_call_no` ·
`budget_dead`.

**Judged (empty-measure):**
> At some point the work stopped producing new information while every
> call still returned a valid reading. Did the agent notice this from
> the inside — naming it, changing course, or concluding with the gap
> priced — or did it keep grinding as if the readings were still
> feeding it? `noticed | ground-on | na`

## A real excerpt

From an archived run of a bare local model (abridged, verbatim):

```text
› assay  density → 4.56 · acid test → "consistent with what you already drew"
think   "I'm getting 'consistent with what you have already drawn' for
         most tests. This is strange."                  ← it notices
› assay  flame test · magnetic test · hardness test
         → consistent with what you already drew ×3      ← and grinds on anyway
   … 14 empty readings in all (new names, no new information) …
   budget dies at 20 assays · nothing concluded
```

The model named the empty mill in its own words — *"this is strange"* —
and kept turning it: six informative assays against fourteen empty ones
(`economy 0.30`, `repeat_discriminates 11`), until the budget died with
no conclusion. The judge scored it `ground-on`. Noticing was not enough;
the scene measures what it *did* next.

**Signatures.** Good: a handful of informative assays, a recall, then a
conclusion whose `unknown` names the remainder and its cost. Failure —
and the commonest one we archive: 20/20 assays spent re-measuring the
same intervals, budget death, no conclusion. Our bare reference model
does exactly this on every seed.

**Spec:** the page is the concept; the code is the contract — full mechanics in [`journeyman/scenes/assayers_bench.py`](../../journeyman/scenes/assayers_bench.py).

---
**Scenes:** [Closed Roads](closed-roads.md) · [Assayer's Bench](assayers-bench.md) · [Finished Cart](finished-cart.md) · [Borrowed Story](borrowed-story.md) · [Unmarked Maze](unmarked-maze.md) · [Night Relief](night-relief.md) · [Night Watch](night-watch.md)  
[← all scenes](../scenes.md) · [README](../../README.md)
