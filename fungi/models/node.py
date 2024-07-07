from typing import Optional

from pydantic import BaseModel, Field


class Node(BaseModel):
    """Representation of a single Node in the P2P network"""

    public_ip: Optional[str] = Field(
        default=None,
        description="Public IP address",
        examples=["125.77.1.1", "25.111.10.27"],
    )
    public_port: Optional[int] = Field(
        default=None,
        description="Public port",
        examples=[8080, 9090],
    )

    local_ip: str = Field(
        default="0.0.0.0",
        description="Local IP address",
        examples=["192.168.1.1", "0.0.0.0"],
        exclude=True,
    )
    local_port: int = Field(
        default=5001,
        description="Local port",
        examples=[5001, 8000],
        exclude=True,
    )

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.public_ip == other.public_ip and self.public_port == other.public_port
        return False
