import asyncio
import logging
from asyncio import StreamReader, StreamWriter
from typing import Optional

import stun
from pydantic import BaseModel, Field

from fungi.network import Network


class Node(BaseModel):
    """Representation of a single Node in the P2P network"""

    network: Optional[Network] = Field(default=None, description="The Network to which the Node belongs")
    public_ip: Optional[str] = Field(default=None, description="Public IP address")
    public_port: Optional[int] = Field(default=None, description="Public port")
    logger: Optional[logging.Logger] = Field(default=None, description="Logger instance")
    connection_alive: bool = Field(default=False, description="Flag indicating if the connection is alive")
    reader: Optional[asyncio.StreamReader] = Field(default=None, description="StreamReader for the connection")
    writer: Optional[asyncio.StreamWriter] = Field(default=None, description="StreamWriter for the connection")

    class Config:
        arbitrary_types_allowed = True

    def _log(self, message: str, level: str = "info") -> None:
        """
        Log a message using the provided logger if available, otherwise print.

        :param str message: The message to log.
        :param str level: The logging level ("info", "warning", "error").
        """
        if self.logger:
            log_method = getattr(self.logger, level, self.logger.info)
            log_method(message)
        else:
            print(message)

    async def _async_get_ip_info(self) -> tuple:
        """Async version of the get ip info stun method

        :return tuple: The public discovered ip and port
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, stun.get_ip_info)

    async def _discover_public_ip_and_port(self) -> None:
        """
        Discover the public IP and port using a STUN server.
        """
        try:
            _, external_ip, external_port = await self._async_get_ip_info()
            self.public_ip = external_ip
            self.public_port = external_port
            self._log(f"Discovered public IP: {self.public_ip}, public port: {self.public_port}")
        except Exception as e:
            self._log(f"Failed to discover public IP and port: {e}", level="error")
            self.public_ip, self.public_port = None, None

    async def initiate_connection(self, other_node: "Node") -> bool:
        """
        Initiate a connection to another node.

        :param Node other_node: The node to connect to.
        :return bool: True if the connection initiation is successful, False otherwise.
        """
        if not self.public_ip or not self.public_port:
            self._log("This node has not discovered its public IP and port yet.", level="warning")
            return False

        if not other_node.public_ip or not other_node.public_port:
            self._log(f"The other node {other_node} has not discovered its public IP and port yet.", level="warning")
            return False

        self._log(f"Connecting to {other_node.public_ip}:{other_node.public_port}")

        try:
            reader, writer = await asyncio.open_connection(other_node.public_ip, other_node.public_port)
            await self._handle_connection(reader, writer)
            return True
        except Exception as e:
            self._log(f"Failed to connect to {other_node.public_ip}:{other_node.public_port}: {e}", level="error")
            return False

    async def _handle_connection(self, reader: StreamReader, writer: StreamWriter) -> None:
        """
        Handle an established connection.

        :param StreamReader reader: StreamReader for the connection.
        :param StreamWriter writer: StreamWriter for the connection.
        """
        self.reader, self.writer = reader, writer
        self._log(f"Connection established with {writer.get_extra_info('peername')}")
        self.connection_alive = True
        asyncio.create_task(self._maintain_connection())
        asyncio.create_task(self._handle_incoming_messages())

    async def _maintain_connection(self) -> None:
        """
        Periodically send messages to maintain the connection.
        """
        if self.writer:
            while self.connection_alive:
                try:
                    self.writer.write(b"KEEP-ALIVE")
                    await self.writer.drain()
                except Exception as e:
                    self._log(f"Failed to send keep-alive message: {e}", level="error")
                    self.connection_alive = False
                await asyncio.sleep(10)

    async def _handle_incoming_messages(self) -> None:
        """
        Handle incoming messages from the connection.
        """
        if self.reader:
            while self.connection_alive:
                try:
                    data = await self.reader.read(100)
                    if not data:
                        self._log("Connection closed by peer")
                        self.connection_alive = False
                        break
                    message = data.decode()
                    self._log(f"Received message: {message}")
                except Exception as e:
                    self._log(f"Failed to read message: {e}", level="error")
                    self.connection_alive = False

    async def _start_server(self) -> None:
        """
        Start the server to accept incoming connections.
        """
        server = await asyncio.start_server(self._handle_client, "0.0.0.0", self.public_port)
        self._log(f"Serving on {self.public_ip}:{self.public_port}")
        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader: StreamReader, writer: StreamWriter) -> None:
        """
        Handle an incoming client connection.

        :param StreamReader reader: StreamReader for the connection.
        :param StreamWriter writer: StreamWriter for the connection.
        """
        self._log("Accepted a new client connection")
        await self._handle_connection(reader, writer)

    async def join_network(self, network: "Network") -> None:
        """
        Join a given network.

        :param Network network: The network to join.
        """
        self.network = network
        await network.add_node(self)
        await self._discover_public_ip_and_port()
        asyncio.create_task(self._start_server())
        self._log(f"Joined network with {len(network.nodes)} nodes.")

    async def leave_network(self) -> None:
        """
        Leave the current network.
        """
        if self.network:
            await self.network.remove_node(self)
            self._log("Left the network.")
            self.connection_alive = False
        else:
            self._log("This node is not part of any network.", level="warning")

    def __str__(self) -> str:
        """
        String representation of the Node.
        """
        return f"Node(public_ip={self.public_ip}, public_port={self.public_port})"


# Example usage
if __name__ == "__main__":

    async def main():
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("Node")

        network = Network()

        node1 = Node(logger=logger)
        await node1.join_network(network)

        node2 = Node(logger=logger)
        await node2.join_network(network)

        await node2.initiate_connection(node1)

    asyncio.run(main())
