import asyncio
import os
from typing import Any, Awaitable, Dict, List

import redis
from node import Node
from pydantic import BaseModel, Field, PrivateAttr


class NetworkService(BaseModel):
    """Signaling server for managing P2P network nodes"""

    redis_host: str = Field(default=os.environ.get("REDIS_HOST", "localhost"), description="Redis host")
    redis_port: int = Field(default=int(os.environ.get("REDIS_PORT", 6379)), description="Redis port")
    redis_db: int = Field(default=0, description="Redis database index")
    _redis_client: redis.Redis = PrivateAttr(default=None)
    _redis_key: str = PrivateAttr(default="p2p_nodes")

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        """Initialize the service"""
        super().__init__(**data)
        self._redis_client = redis.Redis(host=self.redis_host, port=self.redis_port, db=self.redis_db)

    async def _add_node_to_storage(self, node: Node) -> None:
        """
        Add a node to the Redis storage.

        :param Node node: The node to add.
        """
        node_key = f"{node.public_ip}:{node.public_port}"
        node_data = node.model_dump_json()
        await asyncio.to_thread(self._redis_client.hset, self._redis_key, node_key, node_data)

    async def _remove_node_from_storage(self, node: Node) -> None:
        """
        Remove a node from the Redis storage.

        :param Node node: The node to remove.
        """
        node_key = f"{node.public_ip}:{node.public_port}"
        await asyncio.to_thread(self._redis_client.hdel, self._redis_key, node_key)

    async def _load_nodes_from_storage(self) -> List[Node]:
        """
        Load nodes from the Redis storage.

        :return List[Node]: A list of nodes currently in the network.
        """
        nodes_data: Awaitable[dict[Any, Any]] | Dict[Any, Any] = await asyncio.to_thread(
            self._redis_client.hgetall, self._redis_key
        )
        if isinstance(nodes_data, dict):
            return [Node.model_validate_json(node_data) for node_data in nodes_data.values()]
        return []

    async def add_node(self, node: Node) -> None:
        """
        Add a node to the network.

        :param Node node: The node to add to the network.
        """
        await self._add_node_to_storage(node)

    async def remove_node(self, node: Node) -> None:
        """
        Remove a node from the network.

        :param Node node: The node to remove from the network.
        """
        await self._remove_node_from_storage(node)

    async def list_nodes(self) -> List[Node]:
        """
        List all nodes in the network.

        :return List[Node]: A list of nodes currently in the network.
        """
        return await self._load_nodes_from_storage()
