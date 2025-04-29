from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from fungi.models.node import Node
import logging
from fungi.utils.constants import config
from fastapi import HTTPException


class NetworkService:
    """
    Signaling server for managing P2P network nodes in SQLite using SQLModel.
    """

    def __init__(self) -> None:
        """
        Initialize the NetworkService and connect to SQLite.
        """
        self.engine = create_async_engine(config.sqlite_db_url, echo=False, future=True)
        self._logger = logging.getLogger("P2P_Server")

    async def init_db(self) -> None:
        """
        Initialize the database and create tables if they do not exist.
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        self._logger.info("✅ SQLite DB initialized and tables created.")

    async def add_node(self, node: Node) -> Node:
        """
        Add a node to the network.

        :param Node node: The node to add.
        """
        async with AsyncSession(self.engine) as session:
            session.add(node)
            await session.commit()
            await session.refresh(node)
        self._logger.info(f"✅ Node added: {node.public_ip}:{node.public_port}")
        return node

    async def remove_node(self, node: Node) -> None:
        """
        Remove a node from the network.

        :param Node node: The node to remove.
        :raises HTTPException 404: If the node does not exist.
        """
        async with AsyncSession(self.engine) as session:
            statement = select(Node).where(
                Node.public_ip == node.public_ip, Node.public_port == node.public_port
            )
            result = await session.exec(statement)
            db_node = result.first()
            if db_node:
                await session.delete(db_node)
                await session.commit()
                self._logger.info(
                    f"❎ Node removed: {node.public_ip}:{node.public_port}"
                )
            else:
                self._logger.warning(
                    f"❎ Node not found: {node.public_ip}:{node.public_port}"
                )
                raise HTTPException(status_code=404, detail="Node not found")

    async def list_nodes(self) -> list[Node]:
        """
        List all nodes in the network.

        :return list[Node]: A list of all nodes in the network.
        """
        async with AsyncSession(self.engine) as session:
            statement = select(Node)
            result = await session.exec(statement)
            nodes = result.all()
        return nodes

    async def update_node(self, node: Node) -> None:
        """
        Update node information in the SQLite DB.

        :param Node node: The node to update.
        :raises HTTPException 404: If the node does not exist.
        """
        async with AsyncSession(self.engine) as session:
            statement = select(Node).where(
                Node.public_ip == node.public_ip, Node.public_port == node.public_port
            )
            result = await session.exec(statement)
            db_node = result.first()
            if db_node:
                db_node.local_ip = node.local_ip
                db_node.local_port = node.local_port
                db_node.nat_type = node.nat_type
                await session.commit()
                self._logger.info(
                    f"💡 Node updated: {node.public_ip}:{node.public_port}"
                )
            else:
                self._logger.warning(
                    f"❎ Node not found for update: {node.public_ip}:{node.public_port}"
                )
                raise HTTPException(status_code=404, detail="Node not found")
