from typing import AsyncGenerator

from annatar.indexers import Category, Indexer
from annatar.torrent import Torrent, TorrentMeta


class EZTV(Indexer):
    id: str = "eztv"
    name: str = "EZTV"
    categories: list[Category] = [Category.SERIES]
    supports_imdb: bool = False

    async def search(
        self,
        imdb: str,
        category: Category,
    ) -> AsyncGenerator[Torrent, None]:
        yield TorrentMeta.parse_title(
            "The Walking Dead S11E01 720p WEB H264-GGWP [eztv]"
        ).to_torrent("fake_hash")
        raise StopAsyncIteration
