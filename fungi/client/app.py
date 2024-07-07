from typing import List

import gradio as gr

from fungi.client.client import Client
from fungi.models.node import Node
from fungi.tools.constants import SERVER_URL
from fungi.tools.utils import get_logger


class P2PNetworkLauncher:
    def __init__(self):
        self.logger = get_logger(name="P2P_Client")
        self.client = Client(logger=self._log, server_url=SERVER_URL)
        self.connection_status = "off"
        self.log = ""

    def _log(self, message: str, level: str = "info") -> None:
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(message)
        self.log += f"{level.upper()}: {message}\n"

    async def _join_network(self) -> None:
        await self.client.join_network()
        self.connection_status = "on"

    async def _leave_network(self) -> None:
        await self.client.leave_network()
        self.connection_status = "off"

    async def _update_current_nodes(self) -> List[Node]:
        current_nodes = await self.client.get_nodes()
        self._log(f"Current nodes: {current_nodes}")
        return current_nodes

    async def _connect_to_node(self, target_node: Node) -> None:
        self.connection_status = "connecting"
        try:
            success = await self.client.connect_to(target_node)
            self.connection_status = {True: "on", False: "off"}[success["status"] == "success"]
        except Exception as e:
            self.connection_status = "error"
            self._log(f"Connection failed: {e}", level="error")

    def run(self):
        async def join_network():
            await self._join_network()
            current_nodes = await self._update_current_nodes()
            node_choices = [f"{node.public_ip}:{node.public_port}" for node in current_nodes]
            return (
                self.log,
                gr.update(
                    choices=node_choices,
                    interactive=True,
                    value=node_choices[0] if len(node_choices) > 0 else None,
                ),  # list
                gr.update(interactive=False),  # join
                gr.update(interactive=True),  # leave
                gr.update(interactive=True),  # refresh
                gr.update(interactive=len(node_choices) > 0),  # connect
            )

        async def leave_network():
            await self._leave_network()
            return (
                self.log,
                gr.update(choices=[], interactive=False),  # list
                gr.update(interactive=True),  # join
                gr.update(interactive=False),  # leave
                gr.update(interactive=False),  # refresh
                gr.update(interactive=False),  # connect
            )

        async def refresh_nodes():
            current_nodes = await self._update_current_nodes()
            node_choices = [f"{node.public_ip}:{node.public_port}" for node in current_nodes]
            return (
                self.log,
                gr.update(choices=node_choices),  # list
                gr.update(interactive=len(current_nodes) > 0),  # connect
            )

        async def connect_to_node(node: str):
            ip, port = node.split(":")
            target_node = Node(public_ip=ip, public_port=int(port))
            await self._connect_to_node(target_node)
            return self.log

        with gr.Blocks() as demo:
            gr.Markdown("# P2P Network Launcher")
            with gr.Row():
                join_btn = gr.Button("Join Network")
                leave_btn = gr.Button("Leave Network", interactive=False)
                refresh_btn = gr.Button("Refresh Nodes", interactive=False)

            node_selector = gr.Dropdown(label="Available Nodes", choices=[], interactive=False)
            connect_btn = gr.Button("Connect to Node", interactive=False)
            log_output = gr.Textbox(label="Logs", placeholder="Logs will appear here...", lines=10)

            join_btn.click(
                fn=join_network,
                outputs=[log_output, node_selector, join_btn, leave_btn, refresh_btn, connect_btn],
            )
            leave_btn.click(
                fn=leave_network,
                outputs=[log_output, node_selector, join_btn, leave_btn, refresh_btn, connect_btn],
            )
            refresh_btn.click(fn=refresh_nodes, outputs=[log_output, node_selector, connect_btn])
            connect_btn.click(fn=connect_to_node, inputs=[node_selector], outputs=[log_output])

        demo.launch()


def main():
    launcher = P2PNetworkLauncher()
    launcher.run()
