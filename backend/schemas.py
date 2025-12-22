from pydantic import BaseModel, ConfigDict, Field, field_validator


class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_address: str
    destination_address: str
    avoid: list[str] = Field(default_factory=list)

    @field_validator("start_address", "destination_address")
    @classmethod
    def validate_addresses(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Start and destination addresses cannot be empty.")
        return v

    @field_validator("avoid")
    @classmethod
    def validate_avoid(cls, streets: list[str]) -> list[str]:
        cleaned: list[str] = []
        for s in streets:
            s2 = s.strip()
            if (
                s2
            ):  # if user accidentally enters an empty string as a dispreferred street name, we just ignore it.
                cleaned.append(s2)
        return cleaned
