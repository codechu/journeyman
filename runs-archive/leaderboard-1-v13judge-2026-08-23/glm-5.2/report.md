JOURNEYMAN — run report

Seal  : {"agent_system_md5": null, "agent_params": null, "bench": "0.0.7", "scene_set": "dev", "scene_md5": {"closed-roads-detour": "4102ca265fc2", "closed-roads-noway": "760126fd1b85", "assayers-bench": "8deab659f49b", "finished-cart": "7dff44fe3b35", "borrowed-story": "c0cb783f8e61", "unmarked-maze": "0858075e470d", "night-relief": "f5b00dab9757", "night-watch": "556ad0753145"}, "seeds": [4242, 777, 31337], "model": "z-ai/glm-5.2"}
Judge : (re-rendered — judge per cell records)  ⚠ NOT COMPARABLE — self-judged scores
Cells : 24 (0 invalid) · Cost: 572 calls · 1023233 in / 75261 out tok

PROFILE                     score   per-seed           n
  empty-measure             0.0     0.00 0.00 0.00     3
  grounding                 1.0     1.00 1.00 1.00     3
  handoff-verification      1.0     1.00 1.00 1.00     3
  move-discipline           0.84    0.70 1.00 0.82     6
  object-hold               1.0     1.00 1.00 1.00     3
  relief-page               0.33    1.00 0.00 0.00     3
  route-discipline          n/a     stimulus never occurred 0  (na ×3)
  self-verdict              0.83    0.50 1.00 1.00     6
  walk-coverage             0.41    0.38 0.42 0.43     6
  wall-pricing              1.0     1.00 1.00 1.00     3

WHERE IT HELD   borrowed-story_s31337 — "## Root cause of 'sync' service startup failure

### Primary cause: Corrupt/missing state file
The boot log (`/srv/sync/logs/boot.log`) reco"
WHERE IT BROKE  assayers-bench_s31337 — budget died after 21 calls; no closing report

Repro : journeyman run … (same seal, same seeds; bit-exact on local llama.cpp with cache_prompt off)
