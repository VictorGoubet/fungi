import logging
from typing import Optional

from pydantic import BaseModel, Field

from fungi.tools.async_stun import async_get_ip_info


class Node(BaseModel):
    """Representation of a single Node in the P2P network"""

    public_ip: Optional[str] = Field(default=None, description="Public IP address")
    public_port: Optional[int] = Field(default=None, description="Public port")
    logger: Optional[logging.Logger] = Field(default=None, description="Logger instance")

    class Config:
        arbitrary_types_allowed = True

    def log(self, message: str, level: str = "info") -> None:
        """
        Log a message using the provided logger if available, otherwise print.

        :param message: The message to log.
        :param level: The logging level ("info", "warning", "error").
        """
        if self.logger:
            log_method = getattr(self.logger, level, self.logger.info)
            log_method(message)
        else:
            print(message)

    async def discover_public_ip_and_port(self) -> None:
        """
        Discover the public IP and port using a STUN server.
        """
        try:
            _, external_ip, external_port = await async_get_ip_info()
            self.public_ip = external_ip
            self.public_port = external_port
            self.log(f"Discovered public IP: {self.public_ip}, public port: {self.public_port}")
        except Exception as e:
            self.log(f"Failed to discover public IP and port: {e}", level="error")
            self.public_ip, self.public_port = None, None

    async def connect_to(self, other_node: "Node") -> bool:
        """
        Connect to another node.

        :param other_node: The node to connect to.
        :return: True if the connection is successful, False otherwise.
        """
        if not self.public_ip or not self.public_port:
            self.log("This node has not discovered its public IP and port yet.", level="warning")
            return False

        if not other_node.public_ip or not other_node.public_port:
            self.log(f"The other node {other_node} has not discovered its public IP and port yet.", level="warning")
            return False

        # Simulate connection logic here
        self.log(f"Connecting {self.public_ip}:{self.public_port} to {other_node.public_ip}:{other_node.public_port}")
        return True

    def __str__(self) -> str:
        """
        String representation of the Node.
        """
        return f"Node(public_ip={self.public_ip}, public_port={self.public_port})"


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        node1 = Node()
        await node1.discover_public_ip_and_port()

        node2 = Node()
        await node2.discover_public_ip_and_port()

        await node1.connect_to(node2)

    asyncio.run(main())
