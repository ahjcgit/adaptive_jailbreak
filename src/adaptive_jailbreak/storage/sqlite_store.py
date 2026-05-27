from __future__ import annotations


class SQLiteTrajectoryStore:
    '''Reserved optional store.

    JSONL is the canonical first implementation. This class marks the intended extension point
    without introducing a second persistence path before the JSONL schema stabilizes.
    '''

    def __init__(self, *args, **kwargs) -> None:
        raise NotImplementedError("SQLite storage is planned after the JSONL schema stabilizes.")
