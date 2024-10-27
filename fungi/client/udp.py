import asyncio
from socket import AF_INET, SOCK_DGRAM, socket
from typing import Callable, Optional, Tuple


class UDPServer(asyncio.DatagramProtocol):
    """A UDP server for handling P2P communications."""

    def __init__(self, message_handler: Callable[[str, Tuple[str, int]], None]) -> None:
        """
        Initialize the UDP server.

        :param Callable[[str, Tuple[str, int]], None] message_handler: Callback function to handle received messages.
        """
        super().__init__()
        self._send_socket = socket(AF_INET, SOCK_DGRAM)
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._message_handler = message_handler
        self.connection_callback: Optional[Callable[[], None]] = None

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        """
        Called when a connection is made.

        :param asyncio.DatagramTransport transport: The transport representing the connection.
        """
        self._transport = transport

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """
        Called when a datagram is received.

        :param bytes data: The received data.
        :param Tuple[str, int] addr: The address of the sender.
        """
        message = data.decode()
        self._message_handler(message, addr)

    def send_message(self, message: str, target_ip: str, target_port: int) -> None:
        """
        Send a message to a specified target.

        :param str message: The message to send.
        :param str target_ip: The target IP address.
        :param int target_port: The target port number.
        """
        self._send_socket.sendto(message.encode(), (target_ip, target_port))

    def set_connection_callback(self, callback: Optional[Callable[[], None]]) -> None:
        """
        Set the callback function for successful connections.

        :param Optional[Callable[[], None]] callback: The callback function to handle successful connections.
        """
        self.connection_callback = callback

    async def start(self, ip: str, port: int) -> None:
        """
        Start the UDP server.

        :param str ip: The IP address to bind to.
        :param int port: The port number to bind to.
        """
        loop = asyncio.get_running_loop()
        await loop.create_datagram_endpoint(lambda: self, local_addr=(ip, port))

    async def stop(self) -> None:
        """
        Stop the UDP server.
        """
        if self._transport:
            self._transport.close()
            self._transport = None
        if self._send_socket:
            self._send_socket.close()
        # Wait a short time to ensure the socket is fully closed
        await asyncio.sleep(0.1)
