import httpx

from app.amap.exceptions import (
    AmapAddressFetchError,
    AmapAddressNotFoundError,
    AmapConfigurationError,
    AmapServiceTimeoutError,
    AmapServiceUnavailableError,
)
from app.amap.models import AmapResolvedLocation
from app.core.config import settings


class AmapClient:
    """调用高德 Web 服务 API 的异步客户端。"""

    _DIRECT_MUNICIPALITIES = {"北京市", "上海市", "天津市", "重庆市"}
    _CONFIGURATION_INFO_CODES = {
        "10001",  # Key 不正确或已过期
        "10005",  # IP 白名单配置错误
        "10006",  # 域名白名单配置错误
        "10007",  # 数字签名校验失败
        "10008",  # MD5 安全码校验失败
        "10009",  # Key 与绑定平台不匹配
        "10012",  # Key 未授权当前服务
        "10041",  # 接口权限已过期
    }
    _UNAVAILABLE_INFO_CODES = {
        "10003",  # 日调用量超限
        "10004",  # 单位时间访问过于频繁
        "10010",  # IP 访问超限
        "10011",  # 服务 QPS 超限
        "10029",  # Key QPS 超限
        "10044",  # 账号日调用量超限
        "10045",  # 账号海外服务日调用量超限
        "40000",  # 服务余额耗尽
        "40002",  # 服务已到期
        "40003",  # 海外服务余额耗尽
    }

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._http_client = http_client

    async def get_poi_detail(self, poi_id: str) -> AmapResolvedLocation:
        """根据 POI ID 发送高德 POI 详情查询请求。"""

        payload = await self._get_json(
            settings.AMAP_POI_DETAIL_URL,
            params={
                "key": settings.AMAP_API_KEY,
                "id": poi_id,
                "output": "json",
            },
        )

        try:
            pois = payload["pois"]
            if not isinstance(pois, list):
                raise TypeError("pois must be a list")
            if not pois:
                raise AmapAddressNotFoundError("未获取到有效地址")

            poi = pois[0]
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
        except AmapAddressNotFoundError:
            raise
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise AmapAddressFetchError("高德地址获取失败") from exc

    async def reverse_geocode(self, location: str) -> AmapResolvedLocation:
        """根据经纬度发送高德逆地理编码请求。"""

        payload = await self._get_json(
            settings.AMAP_REVERSE_GEOCODE_URL,
            params={
                "key": settings.AMAP_API_KEY,
                "location": location,
                "extensions": "base",
                "output": "json",
            },
        )

        try:
            regeocode = payload["regeocode"]
            if not isinstance(regeocode, dict) or not regeocode:
                raise AmapAddressNotFoundError("未获取到有效地址")

            return AmapResolvedLocation(
                formatted_address=regeocode["formatted_address"],
                adcode=regeocode["addressComponent"]["adcode"],
                location=location,
                poi_id=None,
            )
        except AmapAddressNotFoundError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise AmapAddressFetchError("高德地址获取失败") from exc

    async def _get_json(
        self,
        url: str,
        *,
        params: dict[str, str],
    ) -> dict[str, object]:
        try:
            response = await self._http_client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as exc:
            raise AmapServiceTimeoutError("高德服务超时") from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403}:
                raise AmapConfigurationError("地址服务配置错误") from exc
            if exc.response.status_code in {429, 503}:
                raise AmapServiceUnavailableError("地址服务暂时不可用") from exc
            raise AmapAddressFetchError("高德地址获取失败") from exc
        except (httpx.RequestError, ValueError) as exc:
            raise AmapAddressFetchError("高德地址获取失败") from exc

        if not isinstance(payload, dict):
            raise AmapAddressFetchError("高德地址获取失败")

        if payload.get("status") != "1":
            infocode = str(payload.get("infocode", ""))
            if infocode in self._CONFIGURATION_INFO_CODES:
                raise AmapConfigurationError("地址服务配置错误")
            if (
                infocode in self._UNAVAILABLE_INFO_CODES
                or infocode.startswith("3")
            ):
                raise AmapServiceUnavailableError("地址服务暂时不可用")
            raise AmapAddressFetchError("高德地址获取失败")

        return payload
