import asyncio
import logging
from asyncio import StreamReader, StreamWriter
from functools import partial
from typing import Callable, List, Optional, Union

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
    logger: Optional[Union[Callable, logging.Logger]] = Field(default=None, description="Logger instance")
    connection_alive: bool = Field(default=False, description="Flag indicating if the connection is alive")
    reader: Optional[StreamReader] = Field(default=None, description="StreamReader for the connection")
    writer: Optional[StreamWriter] = Field(default=None, description="StreamWriter for the connection")
    server_url: str = Field(default=SERVER_URL, description="URL of the network server")
    server_status: bool = Field(default=False, description="The status of the network server, True is On False is Off")
    server_task: Optional[asyncio.Task] = Field(default=None, description="Server task")

    class Config:
        arbitrary_types_allowed = True

    def _log(self, message: str, level: str = "info") -> None:
        """
        Log a message using the provided logger if available, otherwise print.

        :param str message: The message to log.
        :param str level: The logging level ("info", "warning", "error").
        """
        if self.logger:
            if isinstance(self.logger, logging.Logger):
                log_method = getattr(self.logger, level, self.logger.info)
            else:
                log_method = partial(self.logger, level=level)
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
            self._log(f"Discovered public IP: {self.node.public_ip}, public port: {self.node.public_port}")
        except Exception as e:
            self._log(f"Failed to discover public IP and port: {e}", level="error")
            self.node.public_ip = None
            self.node.public_port = None

    async def initiate_connection(self, other_node: "Node") -> dict:
        """
        Initiate a connection to another node.

        :param Node other_node: The node to connect to.
        :return dict: The status of the initialization.
        """
        status = {"status": "success", "message": None}
        if not self.node.public_ip or not self.node.public_port:
            err = "This node has not discovered its public IP and port yet."
            status["status"], status["message"] = "fail", err
            self._log(err, level="warning")
            return status

        if not other_node.public_ip or not other_node.public_port:
            err = f"The other node {other_node} has not discovered its public IP and port yet."
            status["status"], status["message"] = "fail", err
            self._log(err, level="warning")
            return status

        self._log(f"Connecting to {other_node.public_ip}:{other_node.public_port}")

        try:
            reader, writer = await asyncio.open_connection(other_node.public_ip, other_node.public_port)
            await self._handle_connection(reader, writer)
            return status
        except Exception as e:
            err = f"Failed to connect to {other_node.public_ip}:{other_node.public_port}: {e}"
            status["status"], status["message"] = "fail", err
            self._log(err, level="error")
            return status

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
        if self.server_status:
            self._log("Server is already running")
            return
        try:
            server = await asyncio.start_server(self._handle_client, "0.0.0.0", self.node.public_port)
            self._log(f"Serving on {self.node.public_ip}:{self.node.public_port}")
            self.server_status = True
            self.server_task = asyncio.create_task(server.serve_forever())
            async with server:
                await self.server_task
        except OSError as e:
            self._log(f"Failed to start server: {e}", level="error")

    async def _handle_client(self, reader: StreamReader, writer: StreamWriter) -> None:
        """
        Handle an incoming client connection.

        :param StreamReader reader: StreamReader for the connection.
        :param StreamWriter writer: StreamWriter for the connection.
        """
        self._log("Accepted a new client connection")
        await self._handle_connection(reader, writer)

    async def join_network(self) -> dict:
        """
        Join the network by contacting the central server.

        :return dict: The status of the request
        """
        status = {"status": "success", "message": None}
        if self.server_status:
            self._log("Already part of the network")
            return status

        await self._discover_public_ip_and_port()
        node_data = self.node.model_dump()
        async with httpx.AsyncClient() as client:
            try:
                self._log("Joining the network..")
                response = await client.post(f"{self.server_url}/nodes", json=node_data)
                response.raise_for_status()
                asyncio.create_task(self._start_server())
                self._log("Joined network successfully")
            except httpx.HTTPStatusError as e:
                err = f"Failed to join network: {e.response.text}"
                status["status"], status["message"] = "fail", err
                self._log(err, level="error")
            except httpx.RequestError as e:
                err = f"An error occurred while requesting: {e}"
                status["status"], status["message"] = "fail", err
                self._log(err, level="error")
        return status

    async def leave_network(self) -> dict:
        """
        Leave the network by contacting the central server and shutting down the server.

        :return dict: The status of the request
        """
        status = {"status": "success", "message": None}
        if not self.server_status:
            self._log("Not currently part of the network")
            return status

        params = self.node.model_dump()
        async with httpx.AsyncClient() as client:
            try:
                self._log("Leaving the network..")
                response = await client.delete(f"{self.server_url}/nodes", params=params)
                response.raise_for_status()
                self._log("Left the network.")
                self.connection_alive = False
                if self.server_task:
                    self.server_task.cancel()
                    try:
                        await self.server_task
                    except asyncio.CancelledError:
                        self._log("Server task cancelled.")
            except httpx.HTTPStatusError as e:
                err = f"Failed to leave network: {e.response.text}"
                status["status"], status["message"] = "fail", err
                self._log(err, level="error")
            except httpx.RequestError as e:
                err = f"An error occurred while requesting: {e}"
                status["status"], status["message"] = "fail", err
                self._log(err, level="error")
            finally:
                self.server_status = False
                self._log("Network leave process completed.")
        return status

    async def get_nodes(self) -> List[Node]:
        """Get the list of the current nodes on the network

        :return List[Node]: The list of nodes on the network.
        """
        nodes = []
        async with httpx.AsyncClient() as client:
            try:
                self._log("Getting nodes on network...")
                response = await client.get(f"{SERVER_URL}/nodes")
                response.raise_for_status()
                nodes = list(filter(lambda n: self.node != n, [Node(**x) for x in response.json()]))
                self._log("Got nodes successfully")
            except httpx.HTTPStatusError as e:
                self._log(f"Failed to get nodes: {e.response.text}", level="error")
            except httpx.RequestError as e:
                self._log(f"An error occurred while requesting: {e}", level="error")
        return nodes

    def __str__(self) -> str:
        """
        String representation of the Node.
        """
        return f"Node(public_ip={self.node.public_ip}, public_port={self.node.public_port})"
