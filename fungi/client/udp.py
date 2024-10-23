import asyncio
from socket import socket
from typing import Callable, Optional, Tuple


class UDPServer(asyncio.DatagramProtocol):
    """A UDP server for handling P2P communications."""

    def __init__(self, send_socket: socket) -> None:
        """
        Initialize the UDP server.

        :param socket send_socket: Socket used for sending messages.
        """
        self._send_socket = send_socket
        self._transport = None
        self._message_callback: Optional[Callable[[str], None]] = None

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
        if self._message_callback:
            self._message_callback(message)

    def send_message(self, message: str, target_ip: str, target_port: int) -> None:
        """
        Send a message to a specified target.

        :param str message: The message to send.
        :param str target_ip: The target IP address.
        :param int target_port: The target port number.
        """
        self._send_socket.sendto(message.encode(), (target_ip, target_port))

    def set_message_callback(self, callback: Callable[[str], None]) -> None:
        """
        Set the callback function for received messages.

        :param Callable[[str], None] callback: The callback function to handle received messages.
        """
        self._message_callback = callback
