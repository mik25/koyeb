from .base import Category, Indexer
from .eztv import EZTV

ALL_INDEXERS: list[Indexer] = [EZTV()]


def get_indexer_by_id(indexer_id: str) -> Indexer | None:
    for indexer in ALL_INDEXERS:
        if indexer.id == indexer_id:
            return indexer
    return None
