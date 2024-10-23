from typing import Optional

from pydantic import BaseModel, Field, IPvAnyAddress


class Node(BaseModel):
    """
    Represents a node in the P2P network.
    """

    local_ip: IPvAnyAddress = Field(default="127.0.0.1", description="Local IP address of the node")
    local_port: int = Field(default=0, description="Local port of the node")
    public_ip: Optional[IPvAnyAddress] = Field(default=None, description="Public IP address of the node")
    public_port: Optional[int] = Field(default=None, description="Public port of the node")

    class Config:
        """
        Pydantic configuration for the Node model.
        """

        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "local_ip": "192.168.1.100",
                "local_port": 8000,
                "public_ip": "203.0.113.1",
                "public_port": 9000,
            }
        }

    def __str__(self) -> str:
        """
        String representation of the Node.

        :return: A string representation of the Node.
        """
        return f"Node(public_ip={self.public_ip}, public_port={self.public_port})"

    def __eq__(self, other: object) -> bool:
        """
        Check if two Node objects are equal.

        :param other: The other object to compare with.
        :return: True if the objects are equal, False otherwise.
        """
        if not isinstance(other, Node):
            return False
        same_public_ip = str(self.public_ip) == str(other.public_ip)
        same_public_port = self.public_port == other.public_port
        same_local_ip = str(self.local_ip) == str(other.local_ip)
        same_local_port = self.local_port == other.local_port
        return same_public_ip and same_public_port and same_local_ip and same_local_port

    def __hash__(self) -> int:
        """
        Generate a hash value for the Node.

        :return: The hash value of the Node.
        """
        return hash((self.public_ip, self.public_port, self.local_ip, self.local_port))
