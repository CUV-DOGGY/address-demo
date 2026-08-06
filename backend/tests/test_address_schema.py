import unittest

from pydantic import ValidationError

from app.schema.address_schema import (
    AddressCreateRequest,
    PoiAddressLocation,
    PositionAddressLocation,
)


def make_request_payload() -> dict[str, object]:
    return {
        "receiver_name": "张三",
        "phone_number": "13800138000",
        "shipping_address": "广东省深圳市南山区白石路",
        "detail_address": "9 栋 B 座 1001 室",
        "location": {
            "source": "poi",
            "coordinate": {
                "longitude": 113.946123,
                "latitude": 22.530456,
            },
            "adcode": "440305",
            "amap_poi_id": "B0XXXXXX",
            "poi_name": "深圳湾科技生态园",
        },
    }


class AddressCreateRequestTests(unittest.TestCase):
    def test_accepts_valid_poi_location(self) -> None:
        request = AddressCreateRequest.model_validate(make_request_payload())

        self.assertIsInstance(request.location, PoiAddressLocation)
        self.assertEqual(request.location.amap_poi_id, "B0XXXXXX")
        self.assertEqual(request.location.poi_name, "深圳湾科技生态园")
        self.assertFalse(request.is_default)

    def test_poi_location_requires_poi_id_and_name(self) -> None:
        for missing_field in ("amap_poi_id", "poi_name"):
            with self.subTest(missing_field=missing_field):
                payload = make_request_payload()
                location = payload["location"]
                self.assertIsInstance(location, dict)
                location.pop(missing_field)

                with self.assertRaises(ValidationError):
                    AddressCreateRequest.model_validate(payload)

    def test_poi_location_rejects_blank_poi_id_and_name(self) -> None:
        for blank_field in ("amap_poi_id", "poi_name"):
            with self.subTest(blank_field=blank_field):
                payload = make_request_payload()
                location = payload["location"]
                self.assertIsInstance(location, dict)
                location[blank_field] = "   "

                with self.assertRaises(ValidationError):
                    AddressCreateRequest.model_validate(payload)

    def test_accepts_position_location_without_poi_fields(self) -> None:
        payload = make_request_payload()
        payload["location"] = {
            "source": "position",
            "coordinate": {
                "longitude": 113.946123,
                "latitude": 22.530456,
            },
            "adcode": "440305",
        }

        request = AddressCreateRequest.model_validate(payload)

        self.assertIsInstance(request.location, PositionAddressLocation)
        self.assertIsNone(request.location.amap_poi_id)
        self.assertIsNone(request.location.poi_name)

    def test_accepts_position_location_with_null_poi_fields(self) -> None:
        payload = make_request_payload()
        payload["location"] = {
            "source": "position",
            "coordinate": {
                "longitude": 113.946123,
                "latitude": 22.530456,
            },
            "adcode": "440305",
            "amap_poi_id": None,
            "poi_name": None,
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

    def test_requires_longitude_and_latitude(self) -> None:
        for missing_field in ("longitude", "latitude"):
            with self.subTest(missing_field=missing_field):
                payload = make_request_payload()
                location = payload["location"]
                self.assertIsInstance(location, dict)
                coordinate = location["coordinate"]
                self.assertIsInstance(coordinate, dict)
                coordinate.pop(missing_field)

                with self.assertRaises(ValidationError):
                    AddressCreateRequest.model_validate(payload)

    def test_accepts_coordinate_boundary_values(self) -> None:
        boundary_coordinates = (
            {"longitude": -180, "latitude": -90},
            {"longitude": 180, "latitude": 90},
        )

        for coordinate in boundary_coordinates:
            with self.subTest(coordinate=coordinate):
                payload = make_request_payload()
                location = payload["location"]
                self.assertIsInstance(location, dict)
                location["coordinate"] = coordinate

                request = AddressCreateRequest.model_validate(payload)

                self.assertEqual(
                    request.location.coordinate.longitude,
                    coordinate["longitude"],
                )
                self.assertEqual(
                    request.location.coordinate.latitude,
                    coordinate["latitude"],
                )

    def test_rejects_out_of_range_coordinates(self) -> None:
        invalid_coordinates = (
            {"longitude": -180.000001, "latitude": 0},
            {"longitude": 180.000001, "latitude": 0},
            {"longitude": 0, "latitude": -90.000001},
            {"longitude": 0, "latitude": 90.000001},
        )

        for coordinate in invalid_coordinates:
            with self.subTest(coordinate=coordinate):
                payload = make_request_payload()
                location = payload["location"]
                self.assertIsInstance(location, dict)
                location["coordinate"] = coordinate

                with self.assertRaises(ValidationError):
                    AddressCreateRequest.model_validate(payload)

    def test_preserves_original_coordinate_validation(self) -> None:
        payload = make_request_payload()
        location = payload["location"]
        self.assertIsInstance(location, dict)
        coordinate = location["coordinate"]
        self.assertIsInstance(coordinate, dict)
        coordinate["longitude"] = 181

        with self.assertRaises(ValidationError):
            AddressCreateRequest.model_validate(payload)

    def test_preserves_unknown_field_rejection(self) -> None:
        payload = make_request_payload()
        payload["unexpected"] = "value"

        with self.assertRaises(ValidationError):
            AddressCreateRequest.model_validate(payload)


if __name__ == "__main__":
    unittest.main()
