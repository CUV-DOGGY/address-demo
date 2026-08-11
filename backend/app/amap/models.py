from pydantic import BaseModel, ConfigDict


class AmapResolvedLocation(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
    )
    formatted_address: str
    adcode: str
    location: str
    poi_id: str | None = None
