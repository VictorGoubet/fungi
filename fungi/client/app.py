import asyncio

import gradio as gr
import httpx

from fungi.client.client import Client
from fungi.models.node import Node
from fungi.tools.constants import SERVER_URL
from fungi.tools.utils import get_logger


class P2PNetworkLauncher:
    def __init__(self):
        self.logger = get_logger(name="P2P_Client")
        self.client = Client(logger=self.logger, server_url=SERVER_URL)
        self.connection_status = "off"
        self.current_nodes = []
        self.log = ""

    def _log(self, message: str, level: str = "info") -> None:
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(message)
        self.log += f"{level.upper()}: {message}\n"

    async def _join_network(self) -> None:
        self._log("Joining the network...")
        await self.client.join_network()
        self.connection_status = "off"
        await self._update_current_nodes()
        self._log("Joined the network.")

    async def _leave_network(self) -> None:
        self._log("Leaving the network...")
        await self.client.leave_network()
        self.connection_status = "off"
        await self._update_current_nodes()
        self._log("Left the network.")

    async def _update_current_nodes(self) -> None:
        self._log("Updating listing...")
        self.current_nodes = await self.client.get_nodes()
        self._log("Listing updated")

    async def _connect_to_node(self, target_node: Node) -> None:
        self.connection_status = "connecting"
        self._log(f"Connecting to {target_node.public_ip}:{target_node.public_port}...")
        try:
            success = await self.client.initiate_connection(target_node)
            if success:
                self.connection_status = "on"
                self._log(f"Connected to {target_node.public_ip}:{target_node.public_port}.")
            else:
                self.connection_status = "error"
                self._log(f"Failed to connect to {target_node.public_ip}:{target_node.public_port}.", level="error")
        except Exception as e:
            self.connection_status = "error"
            self._log(f"Connection failed: {e}", level="error")

    def run(self):
        async def join_network():
            await self._join_network()
            return self.log, self.current_nodes

        async def leave_network():
            await self._leave_network()
            return self.log, self.current_nodes

        async def connect_to_node(node: str):
            ip, port = node.split(":")
            target_node = Node(public_ip=ip, public_port=int(port))
            await self._connect_to_node(target_node)
            return self.log

        with gr.Blocks() as demo:
            gr.Markdown("# P2P Network Launcher")
            join_btn = gr.Button("Join Network")
            leave_btn = gr.Button("Leave Network")
            node_selector = gr.Dropdown(label="Available Nodes", choices=[], interactive=True)
            connect_btn = gr.Button("Connect to Node")
            log_output = gr.Textbox(label="Logs", placeholder="Logs will appear here...", lines=10)
            result_output = gr.Textbox(label="Result", placeholder="Result will appear here...", lines=2)

            join_btn.click(fn=join_network, outputs=[log_output, result_output, node_selector])
            leave_btn.click(fn=leave_network, outputs=[log_output, result_output, node_selector])
            connect_btn.click(fn=connect_to_node, inputs=[node_selector], outputs=[log_output, result_output])

        demo.launch()


def main():
    launcher = P2PNetworkLauncher()
    launcher.run()
