from pydantic import BaseModel, Field
from .nat_type import NatType


class DiscoveryResult(BaseModel):
    """
    Represents the result of a NAT discovery operation.

    :param NatType nat_type: The detected NAT type.
    :param str public_ip: The discovered public IP address.
    :param int public_port: The discovered public port.
    """

    nat_type: NatType = Field(
        description="The detected NAT type.",
        examples=[NatType.FULL_CONE],
    )
    public_ip: str = Field(
        description="The discovered public IP address.",
        examples=["192.168.1.100"],
    )
    public_port: int = Field(
        description="The discovered public port.",
        examples=[8000],
    )
