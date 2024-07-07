import asyncio
from typing import Callable


class UDPServer(asyncio.DatagramProtocol):

    def __init__(self, handle_incoming_message: Callable) -> None:
        self.handle_incoming_message = handle_incoming_message

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode()
        self.handle_incoming_message(message, addr)
