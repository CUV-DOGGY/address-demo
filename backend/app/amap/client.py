import httpx
from app.amap.models import AmapResolvedLocation
from app.core.config import settings


class AmapClient:
    """调用高德 Web 服务 API 的异步客户端。"""

    _DIRECT_MUNICIPALITIES = {"北京市", "上海市", "天津市", "重庆市"}

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http_client = http_client

    async def get_poi_detail(self, poi_id: str) -> AmapResolvedLocation:
        """根据 POI ID 发送高德 POI 详情查询请求。"""

        response = await self._http_client.get(
            settings.AMAP_POI_DETAIL_URL,
            params={
                "key": settings.AMAP_API_KEY,
                "id": poi_id,
                "output": "json",
            },
        )

        poi = response.json()["pois"][0]
        address_parts = [poi["pname"]]
        if poi["pname"] not in self._DIRECT_MUNICIPALITIES:
            address_parts.append(poi["cityname"])
        address_parts.extend((poi["adname"], poi["address"]))

        return AmapResolvedLocation(
            formatted_address="".join(address_parts),
            adcode=poi["adcode"],
            location=poi["location"],
            poi_id=poi["id"],
        )

    async def reverse_geocode(self, location: str) -> AmapResolvedLocation:
        """根据经纬度发送高德逆地理编码请求。"""

        response = await self._http_client.get(
            settings.AMAP_REVERSE_GEOCODE_URL,
            params={
                "key": settings.AMAP_API_KEY,
                "location": location,
                "extensions": "base",
                "output": "json",
            },
        )

        regeocode = response.json()["regeocode"]
        return AmapResolvedLocation(
            formatted_address=regeocode["formatted_address"],
            adcode=regeocode["addressComponent"]["adcode"],
            location=location,
            poi_id=None,
        )
