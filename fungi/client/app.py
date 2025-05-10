from ipaddress import ip_address
from logging import DEBUG, Handler, Logger, LogRecord
from gradio import Blocks, Button, Dropdown, Markdown, Row, Textbox, Column, Box

from fungi.client.client import P2PClient
from fungi.models.node import Node
from fungi.utils.logger import get_logger
from fungi.utils.constants import config

class LogHandler(Handler):
    """
    Custom logging handler to update the app's log panel.
    """

    def __init__(self, callback) -> None:
        """
        Initialize the LogHandler.

        :param callback: The callback function to update the log panel.
        """
        super().__init__()
        self._callback = callback

    def emit(self, record: LogRecord) -> None:
        """
        Emit a log record.

        :param LogRecord record: The log record to emit.
        """
        if record.levelno > 10:
            log_entry = self.format(record)
            self._callback(log_entry)


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
        self._client: P2PClient = P2PClient(server_url=config.server_url, logger=client_logger)
        self._connection_status: str = "off"
        self._log: str = ""
        self._chat_history: str = ""
        self._connected_node: str | None = None
        self._nat_type: str | None = None
        self._public_ip: str | None = None
        self._public_port: int | None = None

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

    async def _discover_network_info(self) -> list[any]:
        """
        Discover NAT type, public IP, and port, and update the UI.

        :return list[any]: The updated UI components.
        """
        response = await self._client.discover_network_info()
        if response.status == "success" and response.result:
            self._nat_type = str(response.result.nat_type)
            self._public_ip = response.result.public_ip
            self._public_port = response.result.public_port
        else:
            self._nat_type = None
            self._public_ip = None
            self._public_port = None
        return await self._update_ui()

    async def _join_network(self) -> list[any]:
        """
        Join the P2P network and update the UI.

        :return list[any]: The updated UI components.
        """
        result = await self._client.join_network()
        self._connection_status = "on" if result.status == "success" else "off"
        return await self._update_ui()

    async def _leave_network(self) -> list[any]:
        """
        Leave the P2P network and update the UI.

        :return list[any]: The updated UI components.
        """
        result = await self._client.leave_network()
        self._connection_status = (
            "off" if result.status == "success" else self._connection_status
        )
        return await self._update_ui()

    async def _update_current_nodes(self) -> list[Node]:
        """
        Update the list of current nodes in the network.

        :return list[Node]: A list of current nodes.
        """
        return await self._client.get_nodes()

    async def _connect_to_node(self, target_node: str) -> list[any]:
        """
        Connect to a specific node in the network and update the UI.

        :param str target_node: The node to connect to (in "ip:port" format).
        :return list[any]: The updated UI components.
        """
        self._connection_status = "connecting"
        try:
            ip, port = target_node.split(":")
            node = Node(public_ip=ip_address(ip), public_port=int(port))
            result = await self._client.connect_to(node)
            if result.status == "success":
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
            result = await self._client.send_message(
                message, ip, int(port)
            )
            if result.status == "success":
                self._add_chat_message(f"You: {message}")
        return self._chat_history

    async def _update_ui(self) -> list[any]:
        """
        Update the UI components based on the current state.

        :return list[any]: The updated UI components.
        """
        current_nodes = await self._update_current_nodes()
        node_choices = [
            f"{node.public_ip}:{node.public_port}"
            for node in current_nodes
            if node != self._client._node
        ]
        nat_status = self._nat_type if self._nat_type else "Unknown"
        public_ip_status = self._public_ip if self._public_ip else "Unknown"
        public_port_status = self._public_port if self._public_port else "Unknown"
        return [
            self._log,
            nat_status,
            public_ip_status,
            public_port_status,
            Dropdown(
                choices=node_choices,
                interactive=True,
                value=self._connected_node if self._connected_node else None,
            ),
            Button(interactive=self._connection_status == "off"),
            Button(interactive=self._connection_status == "on"),
            Button(interactive=self._connection_status == "on"),
            Button(interactive=bool(node_choices)),
            Button(
                interactive=self._connection_status == "on"
                and self._connected_node is not None
            ),
        ]

    def run(self) -> None:
        """
        Run the P2P Network Launcher application with improved UI.
        """
        with Blocks(theme="soft") as demo:
            Markdown("# 🌐 P2P Network Launcher", elem_id="main-title")
            with Row():
                with Column():
                    with Box():
                        Markdown("### Network Status")
                        nat_type_output = Textbox(label="NAT Type", value="Unknown", interactive=False)
                        public_ip_output = Textbox(label="Public IP", value="Unknown", interactive=False)
                        public_port_output = Textbox(label="Public Port", value="Unknown", interactive=False)
                        detect_nat_btn = Button("🔍 Detect NAT / Public IP / Port")
                    with Box():
                        Markdown("### Nodes")
                        node_selector = Dropdown(
                            label="Available Nodes", choices=[], interactive=False
                        )
                        with Row():
                            join_btn = Button("🔗 Join Network")
                            leave_btn = Button("❌ Leave Network", interactive=False)
                            refresh_btn = Button("🔄 Refresh Nodes", interactive=False)
                            connect_btn = Button("🔌 Connect to Node", interactive=False)
                with Column():
                    Markdown("### Logs")
                    log_output = Textbox(
                        label="Logs", placeholder="Logs will appear here...", lines=10, interactive=False
                    )
            with Box():
                Markdown("### Chat")
                with Row():
                    chat_message = Textbox(
                        label="Chat Message", placeholder="Type your message here..."
                    )
                    send_btn = Button("📤 Send", interactive=False)
                chat_log_output = Textbox(
                    label="Chat Log",
                    placeholder="Chat messages will appear here...",
                    lines=10,
                    interactive=False
                )

            detect_nat_btn.click(
                fn=self._discover_network_info,
                outputs=[
                    log_output,
                    nat_type_output,
                    public_ip_output,
                    public_port_output,
                    node_selector,
                    join_btn,
                    leave_btn,
                    refresh_btn,
                    connect_btn,
                    send_btn,
                ],
            )
            join_btn.click(
                fn=self._join_network,
                outputs=[
                    log_output,
                    nat_type_output,
                    public_ip_output,
                    public_port_output,
                    node_selector,
                    join_btn,
                    leave_btn,
                    refresh_btn,
                    connect_btn,
                    send_btn,
                ],
            )
            leave_btn.click(
                fn=self._leave_network,
                outputs=[
                    log_output,
                    nat_type_output,
                    public_ip_output,
                    public_port_output,
                    node_selector,
                    join_btn,
                    leave_btn,
                    refresh_btn,
                    connect_btn,
                    send_btn,
                ],
            )
            refresh_btn.click(
                fn=self._update_ui,
                outputs=[
                    log_output,
                    nat_type_output,
                    public_ip_output,
                    public_port_output,
                    node_selector,
                    join_btn,
                    leave_btn,
                    refresh_btn,
                    connect_btn,
                    send_btn,
                ],
            )
            connect_btn.click(
                fn=self._connect_to_node,
                inputs=[node_selector],
                outputs=[
                    log_output,
                    nat_type_output,
                    public_ip_output,
                    public_port_output,
                    node_selector,
                    join_btn,
                    leave_btn,
                    refresh_btn,
                    connect_btn,
                    send_btn,
                ],
            )
            send_btn.click(
                fn=self._send_chat_message,
                inputs=[node_selector, chat_message],
                outputs=[chat_log_output],
            )

        demo.launch(server_name="0.0.0.0", server_port=7860)


def main() -> None:
    """
    Main function to launch the P2P Network application.
    """
    launcher = P2PNetworkLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
