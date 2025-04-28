from sqlmodel import SQLModel, Field
from enum import Enum


class NatType(str, Enum):
    FULL_CONE = "Full Cone"
    RESTRICTED_CONE = "Restricted Cone"
    PORT_RESTRICTED_CONE = "Port Restricted Cone"
    SYMMETRIC = "Symmetric"


class Node(SQLModel, table=True):
    """
    Represents a node in the P2P network (as a SQLModel table).
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
                    "nat_type": "Full Cone"
                }
            ]
        }
    }

    @classmethod
    def get_example(cls) -> dict[str, any]:
        """
        Dynamically build an example using the 'examples' metadata of each field.
        """
        example = {}
        for field_name, model_field in cls.model_fields.items():
            value = None
            for meta in model_field.metadata:
                if isinstance(meta, dict) and "json_schema_extra" in meta:
                    js_extra = meta["json_schema_extra"]
                    if js_extra and "examples" in js_extra:
                        value = js_extra["examples"][0]
                        if isinstance(value, Enum):
                            value = value.value
                        break
            example[field_name] = value
        return example

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
