from pydantic import BaseModel, Field
from typing import Literal


class ClientResponse(BaseModel):
    """
    Represents a standard response for client operations.

    :param Literal['success', 'fail'] status: The status of the operation.
    :param str message: A descriptive message about the operation result.
    """

    status: Literal["success", "fail"] = Field(
        description="The status of the operation.",
        examples=["success", "fail"],
    )
    message: str = Field(
        description="A descriptive message about the operation result.",
        examples=["Operation successful", "Operation failed"],
    )
