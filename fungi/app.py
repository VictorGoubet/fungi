import asyncio
import json
import logging
from typing import List

import streamlit as st

from fungi.network import Network
from fungi.node import Node


class P2PNetworkLauncher:
    """
    A class to represent the P2P Network Launcher using Streamlit.
    """

    def __init__(self):
        """
        Initialize the P2PNetworkLauncher class.
        """
        self.logger = self._setup_logger()
        self.network = Network()
        self._setup_session_state()

    def _setup_logger(self) -> logging.Logger:
        """
        Set up the logger for the application.

        :return logging.Logger: Configured logger instance.
        """
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger("StreamlitApp")

    def _setup_session_state(self):
        """
        Set up the session state for the application.
        """
        if "node" not in st.session_state:
            st.session_state.node = None
        if "connection_status" not in st.session_state:
            st.session_state.connection_status = "off"
        if "current_nodes" not in st.session_state:
            st.session_state.current_nodes = []

    async def join_network(self):
        """
        Join the network by adding the current node's information to the network.
        """
        node = Node(logger=self.logger)
        await node.join_network(self.network)
        st.session_state.node = node
        st.session_state.connection_status = "off"
        self.update_current_nodes()

    async def leave_network(self):
        """
        Leave the network by removing the current node's information from the network.
        """
        if st.session_state.node:
            await st.session_state.node.leave_network()
            st.session_state.node = None
            st.session_state.connection_status = "off"
            self.update_current_nodes()

    def update_current_nodes(self):
        """
        Update the list of current nodes in the network.
        """
        st.session_state.current_nodes = self.network.list_nodes()

    async def connect_to_node(self, target_node: Node):
        """
        Connect to a specified target node.

        :param Node target_node: The node to connect to.
        """
        if st.session_state.node:
            st.session_state.connection_status = "connecting"
            try:
                success = await st.session_state.node.initiate_connection(target_node)
                if success:
                    st.session_state.connection_status = "on"
                else:
                    st.session_state.connection_status = "error"
            except Exception as e:
                st.session_state.connection_status = "error"
                self.logger.error(f"Connection failed: {e}")

    def run(self):
        """
        Run the Streamlit application for the P2P Network Launcher.
        """
        st.title("P2P Network Launcher")

        if st.session_state.node is None:
            if st.button("Join Network"):
                asyncio.run(self.join_network())
        else:
            if st.button("Leave Network"):
                asyncio.run(self.leave_network())

        st.markdown("## Current Nodes")
        if st.session_state.node:
            self.update_current_nodes()
            for node in st.session_state.current_nodes:
                if (
                    node.public_ip != st.session_state.node.public_ip
                    or node.public_port != st.session_state.node.public_port
                ):
                    if st.button(f"Connect to {node.public_ip}:{node.public_port}"):
                        asyncio.run(self.connect_to_node(node))

        status = st.session_state.connection_status

        if status == "connecting":
            st.spinner("Connecting...")
        elif status == "on":
            st.success("Connected to the node.")
        elif status == "error":
            st.error("Connection failed.")
        else:
            st.info("Not connected to any node.")


if __name__ == "__main__":
    launcher = P2PNetworkLauncher()
    launcher.run()
