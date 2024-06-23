from typing import Optional

from pydantic import BaseModel, Field


class Node(BaseModel):
    """Representation of a single Node in the P2P network"""

    public_ip: Optional[str] = Field(default=None, description="Public IP address")
    public_port: Optional[int] = Field(default=None, description="Public port")
