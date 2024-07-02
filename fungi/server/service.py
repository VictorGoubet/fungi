import asyncio
import json
import os
from typing import List

import redis
from node import Node
from pydantic import BaseModel, Field


class NetworkService(BaseModel):
    """Signaling server"""

    redis_host: str = Field(default=os.environ["REDIS_HOST"], description="Redis host")
    redis_port: int = Field(default=os.environ["REDIS_PORT"], description="Redis port")
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

    async def _add_node_to_storage(self, node: Node) -> None:
        """
        Add a node to the Redis storage.

        :param Node node: The node to add.
        """
        node_key = f"{node.public_ip}:{node.public_port}"
        node_data = node.model_dump()
        await asyncio.to_thread(self.redis_client.hset, self.redis_key, node_key, json.dumps(node_data))

    async def _remove_node_from_storage(self, node: Node) -> None:
        """
        Remove a node from the Redis storage.

        :param Node node: The node to remove.
        """
        node_key = f"{node.public_ip}:{node.public_port}"
        await asyncio.to_thread(self.redis_client.hdel, self.redis_key, node_key)

    async def _load_nodes_from_storage(self) -> List[Node]:
        """
        Load nodes from the Redis storage.

        :return List[Node]: A list of nodes currently in the network.
        """
        nodes_data = await asyncio.to_thread(self.redis_client.hgetall, self.redis_key)
        nodes = [Node(**json.loads(node_data)) for node_data in nodes_data.values()]
        return nodes

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
