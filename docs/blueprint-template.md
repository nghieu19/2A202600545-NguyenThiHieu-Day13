# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: 2A202600545 - Nguyen Thi Hieu (individual submission)
- [REPO_URL]: https://github.com/nghieu19/2A202600545-NguyenThiHieu-Day13
- [MEMBERS]:
  - Member A: Nguyen Thi Hieu | Role: Logging, PII, tracing, SLOs, alerts, load testing, dashboard, and report
  - Member B: N/A | Role: Individual submission
  - Member C: N/A | Role: Individual submission
  - Member D: N/A | Role: Individual submission
  - Member E: N/A | Role: Individual submission

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 131 instrumented successful chat requests (131 unique chat correlation IDs); live Langfuse UI count was not exported to the repository
- [PII_LEAKS_FOUND]: 0

Verification on June 15, 2026: `data/logs.jsonl` contained 285 valid JSON records, 131 successful chat requests, 135 unique correlation IDs overall, no missing required/enrichment fields, and no PII leak detected by `scripts/validate_logs.py`.

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: Screenshot not committed; machine-readable evidence is in `data/logs.jsonl` (for example correlation ID `req-7130eb6b`) and implementation is in `app/middleware.py`.
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: Screenshot not committed; `data/logs.jsonl` lines 269 and 279 contain `[REDACTED_EMAIL]` and `[REDACTED_CREDIT_CARD]` with zero validator leaks.
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: Screenshot not committed; trace/span instrumentation is in `app/agent.py` with `agent.run`, `rag.retrieve`, and `llm.generate` observations.
- [TRACE_WATERFALL_EXPLANATION]: In the `rag_slow` scenario, the `rag.retrieve` span is the dominant span because `app/mock_rag.py` injects a 2.5-second delay. The LLM span remains comparatively stable, so the waterfall localizes the latency to retrieval rather than generation.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: Screenshot not committed. The six-panel design is documented in `docs/dashboard-example.md`; the current `docs/grafana-dashboard.json` export contains 3 configured panels, so the six-panel dashboard is not yet fully evidenced.
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 161ms |
| Error Rate | < 2% | 28d | 0% (0 errors / 21 requests) |
| Cost Budget | < $2.5/day | 1d | $0.0395 captured run total |
| Quality Score Average | >= 0.75 | 28d | 0.8762 |

Current values come from `data/metrics_snapshot.json`. The snapshot is a captured test run, not a complete 28-day production window.

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: Screenshot not committed; four rules are defined in `config/alert_rules.yaml`: high latency, high error rate, cost spike, and low quality score.
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#1-high-latency-p95](alerts.md#1-high-latency-p95)

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Tail latency increased from the normal snapshot P95 of 161ms to approximately 2.65-2.69 seconds; 20 recorded responses exceeded 2000ms.
- [ROOT_CAUSE_PROVED_BY]: Log correlation ID `req-47201aee` recorded `latency_ms=2664`; `app/mock_rag.py` proves the cause with `time.sleep(2.5)` when the `rag_slow` incident toggle is enabled. The corresponding trace should show the delay in `rag.retrieve`.
- [FIX_ACTION]: Disable the incident with `python scripts/inject_incident.py --scenario rag_slow --disable`, then repeat the load test and confirm P95 returns below the 3000ms SLO.
- [PREVENTIVE_MEASURE]: Keep the retrieval span separately instrumented, alert on sustained P95 latency, add a retrieval timeout/fallback source, and verify recovery with the same correlation-ID flow from metrics to traces to logs.

---

## 5. Individual Contributions & Evidence

### [MEMBER_A_NAME]: Nguyen Thi Hieu
- [TASKS_COMPLETED]: Implemented request correlation ID propagation and response headers; bound hashed user/session/feature/model context to structured logs; enabled recursive PII redaction for email, phone, identity numbers, cards, credentials, passport, and address data; added RAG/LLM tracing metadata and token usage; added quality, cost, token, traffic, and latency metrics; defined SLOs and four alert rules; created dashboard artifacts and completed incident analysis/reporting.
- [EVIDENCE_LINK]: [Commit cb73bc5](https://github.com/nghieu19/2A202600545-NguyenThiHieu-Day13/commit/cb73bc566c317f3883e19d6cc6d8421cfa77302b) and the current working-tree files `app/agent.py`, `app/pii.py`, `app/tracing.py`, `config/slo.yaml`, `config/alert_rules.yaml`, `docs/grafana-dashboard.json`, and `scripts/evaluate_alerts.py`.

### [MEMBER_B_NAME]: N/A
- [TASKS_COMPLETED]: N/A - individual submission.
- [EVIDENCE_LINK]: N/A

### [MEMBER_C_NAME]: N/A
- [TASKS_COMPLETED]: N/A - individual submission.
- [EVIDENCE_LINK]: N/A

### [MEMBER_D_NAME]: N/A
- [TASKS_COMPLETED]: N/A - individual submission.
- [EVIDENCE_LINK]: N/A

### [MEMBER_E_NAME]: N/A
- [TASKS_COMPLETED]: N/A - individual submission.
- [EVIDENCE_LINK]: N/A

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: Token-based cost estimation and per-request/total cost metrics are implemented in `app/agent.py` and `app/metrics.py`; no before/after optimization benchmark is claimed.
- [BONUS_AUDIT_LOGS]: Not implemented; application logs are written to `data/logs.jsonl`, but no separate `data/audit.jsonl` pipeline is evidenced.
- [BONUS_CUSTOM_METRIC]: Implemented `quality_score` per response and `quality_avg` aggregation. The captured average is 0.8762 against the 0.75 SLO, with a `low_quality_score` alert rule.
