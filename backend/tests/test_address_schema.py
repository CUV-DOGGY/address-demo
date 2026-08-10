import unittest
from uuid import uuid4

from pydantic import ValidationError

from app.schema.address_schema import (
    AddressCreateRequest,
    AddressUpdateRequest,
    PoiAddressLocation,
    PositionAddressLocation,
)


def make_request_payload() -> dict[str, object]:
    return {
        "receiver_name": "张三",
        "phone_number": "13800138000",
        "display_address": "白石路附近",
        "detail_address": "9 栋 B 座 1001 室",
        "location": {
            "source": "poi",
            "coordinate": "113.946123,22.530456",
            "adcode": "440305",
            "amap_poi_id": "B0XXXXXX",
        },
    }


class AddressCreateRequestTests(unittest.TestCase):
    def test_accepts_valid_poi_location(self) -> None:
        request = AddressCreateRequest.model_validate(make_request_payload())

        self.assertEqual(request.display_address, "白石路附近")
        self.assertIsInstance(request.location, PoiAddressLocation)
        self.assertEqual(request.location.amap_poi_id, "B0XXXXXX")
        self.assertEqual(request.location.coordinate, "113.946123,22.530456")
        self.assertFalse(request.is_default)

    def test_accepts_legacy_shipping_address_as_display_alias(self) -> None:
        payload = make_request_payload()
        payload["shipping_address"] = payload.pop("display_address")

        request = AddressCreateRequest.model_validate(payload)

        self.assertEqual(request.display_address, "白石路附近")

    def test_rejects_client_supplied_canonical_address(self) -> None:
        payload = make_request_payload()
        payload["canonical_address"] = "客户端伪造的规范地址"

        with self.assertRaises(ValidationError):
            AddressCreateRequest.model_validate(payload)

    def test_update_accepts_location_and_default_fields(self) -> None:
        address_id = uuid4()

        request = AddressUpdateRequest.model_validate(
            {
                "address_id": str(address_id),
                "location": make_request_payload()["location"],
                "is_default": True,
            }
        )

        self.assertEqual(request.address_id, address_id)
        self.assertIsInstance(request.location, PoiAddressLocation)
        self.assertTrue(request.is_default)

    def test_update_rejects_server_owned_address_fields(self) -> None:
        forbidden_fields: tuple[tuple[str, object], ...] = (
            ("canonical_address", "客户端伪造地址"),
            ("adcode", "440305"),
        )

        for field, value in forbidden_fields:
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    AddressUpdateRequest.model_validate(
                        {
                            "address_id": str(uuid4()),
                            "receiver_name": "李四",
                            field: value,
                        }
                    )

    def test_update_requires_at_least_one_update_field(self) -> None:
        with self.assertRaises(ValidationError):
            AddressUpdateRequest.model_validate({"address_id": str(uuid4())})

    def test_poi_location_requires_poi_id(self) -> None:
        payload = make_request_payload()
        location = payload["location"]
        self.assertIsInstance(location, dict)
        location.pop("amap_poi_id")

        with self.assertRaises(ValidationError):
            AddressCreateRequest.model_validate(payload)

    def test_poi_location_rejects_blank_poi_id(self) -> None:
        payload = make_request_payload()
        location = payload["location"]
        self.assertIsInstance(location, dict)
        location["amap_poi_id"] = "   "

        with self.assertRaises(ValidationError):
            AddressCreateRequest.model_validate(payload)

    def test_accepts_position_location_without_poi_fields(self) -> None:
        payload = make_request_payload()
        payload["location"] = {
            "source": "position",
            "coordinate": "113.946123,22.530456",
            "adcode": "440305",
        }

        request = AddressCreateRequest.model_validate(payload)

        self.assertIsInstance(request.location, PositionAddressLocation)
        self.assertIsNone(request.location.amap_poi_id)

    def test_accepts_position_location_with_null_poi_fields(self) -> None:
        payload = make_request_payload()
        payload["location"] = {
            "source": "position",
            "coordinate": "113.946123,22.530456",
            "adcode": "440305",
            "amap_poi_id": None,
        }

        request = AddressCreateRequest.model_validate(payload)

        self.assertIsInstance(request.location, PositionAddressLocation)

    def test_rejects_invalid_adcode(self) -> None:
        invalid_adcodes: tuple[object, ...] = (
            "44030",
            "4403050",
            "44A305",
            "１２３４５６",
            440305,
        )

        for adcode in invalid_adcodes:
            with self.subTest(adcode=adcode):
                payload = make_request_payload()
                location = payload["location"]
                self.assertIsInstance(location, dict)
                location["adcode"] = adcode

                with self.assertRaises(ValidationError):
                    AddressCreateRequest.model_validate(payload)

    def test_preserves_original_string_and_default_validation(self) -> None:
        payload = make_request_payload()
        payload["receiver_name"] = "  张三  "

        request = AddressCreateRequest.model_validate(payload)

        self.assertEqual(request.receiver_name, "张三")
        self.assertFalse(request.is_default)

    def test_preserves_original_phone_validation(self) -> None:
        payload = make_request_payload()
        payload["phone_number"] = "12345678901"

        with self.assertRaises(ValidationError):
            AddressCreateRequest.model_validate(payload)

    def test_accepts_valid_mainland_china_phone_number(self) -> None:
        payload = make_request_payload()
        payload["phone_number"] = "13800138000"

        request = AddressCreateRequest.model_validate(payload)

        self.assertEqual(request.phone_number, "13800138000")

    def test_rejects_invalid_mainland_china_phone_numbers(self) -> None:
        invalid_phone_numbers = (
            "1380013800",
            "138001380000",
            "12800138000",
            "1380013800A",
        )

        for phone_number in invalid_phone_numbers:
            with self.subTest(phone_number=phone_number):
                payload = make_request_payload()
                payload["phone_number"] = phone_number

                with self.assertRaises(ValidationError):
                    AddressCreateRequest.model_validate(payload)

    def test_requires_coordinate(self) -> None:
        payload = make_request_payload()
        location = payload["location"]
        self.assertIsInstance(location, dict)
        location.pop("coordinate")

        with self.assertRaises(ValidationError):
            AddressCreateRequest.model_validate(payload)

    def test_accepts_and_normalizes_valid_coordinates(self) -> None:
        boundary_coordinates = (
            ("113.934528, 22.540503", "113.934528,22.540503"),
            ("-180,-90", "-180,-90"),
            ("180.000000,90.000000", "180.000000,90.000000"),
        )

        for coordinate, expected in boundary_coordinates:
            with self.subTest(coordinate=coordinate):
                payload = make_request_payload()
                location = payload["location"]
                self.assertIsInstance(location, dict)
                location["coordinate"] = coordinate

                request = AddressCreateRequest.model_validate(payload)

                self.assertEqual(request.location.coordinate, expected)

    def test_rejects_out_of_range_coordinates(self) -> None:
        invalid_coordinates = (
            "-180.000001,0",
            "180.000001,0",
            "0,-90.000001",
            "0,90.000001",
        )

        for coordinate in invalid_coordinates:
            with self.subTest(coordinate=coordinate):
                payload = make_request_payload()
                location = payload["location"]
                self.assertIsInstance(location, dict)
                location["coordinate"] = coordinate

                with self.assertRaises(ValidationError):
                    AddressCreateRequest.model_validate(payload)

    def test_rejects_invalid_coordinate_formats(self) -> None:
        invalid_coordinates: tuple[object, ...] = (
            "113.934528",
            "113.934528,22.540503,1",
            "longitude,latitude",
            "113.934528,22.5405031",
            "113.934528 22.540503",
            "113.934528,",
            {"longitude": 113.934528, "latitude": 22.540503},
        )

        for coordinate in invalid_coordinates:
            with self.subTest(coordinate=coordinate):
                payload = make_request_payload()
                location = payload["location"]
                self.assertIsInstance(location, dict)
                location["coordinate"] = coordinate

                with self.assertRaises(ValidationError):
                    AddressCreateRequest.model_validate(payload)

    def test_preserves_unknown_field_rejection(self) -> None:
        payload = make_request_payload()
        payload["unexpected"] = "value"

        with self.assertRaises(ValidationError):
            AddressCreateRequest.model_validate(payload)


if __name__ == "__main__":
    unittest.main()
