from sqlmodel import SQLModel, Field
from .nat_type import NatType


class Node(SQLModel, table=True):
    """
    Represents a peer in the P2P network (SQLModel table).
    """

    id: int | None = Field(
        default=None,
        primary_key=True,
        schema_extra={"examples": [1]},
    )
    local_ip: str = Field(
        default="127.0.0.1",
        description="Local IP address of the node",
        schema_extra={"examples": ["192.168.1.100"]},
    )
    local_port: int = Field(
        default=0,
        description="Local port of the node",
        schema_extra={"examples": [8000]},
    )
    public_ip: str | None = Field(
        default=None,
        description="Public IP address of the node",
        schema_extra={"examples": ["203.0.113.1"]},
    )
    public_port: int | None = Field(
        default=None,
        description="Public port of the node",
        schema_extra={"examples": [9000]},
    )
    nat_type: NatType | None = Field(
        default=None,
        description="NAT type of the node",
        schema_extra={"examples": [NatType.FULL_CONE]},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "local_ip": "192.168.1.100",
                    "local_port": 8000,
                    "public_ip": "203.0.113.1",
                    "public_port": 9000,
                    "nat_type": "Full Cone",
                }
            ]
        }
    }

    @classmethod
    def get_example(cls) -> dict[str, any]:
        """
        Returns a sample node from the schema config.
        :return dict[str, any]: Example node as a dictionary.
        """
        return cls.model_config["json_schema_extra"]["examples"][0]

    def __str__(self) -> str:
        """
        Returns a string with the node's public IP and port.
        :return str: String representation of the node.
        """
        return f"Node(public_ip={self.public_ip}, public_port={self.public_port})"

    def __eq__(self, other: object) -> bool:
        """
        Checks if two nodes have the same public IP and port.
        :param object other: The object to compare with.
        :return bool: True if the nodes are equal, False otherwise.
        """
        if not isinstance(other, Node):
            return False
        return str(self.public_ip) == str(other.public_ip) and self.public_port == other.public_port

    def __hash__(self) -> int:
        """
        Hashes the node using its public and local addresses.
        :return int: Hash value for the node.
        """
        return hash((self.public_ip, self.public_port, self.local_ip, self.local_port))
