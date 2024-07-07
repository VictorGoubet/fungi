import asyncio
import logging
from functools import partial
from typing import Callable, List, Optional, Union

import httpx
import stun
from pydantic import BaseModel, Field

from fungi.client.udp import UDPServer
from fungi.models.node import Node
from fungi.tools.constants import SERVER_URL


class Client(BaseModel):
    """Client to join the P2P network"""

    node: Node = Field(default=Node(), description="The current node")
    public_ip: Optional[str] = Field(default=None, description="Public IP address")
    public_port: Optional[int] = Field(default=None, description="Public port")
    logger: Optional[Union[Callable, logging.Logger]] = Field(default=None, description="Logger instance")
    connection_alive: bool = Field(default=False, description="Flag indicating if the connection is alive")
    transport: Optional[asyncio.DatagramTransport] = Field(default=None, description="UDP transport")
    server_url: str = Field(default=SERVER_URL, description="URL of the network server")
    server_status: bool = Field(default=False, description="The status of the network server, True is On False is Off")
    response_received: asyncio.Event = Field(default_factory=asyncio.Event, description="Response Event")

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
        get_ip_info_partial = partial(
            stun.get_ip_info,
            stun_host=stun_server[0],
            stun_port=stun_server[1],
            source_port=self.node.local_port,
        )
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

    async def connect_to(self, other_node: "Node", timeout: int = 30) -> dict:
        """
        Initiate a connection to another node, retrying until a timeout.

        :param Node other_node: The node to connect to.
        :param int timeout: The timeout period in seconds for retrying the connection.
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

        if not self.transport:
            err = "The current node is not listening for response yet."
            status["status"], status["message"] = "fail", err
            self._log(err, level="warning")
            return status

        end_time = asyncio.get_event_loop().time() + timeout

        while asyncio.get_event_loop().time() < end_time:
            try:
                await self.send_message(f"Hello from {self.node}", other_node.public_ip, other_node.public_port)
                await asyncio.sleep(1)
                if self.response_received.is_set():
                    return status
            except Exception as e:
                self._log(f"Connection attempt failed: {e}", level="error")
                await asyncio.sleep(1)

        status["status"], status["message"] = "fail", f"Timed out after {timeout} seconds."
        self._log(status["message"], level="error")
        return status

    async def send_message(self, message: str, target_ip: str, target_port: int) -> None:
        """
        Send a message to a specified target IP and port.

        :param str message: The message to send.
        :param str target_ip: The target IP address.
        :param int target_port: The target port number.
        """
        if not self.transport:
            self._log("Transport is not available. Please start the server first.", level="error")
            return

        self.transport.sendto(message.encode(), (target_ip, target_port))
        self._log(f"Sent message to {target_ip}:{target_port}")

    def handle_incoming_message(self, message: str, sender):
        """
        Handle an incoming message and set the response received flag.

        :param str message: The incoming message.
        :param sender: The sender's address.
        """
        self._log(f"Received message from {sender}: {message}")
        self.response_received.set()

    async def _start_server(self) -> None:
        """
        Start the server to accept incoming connections.
        """
        if self.server_status:
            self._log("Server is already running")
            return
        try:
            loop = asyncio.get_running_loop()
            self.transport, _ = await loop.create_datagram_endpoint(
                lambda: UDPServer(self.handle_incoming_message),
                local_addr=(self.node.local_ip, self.node.local_port),
            )
            self._log(f"Serving on {self.node.public_ip}:{self.node.public_port}")
            self.server_status = True
        except OSError as e:
            self._log(f"Failed to start server: {e}", level="error")

    async def _stop_server(self) -> None:
        """
        Stop the server from accepting incoming connections.
        """
        if not self.server_status:
            self._log("Server is not running")
            return
        if self.transport:
            self.transport.close()
            self.transport = None
            self.server_status = False
            self._log("Server has been stopped")

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
                await self._stop_server()
                self.connection_alive = False
                self._log("Left the network.")
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
