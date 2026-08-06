from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AddressCoordinate(BaseModel):
    """地图选点坐标。"""

    model_config = ConfigDict(extra="forbid")

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="经度",
    )
    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="纬度",
    )


class AddressCreateRequest(BaseModel):
    """添加收货地址的请求模型。"""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "receiver_name": "张三",
                "phone_number": "13800138000",
                "shipping_address": "广东省深圳市南山区科技园",
                "detail_address": "某某大厦 10 楼 1001 室",
                "coordinate": {
                    "longitude": 113.934528,
                    "latitude": 22.540503,
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
    shipping_address: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="地图选点得到的收货地址",
    )
    detail_address: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="门牌号、楼层、房间号等详细地址",
    )
    coordinate: AddressCoordinate = Field(
        ...,
        description="地图选点的经纬度坐标",
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
                "data": {
                    "address_id": "550e8400-e29b-41d4-a716-446655440000"
                },
            }
        }
    )

    code: Literal[200] = Field(default=200, description="业务状态码")
    message: str = Field(default="地址添加成功", description="响应消息")
    data: AddressCreateResponseData
