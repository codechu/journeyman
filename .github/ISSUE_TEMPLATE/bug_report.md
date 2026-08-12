---
name: Bug report
about: Something went wrong in a run
labels: bug
---

**What happened**
A clear description of the problem.

**To reproduce**
The exact `journeyman ...` command, the endpoint/server (e.g. llama.cpp,
vLLM, LM Studio, Ollama, OpenAI) and its version.

**Attach**
The `events.jsonl` from the run directory (and the failing
`cells/<id>.json` if you have it) — this usually pinpoints it fast.

**Environment**
`journeyman --version`/PyPI version · Python version · OS.
