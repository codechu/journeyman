#!/usr/bin/env python3
"""Publish the shipped calibration set to a Hugging Face dataset repo.

Why a script and not a manual upload: the set is not static — it went through
four revisions in two days (70 -> 82 cases, three key corrections). A dataset
card that drifts from the package is worse than no card, so this runs from the
release workflow, on the same tag that ships the package.

The card is generated from the set's own metadata, so its case counts and its
provenance note cannot disagree with the file next to it.

  scripts/journeyman_hf_sync.py --dry-run        # render the card, upload nothing
  scripts/journeyman_hf_sync.py                  # needs HF_TOKEN

Without HF_TOKEN it exits 0 after saying so: a repository that has not been
given the secret should not fail its release.
"""
import argparse
import json
import os
import sys

# Two layouts run this: the dev monorepo (scripts/ next to journeyman/) and the
# public mirror, where the package sits at the root and this file is tools/.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = next((c for c in (os.path.join(ROOT, "journeyman", "journeyman", "calibration"),
                        os.path.join(ROOT, "journeyman", "calibration"))
            if os.path.isdir(c)), None)
if CAL is None:
    sys.exit("calibration/ not found — run from the repo, not elsewhere")
REPO = "codechu/journeyman-calibration"

CARD = """---
license: apache-2.0
task_categories: [text-classification]
tags: [agents, agent-evaluation, llm-as-a-judge, benchmark, process-quality]
pretty_name: Journeyman judge-calibration set
---

# Journeyman — judge-calibration set ({n} cases, {axes} axes)

This is the exam a judge sits before it is allowed to score anything in
[Journeyman](https://github.com/codechu/journeyman), a process-quality
benchmark for LLM agents. Each case is a real agent record plus the label a
judge should return for one axis. A judge that misses any axis does not get
the badge; the ones that failed are published too, in the
[judge registry](https://github.com/codechu/journeyman/blob/master/docs/judges.md).

## What is in it

| axis | cases |
|---|---|
{axis_table}

Labels come from a three-family council (claude-sonnet-5, kimi-k2, grok-4.3):
a blind round, then an anonymous round where each labeller had to quote its
evidence. A label is sealed only with support from at least two families; the
maintainer ruled the cases the council split on; empty-measure is counted
mechanically under its published definition.

## Honest limits

- **{n} cases.** Small next to human-annotated process benchmarks. It is sized
  for what it claims — licensing a judge — not for ranking a field.
- **Labels are model-produced**, not human. The council is cross-family and the
  protocol was frozen before labelling, but this is not a human gold standard.
- **The set has been corrected**, and every correction is in the file's own
  `note` field: four cases whose only closing report the scene refused were
  relabelled, twelve fresh cases were harvested when unfiled reports came to
  dominate two axes, and one case was relabelled after every examined judge
  read it against the key.

## Provenance

Set version `{version}`. Shipped inside the package as
`journeyman/calibration/v2_real.json` — `pip install journeyman-bench`.
Archived releases carry a DOI: [10.5281/zenodo.22085820](https://doi.org/10.5281/zenodo.22085820).

```
journeyman qualify --judge <endpoint> --judge-model <model> --repeats 3
```

## Looking for an arXiv endorser (cs.AI / cs.LG)

The write-up describing this set is in progress. arXiv requires an endorsement
for a first submission in a category and we have no institutional affiliation
to bypass it. If you publish in this area and think the work is worth
endorsing, please open an issue on
[the repository](https://github.com/codechu/journeyman/issues) — and if you
read it and think it is not, that is useful to hear too.

Generated from the set itself by `scripts/journeyman_hf_sync.py`.
"""


def render_card():
    d = json.load(open(os.path.join(CAL, "v2_real.json")))
    from collections import Counter
    c = Counter(case["axis"] for case in d["cases"])
    table = "\n".join(f"| `{a}` | {n} |" for a, n in sorted(c.items()))
    return CARD.format(n=len(d["cases"]), axes=len(c), axis_table=table,
                       version=d.get("version", "?"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    card = render_card()
    if a.dry_run:
        print(card)
        return

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("HF_TOKEN not set — skipping the dataset sync (not an error)")
        return

    from huggingface_hub import HfApi
    api = HfApi(token=token)
    api.create_repo(a.repo, repo_type="dataset", exist_ok=True)
    api.upload_file(path_or_fileobj=card.encode(), path_in_repo="README.md",
                    repo_id=a.repo, repo_type="dataset")
    for name in ("v2_real.json", "v0_synthetic.json", "handoff_v0.json"):
        p = os.path.join(CAL, name)
        if os.path.exists(p):
            api.upload_file(path_or_fileobj=p, path_in_repo=f"calibration/{name}",
                            repo_id=a.repo, repo_type="dataset")
    print(f"synced to https://huggingface.co/datasets/{a.repo}")


if __name__ == "__main__":
    sys.exit(main())
