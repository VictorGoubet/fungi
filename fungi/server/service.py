import asyncio
import json
from typing import List

import redis
from pydantic import BaseModel, Field

from fungi.models.node import Node
from fungi.tools.constants import REDIS_HOST, REDIS_PORT


class NetworkService(BaseModel):
    """Signaling server"""

    redis_host: str = Field(default=REDIS_HOST, description="Redis host")
    redis_port: int = Field(default=REDIS_PORT, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database index")
    redis_client: redis.Redis = Field(default=None, init=False, description="Redis client")
    redis_key: str = Field(default="p2p_nodes", description="Redis key for storing nodes")

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        """Initialize the service"""
        super().__init__(**data)
        self.redis_client = redis.Redis(host=self.redis_host, port=self.redis_port, db=self.redis_db)
        self.redis_key = "p2p_nodes"

    async def _load_nodes_from_storage(self) -> List[Node]:
        """
        Load nodes from the Redis storage.

        :return List[Node]: A list of nodes currently in the network.
        """
        nodes_json = await asyncio.to_thread(self.redis_client.get, self.redis_key)
        if isinstance(nodes_json, str):
            nodes_data = json.loads(nodes_json)
            return [Node(**node_data) for node_data in nodes_data]
        return []

    async def _save_nodes_to_storage(self, nodes: List[Node]) -> None:
        """
        Save nodes to the Redis storage.

        :param List[Node] nodes: The current list of nodes.
        """
        nodes_data = [node.model_dump() for node in nodes]
        await asyncio.to_thread(self.redis_client.set, self.redis_key, json.dumps(nodes_data))

    async def add_node(self, node: Node) -> None:
        """
        Add a node to the network.

        :param Node node: The node to add to the network.
        """
        nodes = await self._load_nodes_from_storage()
        nodes.append(node)
        await self._save_nodes_to_storage(nodes)

    async def remove_node(self, node: Node) -> None:
        """
        Remove a node from the network.

        :param Node node: The node to remove from the network.
        """
        nodes = await self._load_nodes_from_storage()
        nodes = [n for n in nodes if not (n.public_ip == node.public_ip and n.public_port == node.public_port)]
        await self._save_nodes_to_storage(nodes)

    async def list_nodes(self) -> List[Node]:
        """
        List all nodes in the network.

        :return List[Node]: A list of nodes currently in the network.
        """
        return await self._load_nodes_from_storage()
