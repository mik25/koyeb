from annatar.debrid import pm
from annatar.debrid.debrid_service import DebridService
from annatar.debrid.models import StreamLink


class PremiumizeProvider(DebridService):
    def __str__(self) -> str:
        return "PremiumizeProvider"

    def short_name(self) -> str:
        return "PM"

    def name(self) -> str:
        return "premiumize.me"

    def id(self) -> str:
        return "premiumize"

    def shared_cache(self):
        return False

    async def get_stream_link(
        self,
        info_hash: str,
        season: int | None = None,
        episode: int | None = None,
    ) -> StreamLink | None:
        return await pm.get_stream_link(
            info_hash=info_hash,
            debrid_token=self.api_key,
            season=season,
            episode=episode,
        )
