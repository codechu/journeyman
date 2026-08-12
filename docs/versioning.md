# Versioning & release rules

Rules we hold ourselves to. Short on purpose.

## Semantic versioning

- **patch** (0.0.x) — fixes, docs, ergonomics; nothing that changes a
  score or breaks a command.
- **minor** (0.x.0) — new scenes/modes, new flags, additive changes.
  Adding a scene to the standard set is minor (it changes composite
  scores, so we say so in the changelog).
- **major** (x.0.0) — anything that breaks a frozen contract below.

Every release gets a changelog entry, and the changelog entry is the
release note.

## What "1.0" means here

1.0 is **not** a claim that the science is finished — it is a promise of
**stability**. We tag 1.0 when:

1. the standard scene set is sealed (composition + md5s won't change
   under 1.x),
2. `report.json` matches its published JSON Schema and we won't break it
   backward-incompatibly in 1.x,
3. the CLI flags are stable (no removals or meaning changes in 1.x),
4. it has run against more than one kind of endpoint, and
5. the known limitations are stated honestly (they already are).

Deeper validation — multi-model separation, a real calibration set, a
pinned reference judge, full teach-leak passes — keeps improving across
1.x. It is roadmap, not a 1.0 gate.

## Standing rules (every version)

- **Zero runtime dependencies.**
- **Events count facts; judgment is the judge's job.** Never move a
  judgment into a deterministic counter to save a call.
- **Non-standard runs are stamped; single-seed scores aren't published
  as results.**
- **A number that enters a score carries provenance** (the seal, the
  stamps).
- **Scenes declare tools and budget; they never teach the wanted
  behaviour.**
- **Don't overclaim.** If something isn't shown, the docs say so.
