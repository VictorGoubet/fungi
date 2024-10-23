import asyncio
from functools import partial
from ipaddress import ip_address
from logging import Logger
from socket import AF_INET, SOCK_DGRAM, socket
from typing import Any, Dict, List, Optional, Tuple

import httpx
import stun
from pydantic import IPvAnyAddress

from fungi.client.udp import UDPServer
from fungi.models.node import Node
from fungi.utils.constants import SERVER_URL, STUN_SERVER
from fungi.utils.logger import get_logger


class Client:
    """Client to join the P2P network"""

    def __init__(self, server_url: str = SERVER_URL, logger: Logger = get_logger(name="P2P_Client")) -> None:
        """
        Initialize the Client.

        :param str server_url: The URL of the server.
        :param Logger logger: The logger instance to use.
        """
        self._node: Node = Node()
        self._logger: Logger = logger
        self._server_url: str = server_url
        self._server_status: bool = False
        self._response_received: asyncio.Event = asyncio.Event()
        self._send_socket: socket = socket(AF_INET, SOCK_DGRAM)
        self._transport: Optional[asyncio.DatagramTransport] = None

    async def _discover_public_ip_and_port(self) -> bool:
        """
        Discover the public IP and port using a STUN server.

        :return bool: True if discovery was successful, False otherwise.
        """
        try:
            _, external_ip, external_port = await self._async_get_ip_info()
            self._node.public_ip = ip_address(external_ip)
            self._node.public_port = external_port
            self._logger.info(
                f" 💡 Discovered public IP: {self._node.public_ip}, public port: {self._node.public_port}"
            )
            return True
        except Exception as e:
            self._logger.error(f" ❌ Failed to discover public IP and port: {e}")
            self._node.public_ip = None
            self._node.public_port = None
            return False

    async def _async_get_ip_info(self) -> Tuple[str, str, int]:
        """
        Async version of the get ip info stun method.

        :return Tuple[str, str, int]: A tuple containing NAT type, external IP, and external port.
        """
        loop = asyncio.get_running_loop()
        get_ip_info_partial = partial(
            stun.get_ip_info,
            stun_host=STUN_SERVER[0],
            stun_port=STUN_SERVER[1],
            source_port=self._node.local_port,
        )
        return await loop.run_in_executor(None, get_ip_info_partial)

    async def connect_to(self, other_node: Node, timeout: int = 30) -> Dict[str, Any]:
        """
        Initiate a connection to another node, retrying until a timeout.

        :param Node other_node: The node to connect to.
        :param int timeout: The timeout in seconds.
        :return Dict[str, Any]: A dictionary containing the connection status and message.
        """
        if not self._validate_connection_prerequisites(other_node):
            return {"status": "fail", "message": "Connection prerequisites not met"}

        punch_result = await self._send_punch_messages(other_node)
        if punch_result["status"] != "success":
            return punch_result

        return await self._wait_for_connection_response(timeout)

    def _validate_connection_prerequisites(self, other_node: Node) -> bool:
        """
        Validate the prerequisites for establishing a connection.

        :param Node other_node: The other node to connect to.
        :return bool: True if the prerequisites are met, False otherwise.
        """
        if not self._node.public_ip or not self._node.public_port:
            self._logger.warning(" ⚠️ This node has not discovered its public IP and port yet.")
            return False
        if not other_node.public_ip or not other_node.public_port:
            self._logger.warning(f" ⚠️ The other node {other_node} has not discovered its public IP and port yet.")
            return False
        if not self._transport:
            self._logger.warning(" ⚠️ The current node is not listening for response yet.")
            return False
        return True

    async def _send_punch_messages(self, other_node: Node) -> Dict[str, Any]:
        """
        Send punch messages to initiate hole punching.

        :param Node other_node: The node to send punch messages to.
        :return Dict[str, Any]: A dictionary containing the punch status and message.
        """
        if other_node.public_ip is not None and other_node.public_port is not None:
            result1 = await self.send_message("punch", other_node.public_ip, other_node.public_port)
            if result1["status"] != "success":
                return result1
            result2 = await self.send_message("punch", other_node.public_ip, other_node.public_port)
            if result2["status"] != "success":
                return result2
            return {"status": "success", "message": "Punch messages sent successfully"}
        else:
            error_message = "Cannot send punch messages: other node's public IP or port is None"
            self._logger.error(f" ❌ {error_message}")
            return {"status": "fail", "message": error_message}

    async def _wait_for_connection_response(self, timeout: int) -> Dict[str, Any]:
        """
        Wait for a connection response within the specified timeout.

        :param int timeout: The timeout in seconds.
        :return Dict[str, Any]: A dictionary containing the connection status and message.
        """
        try:
            await asyncio.wait_for(self._response_received.wait(), timeout=timeout)
            return {"status": "success", "message": "Connection established"}
        except asyncio.TimeoutError:
            return {"status": "fail", "message": "Connection timed out"}

    async def send_message(self, message: str, target_ip: IPvAnyAddress, target_port: int) -> Dict[str, Any]:
        """
        Send a message to a specified target IP and port.

        :param str message: The message to send.
        :param IPvAnyAddress target_ip: The target IP address.
        :param int target_port: The target port number.
        :return Dict[str, Any]: A dictionary containing the send status and message.
        """
        try:
            self._send_socket.sendto(message.encode(), (str(target_ip), target_port))
            self._logger.info(f" ✅ Sent message to {target_ip}:{target_port}")
            return {"status": "success", "message": f"Message sent to {target_ip}:{target_port}"}
        except Exception as e:
            error_message = f"Failed to send message: {e}"
            self._logger.error(f" ❌ {error_message}")
            return {"status": "error", "message": error_message}

    def handle_incoming_message(self, message: str, sender: Tuple[str, int]) -> None:
        """
        Handle an incoming message and set the response received flag.

        :param str message: The received message.
        :param Tuple[str, int] sender: The sender's address (IP, port).
        """
        self._logger.info(f" 💡 Received message from {sender}: {message}")
        self._response_received.set()

    async def _start_server(self) -> Dict[str, Any]:
        """
        Start the server to accept incoming connections.

        :return Dict[str, Any]: A dictionary containing the start status and message.
        """
        if self._server_status:
            self._logger.info(" 💡 Server is already running")
            return {"status": "success", "message": "Server is already running"}
        try:
            loop = asyncio.get_running_loop()
            self._send_socket.bind((str(self._node.local_ip), 0))  # Use a different port for sending
            self._transport, _ = await loop.create_datagram_endpoint(
                lambda: UDPServer(self.handle_incoming_message, self._send_socket),
                local_addr=(str(self._node.local_ip), self._node.local_port),
            )
            self._logger.info(f" ✅ Serving on {self._node.local_ip}:{self._node.local_port}")
            self._server_status = True
            return {"status": "success", "message": f"Server started on {self._node.local_ip}:{self._node.local_port}"}
        except OSError as e:
            error_message = f"Failed to start server: {e}"
            self._logger.error(f" ❌ {error_message}")
            return {"status": "fail", "message": error_message}

    async def _stop_server(self) -> Dict[str, Any]:
        """
        Stop the server from accepting incoming connections.

        :return Dict[str, Any]: A dictionary containing the stop status and message.
        """
        if not self._server_status:
            self._logger.info(" 💡 Server is not running")
            return {"status": "success", "message": "Server is not running"}
        if self._transport:
            self._transport.close()
            self._transport = None
        if self._send_socket:
            self._send_socket.close()
        self._server_status = False
        self._logger.info(" ✅ Server has been stopped")
        return {"status": "success", "message": "Server has been stopped"}

    async def join_network(self) -> Dict[str, Any]:
        """
        Join the network by contacting the central server.

        :return Dict[str, Any]: A dictionary containing the join status and message.
        """
        if self._server_status:
            self._logger.info(" 💡 Already part of the network")
            return {"status": "success", "message": "Already part of the network"}

        if not await self._discover_public_ip_and_port():
            return {"status": "fail", "message": "Failed to discover public IP and port"}

        node_data = self._node.model_dump(mode="json")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self._server_url}/nodes", json=node_data)
                response.raise_for_status()

            start_result = await self._start_server()
            if start_result["status"] != "success":
                return start_result

            asyncio.create_task(self.keep_alive())
            self._logger.info(" ✅ Joined network successfully")
            return {"status": "success", "message": "Joined network successfully"}
        except httpx.HTTPStatusError as e:
            err = f"Failed to join network: {e.response.text}"
            self._logger.error(f" ❌ {err}")
            return {"status": "fail", "message": err}
        except httpx.RequestError as e:
            err = f"An error occurred while requesting: {e}"
            self._logger.error(f" ❌ {err}")
            return {"status": "fail", "message": err}

    async def leave_network(self) -> Dict[str, Any]:
        """
        Leave the network by contacting the central server and shutting down the server.

        :return Dict[str, Any]: A dictionary containing the leave status and message.
        """
        if not self._server_status:
            self._logger.info(" 💡 Not currently part of the network")
            return {"status": "success", "message": "Not currently part of the network"}

        params = self._node.model_dump(mode="json")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{self._server_url}/nodes", params=params)
                response.raise_for_status()

            stop_result = await self._stop_server()
            if stop_result["status"] != "success":
                return stop_result

            self._logger.info(" ✅ Left the network.")
            return {"status": "success", "message": "Left the network successfully"}
        except httpx.HTTPStatusError as e:
            err = f"Failed to leave network: {e.response.text}"
            self._logger.error(f" ❌ {err}")
            return {"status": "fail", "message": err}
        except httpx.RequestError as e:
            err = f"An error occurred while requesting: {e}"
            self._logger.error(f" ❌ {err}")
            return {"status": "fail", "message": err}
        finally:
            self._server_status = False
            self._logger.info(" 💡 Network leave process completed.")

    async def get_nodes(self) -> List[Node]:
        """
        Get the list of the current nodes on the network.

        :return List[Node]: A list of current nodes on the network.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self._server_url}/nodes")
                response.raise_for_status()
            nodes = [Node(**x) for x in response.json() if Node(**x) != self._node]
            self._logger.info(" ✅ Got nodes successfully")
            return nodes
        except httpx.HTTPStatusError as e:
            self._logger.error(f" ❌ Failed to get nodes: {e.response.text}")
        except httpx.RequestError as e:
            self._logger.error(f" ❌ An error occurred while requesting: {e}")
        return []

    async def keep_alive(self) -> None:
        """
        Periodically rediscover public IP and port to keep the NAT mapping alive.
        """
        while self._server_status:
            await self._discover_public_ip_and_port()
            await asyncio.sleep(30)  # Send keep-alive every 30 seconds

    def __str__(self) -> str:
        """
        String representation of the Client.

        :return str: A string representation of the Client.
        """
        return f"Client(node={self._node})"
