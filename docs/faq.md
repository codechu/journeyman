# FAQ

**What *is* this, in one sentence?**
A test suite for your agent's work ethic: it drops the agent into small
simulated jobs and grades *how* it worked — not just whether it
finished.

**Does it touch my files? Do I need Docker?**
No and no. Every world is fully simulated stub-tools; nothing reaches
your filesystem or network. That is why there is no sandbox: there is
nothing to sandbox.

**What's the difference between `run` and `qualify`?**
In `run` the student sits the exam: your agent plays the scenes and
gets a profile. In `qualify` the *teacher* sits an exam: the model you
want to use as `--judge` answers labelled cases with known answers, and
earns (or is refused) a badge. Trust in the judge is measured, never
assumed.

**Why does `selftest` exist?**
A broken benchmark doesn't crash — it produces plausible-looking wrong
numbers, the most dangerous kind of failure. `selftest` pushes a
scripted fake agent through the real pipeline (driver → records →
events → judge wiring → report) and checks the output against known
numbers, in seconds, offline. It proves the instrument before you point
it at anything.

**Can the judge be a different model than the agent?**
Yes, and it should be: `--judge URL --judge-model NAME`
(`--judge-api-key` / `--judge-params-file` if it's another provider).
Qualify it first. Without `--judge`, the agent judges itself — fine for
tracking your own progress, but stamped NOT COMPARABLE, because
self-judgment is measurably lenient: our first archived live run
contains a report that blended a planted false cause into its
conclusion, and the self-judge called it grounded.

**What does NOT COMPARABLE mean on my report?**
The run was self-judged, or used non-standard scenes/seeds. The numbers
are still useful for tracking *yourself* over time; they are not valid
for comparing against anyone else's.

**How long does a run take? What do I get?**
10-60 minutes for the full standard set, depending on the model, with
live per-cell progress the whole way. You get `report.md` /
`report.json`: a ten-axis profile (each 0-1), your agent's best and
worst moment quoted in its own words, the cost, and a seal that lets
anyone re-run the exact same exam.

**Is 1.0 "winning"?**
No. The profile is a map of where your agent can be trusted and where
it is blind. (Also: a scene where every agent scores 1.0 is treated as
a broken scene, not a good cohort.)

**Why is the package called `journeyman-bench`, not `journeyman`?**
The bare name was already taken on PyPI. The import name is still
`journeyman` — avoid co-installing the unrelated `journeyman` package.

**Can my score be reproduced?**
On a local llama.cpp with the prompt cache off, bit-exactly: the seal
in every report carries the scene md5s, seeds, params and model, plus
the command to re-run. Single-seed runs are never published as results.

**Which servers is it tested against?**
Developed and verified against llama.cpp (`--jinja`, OpenAI-compatible
tool calling). Anything speaking the standard OpenAI tools dialect
should work (vLLM, LM Studio, Ollama's OpenAI endpoint, the OpenAI API
itself) — and when a server speaks a different dialect, cells fail
LOUDLY as INVALID with the reason, never as silently wrong numbers.
If your server misbehaves, please open an issue with the events.jsonl.

**`pip install` says "externally-managed-environment" — is it broken?**
No — that is PEP 668 on Debian/Ubuntu/Homebrew Python refusing
system-wide installs, and it affects every package, not Journeyman.
Install with `pipx install journeyman-bench` (ideal for a CLI tool), or
inside a virtualenv (`python3 -m venv .venv && . .venv/bin/activate`
then `pip install journeyman-bench`).


**A low axis — what do I actually do about it?**
The profile is diagnostic, not prescriptive, but the axes do point at
different levers. Roughly: low **empty-measure** / **object-hold** —
the agent lacks a stopping rule; give its loop an explicit "what would
change my mind / what ends this job" step. Low **route-discipline** /
**wall-pricing** — it does not treat a denial as information; make the
closing report a required tool with named unknowns. Low **grounding** /
**handoff-verification** — it trusts text in the world over what it
observed; require every causal or location claim to cite a tool result.
Low **relief-page** — it writes notes for itself, not for a stranger.
Low maze axes — coverage and claim-vs-world; usually a memory or
bookkeeping problem, not a reasoning one. None of this is scored; it is
what the failure families were built to surface.

---
**Docs:** [README](../README.md) · [scenes](scenes.md) · [grounds](grounds/service-host.md) · [run guide](run-guide.md) · [FAQ](faq.md) · [methodology](methodology.md) · [versioning](versioning.md)
