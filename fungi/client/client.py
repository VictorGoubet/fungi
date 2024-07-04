import asyncio
import logging
from asyncio import StreamReader, StreamWriter
from functools import partial
from typing import Optional

import httpx
import stun
from pydantic import BaseModel, Field

from fungi.models.node import Node
from fungi.tools.constants import SERVER_URL


class Client(BaseModel):
    """Client to join the P2P network"""

    node: Node = Field(default=Node(), description="The current node")
    public_ip: Optional[str] = Field(default=None, description="Public IP address")
    public_port: Optional[int] = Field(default=None, description="Public port")
    logger: Optional[logging.Logger] = Field(default=None, description="Logger instance")
    connection_alive: bool = Field(default=False, description="Flag indicating if the connection is alive")
    reader: Optional[StreamReader] = Field(default=None, description="StreamReader for the connection")
    writer: Optional[StreamWriter] = Field(default=None, description="StreamWriter for the connection")
    server_url: str = Field(default=SERVER_URL, description="URL of the network server")

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

        :return tuple: The public discovered IP and port
        """
        loop = asyncio.get_event_loop()
        stun_server = ("stun.l.google.com", 19302)
        get_ip_info_partial = partial(stun.get_ip_info, stun_host=stun_server[0], stun_port=stun_server[1])
        return await loop.run_in_executor(None, get_ip_info_partial)

    async def _discover_public_ip_and_port(self) -> None:
        """
        Discover the public IP and port using a STUN server.
        """
        try:
            _, external_ip, external_port = await self._async_get_ip_info()
            self.node.public_ip = external_ip
            self.node.public_port = external_port
            self._log(f"Discovered public IP: {self.public_ip}, public port: {self.public_port}")
        except Exception as e:
            self._log(f"Failed to discover public IP and port: {e}", level="error")
            self.node.public_ip = None
            self.node.public_port = None

    async def initiate_connection(self, other_node: "Node") -> bool:
        """
        Initiate a connection to another node.

        :param Node other_node: The node to connect to.
        :return bool: True if the connection initiation is successful, False otherwise.
        """
        if not self.node.public_ip or not self.node.public_port:
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

    async def join_network(self) -> None:
        """
        Join the network by contacting the central server.
        """
        await self._discover_public_ip_and_port()
        node_data = self.node.model_dump()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.server_url}/nodes", json=node_data)
                response.raise_for_status()
                self._log(f"Joined network with response: {response.json()}")
                asyncio.create_task(self._start_server())
            except httpx.HTTPStatusError as e:
                self._log(f"Failed to join network: {e.response.text}", level="error")
            except httpx.RequestError as e:
                self._log(f"An error occurred while requesting: {e}", level="error")

    async def leave_network(self) -> None:
        """
        Leave the network by contacting the central server.
        """
        node_data = self.node.model_dump()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(f"{self.server_url}/nodes", json=node_data)
                response.raise_for_status()
                self._log("Left the network.")
                self.connection_alive = False
            except httpx.HTTPStatusError as e:
                self._log(f"Failed to leave network: {e.response.text}", level="error")
            except httpx.RequestError as e:
                self._log(f"An error occurred while requesting: {e}", level="error")

    def __str__(self) -> str:
        """
        String representation of the Node.
        """
        return f"Node(public_ip={self.node.public_ip}, public_port={self.node.public_port})"
