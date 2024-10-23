from ipaddress import ip_address
from logging import DEBUG, Handler, Logger, LogRecord
from typing import Any, Dict, List, Optional

from gradio import Blocks, Button, Dropdown, Markdown, Row, Textbox

from fungi.client.client import Client
from fungi.models.node import Node
from fungi.utils.constants import SERVER_URL
from fungi.utils.logger import get_logger


class LogHandler(Handler):
    """
    Custom logging handler to update the app's log panel.
    """

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record: LogRecord) -> None:
        """
        Emit a log record.

        :param LogRecord record: The log record to emit.
        """
        if record.levelno > 10:  # Filter out DEBUG logs (level 10)
            log_entry = self.format(record)
            self.callback(log_entry)


class P2PNetworkLauncher:
    """
    A class to manage the P2P Network Launcher application.
    """

    def __init__(self) -> None:
        """
        Initialize the P2P Network Launcher.
        """
        self._logger: Logger = get_logger(name="P2P_Launcher", level=DEBUG)
        client_logger = get_logger(name="P2P_Client", level=DEBUG)
        client_logger.addHandler(LogHandler(self._update_log))
        self._client: Client = Client(server_url=SERVER_URL, logger=client_logger)
        self._connection_status: str = "off"
        self._log: str = ""
        self._chat_history: str = ""
        self._connected_node: Optional[str] = None

    def _update_log(self, message: str) -> None:
        """
        Update the log panel with a new message.

        :param str message: The message to add to the log panel.
        """
        self._log += f"{message}\n"

    def _add_chat_message(self, message: str) -> None:
        """
        Add a message to the chat log.

        :param str message: The message to add to the chat log.
        """
        self._chat_history += f"{message}\n"

    async def _join_network(self) -> List[Any]:
        """
        Join the P2P network.

        :return List[Any]: A list containing the updated UI components.
        """
        result: Dict[str, Any] = await self._client.join_network()
        self._connection_status = "on" if result["status"] == "success" else "off"
        return await self._update_ui()

    async def _leave_network(self) -> List[Any]:
        """
        Leave the P2P network.

        :return List[Any]: A list containing the updated UI components.
        """
        result: Dict[str, Any] = await self._client.leave_network()
        self._connection_status = "off" if result["status"] == "success" else self._connection_status
        return await self._update_ui()

    async def _update_current_nodes(self) -> List[Node]:
        """
        Update the list of current nodes in the network.

        :return List[Node]: A list of current nodes.
        """
        return await self._client.get_nodes()

    async def _connect_to_node(self, target_node: str) -> List[Any]:
        """
        Connect to a specific node in the network.

        :param str target_node: The node to connect to (in "ip:port" format).
        :return List[Any]: A list containing the updated UI components.
        """
        self._connection_status = "connecting"
        try:
            ip, port = target_node.split(":")
            node = Node(public_ip=ip_address(ip), public_port=int(port))
            result: Dict[str, Any] = await self._client.connect_to(node)
            if result["status"] == "success":
                self._connection_status = "on"
                self._connected_node = target_node
            else:
                self._connection_status = "off"
                self._connected_node = None
        except Exception:
            self._connection_status = "error"
            self._connected_node = None
        return await self._update_ui()

    async def _send_chat_message(self, target_node: str, message: str) -> str:
        """
        Send a chat message to a specific node.

        :param str target_node: The node to send the message to (in "ip:port" format).
        :param str message: The message to send.
        :return str: The updated chat log.
        """
        if target_node and target_node == self._connected_node:
            ip, port = target_node.split(":")
            result: Dict[str, Any] = await self._client.send_message(message, ip_address(ip), int(port))
            if result["status"] == "success":
                self._add_chat_message(f"You: {message}")
        return self._chat_history

    async def _update_ui(self) -> List[Any]:
        """
        Update the UI components based on the current state.

        :return List[Any]: A list containing the updated UI components.
        """
        current_nodes = await self._update_current_nodes()
        node_choices = [f"{node.public_ip}:{node.public_port}" for node in current_nodes if node != self._client._node]
        return [
            self._log,
            Dropdown(
                choices=node_choices, interactive=True, value=self._connected_node if self._connected_node else None
            ),
            Button(interactive=self._connection_status == "off"),
            Button(interactive=self._connection_status == "on"),
            Button(interactive=self._connection_status == "on"),
            Button(interactive=bool(node_choices)),
            Button(interactive=self._connection_status == "on" and self._connected_node is not None),
        ]

    def run(self) -> None:
        """
        Run the P2P Network Launcher application.
        """
        with Blocks() as demo:
            Markdown("# P2P Network Launcher")
            with Row():
                join_btn = Button("Join Network")
                leave_btn = Button("Leave Network", interactive=False)
                refresh_btn = Button("Refresh Nodes", interactive=False)

            node_selector = Dropdown(label="Available Nodes", choices=[], interactive=False)
            connect_btn = Button("Connect to Node", interactive=False)
            log_output = Textbox(label="Logs", placeholder="Logs will appear here...", lines=10)

            with Row():
                chat_message = Textbox(label="Chat Message", placeholder="Type your message here...")
                send_btn = Button("Send Message", interactive=False)
            chat_log_output = Textbox(label="Chat Log", placeholder="Chat messages will appear here...", lines=10)

            join_btn.click(
                fn=self._join_network,
                outputs=[log_output, node_selector, join_btn, leave_btn, refresh_btn, connect_btn, send_btn],
            )
            leave_btn.click(
                fn=self._leave_network,
                outputs=[log_output, node_selector, join_btn, leave_btn, refresh_btn, connect_btn, send_btn],
            )
            refresh_btn.click(
                fn=self._update_ui,
                outputs=[log_output, node_selector, join_btn, leave_btn, refresh_btn, connect_btn, send_btn],
            )
            connect_btn.click(
                fn=self._connect_to_node,
                inputs=[node_selector],
                outputs=[log_output, node_selector, join_btn, leave_btn, refresh_btn, connect_btn, send_btn],
            )
            send_btn.click(
                fn=self._send_chat_message,
                inputs=[node_selector, chat_message],
                outputs=[chat_log_output],
            )

        demo.launch()


def main() -> None:
    """
    Main function to launch the P2P Network application.
    """
    launcher = P2PNetworkLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
