import asyncio

import httpx
import streamlit as st

from fungi.client.client import Client
from fungi.models.node import Node
from fungi.tools.constants import SERVER_URL
from fungi.tools.utils import get_logger


class P2PNetworkLauncher:
    """
    A class to represent the P2P Network Launcher using Streamlit.
    """

    def __init__(self):
        """
        Initialize the P2PNetworkLauncher class.
        """
        self.logger = get_logger(name="P2P_Client")
        self._setup_session_state()
        self.client = Client(logger=self.logger, server_url=SERVER_URL)

    def _setup_session_state(self):
        """
        Set up the session state for the application.
        """
        st.session_state.setdefault("client", None)
        st.session_state.setdefault("connection_status", "off")
        st.session_state.setdefault("current_nodes", [])
        st.session_state.setdefault("log", "")

    def _log(self, message: str, level: str = "info") -> None:
        """
        Log a message to the session log and logger.

        :param str message: The message to log.
        :param str level: The logging level ("info", "warning", "error").
        """
        if self.logger:
            log_method = getattr(self.logger, level, self.logger.info)
            log_method(message)
        st.session_state.log += f"{level.upper()}: {message}\n"
        st.rerun()

    async def _join_network(self) -> None:
        """
        Join the network by adding the current client's information to the network.
        """
        self._log("Joining the network...")
        await self.client.join_network()
        st.session_state.client = self.client
        st.session_state.connection_status = "off"
        await self._update_current_nodes()
        self._log("Joined the network.")

    async def _leave_network(self) -> None:
        """
        Leave the network by removing the current client's information from the network.
        """
        if st.session_state.client:
            self._log("Leaving the network...")
            await st.session_state.client.leave_network()
            st.session_state.client = None
            st.session_state.connection_status = "off"
            await self._update_current_nodes()
            self._log("Left the network.")

    async def _update_current_nodes(self) -> None:
        """
        Update the list of current nodes in the network.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{SERVER_URL}/nodes")
                response.raise_for_status()
                st.session_state.current_nodes = response.json()
            except httpx.HTTPStatusError as e:
                self._log(f"Failed to update nodes: {e.response.text}", level="error")
            except httpx.RequestError as e:
                self._log(f"An error occurred while requesting: {e}", level="error")

    async def _connect_to_node(self, target_node: Node) -> None:
        """
        Connect to a specified target node.

        :param Node target_node: The node to connect to.
        """
        if st.session_state.client:
            st.session_state.connection_status = "connecting"
            self._log(f"Connecting to {target_node.public_ip}:{target_node.public_port}...")
            try:
                success = await st.session_state.client.initiate_connection(target_node)
                if success:
                    st.session_state.connection_status = "on"
                    self._log(f"Connected to {target_node.public_ip}:{target_node.public_port}.")
                else:
                    st.session_state.connection_status = "error"
                    self._log(
                        f"Failed to connect to {target_node.public_ip}:{target_node.public_port}.", level="error"
                    )
            except Exception as e:
                st.session_state.connection_status = "error"
                self._log(f"Connection failed: {e}", level="error")

    def _display_logs(self) -> None:
        """
        Display the log messages in a Streamlit text area.
        """
        st.text_area("Logs", value=st.session_state.get("log", ""), height=200, max_chars=None)

    def run(self) -> None:
        """
        Run the Streamlit application for the P2P Network Launcher.
        """
        st.title("P2P Network Launcher")

        if st.session_state.client is None:
            if st.button("Join Network"):
                asyncio.run(self._join_network())
        else:
            if st.button("Leave Network"):
                asyncio.run(self._leave_network())

        st.markdown("## Current Nodes")
        if st.session_state.client:
            asyncio.run(self._update_current_nodes())
            for node in st.session_state.current_nodes:
                if (
                    node["public_ip"] != st.session_state.client.node.public_ip
                    or node["public_port"] != st.session_state.client.node.public_port
                ):
                    if st.button(f"Connect to {node['public_ip']}:{node['public_port']}"):
                        target_node = Node(**node)
                        asyncio.run(self._connect_to_node(target_node))

        status = st.session_state.connection_status

        if status == "connecting":
            st.spinner("Connecting...")
        elif status == "on":
            st.success("Connected to the node.")
        elif status == "error":
            st.error("Connection failed.")
        else:
            st.info("Not connected to any node.")

        self._display_logs()


if __name__ == "__main__":
    launcher = P2PNetworkLauncher()
    launcher.run()
