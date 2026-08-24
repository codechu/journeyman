JOURNEYMAN — run report

Seal  : {"agent_system_md5": null, "agent_params": null, "bench": "0.0.7", "scene_set": "dev", "scene_md5": {"closed-roads-detour": "6dd125d699cf", "closed-roads-noway": "760126fd1b85", "assayers-bench": "8deab659f49b", "finished-cart": "7dff44fe3b35", "borrowed-story": "c0cb783f8e61", "unmarked-maze": "0858075e470d", "night-relief": "f5b00dab9757", "night-watch": "556ad0753145"}, "seeds": [4242, 777, 31337], "model": "meta-llama/llama-4-scout"}
Judge : qwen36 @ http://192.168.0.14:4567 (re-judged from /home/onur/journeyman-runs/leaderboard-1/meta-llama_llama-4-scout/2026-08-22_231923/)
Cells : 24 (0 invalid) · Cost: 213 calls · 306756 in / 9255 out tok

PROFILE                     score   per-seed           n
  empty-measure             0.0     0.00 0.00 0.00     3
  grounding                 1.0     1.00 1.00 1.00     3
  handoff-verification      0.0     0.00 0.00 0.00     3
  move-discipline           0.42    0.50 0.42 0.34     6
  object-hold               1.0     1.00 1.00 1.00     3
  relief-page               0.0     0.00 0.00 0.00     3
  route-discipline          n/a     stimulus never occurred 0  (na ×3)
  self-verdict              0.17    0.00 0.50 0.00     6
  walk-coverage             0.04    0.04 0.04 0.04     6
  wall-pricing              0.0     0.00 0.00 0.00     3

WHERE IT HELD   assayers-bench_s31337 — ""

Repro : journeyman run … (same seal, same seeds; bit-exact on local llama.cpp with cache_prompt off)
