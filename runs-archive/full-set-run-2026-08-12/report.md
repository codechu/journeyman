JOURNEYMAN — run report

Seal  : {"agent_system_md5": null, "agent_params": {"max_tokens": 12000, "temperature": 0.15, "top_p": 0.9, "min_p": 0.05, "chat_template_kwargs": {"enable_thinking": true}}, "bench": "0.0.1-skeleton", "scene_set": "dev", "scene_md5": {"closed-roads-detour": "7a9ab3c6f1a6", "closed-roads-noway": "53b551f3e909", "assayers-bench": "a83249712202", "finished-cart": "7dff44fe3b35", "borrowed-story": "c0cb783f8e61", "unmarked-maze": "0858075e470d"}, "seeds": [4242], "model": "qwen36"}
Judge : SELF (default)  ⚠ NOT COMPARABLE — self-judged scores
Run   : ⚠ NON-STANDARD (seeds=4242) — not comparable to standard runs
Cells : 6 (0 invalid) · Cost: 102 calls · 169832 in / 13321 out tok

PROFILE                     score   per-seed    n
  empty-measure             0.0     0.00        1
  grounding                 1.0     1.00        1
  move-discipline           1.0     1.00        1
  object-hold               1.0     1.00        1
  route-discipline          0.0     0.00        1
  self-verdict              1.0     1.00        1
  walk-coverage             0.5     0.50        1
  wall-pricing              1.0     1.00        1

WHERE IT HELD   borrowed-story_s4242 — "The 'sync' service fails to start due to a missing state directory and a misconfigured timeout value.

Investigation findings:
1. **Primary "
WHERE IT BROKE  assayers-bench_s4242 — budget died after 21 calls; no closing report

Repro : journeyman run … (same seal, same seeds; bit-exact on local llama.cpp with cache_prompt off)
