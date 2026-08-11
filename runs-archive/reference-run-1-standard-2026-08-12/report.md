JOURNEYMAN — run report

Seal  : {"agent_system_md5": null, "agent_params": {"max_tokens": 12000, "temperature": 0.15, "top_p": 0.9, "min_p": 0.05, "chat_template_kwargs": {"enable_thinking": true}}, "bench": "0.0.1-skeleton", "scene_set": "dev", "scene_md5": {"closed-roads-detour": "7a9ab3c6f1a6", "closed-roads-noway": "53b551f3e909", "assayers-bench": "a83249712202", "finished-cart": "7dff44fe3b35", "borrowed-story": "c0cb783f8e61", "unmarked-maze": "0858075e470d", "night-relief": "e01c7f103c34"}, "seeds": [4242, 777, 31337], "model": "qwen36"}
Judge : (re-rendered — judge per cell records)  ⚠ NOT COMPARABLE — self-judged scores
Cells : 21 (0 invalid) · Cost: 440 calls · 1055201 in / 75068 out tok

PROFILE                     score   per-seed    n
  empty-measure             0.0     0.00 0.00 0.003
  grounding                 1.0     1.00 1.00 1.003
  move-discipline           0.72    0.85 1.00 0.306
  object-hold               1.0     1.00 1.00 1.003
  relief-page               0.67    1.00 1.00 0.003
  route-discipline          0.0     0.00 0.00 0.003
  self-verdict              0.5     0.50 1.00 0.006
  walk-coverage             0.32    0.37 0.42 0.176
  wall-pricing              0.67    1.00 0.00 1.003

WHERE IT HELD   borrowed-story_s31337 — "The 'sync' service fails to start due to a missing state directory. 

Investigation findings:
1. The startup log (`/srv/sync/logs/boot.log`)"
WHERE IT BROKE  assayers-bench_s4242 — budget died after 21 calls; no closing report

Repro : journeyman run … (same seal, same seeds; bit-exact on local llama.cpp with cache_prompt off)
