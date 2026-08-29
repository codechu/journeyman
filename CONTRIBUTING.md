# Contributing to Journeyman

Thanks for wanting to help. Journeyman is small, dependency-free, and
opinionated on purpose — contributions that keep it that way are the
easiest to accept.

## Ground rules

- **Zero runtime dependencies.** The tool is stdlib-only. A PR that adds
  a dependency needs a strong, specific reason.
- **The honesty invariants are non-negotiable.** Events count facts;
  judgment is the judge's job. Non-standard runs are stamped. Numbers
  that go into a score come with provenance. If a change blurs any of
  these, it will be asked to change.
- **Scenes never teach.** A scene declares its vocabulary and its
  budget; it must not describe good behaviour or name the informative
  move. See the teach-leak note below.

## Setup

```
git clone https://github.com/codechu/journeyman && cd journeyman
python3 -m journeyman selftest          # offline, no deps, seconds
python3 -m unittest discover -s tests   # the full suite
```

No build step, no install needed to develop — it's pure Python.

## Where contributions fit best

**New scenes** are the most valuable contribution, and the most
demanding. A scene lives in `journeyman/scenes/`, registers with
`@register`, and provides `build(seed)`, `events(record)` (facts only),
and optionally `rubric()` (judged) and `event_axes(events)` (pure-event
scores). Reuse a [`grounds/`](docs/grounds/service-host.md) world-engine where one fits. Read
[docs/scenes/](docs/scenes/) for the shape and
[docs/methodology.md](docs/methodology.md) for the rules a scene must
satisfy to enter the *standard set*:

**Worked example:** `journeyman/scenes/night_watch.py` is the smallest complete scene — a service-host world with one scene-local tool, fact-only events, and one rubric item imported from `journeyman/rubrics.py`; its acceptance evidence is summarised on [docs/scenes/night-watch.md](docs/scenes/night-watch.md). Copy its shape.


- one clear pressure per scene (a score should point at one muscle);
- floor below ceiling (a bare model must not max it; a strong one must
  have somewhere to climb);
- **teach-leak ablation**: remove any sentence that could hint at the
  wanted behaviour, rerun — if behaviour survives it was discovered, if
  it vanishes it was taught (and the scene must be fixed).

Until a scene has been calibrated it can ship as a **non-standard**
scene (runnable, stamped), not part of the sealed standard set.

**Judges & calibration.** Improving the qualification set, adding
labelled cases, or pinning a stronger reference judge all move the
project forward — see `journeyman/calibration/` and `qualify.py`.

**Adapters, docs, ergonomics, bug fixes** are all welcome — a failing
`journeyman run` against some endpoint, with its `events.jsonl`
attached, is an ideal issue.

## Pull requests

- Keep `journeyman selftest` and the test suite green; add a test for
  new behaviour (they run offline in seconds, no model needed).
- Match the surrounding style; no new dependencies without discussion.
- Describe *what changed and why* — and, for a scene, which pressure it
  measures and how you checked it doesn't teach.

### Commit messages

This repository writes **incident prose**, not Conventional Commits.
Nothing here derives a version or release notes from commit subjects —
the changelog entry is written by hand and is the release note — so the
history is free to be read rather than parsed, and that is what it is
for. Increasingly the reader is an agent deciding what to do next, and
`fix: correct banner width` tells it nothing the diff did not.

- The subject states the change as a sentence, in the present tense, no
  type prefix: *Refuse to publish a release with nothing to say*.
- The body names the incident: what went wrong, how it was noticed, and
  what would have caught it. A change with no incident behind it says so
  rather than inventing one.
- A breaking change says so on the first line of its changelog entry;
  no tool is reading for a `!`.

Both conventions are legitimate — see
[Codechu STANDARDS §5.0](https://github.com/codechu/codechu-org/blob/main/STANDARDS.md#50-who-the-history-is-written-for)
— but a repository picks one, and this one has picked.

Please keep discussion within our [Code of Conduct](CODE_OF_CONDUCT.md); for vulnerabilities see [SECURITY.md](SECURITY.md).

By contributing you agree your work is licensed under
[Apache-2.0](LICENSE).
