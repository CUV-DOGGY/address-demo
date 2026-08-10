from math import asin, cos, radians, sin, sqrt

from app.amap.client import AmapClient
from app.amap.models import AmapResolvedLocation
from app.schema.address_schema import AddressValidData


class AddressAcodeError(RuntimeError):
    """地址的行政编码错误"""


class AddressLocationError(RuntimeError):
    """地址的经纬坐标错误"""


class AddressValidation:
    _EARTH_RADIUS_METERS = 6_371_000
    _MAX_SELECTED_POI_DISTANCE_METERS = 200
    _MAX_POSITION_POI_DISTANCE_METERS = 500

    def __init__(self, amap_client: AmapClient) -> None:
        self._amap_client = amap_client

    async def address_validation(self, addressdata) -> AmapResolvedLocation:
        """Verify the submitted location against current Amap data."""

        if not isinstance(addressdata, AddressValidData):
            addressdata = AddressValidData(location=addressdata)
        location = addressdata.location
        if location.source == "position":
            resolved_location = await self._amap_client.reverse_geocode(
                location.coordinate
            )
            if resolved_location.adcode != location.adcode:
                raise AddressAcodeError("地址的行政编码错误")

            if location.amap_poi_id is None:
                return resolved_location

            poi = await self._amap_client.get_poi_detail(location.amap_poi_id)

            if (
                self._distance_in_meters(location.coordinate, poi.location)
                > self._MAX_POSITION_POI_DISTANCE_METERS
            ):
                raise AddressLocationError("地址的经纬坐标错误")
            return resolved_location

        poi = await self._amap_client.get_poi_detail(location.amap_poi_id)
        if poi.adcode != location.adcode:
            raise AddressAcodeError("地址的行政编码错误")

        if (
            self._distance_in_meters(location.coordinate, poi.location)
            > self._MAX_SELECTED_POI_DISTANCE_METERS
        ):
            raise AddressLocationError("地址的经纬坐标错误")
        return poi

    @classmethod
    def _distance_in_meters(cls, first: str, second: str) -> float:
        first_longitude, first_latitude = cls._parse_coordinate(first)
        second_longitude, second_latitude = cls._parse_coordinate(second)

        latitude_delta = radians(second_latitude - first_latitude)
        longitude_delta = radians(second_longitude - first_longitude)
        first_latitude_radians = radians(first_latitude)
        second_latitude_radians = radians(second_latitude)

        haversine = (
            sin(latitude_delta / 2) ** 2
            + cos(first_latitude_radians)
            * cos(second_latitude_radians)
            * sin(longitude_delta / 2) ** 2
        )
        return 2 * cls._EARTH_RADIUS_METERS * asin(sqrt(haversine))

    @staticmethod
    def _parse_coordinate(coordinate: str) -> tuple[float, float]:
        longitude, latitude = coordinate.split(",")
        return float(longitude), float(latitude)
