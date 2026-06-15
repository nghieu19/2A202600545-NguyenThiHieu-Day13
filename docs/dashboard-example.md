Six-panel dashboard example

Panels:

1. Traffic
- Metric: `traffic`
- Visualization: single value + timeseries

2. Latency
- Metrics: `latency_p50`, `latency_p95`, `latency_p99`
- Visualization: line chart with p50/p95/p99 bands

3. Error Rate
- Metric: derived `error_rate_pct` = sum(errors)/traffic * 100
- Visualization: single value + timeseries, alert when > 5%

4. Cost
- Metrics: `avg_cost_usd`, `total_cost_usd`
- Visualization: single value + bar chart hourly

5. Tokens
- Metrics: `tokens_in_total`, `tokens_out_total`
- Visualization: stacked bar or timeseries

6. Quality
- Metric: `quality_avg`
- Visualization: gauge or single value, target > 0.8

Notes:
- Export metrics from GET /metrics and import into your dashboard tool (Grafana/Looker).
- Use `correlation_id` to link logs and traces when investigating an alert.
