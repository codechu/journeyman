# Versioning & release rules

Rules we hold ourselves to. Short on purpose.

## Semantic versioning

- **patch** (0.0.x) — fixes, docs, ergonomics; nothing that changes a
  score or breaks a command.
- **minor** (0.x.0) — new scenes/modes, new flags, additive changes.
  Adding a scene to the standard set is minor (it changes composite
  scores, so we say so in the changelog).
- **major** (x.0.0) — anything that breaks a frozen contract below.

**Pre-1.0, minor is the breaking slot.** While the version starts with a
zero there is no stability promise to break — that promise is what 1.0
*is*, and reserving the major digit for it means a pre-1.0 break has
nowhere else to go. So in 0.x a breaking change bumps the minor and says
so on the first line of its changelog entry; it does not quietly ride in
a patch, and it does not spend the 1.0 digit. 0.1.0 was the first of
these: `kind` became a required field in `report.json`, so reports
written by 0.0.x no longer validate. When we tag 1.0, this paragraph
retires and the table above applies as written.

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

- **Pin on `schema_version`, not on the package version.** Every
  `report.json` carries an integer `schema_version` (1 as of 0.1.0), bumped
  only when the shape changes in a way that can break a reader — not on
  every release, because the package moves for reasons that never touch the
  report. On a value your code does not know, stop rather than guess. The
  release number is a signal for humans reading the changelog; this field is
  the one a program should branch on.
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
  Worth saying plainly, because it bit the first integrator: `report.json`
  is an aggregate profile and carries no per-cell rows, so a consumer that
  needs one result per scene × seed — transcript, events, duration — has to
  read `cells/<id>.json`, which is exactly the surface with the weaker
  promise. We are not asking anyone to guess: tell us which cell fields you
  depend on and we will either pin them or warn before they move.
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
