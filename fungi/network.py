import json
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from fungi.node import Node


class Network:
    """Representation of the P2P network"""

    def __init__(self, storage_path: str = "nodes.json") -> None:
        """
        Initialize the network with an optional storage path for node information.

        :param storage_path: Path to the storage file for node information.
        """
        self.nodes: List["Node"] = []
        self.storage_path = storage_path
        self._load_nodes_from_storage()

    def _load_nodes_from_storage(self) -> None:
        """
        Load nodes from the storage file.

        This method reads the node information from the specified storage file
        and initializes the list of nodes. If the file does not exist or contains
        invalid data, the nodes list will be empty.
        """
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                for node_data in data:
                    node = Node(**node_data)
                    self.nodes.append(node)
        except (FileNotFoundError, json.JSONDecodeError):
            self.nodes = []

    def _save_nodes_to_storage(self) -> None:
        """
        Save nodes to the storage file.

        This method writes the current list of nodes to the specified storage file
        in JSON format.
        """
        with open(self.storage_path, "w") as f:
            json.dump([node.model_dump() for node in self.nodes], f)

    async def add_node(self, node: "Node") -> None:
        """
        Add a node to the network.

        This method appends the given node to the list of nodes, updates the storage file,
        and sets the node's network reference to this network.

        :param Node node: The node to add to the network.
        """
        self.nodes.append(node)
        self._save_nodes_to_storage()
        node.network = self

    async def remove_node(self, node: "Node") -> None:
        """
        Remove a node from the network.

        This method removes the given node from the list of nodes, updates the storage file,
        and clears the node's network reference.

        :param Node node: The node to remove from the network.
        """
        self.nodes.remove(node)
        self._save_nodes_to_storage()
        node.network = None

    def list_nodes(self) -> List["Node"]:
        """
        List all nodes in the network.

        :return List[Node]: A list of nodes currently in the network.
        """
        return self.nodes

    def __str__(self) -> str:
        """
        String representation of the network.

        :return str: A string representing the number of nodes in the network.
        """
        return f"Network(nodes={len(self.nodes)})"
