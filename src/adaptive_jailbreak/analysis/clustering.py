from __future__ import annotations

from collections import defaultdict

from adaptive_jailbreak.schemas import TrajectoryRecord


def cluster_by_strategy_tags(records: list[TrajectoryRecord]) -> dict[str, list[TrajectoryRecord]]:
    clusters: dict[str, list[TrajectoryRecord]] = defaultdict(list)
    for record in records:
        key = ",".join(record.strategy_tags) if record.strategy_tags else "untagged"
        clusters[key].append(record)
    return dict(clusters)
