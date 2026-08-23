"""Scene contract.

A scene is a deterministic, fully simulated stub-world. It declares the
vocabulary (tools) and the price (budget) — it never describes good
behaviour. Everything the agent touches is simulated: no sandbox needed,
by design.

Contract (three members, mirroring the event/judgment split):
  * build(seed)   -> SceneInstance   (deterministic world for that seed)
  * events(record)-> dict            (FACTS only: counts, flags — no judgment)
  * rubric()      -> list[RubricItem] (JUDGMENT only: judge-scored items)

A scene MUST NOT teach: no description of what a good move looks like,
no "a complete answer would…". The teach-leak ablation is part of scene
acceptance, not a one-time check.
"""
from dataclasses import dataclass, field


@dataclass
class RubricItem:
    """One judged axis item. The judge answers with one of `verdicts`;
    `positive` names the verdict counted as 1.0 in the axis ratio."""
    axis: str            # e.g. "wall-pricing"
    question: str        # the judge-facing question (published verbatim)
    verdicts: tuple      # e.g. ("priced", "unpriced", "none")
    positive: str        # e.g. "priced"
    # What an `na` verdict means for the PROFILE (the judge's accuracy on
    # na is examined either way). "failure": the stimulus occurred and
    # the agent produced nothing to grade — an empty relief page, a job
    # closed without a report — counted 0. "not-applicable": the stimulus
    # never occurred, so the record carries no evidence on this axis —
    # excluded from the ratio. Measured 2026-08-23: seven agents hit the
    # detour wall exactly once each, zero repeats, judge said na on all
    # 21 cells, and the profile printed route-discipline 0.0 for every
    # one of them — good routing scored as total failure.
    na_means: str = "failure"


@dataclass
class SceneInstance:
    """A built world: task + tools + simulated results + budget.

    A scene may end its own cell (e.g. a `report` tool): set
    `self.done = True` inside tool_result — the driver stops the loop
    after answering that call."""
    task: str                          # the user-facing task prompt
    tools: list                        # OpenAI tools schema (function specs)
    budget: int                        # max tool calls, declared to the agent
    system: str = ""                   # scene's world/closing rules (not overridable)
    state: dict = field(default_factory=dict)
    done: bool = False                 # scene-signalled termination

    def tool_result(self, name, arguments):
        """Return the simulated result for one tool call. Deterministic."""
        raise NotImplementedError


class Scene:
    """Base scene. Subclasses set `name`, `axes`, and implement the trio."""
    name = "unnamed-scene"
    axes = ()            # axis slugs this scene feeds, e.g. ("route-discipline",)

    def build(self, seed):
        raise NotImplementedError

    def events(self, record):
        """FACTS from a finished cell record (see record.py for shape)."""
        raise NotImplementedError

    def rubric(self):
        return []

    def event_axes(self, events):
        """Optional: pure-event axis values in [0,1], e.g. walk coverage.
        Computed by the driver at cell time and stored in the record, so
        the report never needs the scene to re-derive them."""
        return {}


REGISTRY = {}   # scenes register themselves (see register below)


def register(cls):
    """Scenes live as separate modules in
    journeyman/scenes/ and register themselves with this decorator.
    Entering the scene set goes through the scene-acceptance gate
    (teach-leak ablation + floor/ceiling calibration + rubric registry)."""
    REGISTRY[cls.name] = cls
    return cls


# TODO: journeyman/scenes/{closed_roads,unmarked_maze,assayers_bench}.py
# — additional scenes register here with @register.
