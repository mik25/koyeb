from pydantic import BaseModel, Field

from annatar.torrent import TorrentMeta


class StreamLink(BaseModel):
    torrent: TorrentMeta = Field(..., exclude=True)
    size: int
    name: str
    url: str
