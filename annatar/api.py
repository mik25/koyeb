import asyncio
import math
from collections import defaultdict
from datetime import datetime
from itertools import chain
from typing import Optional

import structlog
from prometheus_client import Counter, Histogram

from annatar import human, instrumentation
from annatar.database import db
from annatar.debrid.models import StreamLink
from annatar.debrid.providers import DebridService
from annatar.indexers import Category, Indexer, parallel
from annatar.meta.cinemeta import MediaInfo, get_media_info
from annatar.stremio import Stream, StreamResponse
from annatar.torrent import Torrent, TorrentMeta

log = structlog.get_logger(__name__)

UNIQUE_SEARCHES: Counter = Counter(
    name="unique_searches",
    documentation="Unique stream search counter",
    registry=instrumentation.registry(),
)


async def _search(
    category: Category,
    max_results: int,
    debrid: DebridService,
    imdb_id: str,
    season_episode: list[int] = [],
    indexers: list[Indexer] = [],
) -> StreamResponse:
    if await db.unique_add("stream_request", f"{imdb_id}:{season_episode}"):
        log.debug("unique search")
        UNIQUE_SEARCHES.inc()

    media_info: Optional[MediaInfo] = await get_media_info(id=imdb_id, type=category.name)
    if not media_info:
        log.error("error getting media info", type=type, id=imdb_id)
        return StreamResponse(streams=[], error="Error getting media info")
    log.info("found media info", type=type, id=id, media_info=media_info.model_dump())

    torrent_queue: asyncio.Queue[Torrent] = asyncio.Queue(maxsize=5)
    cancel: asyncio.Event = asyncio.Event()
    asyncio.create_task(
        parallel.search(
            imdb=imdb_id,
            category=category,
            indexers=indexers,
            queue=torrent_queue,
            cancel=cancel,
        )
    )

    gather_tasks = [
        gather_stream_links(
            debrid=debrid,
            queue=torrent_queue,
            cancel=cancel,
            max_results=max_results / 3,
        )
        for _ in range(5)
    ]

    streams: list[Stream] = []
    for link in stream_links:
        meta: TorrentMeta = TorrentMeta.parse_title(link.name)
        torrent_name_parts: list[str] = [f"{meta.title}"]
        if type == "series":
            torrent_name_parts.append(
                f"S{str(meta.season[0]).zfill(1)}E{str(meta.episode[0]).zfill(2)}"
                if meta.season and meta.episode
                else ""
            )
            torrent_name_parts.append(f"{meta.episodeName}" if meta.episodeName else "")

        torrent_name: str = " ".join(torrent_name_parts)
        # squish the title portion before appending more parts
        meta_parts: list[str] = []
        if meta.resolution:
            meta_parts.append(f"📺{meta.resolution}")
        if meta.audio_channels:
            meta_parts.append(f"🔊{meta.audio_channels}")
        if meta.codec:
            meta_parts.append(f"{meta.codec}")
        if meta.quality:
            meta_parts.append(f"{meta.quality}")

        meta_parts.append(f"💾{human.bytes(float(link.size))}")

        name = f"[{debrid.short_name()}+] Annatar"
        name += f" {meta.resolution}" if meta.resolution else ""
        name += f" {meta.audio_channels}" if meta.audio_channels else ""
        streams.append(
            Stream(
                url=link.url.strip(),
                title="\n".join(
                    [
                        torrent_name,
                        arrange_into_rows(strings=meta_parts, rows=2),
                    ]
                ),
                name=name.strip(),
            )
        )

    return StreamResponse(streams=streams)


async def gather_stream_links(
    debrid: DebridService,
    queue: asyncio.Queue[Torrent],
    max_results: int,
    season: int | None = None,
    episode: int | None = None,
) -> list[StreamLink]:
    stream_links: list[StreamLink] = []
    while len(stream_links) < max_results:
        try:
            torrent: Torrent = await asyncio.wait_for(queue.get(), timeout=5)
        except asyncio.TimeoutError:
            break
        if not torrent:
            break
        link: StreamLink | None = await debrid.get_stream_link(
            info_hash=torrent.info_hash,
            season=season,
            episode=episode,
        )
        stream_links.extend(links)
        if len(stream_links) >= max_results:
            break
    return stream_links


def arrange_into_rows(strings: list[str], rows: int) -> str:
    split_index = (len(strings) + 1) // rows
    first_row = strings[:split_index]
    second_row = strings[split_index:]
    arranged_string = "\n".join([" ".join(first_row), " ".join(second_row)])
    return arranged_string


REQUEST_DURATION = Histogram(
    name="api_request_duration_seconds",
    documentation="Duration of API requests in seconds",
    labelnames=["type", "debrid_service", "cached", "error"],
    registry=instrumentation.registry(),
)


async def get_hashes(
    imdb_id: str,
    limit: int = 20,
    season: int | None = None,
    episode: int | None = None,
) -> list[db.ScoredItem]:
    cache_key: str = f"jackett:search:{imdb_id}"
    if not season and not episode:
        res = await db.unique_list_get_scored(f"{cache_key}:torrents")
        return res[:limit]
    if season and episode:
        cache_key += f":{season}:{episode}"
        res = await db.unique_list_get_scored(cache_key)
        return res[:limit]
    else:
        items: dict[str, db.ScoredItem] = {}
        cache_key += f":{season}:*"
        keys = await db.list_keys(f"{cache_key}:*")
        for values in asyncio.gather(asyncio.create_task(db.unique_list_get(key)) for key in keys):
            for value in values:
                items[value.value] = value
                if len(items) >= limit:
                    return list(items.values())[:limit]
        return list(items.values())[:limit]


async def search(
    type: str,
    max_results: int,
    debrid: DebridService,
    imdb_id: str,
    season_episode: list[int] = [],
    indexers: list[str] = [],
) -> StreamResponse:
    start_time = datetime.now()
    res: Optional[StreamResponse] = None
    try:
        res = await _search(
            type=type,
            max_results=max_results,
            debrid=debrid,
            imdb_id=imdb_id,
            season_episode=season_episode,
            indexers=indexers,
        )
        return res
    except Exception as e:
        log.error("error searching", type=type, id=imdb_id, exc_info=e)
        res = StreamResponse(streams=[], error="Error searching")
        return res
    finally:
        secs = (datetime.now() - start_time).total_seconds()
        REQUEST_DURATION.labels(
            type=type,
            debrid_service=debrid.id(),
            cached=res.cached if res else False,
            error=True if res and res.error else False,
        ).observe(
            secs,
            exemplar={
                "imdb": imdb_id,
                "season_episode": ",".join([str(i) for i in season_episode]),
            },
        )
