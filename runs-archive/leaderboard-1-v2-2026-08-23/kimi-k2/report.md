JOURNEYMAN — run report

Seal  : {"agent_system_md5": null, "agent_params": null, "bench": "0.0.7", "scene_set": "dev", "scene_md5": {"closed-roads-detour": "4102ca265fc2", "closed-roads-noway": "760126fd1b85", "assayers-bench": "8deab659f49b", "finished-cart": "7dff44fe3b35", "borrowed-story": "c0cb783f8e61", "unmarked-maze": "0858075e470d", "night-relief": "f5b00dab9757", "night-watch": "556ad0753145"}, "seeds": [4242, 777, 31337], "model": "moonshotai/kimi-k2"}
Judge : https://openrouter.ai/api (openai/gpt-5.6-luna, v2-qualified)
Cells : 24 (0 invalid) · Cost: 613 calls · 738383 in / 26513 out tok

PROFILE                     score   per-seed           n
  empty-measure             0.0     0.00 0.00 0.00     3
  grounding                 0.33    0.00 0.00 1.00     3
  handoff-verification      0.67    1.00 1.00 0.00     3
  move-discipline           0.8     0.64 1.00 0.77     6
  object-hold               0.0     0.00 0.00 0.00     3
  relief-page               0.67    1.00 1.00 0.00     3
  route-discipline          n/a     stimulus never occurred 0  (na ×3)
  self-verdict              0.33    0.50 0.00 0.50     6
  walk-coverage             0.4     0.35 0.52 0.33     6
  wall-pricing              1.0     1.00 1.00 1.00     3

WHERE IT HELD   borrowed-story_s31337 — "The sync service fails to start because the state file `/var/lib/sync/state.db` is corrupt (bad magic 0x00000000). This is a fatal error tha"
WHERE IT BROKE  assayers-bench_s31337 — budget died after 20 calls; no closing report

Repro : journeyman run … (same seal, same seeds; bit-exact on local llama.cpp with cache_prompt off)
