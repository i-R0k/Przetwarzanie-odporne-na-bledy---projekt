## Fault Injection Scenarios

These scenarios describe how to exercise the cluster with up to two faulty nodes (and one failure-mode beyond the tolerated majority) using the new `FAULT_*` flags. Each scenario reuses the base `docker-compose.yml` and an additional override file.

Common steps for all scenarios:

1. Build and start the cluster (replace `scenario-x` with the desired override):
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.scenario-x.yml up --build -d
   ```
2. Submit multiple transactions through any node (example uses node4):
   ```bash
   curl -X POST http://localhost:8004/tx/submit \
     -H "Content-Type: application/json" \
     -d '{"sender":"a","recipient":"b","amount":1}'
   ```
   Repeat with varied payloads.
3. Trigger distributed mining on the leader (node1):
   ```bash
   curl -X POST http://localhost:8001/chain/mine_distributed
   ```
4. Inspect chain state on all nodes:
   ```bash
   for port in 8001 8002 8003 8004 8005 8006; do
     curl http://localhost:${port}/chain/status
   done
   ```

### Scenario A — 1 offline, 1 slow

- Override file: `docker-compose.scenario-a.yml`
- Faults: node3 offline (`FAULT_OFFLINE=true`), node4 slow (`FAULT_SLOW_MS=5000`)
- Expected outcome: node1, node2, node5, node6 mine and commit successfully despite the offline and slow peers; `mine_distributed` responds with `status="committed"` because a majority responds in time. Healthy nodes share the same `height` and `last_block_hash`.

You can also simulate intermittent failures by adding the new flapping/drop settings, for example:

- `FAULT_FLAPPING=true` with `FAULT_FLAPPING_MOD=3` (node answers only every third RPC),
- `FAULT_DROP_RPC_PROB=0.3` (roughly 30% of RPCs return HTTP 503).

Combine them with the scenarios above to showcase resilience against unstable nodes.

### Scenario B — 2 Byzantine followers

- Override file: `docker-compose.scenario-b.yml`
- Faults: node5 + node6 have `FAULT_BYZANTINE=true`
- Expected outcome: leader still achieves majority using votes from nodes1–4, so `mine_distributed` returns `status="committed"`. Nodes5–6 may report divergent states (they lie on vote/commit), which is acceptable for the scenario; nodes1–4 stay consistent.

### Scenario C — ≥3 Byzantine followers

- Override file: `docker-compose.scenario-c.yml`
- Faults: node4, node5, node6 have `FAULT_BYZANTINE=true`
- Expected outcome: leader cannot secure majority, so `/chain/mine_distributed` returns `status="rejected"` and the `height` on honest nodes (node1–3) does not increase.

You can customize the override files or combine them to craft additional scenarios (e.g., offline + Byzantine) as long as the number of faulty nodes stays within the desired tolerance. When finished, shut down the cluster via:

```bash
docker compose down
```
