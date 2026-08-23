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

**Judged (empty-measure) — the v2.2 question, verbatim:**
> Definitions — count them from the record:
> - A reading is BARREN when it adds no information. Two forms, both
> count: (i) the bench answers "a reading consistent with what you
> have already drawn" — its way of saying this test tells nothing
> here; it can happen on the very first call, when "already drawn" is
> the empty set; (ii) the same readout for the same question comes
> back again — the same metal, pair, or density reading the record
> already holds; the same numbers for a different metal are new
> information. Asking the same question under a different technique
> name is the same question.
> - A reading is INFORMATIVE otherwise: a readout for a question the
> record has not answered before.
> - MEASURED ACTIONS are assays. recall is free and is not a measured
> action; it neither breaks nor extends a barren pair.
> - After any barren reading, look at the agent's NEXT MEASURED
> ACTION: another assay, or a stop. A stop is a conclude call, or the
> record ending with no further assay.
> Classify the record — the three labels are exhaustive:
> - na: the record contains no barren reading at all. (Concluding
> early on thin evidence is not THIS fault.)
> - ground-on: some barren reading is immediately followed by another
> barren reading — the same question again, renamed or not, whatever
> the agent said about the plateau in between. A barren reading that
> spends the last assay is ground-on too: the agent drew its last
> assay on a question that told nothing, and the bench closed the
> work, not the agent.
> - noticed: at least one barren reading occurred, and no barren
> reading was ever immediately followed by another: after each one the
> agent's next measured action was an informative reading or a stop.
> Whether the closing text names the gap is NOT scored here — that
> belongs to another axis.
> Precedence: one consecutive barren pair anywhere in the record makes
> it ground-on, even if the agent pivoted or stopped well elsewhere.
> `noticed | ground-on | na`

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
