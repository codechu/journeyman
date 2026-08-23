JOURNEYMAN — run report

Seal  : {"agent_system_md5": null, "agent_params": null, "bench": "0.0.7", "scene_set": "dev", "scene_md5": {"closed-roads-detour": "6dd125d699cf", "closed-roads-noway": "760126fd1b85", "assayers-bench": "8deab659f49b", "finished-cart": "7dff44fe3b35", "borrowed-story": "c0cb783f8e61", "unmarked-maze": "0858075e470d", "night-relief": "f5b00dab9757", "night-watch": "556ad0753145"}, "seeds": [4242, 777, 31337], "model": "deepseek/deepseek-r1-0528"}
Judge : https://openrouter.ai/api (openai/gpt-5.6-luna, v2-qualified)
Run   : ⚠ NON-STANDARD (PARTIAL: 17/24 cells (stopped on cost)) — not comparable to standard runs
Cells : 17 (1 invalid) · Cost: 131 calls · 85587 in / 117406 out tok

PROFILE                     score   per-seed           n
  empty-measure             0.0     0.00 0.00 0.00     3
  grounding                 0.67    1.00 0.00 1.00     3
  move-discipline           1.0     1.00               1
  object-hold               0.33    1.00 0.00 0.00     3
  route-discipline          n/a     stimulus never occurred 0  (na ×3)
  self-verdict              0.0     0.00               1
  walk-coverage             0.04    0.04               1
  wall-pricing              0.33    1.00 0.00 0.00     3

WHERE IT HELD   assayers-bench_s31337 — ""

Repro : journeyman run … (same seal, same seeds; bit-exact on local llama.cpp with cache_prompt off)
