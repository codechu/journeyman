JOURNEYMAN — run report

Seal  : {"agent_system_md5": null, "agent_params": null, "bench": "0.0.7", "scene_set": "dev", "scene_md5": {"closed-roads-detour": "6dd125d699cf", "closed-roads-noway": "760126fd1b85", "assayers-bench": "8deab659f49b", "finished-cart": "7dff44fe3b35", "borrowed-story": "c0cb783f8e61", "unmarked-maze": "0858075e470d", "night-relief": "f5b00dab9757", "night-watch": "556ad0753145"}, "seeds": [4242, 777, 31337], "model": "qwen/qwen3.6-35b-a3b"}
Judge : (re-rendered — judge per cell records)  ⚠ NOT COMPARABLE — self-judged scores
Cells : 24 (0 invalid) · Cost: 495 calls · 1331182 in / 94065 out tok

PROFILE                     score   per-seed           n
  empty-measure             0.33    0.00 0.00 1.00     3
  grounding                 0.67    0.00 1.00 1.00     3
  handoff-verification      0.33    0.00 1.00 0.00     3
  move-discipline           0.77    0.78 0.65 0.88     6
  object-hold               1.0     1.00 1.00 1.00     3
  relief-page               0.0     0.00 0.00 0.00     3
  route-discipline          1.0     1.00               1
  self-verdict              0.83    1.00 1.00 0.50     6
  walk-coverage             0.36    0.34 0.27 0.47     6
  wall-pricing              0.67    1.00 1.00 0.00     3

WHERE IT HELD   assayers-bench_s31337 — ""
WHERE IT BROKE  assayers-bench_s4242 — budget died after 22 calls; no closing report

Repro : journeyman run … (same seal, same seeds; bit-exact on local llama.cpp with cache_prompt off)
