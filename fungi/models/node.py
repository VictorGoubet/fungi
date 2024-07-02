from typing import Optional

from pydantic import BaseModel, Field


class Node(BaseModel):
    """Representation of a single Node in the P2P network"""

    public_ip: Optional[str] = Field(
        default=None,
        description="Public IP address",
        examples=["192.168.1.1", "192.168.1.2"],
    )
    public_port: Optional[int] = Field(
        default=None,
        description="Public port",
        examples=[8080, 9090],
    )
