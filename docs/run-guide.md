# Anatomy of a run

What actually happens when you type `journeyman run`, and what every
file in the run directory means.

## The phases

1. **Seal.** Before anything runs, the seal is written: bench version,
   per-scene source md5, seeds, model, your system-file md5 and params
   verbatim. The seal is the run's identity — change any part and it is
   a different run.
2. **Cells, sequentially.** One cell = one scene × one seed. The driver
   opens a conversation (your `--system-file` first, then the scene's
   own world rules), hands the agent the task and tools, and relays
   tool calls to the simulated world until the scene closes itself
   (e.g. the `report` tool), the budget dies, or the agent stops
   calling tools. Multi-episode scenes (Night Relief) end the
   conversation at the bell and wake a fresh one — the world persists,
   the wire does not. Cells run strictly one at a time: parallel
   batching measurably perturbs local-model numerics.
3. **Events.** The moment a cell ends, its facts are computed — counts,
   flags, and for the maze family a full REPLAY: the world is rebuilt
   from the seed and the recorded calls re-run through the same engine.
   Facts only; no opinions.
4. **Judging.** After all cells, the judge (self by default, or your
   `--judge`) reads each cell's record and answers each rubric item —
   one small call per item, verdict echoed from a fixed label set.
   Unparsed answers are recorded as unparsed, never guessed.
5. **Report.** `report.md` (human) and `report.json` (machine) are
   rendered FROM the records. Terminal lines, event stream and report
   are three views of the same files — they cannot disagree.

## The run directory

```
runs/<stamp>/
  events.jsonl     every event, line-buffered, tail -f friendly:
                   run_start (with seal), cell_start/cell_end,
                   judging_start, cell_judged, run_end
  cells/<id>.json  one file per cell: the full message transcript,
                   episode markers, events, event_axes, verdicts
                   (with the judge's raw text), seal, cost, timing
  report.md        the human report — profile, quotes, cost, seal
  report.json      the same, machine-readable
```

## Reading a cell record

The interesting fields of `cells/<id>.json`:

- `messages` — the complete conversation, OpenAI format, including
  every tool call and simulated result (and `reasoning_content` when
  the endpoint returns it).
- `events` — the facts: calls, wall hits, budget death, which sources
  were read, replay-derived walk metrics…
- `verdicts` — per axis: the judge's verdict, the positive label it is
  scored against, and the judge's raw reasoning text.
- `invalid` / `invalid_reason` — a cell that failed to run (timeout,
  endpoint error) is INVALID with its reason and excluded from scores;
  it is never silently retried.

## Re-judging and re-rendering

Verdicts live in the cell records, so you can re-judge a finished run
with a better judge later and re-render without re-running anything:
the walk is history; the opinion about it is replaceable.
`journeyman report runs/<stamp>` re-renders from whatever the records
now hold.

## Resume

If a run dies mid-way, run the same command with the same `--runs-dir`
target: finished cells are detected and skipped, unfinished ones run
again. Partial work is never lost — each cell seals itself the moment
it completes.

## Cost accounting

Every endpoint response's token usage is summed into the cell record
and the report. If your endpoint does not report usage, the report says
`tokens UNREPORTED` — zero and unknown are different numbers here.
