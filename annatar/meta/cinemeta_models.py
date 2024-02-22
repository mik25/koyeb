from typing import Any, Optional

from pydantic import BaseModel, computed_field, field_validator


class Video(BaseModel):
    id: str  # <imdb_id>:<season>:<episode> for series and <imdb_id> for  movies
    name: str
    season: int
    episode: int
    tvdb_id: int
    rating: str


class MediaInfo(BaseModel):
    id: str
    type: str
    name: str
    imdb_id: str

    videos: list[Video] = []

    description: Optional[str] = None
    # A.k.a. year, e.g. "2000" for movies and "2000-2014" or "2000-" for TV shows
    releaseInfo: Optional[str] = ""
    imdbRating: Optional[str] = None
    # ISO 8601, e.g. "2010-12-06T05:00:00.000Z"
    released: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    awards: Optional[str] = None
    website: Optional[str] = None

    @computed_field
    @property
    def year(self) -> int | None:
        return int(self.releaseInfo.split("-")[0]) if self.releaseInfo else None

    @field_validator("videos", mode="before")
    @classmethod
    def ensure_is_list(cls: Any, v: Any):
        if v is None:
            return []
        if isinstance(v, int):
            return [v]
        if isinstance(v, str):
            return [v]
        return v
