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

## What you can lean on today (pre-1.0)

Asked by an integrator, so it belongs here rather than in an issue thread.

- **`report.json` and its [JSON Schema](../journeyman/schema/report.schema.json)** —
  the closest thing we have to an API. There is no universal standard for agent
  process reports, so this schema *is* the contract. It has changed before
  (`na_means`, null scores and `not_applicable` arrived together) and it will
  change again, but always with a changelog entry, never silently.
- **Rubric question text (`rubrics.py`) is deliberately unstable.** It has been
  rewritten five times, three of those inside one week, and it will keep moving:
  the questions are a calibration artefact tied to a set version, not an API.
  One single-sentence edit moved a judge from failing an axis at 0.71 to 0.86 and
  a badge — that is how load-bearing this text is. Pass the question through as
  data; never key behaviour off its wording.
- **The cell record (`record.py`) is internal.** Readable, and you may map it,
  but it is our working format: treat a field's absence as possible.
- **The calibration set is versioned separately** (`version` inside
  `v2_real.json`, currently 2.3). Exam scores do not transfer across revisions,
  so anything that surfaces a qualification result should surface the set
  version beside it — the same reason a score travels with its judge's identity.

If you depend on one of these, say so in an issue and we will warn before
changing it rather than after.

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

---
**Docs:** [README](../README.md) · [scenes](scenes.md) · [grounds](grounds/service-host.md) · [run guide](run-guide.md) · [FAQ](faq.md) · [methodology](methodology.md) · [versioning](versioning.md)
