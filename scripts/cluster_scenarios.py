from __future__ import annotations

import argparse
import random
from typing import Callable

import httpx

NODES = {
    1: "http://localhost:8001",
    2: "http://localhost:8002",
    3: "http://localhost:8003",
    4: "http://localhost:8004",
    5: "http://localhost:8005",
    6: "http://localhost:8006",
}
LEADER_ID = 1


def submit_tx(node_id: int, sender: str, recipient: str, amount: float) -> dict:
    base_url = NODES[node_id]
    try:
        resp = httpx.post(
            f"{base_url}/tx/submit",
            json={"sender": sender, "recipient": recipient, "amount": amount},
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
        print(
            f"[submit_tx] node={node_id} status={resp.status_code} payload={payload}"
        )
        return payload
    except httpx.RequestError as exc:
        print(f"[submit_tx] node={node_id} error={exc}")
        raise


def get_status(node_id: int, client: httpx.Client | None = None) -> dict | None:
    base_url = NODES[node_id]
    request_client = client or httpx.Client()
    try:
        resp = request_client.get(f"{base_url}/chain/status", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except httpx.RequestError as exc:
        print(f"[get_status] node={node_id} error={exc}")
        return None
    except httpx.HTTPStatusError as exc:
        print(f"[get_status] node={node_id} status_error={exc.response.status_code}")
        return None
    finally:
        if client is None:
            request_client.close()


def mine_distributed() -> dict | None:
    base_url = NODES[LEADER_ID]
    try:
        resp = httpx.post(f"{base_url}/chain/mine_distributed", timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        status = payload.get("status")
        votes = payload.get("votes")
        total = payload.get("total")
        print(
            f"[mine_distributed] status={status} votes={votes} total={total} payload={payload}"
        )
        return payload
    except httpx.RequestError as exc:
        print(f"[mine_distributed] leader unreachable: {exc}")
        return None
    except httpx.HTTPStatusError as exc:
        print(
            f"[mine_distributed] leader returned {exc.response.status_code}: {exc.response.text}"
        )
        return None


def print_cluster_status(client: httpx.Client) -> None:
    print("\nCluster status:")
    rows = []
    consensus_set = set()
    for node_id in sorted(NODES):
        status = get_status(node_id, client)
        if not status:
            rows.append((node_id, None, None))
            continue
        height = status.get("height")
        block_hash = status.get("last_block_hash")
        short_hash = block_hash[:8] if block_hash else None
        rows.append((node_id, height, short_hash))
        if height is not None and block_hash:
            consensus_set.add((height, block_hash))

    for node_id, height, short_hash in rows:
        print(f" - node {node_id}: height={height} hash={short_hash}")

    if len(consensus_set) > 1:
        print(
            f"[warning] Nodes disagree on chain tip: {len(consensus_set)} different values"
        )
    elif len(consensus_set) == 1:
        height, block_hash = next(iter(consensus_set))
        print(f"[info] Consensus height={height} hash={block_hash[:8]}")
    else:
        print("[warning] No consensus data collected")


def _send_transactions(target_nodes: list[int], count: int = 3) -> None:
    for i in range(count):
        node_id = random.choice(target_nodes)
        sender = f"user{i}_a"
        recipient = f"user{i}_b"
        amount = 1 + i
        try:
            submit_tx(node_id, sender, recipient, amount)
        except Exception:
            continue


def scenario_healthy() -> None:
    """All nodes healthy; expect full agreement."""
    target_nodes = list(NODES.keys())
    _send_transactions(target_nodes, count=3)
    mine_distributed()
    with httpx.Client() as client:
        print_cluster_status(client)
        verify_cluster(client)


def scenario_faults_offline_slow() -> None:
    """
    Node3 is offline, node4 is slow. Majority of healthy nodes should share the same
    height/hash; node3 may be missing or return 503, node4 may lag but eventually aligns.
    """
    target_nodes = [2, 4, 5]
    _send_transactions(target_nodes, count=4)
    mine_distributed()
    with httpx.Client() as client:
        print_cluster_status(client)
        verify_cluster(client)


def scenario_faults_byzantine_2() -> None:
    """
    Node5 and node6 are Byzantine. Leader should still gather majority and commit;
    nodes1-4 should match, while nodes5/6 may diverge.
    """
    target_nodes = [1, 2, 3, 4, 5, 6]
    _send_transactions(target_nodes, count=4)
    mine_distributed()
    with httpx.Client() as client:
        print_cluster_status(client)
        verify_cluster(client)


def scenario_faults_byzantine_3() -> None:
    """
    Nodes4-6 are Byzantine. Leader should fail to reach majority, so status is rejected
    and heights on nodes1-3 remain unchanged.
    """
    target_nodes = [1, 2, 3, 4, 5, 6]
    _send_transactions(target_nodes, count=4)
    mine_distributed()
    with httpx.Client() as client:
        print_cluster_status(client)
        verify_cluster(client)
    print("[info] Height stability on nodes1-3 is expected in this scenario.")


SCENARIOS: dict[str, Callable[[], None]] = {
    "healthy": scenario_healthy,
    "faults_offline_slow": scenario_faults_offline_slow,
    "faults_byzantine_2": scenario_faults_byzantine_2,
    "faults_byzantine_3": scenario_faults_byzantine_3,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Cluster scenario runner")
    parser.add_argument(
        "scenario",
        choices=SCENARIOS.keys(),
        help="Scenario to run",
    )
    args = parser.parse_args()
    scenario_fn = SCENARIOS.get(args.scenario)
    if not scenario_fn:
        parser.error(f"Unknown scenario {args.scenario}")
    scenario_fn()


if __name__ == "__main__":
    main()
def verify_cluster(client: httpx.Client) -> None:
    print("\n=== /chain/verify on all nodes ===")
    for node_id in sorted(NODES):
        base_url = NODES[node_id]
        url = f"{base_url}/chain/verify"
        try:
            resp = client.get(url, timeout=5.0)
            if resp.status_code != 200:
                print(f"node {node_id}: HTTP {resp.status_code}")
                continue
            data = resp.json()
            status = "OK" if data.get("valid") else "INVALID"
            errors = data.get("errors") or []
            print(
                f"node {node_id}: {status}, height={data.get('height')}, errors={len(errors)}"
            )
            if errors:
                print(f"  first error: {errors[0]}")
        except Exception as exc:
            print(f"node {node_id}: ERROR calling /chain/verify: {exc}")
