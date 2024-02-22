from datetime import timedelta
from typing import Any

from annatar.database import db
from annatar.debrid.models import StreamLink
from annatar.debrid.premiumize_models import DirectDLResponse
from annatar.debrid.rd_models import InstantFileSet
from annatar.jackett_models import SearchResults as JackettSearchResults
from annatar.meta.cinemeta_models import MediaInfo


class MediaInfos:
    @staticmethod
    async def get(type: str, imdb_id: str) -> MediaInfo | None:
        return await db.get_model(f"cinemeta:{imdb_id}", MediaInfo)

    @staticmethod
    async def put(imdb_id: str, info: MediaInfo, ttl: timedelta) -> bool:
        return await db.set_model(f"cinemeta:{imdb_id}", info, ttl=ttl)


class DirectDLResponses:
    @staticmethod
    async def get(info_hash: str) -> None | DirectDLResponse:
        return await db.get_model(f"premiumize:directdl:{info_hash.upper()}", DirectDLResponse)

    @staticmethod
    async def put(info_hash: str, dl: DirectDLResponse, ttl: timedelta) -> bool:
        return await db.set_model(f"premiumize:directdl:{info_hash.upper()}", dl, ttl=ttl)


class StreamLinks:

    @staticmethod
    async def get(provider_short_name: str, info_hash: str, unique_key: str) -> StreamLink | None:
        """
        Get a StreamLink for the provider.
        Unique key is decided by the provider but should identify the file
        within the torrent. Some providers (RD) does not support sharing links,
        so the unique key must be globally unique.
        """
        # XXX support this for a while to avoid breaking changes but remove it
        # later when all the TTLs have expired
        if old := await db.get_model(
            f"{provider_short_name.lower()}:torrent:{info_hash.upper()}:{unique_key}",
            StreamLink,
        ):
            return old

        return await db.get_model(
            f"{provider_short_name.lower()}:stream_links:{info_hash.upper()}:{unique_key}",
            StreamLink,
        )
        return

    @staticmethod
    async def set(
        provider_short_name: str,
        info_hash: str,
        unique_key: str,
        ttl: timedelta,
        sl: StreamLink,
    ) -> bool:
        # only support setting the new keys
        return await db.set_model(
            f"{provider_short_name.lower()}:stream_links:{info_hash.upper()}:{unique_key}",
            sl,
            ttl=ttl,
        )


class RDInstantFileSets:
    @staticmethod
    async def get(info_hash: str) -> InstantFileSet | None:
        return await db.get_model(
            f"rd:instant_file_set:torrent:{info_hash.upper()}", InstantFileSet
        )

    @staticmethod
    async def put(info_hash: str, ifs: InstantFileSet, ttl: timedelta) -> bool:
        return await db.set_model(f"rd:instant_file_set:torrent:{info_hash.upper()}", ifs, ttl=ttl)


class Jackett:
    class SearchResults:
        @staticmethod
        async def get(indexer: str, search_params: dict[str, Any]) -> None | JackettSearchResults:
            return await db.get_model(
                f"jackett:search:{indexer}:{search_params}", JackettSearchResults
            )
            pass

        @staticmethod
        async def put(
            indexer: str,
            search_params: dict[str, Any],
            results: JackettSearchResults,
            ttl: timedelta,
        ) -> bool:
            return await db.set_model(f"jackett:search:{indexer}:{search_params}", results, ttl=ttl)
            pass
