import asyncio
from abc import ABC, abstractmethod
from typing import AsyncGenerator

from annatar.debrid.models import StreamLink
from annatar.torrent import Torrent


class DebridService(ABC):
    api_key: str

    def __str__(self) -> str:
        return self.name()

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    def shared_cache(self) -> bool: ...

    @abstractmethod
    def short_name(self) -> str: ...

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def id(self) -> str: ...

    @abstractmethod
    async def get_stream_link(
        self,
        info_hash: str,
        season: int | None = None,
        episode: int | None = None,
    ) -> StreamLink | None: ...
