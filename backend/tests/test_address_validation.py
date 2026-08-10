import unittest
from unittest.mock import AsyncMock

from app.amap.models import AmapResolvedLocation
from app.schema.address_schema import AddressValidData
from app.service.address_validation import (
    AddressAcodeError,
    AddressLocationError,
    AddressValidation,
)


def make_address_valid_data(
    *,
    source: str = "poi",
    coordinate: str = "113.934528,22.540503",
    adcode: str = "440305",
    amap_poi_id: str | None = None,
) -> AddressValidData:
    location: dict[str, object] = {
        "source": source,
        "coordinate": coordinate,
        "adcode": adcode,
    }
    if source == "poi":
        location["amap_poi_id"] = amap_poi_id or "B0XXXXXX"
    elif amap_poi_id is not None:
        location["amap_poi_id"] = amap_poi_id

    return AddressValidData.model_validate(
        {
            "location": location,
        }
    )


def make_poi(
    *,
    coordinate: str = "113.934528,22.540503",
    adcode: str = "440305",
) -> AmapResolvedLocation:
    return AmapResolvedLocation(
        formatted_address="广东省深圳市南山区科技园",
        adcode=adcode,
        location=coordinate,
        poi_id="B0XXXXXX",
    )


def make_reverse_geocode(*, adcode: str = "440305") -> AmapResolvedLocation:
    return AmapResolvedLocation(
        formatted_address="Guangdong Shenzhen Nanshan",
        adcode=adcode,
        location="113.934528,22.540503",
    )


class AddressValidationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.amap_client = AsyncMock()
        self.validation = AddressValidation(self.amap_client)

    async def test_poi_returns_location_when_adcode_and_coordinate_match(self) -> None:
        address = make_address_valid_data()
        self.amap_client.get_poi_detail.return_value = make_poi()

        resolved_location = await self.validation.address_validation(address)

        self.assertEqual(resolved_location, self.amap_client.get_poi_detail.return_value)
        self.amap_client.get_poi_detail.assert_awaited_once_with("B0XXXXXX")

    async def test_poi_raises_when_adcode_does_not_match(self) -> None:
        address = make_address_valid_data()
        self.amap_client.get_poi_detail.return_value = make_poi(adcode="440304")

        with self.assertRaises(AddressAcodeError):
            await self.validation.address_validation(address)

    async def test_poi_returns_location_when_distance_is_within_200_meters(self) -> None:
        address = make_address_valid_data(coordinate="113.934528,22.540503")
        self.amap_client.get_poi_detail.return_value = make_poi(
            coordinate="113.934528,22.542000"
        )

        resolved_location = await self.validation.address_validation(address)

        self.assertEqual(resolved_location, self.amap_client.get_poi_detail.return_value)

    async def test_poi_raises_when_distance_exceeds_200_meters(self) -> None:
        address = make_address_valid_data(coordinate="113.934528,22.540503")
        self.amap_client.get_poi_detail.return_value = make_poi(
            coordinate="113.934528,22.543000"
        )

        with self.assertRaises(AddressLocationError):
            await self.validation.address_validation(address)

    async def test_position_returns_location_when_reverse_geocode_adcode_matches(
        self,
    ) -> None:
        address = make_address_valid_data(source="position")
        self.amap_client.reverse_geocode.return_value = make_reverse_geocode()

        resolved_location = await self.validation.address_validation(address)

        self.assertEqual(
            resolved_location, self.amap_client.reverse_geocode.return_value
        )
        self.amap_client.reverse_geocode.assert_awaited_once_with(
            "113.934528,22.540503"
        )
        self.amap_client.get_poi_detail.assert_not_awaited()

    async def test_position_raises_when_reverse_geocode_adcode_differs(
        self,
    ) -> None:
        address = make_address_valid_data(
            source="position", amap_poi_id="B0NEARBY"
        )
        self.amap_client.reverse_geocode.return_value = make_reverse_geocode(
            adcode="440304"
        )

        with self.assertRaises(AddressAcodeError):
            await self.validation.address_validation(address)
        self.amap_client.get_poi_detail.assert_not_awaited()

    async def test_position_with_poi_returns_location_when_within_500_meters(
        self,
    ) -> None:
        address = make_address_valid_data(
            source="position", amap_poi_id="B0NEARBY"
        )
        self.amap_client.reverse_geocode.return_value = make_reverse_geocode()
        self.amap_client.get_poi_detail.return_value = make_poi(
            coordinate="113.934528,22.544500"
        )

        resolved_location = await self.validation.address_validation(address)

        self.assertEqual(
            resolved_location, self.amap_client.reverse_geocode.return_value
        )
        self.amap_client.get_poi_detail.assert_awaited_once_with("B0NEARBY")

    async def test_position_with_poi_raises_when_poi_exceeds_500_meters(
        self,
    ) -> None:
        address = make_address_valid_data(
            source="position", amap_poi_id="B0NEARBY"
        )
        self.amap_client.reverse_geocode.return_value = make_reverse_geocode()
        self.amap_client.get_poi_detail.return_value = make_poi(
            coordinate="113.934528,22.545500"
        )

        with self.assertRaises(AddressLocationError):
            await self.validation.address_validation(address)


if __name__ == "__main__":
    unittest.main()
