import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

COORDINATE_NUMBER_PATTERN = re.compile(r"^-?(?:0|[1-9]\d*)(?:\.\d{1,6})?$")


class AddressLocationBase(BaseModel):
    """地址位置的公共字段。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    coordinate: str = Field(
        ...,
        description="高德坐标，格式为 longitude,latitude，最多六位小数",
        examples=["113.934528,22.540503"],
    )
    adcode: str = Field(
        ...,
        pattern=r"^[0-9]{6}$",
        description="中国大陆 6 位行政区划编码",
    )

    @field_validator("coordinate")
    @classmethod
    def validate_coordinate(cls, value: str) -> str:
        parts = value.split(",")
        if len(parts) != 2:
            raise ValueError("坐标必须使用 longitude,latitude 格式")

        longitude_text, latitude_text = (part.strip() for part in parts)
        if not COORDINATE_NUMBER_PATTERN.fullmatch(longitude_text):
            raise ValueError("经度必须是数字且小数点后最多 6 位")
        if not COORDINATE_NUMBER_PATTERN.fullmatch(latitude_text):
            raise ValueError("纬度必须是数字且小数点后最多 6 位")

        longitude = Decimal(longitude_text)
        latitude = Decimal(latitude_text)
        if not Decimal("-180") <= longitude <= Decimal("180"):
            raise ValueError("经度必须在 -180 到 180 之间")
        if not Decimal("-90") <= latitude <= Decimal("90"):
            raise ValueError("纬度必须在 -90 到 90 之间")

        return f"{longitude_text},{latitude_text}"


class PoiAddressLocation(AddressLocationBase):
    """通过高德 POI 选择的地址位置。"""

    source: Literal["poi"]
    amap_poi_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="高德 POI ID",
    )


class PositionAddressLocation(AddressLocationBase):
    """通过地图拖拽选择的地址位置。"""

    source: Literal["position"]
    amap_poi_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="附近的高德 POI ID",
    )


AddressLocation = Annotated[
    PoiAddressLocation | PositionAddressLocation,
    Field(discriminator="source"),
]


class Address(BaseModel):
    """数据库中的完整地址信息。"""

    address_id: UUID
    user_id: UUID
    receiver_name: str
    phone_number: str
    display_address: str = Field(
        ...,
        validation_alias=AliasChoices("display_address", "shipping_address"),
        description="用户确认的展示别名，不作为规范地址依据",
    )
    detail_address: str
    location: AddressLocation
    is_default: bool
    status: Literal["active", "deleted"]
    version: int = Field(..., ge=1)
    canonical_address: str = Field(
        ...,
        validation_alias=AliasChoices("canonical_address", "formatted_address"),
        description="由高德解析得到的规范地址",
    )
    adcode: str
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AddressCreateRequest(BaseModel):
    """添加收货地址的请求模型。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "receiver_name": "张三",
                "phone_number": "13800138000",
                "display_address": "科技园",
                "detail_address": "某某大厦 10 楼 1001 室",
                "location": {
                    "source": "poi",
                    "coordinate": "113.934528, 22.540503",
                    "adcode": "440305",
                    "amap_poi_id": "B0XXXXXX",
                },
                "is_default": False,
            }
        },
    )

    receiver_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="联系人姓名",
    )
    phone_number: str = Field(
        ...,
        pattern=r"^1[3-9]\d{9}$",
        description="中国大陆 11 位手机号码",
    )
    display_address: str = Field(
        ...,
        min_length=1,
        max_length=255,
        validation_alias=AliasChoices("display_address", "shipping_address"),
        description="用户确认的展示别名；规范地址以后端高德解析结果为准",
    )
    detail_address: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="门牌号、楼层、房间号等详细地址",
    )
    location: AddressLocation = Field(
        ...,
        description="经过高德解析并由用户确认的位置",
    )
    is_default: bool = Field(
        default=False,
        description="是否为默认收货地址",
    )


class AddressCreateResponseData(BaseModel):
    """添加地址成功后返回的数据。"""

    address_id: UUID = Field(..., description="新地址的 UUID")


class AddressCreateResponse(BaseModel):
    """添加地址成功时的统一响应模型。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 200,
                "message": "地址添加成功",
                "data": {"address_id": "550e8400-e29b-41d4-a716-446655440000"},
            }
        }
    )

    code: Literal[200] = Field(default=200, description="业务状态码")
    message: str = Field(default="地址添加成功", description="响应消息")
    data: AddressCreateResponseData


class AddressDeleteRequest(BaseModel):
    """删除收货地址的请求模型。"""

    model_config = ConfigDict(extra="forbid")

    address_id: UUID = Field(..., description="待删除地址的 UUID")


class AddressDeleteResponse(BaseModel):
    """删除收货地址成功时的统一响应模型。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 200,
                "message": "地址删除成功",
                "data": None,
            }
        }
    )

    code: Literal[200] = Field(default=200, description="业务状态码")
    message: str = Field(default="地址删除成功", description="响应消息")
    data: None = Field(default=None, description="删除接口无返回数据")


class AddressUpdateRequest(BaseModel):
    """部分更新收货地址的请求模型。"""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    address_id: UUID = Field(..., description="待更新地址的 UUID")
    receiver_name: str | None = Field(default=None, min_length=1, max_length=50)
    phone_number: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")
    display_address: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="用户确认的展示别名；不会改变高德规范地址",
    )
    detail_address: str | None = Field(default=None, min_length=1, max_length=255)
    is_default: bool | None = Field(default=None, description="是否设为默认地址")
    location: AddressLocation | None = None

    @model_validator(mode="after")
    def require_update_fields(self) -> "AddressUpdateRequest":
        if all(
            value is None
            for value in (
                self.receiver_name,
                self.phone_number,
                self.display_address,
                self.detail_address,
                self.is_default,
                self.location,
            )
        ):
            raise ValueError("至少需要提供一个可更新字段")
        return self


class AddressUpdateResponseData(BaseModel):
    """更新成功后的地址版本信息。"""

    address_id: UUID = Field(..., description="待更新地址的 UUID")
    receiver_name: str | None = Field(default=None, min_length=1, max_length=50)
    phone_number: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")
    display_address: str | None = Field(default=None, min_length=1, max_length=255)
    detail_address: str | None = Field(default=None, min_length=1, max_length=255)
    is_default: bool | None = Field(default=None, description="是否设为默认地址")
    location: AddressLocation | None = None


class AddressUpdateResponse(BaseModel):
    """部分更新收货地址成功时的统一响应模型。"""

    code: Literal[200] = Field(default=200, description="业务状态码")
    message: str = Field(default="地址更新成功", description="响应消息")
    data: AddressUpdateResponseData


class AddressValidData(BaseModel):

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "location": {
                    "source": "poi",
                    "coordinate": "113.934528, 22.540503",
                    "adcode": "440305",
                    "amap_poi_id": "B0XXXXXX",
                },
            }
        },
    )
    location: AddressLocation = Field(
        ...,
        description="需要通过高德服务校验的位置",
    )
