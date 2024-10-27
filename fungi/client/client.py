import asyncio
from functools import partial
from ipaddress import ip_address
from logging import INFO, Logger
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

    def __init__(
        self,
        server_url: str = SERVER_URL,
        logger: Logger = get_logger(name="P2P_Client", level=INFO),
    ) -> None:
        """
        Initialize the Client.

        :param str server_url: The URL of the server.
        :param Logger logger: The logger instance to use.
        """
        self._node: Node = Node()
        self._logger: Logger = logger
        self._server_url: str = server_url
        self._server_status: bool = False
        self._udp_server: UDPServer = UDPServer(self._handle_message)

    ############################
    #  Core network operations #
    ############################

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

        insert_result = await self._insert_node()
        if insert_result["status"] != "success":
            return insert_result

        await self._start_server()
        asyncio.create_task(self.keep_alive())
        self._logger.info(" ✅ Joined network successfully")
        return {"status": "success", "message": "Joined network successfully"}

    async def leave_network(self) -> Dict[str, Any]:
        """
        Leave the network by contacting the central server and shutting down the server.

        :return Dict[str, Any]: A dictionary containing the leave status and message.
        """
        if not self._server_status:
            self._logger.info(" 💡 Not currently part of the network")
            return {"status": "success", "message": "Not currently part of the network"}

        delete_result = await self._delete_node()
        if delete_result["status"] != "success":
            return delete_result

        await self._stop_server()
        self._server_status = False
        self._logger.info(" ✅ Left the network.")
        return {"status": "success", "message": "Left the network successfully"}

    async def keep_alive(self) -> None:
        """
        Periodically rediscover public IP and port to keep the NAT mapping alive.
        """
        while self._server_status:
            new_ip, new_port = await self._discover_public_ip_and_port()
            if new_ip is not None and new_port is not None:
                ip_changed = new_ip != self._node.public_ip
                port_changed = new_port != self._node.public_port

                if ip_changed or port_changed:
                    self._node.public_ip = ip_address(new_ip)
                    self._node.public_port = new_port
                    update_result = await self._update_node()
                    if update_result["status"] != "success":
                        self._logger.error(f" ❌ Failed to update node info: {update_result['message']}")

                    if port_changed:
                        self._logger.info(
                            f" 💡 Public port changed from {self._node.local_port} to {new_port}. Restarting server."
                        )
                        await self._stop_server()
                        self._node.local_port = new_port
                        await self._start_server()

            await asyncio.sleep(30)  # Send keep-alive every 30 seconds

    #####################
    #  Node management  #
    #####################

    async def _insert_node(self) -> Dict[str, Any]:
        """
        Insert the node information into the central server.

        :return Dict[str, Any]: A dictionary containing the insert status and message.
        """
        node_data = self._node.model_dump(mode="json")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self._server_url}/nodes", json=node_data)
                response.raise_for_status()
            return {"status": "success", "message": "Node inserted successfully"}
        except httpx.HTTPStatusError as e:
            err = f"Failed to insert node: {e.response.text}"
            self._logger.error(f" ❌ {err}")
            return {"status": "fail", "message": err}
        except httpx.RequestError as e:
            err = f"An error occurred while inserting node: {e}"
            self._logger.error(f" ❌ {err}")
            return {"status": "fail", "message": err}

    async def _delete_node(self) -> Dict[str, Any]:
        """
        Delete the node information from the central server.

        :return Dict[str, Any]: A dictionary containing the delete status and message.
        """
        params = self._node.model_dump(mode="json")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{self._server_url}/nodes", params=params)
                response.raise_for_status()
            return {"status": "success", "message": "Node deleted successfully"}
        except httpx.HTTPStatusError as e:
            err = f"Failed to delete node: {e.response.text}"
            self._logger.error(f" ❌ {err}")
            return {"status": "fail", "message": err}
        except httpx.RequestError as e:
            err = f"An error occurred while deleting node: {e}"
            self._logger.error(f" ❌ {err}")
            return {"status": "fail", "message": err}

    async def _update_node(self) -> Dict[str, Any]:
        """
        Update the node information on the signaling server.

        :return Dict[str, Any]: A dictionary containing the update status and message.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(f"{self._server_url}/nodes", json=self._node.model_dump(mode="json"))
                response.raise_for_status()
            return {"status": "success", "message": "Node updated successfully"}
        except httpx.HTTPStatusError as e:
            err = f"Failed to update node: {e.response.text}"
            self._logger.error(f" ❌ {err}")
            return {"status": "fail", "message": err}
        except httpx.RequestError as e:
            err = f"An error occurred while updating node: {e}"
            self._logger.error(f" ❌ {err}")
            return {"status": "fail", "message": err}

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

    ############################
    # Connection and messaging #
    ############################

    async def connect_to(self, other_node: Node, timeout: int = 30) -> Dict[str, Any]:
        """
        Initiate a connection to another node using hole punching.

        :param Node other_node: The node to connect to.
        :param int timeout: The timeout in seconds.
        :return Dict[str, Any]: A dictionary containing the connection status and message.
        """
        if not self._validate_connection_prerequisites(other_node):
            return {"status": "fail", "message": "Connection prerequisites not met"}

        connection_established = asyncio.Event()
        self._udp_server.set_connection_callback(connection_established.set)

        # Send punch messages
        punch_task = asyncio.create_task(self._send_punch_messages(other_node))

        try:
            await asyncio.wait_for(connection_established.wait(), timeout=timeout)
            return {"status": "success", "message": "Connection established"}
        except asyncio.TimeoutError:
            return {"status": "fail", "message": "Connection attempt timed out"}
        finally:
            punch_task.cancel()
            self._udp_server.set_connection_callback(None)

    async def send_message(self, message: str, target_ip: IPvAnyAddress, target_port: int) -> Dict[str, Any]:
        """
        Send a message to a specified target IP and port.

        :param str message: The message to send.
        :param IPvAnyAddress target_ip: The target IP address.
        :param int target_port: The target port number.
        :return Dict[str, Any]: A dictionary containing the send status and message.
        """
        try:
            self._udp_server.send_message(message, str(target_ip), target_port)
            self._logger.info(f" ✅ Sent message to {target_ip}:{target_port}")
            return {"status": "success", "message": f"Message sent to {target_ip}:{target_port}"}
        except Exception as e:
            error_message = f"Failed to send message: {e}"
            self._logger.error(f" ❌ {error_message}")
            return {"status": "error", "message": error_message}

    ######################
    #  Server management #
    ######################

    async def _start_server(self) -> None:
        """
        Start the server to accept incoming connections.
        """
        if self._server_status:
            self._logger.info(" 💡 Server is already running")
            return
        try:
            await self._udp_server.start(str(self._node.local_ip), self._node.local_port)
            self._logger.info(f" ✅ Serving on {self._node.local_ip}:{self._node.local_port}")
            self._server_status = True
        except OSError as e:
            error_message = f"Failed to start server: {e}"
            self._logger.error(f" ❌ {error_message}")
            raise

    async def _stop_server(self) -> None:
        """
        Stop the server from accepting incoming connections.
        """
        if not self._server_status:
            self._logger.info(" 💡 Server is not running")
            return

        await self._udp_server.stop()
        self._server_status = False
        self._logger.info(" ✅ Server has been stopped")

    #######################
    #  Network discovery  #
    #######################

    async def _discover_public_ip_and_port(self) -> Tuple[Optional[IPvAnyAddress], Optional[int]]:
        """
        Discover the public IP and port using a STUN server.

        :return Tuple[Optional[IPvAnyAddress], Optional[int]]: A tuple containing the public IP and port.
        """
        try:
            _, external_ip, external_port = await self._async_get_ip_info()
            self._logger.debug(f" 💡 Discovered public IP and port: {external_ip}:{external_port}")
            return ip_address(external_ip), external_port
        except Exception as e:
            self._logger.error(f" ❌ Failed to discover public IP and port: {e}")
            return None, None

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

    ####################
    #  Helper methods  #
    ####################

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
        if not self._server_status:
            self._logger.warning(" ⚠️ The current node is not listening for responses yet.")
            return False
        return True

    async def _send_punch_messages(self, other_node: Node, n_tries: int = 30) -> None:
        """
        Send punch messages to initiate hole punching.

        :param Node other_node: The node to send punch messages to.
        :param int n_tries: The number of tries to send punch messages.
        """
        message = f"punch:{self._node.public_ip}:{self._node.public_port}"
        for _ in range(n_tries):
            if other_node.public_ip is not None and other_node.public_port is not None:
                await self.send_message(message, other_node.public_ip, other_node.public_port)
                await asyncio.sleep(1)  # Wait a second between punches

    def _handle_message(self, message: str, sender: Tuple[str, int]) -> None:
        """
        Handle an incoming message.

        :param str message: The received message.
        :param Tuple[str, int] sender: The sender's address (IP, port).
        """
        self._logger.info(f" 💡 Received message from {sender}: {message}")
        if message.startswith("punch"):
            # Respond to punch message
            self._udp_server.send_message("pong", sender[0], sender[1])
        elif message.startswith("pong"):
            # Connection established
            if self._udp_server.connection_callback:
                self._udp_server.connection_callback()

    def __str__(self) -> str:
        """
        String representation of the Client.

        :return str: A string representation of the Client.
        """
        return f"Client(node={self._node})"
