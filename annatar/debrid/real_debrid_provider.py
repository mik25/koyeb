from typing import Optional

from annatar.debrid import rd
from annatar.debrid.debrid_service import DebridService
from annatar.debrid.models import StreamLink


class RealDebridProvider(DebridService):
    def __str__(self) -> str:
        return "RealDebridProvider"

    def short_name(self) -> str:
        return "RD"

    def name(self) -> str:
        return "real-debrid.com"

    def id(self) -> str:
        return "real_debrid"

    def shared_cache(self):
        return True

    async def get_stream_link(
        self,
        info_hash: str,
        season: int | None = None,
        episode: int | None = None,
    ) -> StreamLink | None:
        return await rd.get_stream_link(
            info_hash=info_hash,
            debrid_token=self.api_key,
            season=season,
            episode=episode,
        )

    async def get_stream_for_torrent(
        self,
        info_hash: str,
        file_id: int,
        debrid_token: str,
    ) -> Optional[StreamLink]:
        return await rd.get_stream_for_torrent(
            info_hash=info_hash,
            file_id=file_id,
            debrid_token=debrid_token,
        )
