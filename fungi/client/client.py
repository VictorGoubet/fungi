from asyncio import Event, create_task, sleep, wait_for
from logging import INFO, Logger
from fungi.client.discovery import DiscoveryService
from fungi.client.udp import UDPServer
from fungi.models.node import Node
from fungi.models.discovery import DiscoveryResult
from fungi.models.response import ClientResponse
from fungi.utils.constants import config
from fungi.utils.logger import get_logger
from httpx import AsyncClient


class P2PClient:
    """
    Main P2P client orchestrator for NAT detection, discovery, joining, connecting, and messaging.
    """

    def __init__(
        self,
        server_url: str = config.server_url,
        logger: Logger = get_logger(name="P2P_Client", level=INFO),
    ) -> None:
        """
        Initialize the P2PClient.

        :param str server_url: The URL of the signaling server.
        :param Logger logger: The logger instance to use.
        """
        self._node: Node = Node()
        self._logger: Logger = logger
        self._server_url: str = server_url
        self._server_status: bool = False
        self._udp_server: UDPServer = UDPServer(self._handle_message)
        self._discovery: DiscoveryService = DiscoveryService(
            stun_host=config.stun_server_host, stun_port=config.stun_server_port
        )

    async def detect_nat(self, local_port: int = 54320) -> ClientResponse:
        """
        Detect the NAT type and update the node.

        :param int local_port: The local port to use for detection.
        :return ClientResponse: The status and message of the operation.
        """
        try:
            result: DiscoveryResult = await self._discovery.discover(local_port)
            self._node.nat_type = result.nat_type
            return ClientResponse(status="success", message=str(result.nat_type))
        except Exception as e:
            self._logger.error(f" ❌ NAT detection failed: {e}")
            return ClientResponse(status="fail", message=str(e))

    async def discover_public_ip(self, local_port: int = 54320) -> dict[str, object]:
        """
        Discover public IP and port, update the node.

        :param int local_port: The local port to use for discovery.
        :return dict[str, object]: Public IP, port, and NAT type.
        """
        try:
            result: DiscoveryResult = await self._discovery.discover(local_port)
            self._node.nat_type = result.nat_type
            self._node.public_ip = result.public_ip
            self._node.public_port = result.public_port
            self._node.local_port = local_port
            return {
                "status": "success",
                "public_ip": result.public_ip,
                "public_port": result.public_port,
                "nat_type": result.nat_type,
            }
        except Exception as e:
            self._logger.error(f" ❌ Discovery failed: {e}")
            return {"status": "fail", "message": str(e)}

    async def join_network(self) -> ClientResponse:
        """
        Join the network by registering with the signaling server and starting UDP server.

        :return ClientResponse: The status and message of the operation.
        """
        if self._server_status:
            self._logger.info(" 💡 Already part of the network")
            return ClientResponse(
                status="success", message="Already part of the network"
            )
        if not self._node.public_ip or not self._node.public_port:
            return ClientResponse(
                status="fail", message="Public IP/port not discovered"
            )
        try:
            async with AsyncClient() as client:
                response = await client.post(
                    f"{self._server_url}/nodes", json=self._node.model_dump(mode="json")
                )
                response.raise_for_status()
            await self._udp_server.start(
                str(self._node.local_ip), self._node.local_port
            )
            self._server_status = True
            self._logger.info(" ✅ Joined network successfully")
            return ClientResponse(
                status="success",
                message="Joined network successfully",
            )
        except Exception as e:
            self._logger.error(f" ❌ Failed to join network: {e}")
            return ClientResponse(status="fail", message=str(e))

    async def leave_network(self) -> ClientResponse:
        """
        Leave the network by deregistering from the signaling server and stopping UDP server.

        :return ClientResponse: The status and message of the operation.
        """
        if not self._server_status:
            self._logger.info(" 💡 Not currently part of the network")
            return ClientResponse(
                status="success",
                message="Not currently part of the network",
            )
        try:
            async with AsyncClient() as client:
                response = await client.delete(
                    f"{self._server_url}/nodes",
                    params=self._node.model_dump(mode="json"),
                )
                response.raise_for_status()
            await self._udp_server.stop()
            self._server_status = False
            self._logger.info(" ✅ Left the network.")
            return ClientResponse(
                status="success",
                message="Left the network successfully",
            )
        except Exception as e:
            self._logger.error(f" ❌ Failed to leave network: {e}")
            return ClientResponse(status="fail", message=str(e))

    async def get_nodes(self) -> list[Node]:
        """
        Get the list of current nodes on the network.

        :return list[Node]: A list of current nodes on the network.
        """
        try:
            async with AsyncClient() as client:
                response = await client.get(f"{self._server_url}/nodes")
                response.raise_for_status()
            nodes = [
                Node.model_validate(x)
                for x in response.json()
                if Node.model_validate(x) != self._node
            ]
            self._logger.info(" ✅ Got nodes successfully")
            return nodes
        except Exception as e:
            self._logger.error(f" ❌ Failed to get nodes: {e}")
            return []

    async def connect_to(self, other_node: Node, timeout: int = 8) -> ClientResponse:
        """
        Initiate a connection to another node using UDP hole punching.

        :param Node other_node: The node to connect to.
        :param int timeout: The timeout in seconds.
        :return ClientResponse: The status and message of the operation.
        """
        self._logger.info(f" 💡 Attempting to connect to node {other_node.public_ip}:{other_node.public_port} with timeout {timeout}s...")
        if not self._validate_connection_prerequisites(other_node):
            self._logger.error(" ❌ Connection prerequisites not met.")
            return ClientResponse(
                status="fail",
                message="Connection prerequisites not met",
            )
        connection_established = Event()
        self._udp_server.set_connection_callback(connection_established.set)
        punch_task = create_task(self._send_punch_messages(other_node))
        try:
            self._logger.info(" 💡 Sending punch messages and waiting for connection...")
            await wait_for(connection_established.wait(), timeout=timeout)
            self._logger.info(" ✅ Connection established!")
            return ClientResponse(status="success", message="Connection established")
        except TimeoutError:
            self._logger.error(f" ❌ Connection attempt to {other_node.public_ip}:{other_node.public_port} timed out after {timeout}s.")
            return ClientResponse(status="fail", message="Connection attempt timed out")
        except Exception as e:
            self._logger.error(f" ❌ Error during connection attempt: {e}")
            return ClientResponse(status="fail", message=f"Connection error: {e}")
        finally:
            punch_task.cancel()
            self._udp_server.set_connection_callback(None)

    async def send_message(
        self,
        message: str,
        target_ip: str,
        target_port: int,
    ) -> ClientResponse:
        """
        Send a message to a specified target IP and port.

        :param str message: The message to send.
        :param str target_ip: The target IP address.
        :param int target_port: The target port number.
        :return ClientResponse: The status and message of the operation.
        """
        try:
            self._udp_server.send_message(message, target_ip, target_port)
            return ClientResponse(
                status="success",
                message=f"Message sent to {target_ip}:{target_port}",
            )
        except Exception as e:
            return ClientResponse(status="fail", message=f"Failed to send message: {e}")

    def _validate_connection_prerequisites(self, other_node: Node) -> bool:
        """
        Validate the prerequisites for establishing a connection.

        :param Node other_node: The other node to connect to.
        :return bool: True if the prerequisites are met, False otherwise.
        """
        if not self._node.public_ip or not self._node.public_port:
            self._logger.warning(
                " ⚠️ This node has not discovered its public IP and port yet."
            )
            return False
        if not other_node.public_ip or not other_node.public_port:
            self._logger.warning(
                f" ⚠️ The other node {other_node} has not discovered its public IP and port yet."
            )
            return False
        if not self._server_status:
            self._logger.warning(
                " ⚠️ The current node is not listening for responses yet."
            )
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
                await self.send_message(
                    message,
                    other_node.public_ip,
                    other_node.public_port,
                )
                await sleep(1)

    def _handle_message(self, message: str, sender: tuple[str, int]) -> None:
        """
        Handle an incoming message.

        :param str message: The received message.
        :param tuple[str, int] sender: The sender's address (IP, port).
        """
        self._logger.info(f" 💡 Received message from {sender}: {message}")
        if message.startswith("punch"):
            self._udp_server.send_message("pong", sender[0], sender[1])
        elif message.startswith("pong"):
            if self._udp_server._connection_callback:
                self._udp_server._connection_callback()

    def __str__(self) -> str:
        """
        String representation of the P2PClient.

        :return str: A string representation of the P2PClient.
        """
        return f"P2PClient(node={self._node})"
