from pydantic import BaseModel, Field
from typing import Literal


class ClientResponse(BaseModel):
    """
    Represents a standard response for client operations.

    :param Literal['success', 'fail'] status: The status of the operation.
    :param str message: A descriptive message about the operation result.
    :param any result: Optional result payload (can be any type, e.g., a Pydantic model or dict).
    """

    status: Literal["success", "fail"] = Field(
        description="The status of the operation.",
        examples=["success", "fail"],
    )
    message: str = Field(
        description="A descriptive message about the operation result.",
        examples=["Operation successful", "Operation failed"],
    )
    result: object | None = Field(
        default=None,
        description="Optional result payload (can be any type, e.g., a Pydantic model or dict).",
        examples=[{"public_ip": "203.0.113.1", "public_port": 54321, "nat_type": "Full Cone"}],
    )
