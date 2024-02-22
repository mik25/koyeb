import asyncio
from typing import AsyncGenerator

from annatar.indexers import Category, Indexer
from annatar.torrent import Torrent


async def search(
    indexers: list[Indexer],
    imdb: str,
    category: Category,
    queue: asyncio.Queue[Torrent],
    cancel: asyncio.Event,
):
    searches: list[AsyncGenerator[Torrent, None]] = [
        indexer.search(
            imdb=imdb,
            category=category,
        )
        for indexer in indexers
    ]

    gather_tasks = [asyncio.create_task(gather_items(s, queue)) for s in searches]
    cancel_task = asyncio.create_task(cancel.wait())
    all_tasks = gather_tasks + [cancel_task]
    while not all(task.done() for task in gather_tasks) and not cancel.is_set():
        await asyncio.sleep()


async def gather_items(search: AsyncGenerator[Torrent, None], queue: asyncio.Queue[Torrent]):
    async for torrent in search:
        await queue.put(torrent)
