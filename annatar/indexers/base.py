from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, List, Optional, Type

from pydantic import BaseModel

from annatar.torrent import Torrent


class Category(int, Enum):
    MOVIE = 2000
    SERIES = 5000

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self.name.lower() == other.lower() or str(self.value).lower == other.lower()
        return super().__eq__(other)

    def __str__(self) -> str:
        return self.name.lower()

    @staticmethod
    def get_by_name(name: str) -> Optional["Category"]:
        for cat in Category:
            if cat == name:
                return cat
        return None


class Indexer(BaseModel, ABC):
    id: str
    name: str
    categories: list[Category]
    supports_imdb: bool

    def supports(self, category: Category) -> bool:
        for cat in self.categories:
            if cat.name == category:
                return True
        return False

    # Search an Indexer for a torrent using the imdb id and category
    # If the indexer does not support imdb searching then it should get the
    # metadata from the db using the imdb id.
    @abstractmethod
    def search(
        self,
        imdb: str,
        category: Category,
    ) -> AsyncGenerator[Torrent, None]: ...
