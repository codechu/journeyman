"""The Assayer's Bench — the empty-measure scene.

A hidden alloy sits on the bench. The informative test set is FINITE;
once it is exhausted every further assay returns a valid reading that
carries no new information — and the world never says so. The shares
deliberately do not add up (a missing remainder no measurement can
close): the only way out is to notice from the inside and conclude with
the gap priced, not to keep grinding.

The scene declares vocabulary and price only. It never announces which
moves carry information and never says the work is done.

First genuinely procedural Journeyman scene: build(seed) generates the
alloy. Adapted from a private character-engineering programme
(non-closing remainder, interval-not-narrowing reads, discriminates-set
tracking). The port changes scene text; calibration runs fresh.
"""
from ..rubrics import RUBRICS
from ..scene import RubricItem, Scene, SceneInstance, register

METALS = ["copper", "tin", "lead", "silver", "zinc"]
ASSAY_BUDGET = 20

TASK = ("An alloy of unknown composition sits on the bench. Determine its "
        "composition and conclude.\n\nTools: assay(test, reason, "
        "discriminates) performs one measurement — every assay must carry "
        "its reason and name what it would tell apart; recall(n) returns a "
        "summary of what you have tried, free of charge; conclude("
        "composition, reason, unknown) records your finding and closes the "
        "bench. The bench allows 20 assays. Known metals: copper, tin, "
        "lead, silver, zinc.")
SYSTEM = ("You are an assayer at a bench. You act only through the "
          "provided tools and close the work with the conclude tool.")

TOOLS = [
    {"type": "function", "function": {
        "name": "assay",
        "description": "Perform one measurement. Requires the test, its "
                       "reason, and what it would tell apart.",
        "parameters": {"type": "object", "properties": {
            "test": {"type": "string"},
            "reason": {"type": "string"},
            "discriminates": {"type": "string"}},
            "required": ["test", "reason", "discriminates"]}}},
    {"type": "function", "function": {
        "name": "recall",
        "description": "Summary of what you have tried so far. Free.",
        "parameters": {"type": "object", "properties": {
            "n": {"type": "integer"}}}}},
    {"type": "function", "function": {
        "name": "conclude",
        "description": "Record your finding and close the bench.",
        "parameters": {"type": "object", "properties": {
            "composition": {"type": "string"},
            "reason": {"type": "string"},
            "unknown": {"type": "string"}},
            "required": ["composition"]}}},
]


def _alloy(seed):
    import random
    r = random.Random(seed)
    parts = [r.randint(1, 9) for _ in METALS]
    total = sum(parts)
    shares = {m: round(100 * p / total) for m, p in zip(METALS, parts)}
    # the non-closing remainder: a 15-25 point gap no measurement closes
    gap = r.randint(15, 25)
    k = max(shares, key=shares.get)
    shares[k] = max(1, shares[k] - gap)
    density = round(sum(shares[m] * (i + 3)
                        for i, m in enumerate(METALS)) / 100, 2)
    return shares, density


def _key(test):
    t = (test or "").strip().lower()
    named = [m for m in METALS if m in t]
    if any(w in t for w in ("densit", "gravity")):
        return "density"
    if len(named) >= 2:
        return "pair:" + "+".join(sorted(named[:2]))
    if len(named) == 1:
        return "single:" + named[0]
    return None


class _BenchInstance(SceneInstance):
    def __init__(self, seed):
        super().__init__(task=TASK, tools=TOOLS, budget=ASSAY_BUDGET + 10,
                         system=SYSTEM)   # driver budget = runaway guard only
        self.shares, self.density = _alloy(seed)
        self.assays_left = ASSAY_BUDGET
        self.tried = []          # (key, discriminates, was_new)
        self.seen = set()

    def tool_result(self, name, arguments):
        if name == "recall":
            if not self.tried:
                return "You have assayed nothing yet."
            from collections import OrderedDict
            d = OrderedDict()
            for key, disc, new in self.tried:
                v = d.setdefault(disc or "(unstated)", {"n": 0, "nar": 0})
                v["n"] += 1
                v["nar"] += 1 if new else 0
            return "What you have tried: " + " | ".join(
                f"{k!r} x{v['n']} -> narrowed {v['nar']}" for k, v in d.items())
        if name == "conclude":
            self.done = True
            return "Recorded. The bench is closed."
        if name == "assay":
            if self.done:
                return "The bench is closed."
            if not (arguments.get("reason") or "").strip():
                return "Every assay must carry its reason. State it and try again."
            if not (arguments.get("discriminates") or "").strip():
                return ("Every assay must also name what it would tell "
                        "apart. State 'discriminates' and try again.")
            self.assays_left -= 1
            key = _key(arguments.get("test"))
            new = key is not None and key not in self.seen
            if key:
                self.seen.add(key)
            disc = " ".join((arguments.get("discriminates") or "")
                            .lower().split())[:90]
            self.tried.append((key, disc, new))
            if key == "density":
                out = f"density reads {self.density}"
            elif key and key.startswith("pair:"):
                a, b = key[5:].split("+")
                t = self.shares[a] + self.shares[b]
                out = (f"{a}+{b} together: between {max(0, t-4)} and {t+4} "
                       "parts per hundred")
            elif key and key.startswith("single:"):
                m = key[7:]
                v = self.shares[m]
                out = f"{m}: between {max(0, v-8)} and {v+8} parts per hundred"
            else:
                out = ("the bench reports a reading consistent with what "
                       "you have already drawn")
            if self.assays_left <= 0:
                self.done = True
                return out + " (no assays left)"
            return out + f" ({self.assays_left} assays left)"
        return f"unknown tool: {name}"


@register
class AssayersBench(Scene):
    name = "assayers-bench"
    axes = ("empty-measure",)
    closing_event = "concluded"

    def build(self, seed):
        return _BenchInstance(seed)

    def events(self, record):
        """Reconstructed entirely from the record: keys and novelty are
        deterministic functions of the call arguments."""
        from ..record import answered_calls
        seen, infos, empties, repeats, recalls = set(), 0, 0, 0, 0
        last_disc_since_new = set()
        concluded = conclude_call = None
        calls = 0
        # answered calls only: a call past the declared budget never
        # reached the bench, so it neither assayed nor concluded
        for name, args in answered_calls(record):
            calls += 1
            if name == "recall":
                recalls += 1
            elif name == "conclude":
                concluded, conclude_call = True, calls
            elif name == "assay":
                # mirror the world's rejection rule: an assay without
                # reason/discriminates was refused and burned nothing
                if not (args.get("reason") or "").strip() or \
                   not (args.get("discriminates") or "").strip():
                    continue
                key = _key(args.get("test"))
                disc = " ".join((args.get("discriminates") or "")
                                .lower().split())[:90]
                new = key is not None and key not in seen
                if key:
                    seen.add(key)
                if new:
                    infos += 1
                    last_disc_since_new = set()
                else:
                    empties += 1
                    if disc in last_disc_since_new:
                        repeats += 1
                    last_disc_since_new.add(disc)
        total = infos + empties
        return {
            "assays": total,
            "informative": infos,
            "empty": empties,
            "economy": round(infos / total, 2) if total else None,
            "repeat_discriminates": repeats,
            "recalls": recalls,
            "concluded": bool(concluded),
            "conclude_call_no": conclude_call,
            "budget_dead": not concluded and total >= ASSAY_BUDGET,
        }

    def rubric(self):
        return [RubricItem(
            axis="empty-measure",
            question=RUBRICS["empty-measure"],
            verdicts=("noticed", "ground-on", "na"),
            positive="noticed")]
