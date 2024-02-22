from typing import Optional

import structlog

from annatar import human
from annatar.debrid import premiumize_api as api
from annatar.debrid.models import StreamLink
from annatar.debrid.pm_models import DirectDL, DirectDLResponse
from annatar.torrent import TorrentMeta

log = structlog.get_logger(__name__)


async def select_stream_file(
    files: list[DirectDL],
    season: int | None = None,
    episode: int | None = None,
) -> StreamLink | None:
    sorted_files: list[DirectDL] = sorted(files, key=lambda f: f.size, reverse=True)
    if len(sorted_files) == 0:
        return None
    if not season or not episode:
        """No season_episode is provided, return the biggest file"""
        f: DirectDL = sorted_files[0]
        return StreamLink(name=f.path.split("/")[-1], size=f.size, url=f.link)

    for file in sorted_files:
        if not human.is_video(file.path):
            log.debug("file is not a video", file=file.path)
            continue

        path = file.path.split("/")[-1].lower()
        meta: TorrentMeta = TorrentMeta.parse_title(path)
        if meta.is_season_episode(season=season, episode=episode):
            log.debug("path matches season and episode", path=path, season=season, episode=episode)
            return StreamLink(
                name=file.path.split("/")[-1],
                size=file.size,
                url=file.link,
            )
    log.debug("no file found for season and episode", season=season, episode=episode)
    return None


async def get_stream_link(
    info_hash: str,
    debrid_token: str,
    season: int | None = None,
    episode: int | None = None,
) -> StreamLink | None:
    log.debug("searching for stream link", info_hash=info_hash, season=season, episode=episode)
    dl: Optional[DirectDLResponse] = await api.directdl(
        info_hash=info_hash,
        api_token=debrid_token,
    )

    if not dl or not dl.content:
        log.debug("torrent has no cached content", info_hash=info_hash)
        return None

    stream_link = await select_stream_file(dl.content, season=season, episode=episode)
    if not stream_link:
        return None

    return stream_link
