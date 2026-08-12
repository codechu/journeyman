# Changelog

All notable changes to Journeyman. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions are
[semantic](https://semver.org/). Pre-1.0: minor engineering and docs
land in patch releases.

## [0.0.3] — 2026-08-12

### Added
- Real terminal colour on the progress and judging lines, TTY-gated and
  `NO_COLOR` / `FORCE_COLOR` aware; on Windows, colour turns on only if
  virtual-terminal processing can be enabled — never raw escape codes.
- Published `report.json` contract as JSON Schema
  (`journeyman/schema/report.schema.json`), shipped in the package.
- Trove classifiers (Python 3.10–3.13) so PyPI metadata is complete.
- Deep documentation: per-scene pages under `docs/scenes/`, a FAQ, a run
  guide (anatomy of a run + verbatim record formats), and a report
  format / interoperability note.

### Fixed
- The run seal recorded a hardcoded `0.0.1-skeleton` version regardless
  of the actual release; it now derives from the package version.
- Separate-judge endpoints could not receive their own api-key or
  sampling params (`--judge-api-key`, `--judge-params-file`).
- Legacy-Windows console safety: output degrades unencodable characters
  instead of crashing.

### Changed
- Illustrations converted to JPEG (q90): repository ~15 MB lighter.
- README reordered for a first-time reader; the terminal screenshot is
  redrawn (a real frame, no box-drawing glyphs) and now truthfully
  colour-matched to the CLI.

## [0.0.2] — 2026-08-11

### Added
- Seven sealed scenes/modes on three grounds (service-host, assay bench,
  labyrinth), including the Night Relief watch-handoff mode.
- Judge qualification exam (`qualify`) with a labelled calibration set
  and a published per-axis accuracy registry.
- `report` command to re-render a finished run.
- Brand: banner, guild-seal icon, per-scene illustrations.
- CI across Python 3.10–3.13; tag-gated PyPI release via trusted
  publishing.

### Changed
- Extracted the shared world-engine grounds; three scenes now share one
  physics (~130 lines of duplication removed).

## [0.0.1] — 2026-08-11

Initial public import: scene contract, sequential crash-safe driver,
sealed records, pluggable judge, evidence-quoting reports, offline
selftest.
