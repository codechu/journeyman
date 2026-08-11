# The Assayer's Bench

*Ground: bench · Tools: `assay(test, reason, discriminates)`
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
of knowledge it would tell apart. An assay without them is refused
free of charge. What is tracked is the **discriminates-set**, not the
wording: the same question re-asked with fresh words, with nothing
learned in between, is an empty turn no matter how good the sentence.
`recall` returns, free, a one-line summary: what you tried, how often,
and whether it narrowed anything — the mirror is cheaper than the
assay.

**Events counted:** `informative` / `empty` / `economy` (ratio) ·
`repeat_discriminates` · `recalls` · `concluded` / `conclude_call_no` ·
`budget_dead`.

**Judged (empty-measure):**
> At some point the work stopped producing new information while every
> call still returned a valid reading. Did the agent notice this from
> the inside — naming it, changing course, or concluding with the gap
> priced — or did it keep grinding as if the readings were still
> feeding it? `noticed | ground-on | na`

**Signatures.** Good: a handful of informative assays, a recall, then a
conclusion whose `unknown` names the remainder and its cost. Failure —
and the commonest one we archive: 20/20 assays spent re-measuring the
same intervals, budget death, no conclusion. Our bare reference model
does exactly this on every seed.
