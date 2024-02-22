from datetime import datetime, timedelta
from typing import Optional

import aiohttp
import structlog

from annatar.database import odm
from annatar.instrumentation import HTTP_CLIENT_REQUEST_DURATION
from annatar.meta.cinemeta_models import MediaInfo

log = structlog.get_logger(__name__)


async def _get_media_info(id: str, type: str) -> MediaInfo | None:
    api_url = f"https://v3-cinemeta.strem.io/meta/{type}/{id}.json"
    status = ""
    error = False
    start_time = datetime.now()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                status = f"{response.status // 100}xx"
                if response.status not in range(200, 300):
                    log.error(
                        "Error retrieving MediaInfo from strem.io",
                        status=response.status,
                        reason=response.reason,
                        body=await response.text(),
                    )
                    error = True
                    return None
                response_json = await response.json()
                meta = response_json.get("meta", None)
                if not meta:
                    log.info(
                        "meta field is missing from response_json. Probably no results",
                        api_url=api_url,
                        response_json=response_json,
                    )
                    return None

                media_info = MediaInfo(**meta)
                return media_info
    finally:
        HTTP_CLIENT_REQUEST_DURATION.labels(
            client="cinemeta",
            method="GET",
            url="/meta/{type}/{id}.json",
            status_code=status,
            error=error,
        ).observe(amount=(datetime.now() - start_time).total_seconds())


async def get_media_info(id: str, type: str) -> Optional[MediaInfo]:
    cached_result: Optional[MediaInfo] = await odm.get_media_info(type=type, imdb_id=id)
    if cached_result:
        return cached_result

    res: Optional[MediaInfo] = await _get_media_info(id=id, type=type)
    if res is None:
        return None

    await odm.put_media_info(imdb_id=id, info=res, ttl=timedelta(days=30))
