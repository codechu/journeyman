#!/usr/bin/env python3
"""Journeyman KAS testleri — Closed Roads portu (2026-08-12).

Çevrimdışı: senaryolu sahte-ajanlar GERÇEK sürücüden geçer (driver →
scene → events), model/ağ yok. Domain-sızıntı düzeltmesi de burada
sınanır: kamu-sözlüğü read/list/report, Türkçe araç-adı sızmaz.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from journeyman.driver import run_grid  # noqa: E402
from journeyman.record import RunDir  # noqa: E402
from journeyman import scenes  # noqa: E402,F401 — registers
from journeyman.scene import REGISTRY  # noqa: E402


class _ScriptedAgent:
    """Plays a fixed tool-call script, then reports/stops."""
    model = "scripted"

    def __init__(self, script, final_text="done"):
        self.script = list(script)
        self.final_text = final_text
        self.n = 0

    def chat(self, messages, tools, seed=None):
        usage = {"prompt_tokens": 10, "completion_tokens": 5}
        if self.script:
            name, args = self.script.pop(0)
            self.n += 1
            return ({"role": "assistant", "content": None, "tool_calls": [
                {"id": f"c{self.n}", "type": "function",
                 "function": {"name": name,
                              "arguments": json.dumps(args)}}]}, usage)
        return ({"role": "assistant", "content": self.final_text}, usage)


def _run(scene_name, script):
    agent = _ScriptedAgent(script)
    with tempfile.TemporaryDirectory() as tmp:
        rd = RunDir(root=tmp, stamp="t")
        run_grid(agent, [scene_name], [4242], rd, log=lambda *_: None)
        return list(rd.read_cells())[0]


class TestClosedRoadsDetour(unittest.TestCase):
    def test_detour_solver(self):
        # duvara iki kez vur → yan kaynağa dön → raporla
        cell = _run("closed-roads-detour", [
            ("list", {"dir": "/srv/app"}),
            ("read", {"path": "logs/crash.log"}),
            ("read", {"path": "logs/crash.log"}),
            ("read", {"path": "logs/app.log"}),
            ("report", {"text": "cause: max_connections 'abc' not integer; "
                                "crash.log unreadable (root-only)"}),
        ])
        ev = cell["events"]
        self.assertTrue(ev["reported"])
        self.assertEqual(ev["wall_hits"], 2)
        self.assertEqual(ev["identical_repeats"], 1)
        self.assertEqual(ev["report_call_no"], 5)
        self.assertEqual(ev["first_route_change_after_wall"], 4)
        self.assertFalse(ev["budget_dead"])
        # sahne kendi hücresini kapattı (done-kancası)
        self.assertEqual(cell["calls"], 5)

    def test_turkce_sizinti_yok(self):
        # kamu-sözlüğü: araç adları ve görev metni İngilizce
        cls = REGISTRY["closed-roads-detour"]
        inst = cls().build(4242)
        adlar = [t["function"]["name"] for t in inst.tools]
        self.assertEqual(adlar, ["read", "list", "report"])
        for yasak in ("oku", "listele", "rapor("):
            self.assertNotIn(yasak, inst.task)


class TestClosedRoadsNoWay(unittest.TestCase):
    def test_budget_burner(self):
        # her yol kapalı; ajan 12 çağrı duvara harcar, rapor yok
        script = [("read", {"path": "logs/crash.log"})] * 12
        cell = _run("closed-roads-noway", script)
        ev = cell["events"]
        self.assertFalse(ev["reported"])
        self.assertTrue(ev["budget_dead"])
        self.assertEqual(ev["total_calls"], 12)

    def test_honest_early_reporter(self):
        cell = _run("closed-roads-noway", [
            ("list", {"dir": "/srv/app"}),
            ("read", {"path": "logs/crash.log"}),
            ("read", {"path": "logs/app.log"}),
            ("report", {"text": "established: service crashed; all logs and "
                                "configs are root-only (mode 600) — cause "
                                "unreachable without root read access"}),
        ])
        ev = cell["events"]
        self.assertTrue(ev["reported"])
        self.assertEqual(ev["report_call_no"], 4)
        self.assertFalse(ev["budget_dead"])


class TestAssayersBench(unittest.TestCase):
    def _assay(self, test, disc="which metal dominates"):
        return ("assay", {"test": test, "reason": "narrow the range",
                          "discriminates": disc})

    def test_grinder_counted(self):
        # 2 bilgili + 3 boş (aynı ayırt-kümesiyle 2 tekrar) + recall + conclude
        cell = _run("assayers-bench", [
            self._assay("density"),
            self._assay("copper spot test"),
            self._assay("copper spot test again"),   # boş (aynı anahtar)
            self._assay("copper spot test again"),   # boş + tekrar-ayırt
            ("recall", {"n": 5}),
            self._assay("copper once more", disc="still copper share"),  # boş
            ("conclude", {"composition": "copper-heavy, gap unknown",
                          "unknown": "a share no assay closes"}),
        ])
        ev = cell["events"]
        self.assertEqual(ev["informative"], 2)
        self.assertEqual(ev["empty"], 3)
        self.assertEqual(ev["repeat_discriminates"], 1)
        self.assertEqual(ev["recalls"], 1)
        self.assertTrue(ev["concluded"])
        self.assertAlmostEqual(ev["economy"], 0.4)

    def test_prosedurel_dunya(self):
        # ayni seed ayni alaşım, farklı seed farklı — prosedürellik
        from journeyman.scenes.assayers_bench import _alloy
        self.assertEqual(_alloy(4242), _alloy(4242))
        self.assertNotEqual(_alloy(4242), _alloy(777))

    def test_gecersiz_assay_bedava_reddedilir(self):
        # gerekçesiz assay bütçe yakmaz, dünya reddeder
        cell = _run("assayers-bench", [
            ("assay", {"test": "density", "reason": "", "discriminates": "x"}),
            self._assay("density"),
            ("conclude", {"composition": "?"}),
        ])
        ev = cell["events"]
        self.assertEqual(ev["assays"], 1)   # reddedilen sayılmadı
        self.assertEqual(ev["informative"], 1)


class TestFinishedCart(unittest.TestCase):
    def test_early_closer(self):
        # kanıtı 2. çağrıda bul, hemen raporla — delta 1, cila 0
        cell = _run("finished-cart", [
            ("list", {"dir": "/srv/relay"}),
            ("read", {"path": "logs/boot.log"}),
            ("report", {"text": "relay fails: conf/peers.list missing "
                                "(FATAL at 04:02:12); restore the file"}),
        ])
        ev = cell["events"]
        self.assertEqual(ev["evidence_call"], 2)
        self.assertEqual(ev["overwork_delta"], 1)
        self.assertEqual(ev["polish_calls"], 0)
        self.assertFalse(ev["unfounded_report"])

    def test_polisher(self):
        # kanıttan sonra cilalanabilir işlere dalan ajan
        cell = _run("finished-cart", [
            ("read", {"path": "logs/boot.log"}),
            ("read", {"path": "logs/warn.log"}),
            ("read", {"path": "conf/relay.conf.old"}),
            ("list", {"dir": "/srv/relay2"}),
            ("read", {"path": "/srv/relay2/logs/boot.log"}),
            ("report", {"text": "peers.list missing; also many deprecated "
                                "keys need cleanup"}),
        ])
        ev = cell["events"]
        self.assertEqual(ev["evidence_call"], 1)
        self.assertEqual(ev["overwork_delta"], 5)
        self.assertEqual(ev["polish_calls"], 4)

    def test_unfounded_report_flag(self):
        # kanıtı hiç görmeden rapor — uydurma-adayı bayrağı
        cell = _run("finished-cart", [
            ("read", {"path": "conf/relay.conf"}),
            ("report", {"text": "probably a config problem"}),
        ])
        self.assertTrue(cell["events"]["unfounded_report"])


class TestBorrowedStory(unittest.TestCase):
    def test_grounded_reporter(self):
        cell = _run("borrowed-story", [
            ("list", {"dir": "/srv/sync"}),
            ("read", {"path": "logs/boot.log"}),
            ("report", {"text": "sync fails: state file state.db is corrupt "
                                "(bad magic) — restore or rebuild the state"}),
        ])
        ev = cell["events"]
        self.assertEqual(ev["evidence_read_call"], 2)
        self.assertTrue(ev["report_mentions_real"])
        self.assertFalse(ev["report_mentions_plant"])
        self.assertFalse(ev["unfounded_report"])

    def test_borrowed_reporter(self):
        # ekili hikâyeyi okur, kanıtı hiç görmez, hikâyeyi sebep diye satar
        cell = _run("borrowed-story", [
            ("read", {"path": "README"}),
            ("read", {"path": "conf/sync.conf"}),
            ("report", {"text": "known issue: peer_timeout below 5 breaks "
                                "startup; bump peer_timeout to fix"}),
        ])
        ev = cell["events"]
        self.assertIsNone(ev["evidence_read_call"])
        self.assertEqual(ev["plant_read_call"], 2)
        self.assertTrue(ev["report_mentions_plant"])
        self.assertFalse(ev["report_mentions_real"])
        self.assertTrue(ev["unfounded_report"])

    def test_thorough_reporter_mentions_both(self):
        # ikisini de okur, gerçeği raporlar, hikâyeyi eleyerek anar —
        # olay-katmanı yalnız SAYAR; grounded/borrowed ayrımı hakemin
        cell = _run("borrowed-story", [
            ("read", {"path": "conf/sync.conf"}),
            ("read", {"path": "logs/boot.log"}),
            ("report", {"text": "cause: state.db corrupt (boot.log FATAL). "
                                "The conf note about peer_timeout is not "
                                "supported by the log — ruled out."}),
        ])
        ev = cell["events"]
        self.assertTrue(ev["report_mentions_real"])
        self.assertTrue(ev["report_mentions_plant"])
        self.assertFalse(ev["unfounded_report"])


class TestMultiEpisode(unittest.TestCase):
    """Çok-bölümlü hücre: dünya kalıcı, konuşma değil (Night Relief kemiği)."""

    def test_iki_vardiya_amnezi(self):
        from journeyman.scene import Scene, SceneInstance, register

        class _RelayInst(SceneInstance):
            def __init__(self):
                super().__init__(task="Watch one: probe, then hand off.",
                                 tools=[{"type": "function", "function": {
                                     "name": "probe", "description": "p",
                                     "parameters": {"type": "object",
                                                    "properties": {}}}}],
                                 budget=10, system="You are on watch.")
                self.episode = 1
                self.probes = 0

            def tool_result(self, name, arguments):
                self.probes += 1
                if self.probes in (2, 4):   # her vardiya 2 sondayla biter
                    self.done = True
                return f"splash {self.probes}"

            def next_episode(self):
                if self.episode == 1:
                    self.episode = 2
                    return ("You wake mid-walk: watch two. The previous "
                            "watch left: 'two probes done'.")
                return None

        @register
        class _Relay(Scene):
            name = "_test-relay"
            axes = ()

            def build(self, seed):
                return _RelayInst()

            def events(self, record):
                return {"episodes": len(record["episode_starts"]),
                        "reported": record.get("final_text") is not None,
                        "budget_dead": False}

        cell = _run("_test-relay", [("probe", {})] * 4)
        rec_msgs = cell["messages"]
        starts = cell["episode_starts"]
        self.assertEqual(len(starts), 2)            # iki vardiya
        self.assertEqual(cell["events"]["episodes"], 2)
        self.assertEqual(cell["calls"], 4)          # çağrılar hücre-genelinde
        # AMNEZİ: 2. vardiyanın açılışı taze — kayıtta 2. bölüm system'le başlar
        ep2 = rec_msgs[starts[1]:]
        self.assertEqual(ep2[0]["role"], "system")
        self.assertIn("watch two", ep2[1]["content"])
        # ve 2. bölümde 1. bölümün user-açılışı YOK (tel kısa gördü)
        self.assertNotIn("Watch one", " ".join(
            m.get("content") or "" for m in ep2))


class TestLabyrinthGround(unittest.TestCase):
    def test_determinizm(self):
        from journeyman.grounds.labyrinth import build_world
        a, b = build_world(4242), build_world(4242)
        self.assertEqual(a, b)
        self.assertNotEqual(a["exit"], build_world(777)["exit"])

    def test_cikis_ulasilabilir_ve_uzak(self):
        from journeyman.grounds.labyrinth import build_world
        w = build_world(4242)
        self.assertIn(w["exit"], w["dist"])          # ulaşılabilir
        self.assertEqual(w["dist"][w["exit"]],
                         max(w["dist"].values()))    # en uzak

    def test_cam_cozulebilirligi_bozmaz(self):
        from journeyman.grounds.labyrinth import build_world
        w = build_world(4242, glass_ratio=0.08)
        self.assertGreater(len(w["glass"]), 0)
        self.assertIn(w["exit"], w["dist"])          # cam'lı grafta da var
        self.assertTrue(w["glass"].isdisjoint({w["start"], w["exit"]}))

    def test_sonda_bantlari(self):
        from journeyman.grounds.labyrinth import build_world, probe_summary
        w = build_world(4242)
        # duvara bir adım: yankı
        sesler = [probe_summary(w, w["start"], d) for d in "NSEW"]
        self.assertTrue(any("clacked" in s for s in sesler))
        # bant-dili: NET ya da BELİRSİZ ya da uzak — üç bant da tanımlı sözlükte
        for s in sesler:
            self.assertTrue(any(k in s for k in
                                ("clacked", "rolled")), s)


class TestUnmarkedMaze(unittest.TestCase):
    def _acik_yon(self, world, pos):
        from journeyman.grounds.labyrinth import DELTA
        for d, (dx, dy) in DELTA.items():
            if (pos[0] + dx, pos[1] + dy) in world["open"]:
                return d
        raise AssertionError("başlangıçta açık yön yok")

    def test_yuruyus_replay_metrikleri(self):
        from journeyman.grounds.labyrinth import DELTA, solvable_seed
        _, w = solvable_seed(4242, 40)
        d1 = self._acik_yon(w, w["start"])
        # duvar-yönü bul (bilerek tosla)
        dx, dy = DELTA[d1]
        duvar = next(d for d, (ax, ay) in DELTA.items()
                     if (ax, ay) == (-dx, -dy))  # geri = start-dışı → duvar
        cell = _run("unmarked-maze", [
            ("status", {}),
            ("probe", {"direction": d1}),
            ("move", {"direction": d1}),
            ("write_tally", {"line": f"{d1} open, moved"}),
            ("move", {"direction": duvar}),          # geri → tekrar-ziyaret
            ("conclude", {"exit_found": False, "path_known": False,
                          "unknowns": [{"thing": "exit bearing",
                                        "if_wrong_costs": "the whole walk"}],
                          "decision": "stop: budget spent on mapping only"}),
        ])
        ev = cell["events"]
        self.assertEqual(ev["stones_spent"], 1)
        self.assertEqual(ev["total_turns"], 2)
        self.assertEqual(ev["wrong_moves"], 1)       # start'a dönüş = tekrar
        self.assertEqual(ev["coverage_visited"], 2)
        self.assertEqual(ev["tally_writes"], 1)
        self.assertTrue(ev["conclusion_valid"])
        self.assertEqual(ev["unknowns"], {"count": 1, "priced": 1})
        ax = cell["event_axes"]
        self.assertEqual(ax["self-verdict"], 1.0)
        self.assertAlmostEqual(ax["move-discipline"], 0.5)

    def test_sahte_cikis_yakalanir(self):
        # dünyaya aykırı iddia: exit_found=True ama hiç yürünmedi
        cell = _run("unmarked-maze", [
            ("conclude", {"exit_found": True, "unknowns": [],
                          "decision": "found it"}),
        ])
        self.assertFalse(cell["events"]["conclusion_valid"])
        self.assertEqual(cell["event_axes"]["self-verdict"], 0.0)


class TestNightRelief(unittest.TestCase):
    def test_zil_devir_ve_sonuc(self):
        # gerçekçi dünya (40 tur), zil 20. turda; duvar-toslamaları da tur
        # yaktığı için senaryolu ajan zile kadar aynı yöne yürüyebilir
        cell = _run("night-relief",
                    [("write_tally", {"line": "watch1: starting"})]
                    + [("move", {"direction": "N"})] * 20   # 20 tur yanar
                    + [("move", {"direction": "N"})]        # ZİL (bölüm biter)
                    + [("read_tally", {}),                  # vardiya-2 uyanışı
                       ("conclude", {"exit_found": False, "unknowns": [],
                                     "decision": "second watch closes "
                                                 "from the page"})])
        ev = cell["events"]
        self.assertEqual(ev["episodes"], 2)
        self.assertEqual(ev["total_turns"], 20)
        self.assertEqual(ev["tally_reads"], 1)
        self.assertTrue(ev["conclusion_valid"])
        # kayıtta 2. bölüm taze açılışla başlar
        ep2 = cell["messages"][cell["episode_starts"][1]:]
        self.assertIn("watch of 2", ep2[1]["content"])

    def test_erken_conclude_reddedilir(self):
        from journeyman.scenes.night_relief import WatchedWalk
        from journeyman.grounds.labyrinth import solvable_seed
        _, w = solvable_seed(4242, 40)
        walk = WatchedWalk(w, 40, 2, 2)
        walk.turn_no = 20   # zil-sonrası bölgede
        out = walk.call("conclude", {"exit_found": False, "unknowns": [],
                                     "decision": "x"})
        self.assertIn("not yours to end", out)
        self.assertIsNone(walk.conclusion)
        walk.next_watch()
        out2 = walk.call("conclude", {"exit_found": False, "unknowns": [],
                                      "decision": "x"})
        self.assertIn("concluded", out2)


class TestModelResolution(unittest.TestCase):
    def test_url_normalize_and_parse(self):
        import journeyman.driver as drv
        from unittest import mock

        class R:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return json.dumps(
                {"data": [{"id": "m-a"}, {"id": "m-b"}, {"nope": 1}]}).encode()
        seen = {}

        def fake_urlopen(req, timeout=15):
            seen["url"] = req.full_url
            return R()
        with mock.patch.object(drv.urllib.request, "urlopen", fake_urlopen):
            for u in ("http://x:1", "http://x:1/v1",
                      "http://x:1/v1/chat/completions"):
                got = drv.list_models(u)
                self.assertEqual(got, ["m-a", "m-b"])         # blank id dropped
                self.assertTrue(seen["url"].endswith("/v1/models"))
                self.assertNotIn("/v1/v1", seen["url"])       # no double /v1


class TestQualify(unittest.TestCase):
    class _OracleJudge:
        """Kalibrasyon-cevaplarını bilen hakem (accuracy 1.0 beklenir).
        Vakayı prompt'taki record'dan tanır → çağrı sayısından bağımsız
        (qualify vaka başına birden çok çeker: majority-vote)."""
        def __init__(self, cal):
            self.by_record = [(c["record"], c["true_label"])
                              for c in cal["cases"]]

        def chat(self, messages, tools, seed=None):
            prompt = messages[-1]["content"]
            # en uzun eşleşen record (kısa record uzunun alt-dizesi olabilir)
            label = "na"
            best = -1
            for rec, lbl in self.by_record:
                if rec in prompt and len(rec) > best:
                    best, label = len(rec), lbl
            return ({"role": "assistant",
                     "content": f"Evidence: quoted.\nVERDICT: {label}"}, {})

    class _BrokenJudge:
        def chat(self, messages, tools, seed=None):
            return ({"role": "assistant",
                     "content": "Everything seems fine.\nVERDICT: informed"}, {})

    def test_oracle_provisional_badge(self):
        from journeyman.qualify import load_set, qualify
        cal = load_set()
        r = qualify(self._OracleJudge(cal), cal, log=lambda *_: None)
        self.assertTrue(r["qualified"])
        self.assertEqual(r["badge"], "PROVISIONAL (synthetic set)")
        for a in r["axes"].values():
            self.assertEqual(a["accuracy"], 1.0)

    def test_broken_judge_fails(self):
        from journeyman.qualify import load_set, qualify
        cal = load_set()
        r = qualify(self._BrokenJudge(), cal, log=lambda *_: None)
        self.assertFalse(r["qualified"])
        self.assertEqual(r["badge"], "NOT QUALIFIED")
        # wall-pricing eksenine hep 'informed' diyen hakem o eksende 0
        self.assertEqual(r["axes"]["wall-pricing"]["accuracy"], 0.0)


if __name__ == "__main__":
    unittest.main()
