import asyncio
from socket import AF_INET, SOCK_DGRAM, socket
from collections.abc import Callable
from fungi.utils.logger import get_logger


class UDPServer(asyncio.DatagramProtocol):
    """
    Simple UDP server for P2P communication.
    """

    def __init__(self, message_handler: Callable[[str, tuple[str, int]], None]) -> None:
        """
        Initialize the UDP server and set the message handler.

        :param Callable[[str, tuple[str, int]], None] message_handler: Callback for received messages.
        """
        super().__init__()
        self._send_socket = socket(AF_INET, SOCK_DGRAM)
        self._transport: asyncio.DatagramTransport | None = None
        self._message_handler = message_handler
        self._logger = get_logger("UDPServer")
        self._connection_callback: Callable[[], None] | None = None

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        """
        Called when the UDP server is ready to use.

        :param asyncio.DatagramTransport transport: The transport representing the connection.
        """
        self._transport = transport
        self._logger.info(" ✅ UDP server started.")

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """
        Called when a UDP packet is received.

        :param bytes data: The received data.
        :param tuple[str, int] addr: The address of the sender.
        """
        message = data.decode()
        self._logger.info(f" 💡 Received message from {addr}: {message}")
        self._message_handler(message, addr)

    def send_message(self, message: str, target_ip: str, target_port: int) -> None:
        """
        Send a message to a specific IP and port.

        :param str message: The message to send.
        :param str target_ip: The target IP address.
        :param int target_port: The target port number.
        """
        self._send_socket.sendto(message.encode(), (target_ip, target_port))
        self._logger.info(f" ✅ Sent message to {target_ip}:{target_port}")

    def set_connection_callback(self, callback: Callable[[], None] | None) -> None:
        """
        Set a callback for when a connection is established.

        :param Callable[[], None] | None callback: The callback function to handle successful connections.
        """
        self._connection_callback = callback

    async def start(self, ip: str, port: int) -> None:
        """
        Start the UDP server and bind sockets to the given IP and port.

        :param str ip: The IP address to bind to.
        :param int port: The port number to bind to.
        """
        loop = asyncio.get_running_loop()
        try:
            transport, _ = await loop.create_datagram_endpoint(lambda: self, local_addr=(ip, port))
            self._transport = transport
            # Close and re-bind the sending socket to the same local port
            if self._send_socket:
                self._send_socket.close()
            self._send_socket = socket(AF_INET, SOCK_DGRAM)
            self._send_socket.bind((ip, port))
            self._logger.info(f" ✅ UDP server started and bound to {ip}:{port}")
        except Exception as e:
            self._logger.error(f" ❌ Failed to bind UDP server to {ip}:{port}: {e}")
            raise

    async def stop(self) -> None:
        """
        Stop the UDP server and close sockets.
        """
        if self._transport:
            self._transport.close()
            self._transport = None
        if self._send_socket:
            self._send_socket.close()
        await asyncio.sleep(0.1)
        self._logger.info(" ✅ UDP server stopped.")
