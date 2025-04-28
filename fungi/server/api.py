import json
from fastapi import FastAPI, HTTPException, Query
from fungi.models.node import Node
from pydantic import IPvAnyAddress, ValidationError
from fungi.server.service import NetworkService
from contextlib import asynccontextmanager
from sqlalchemy.exc import IntegrityError

network_service = NetworkService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await network_service.init_db()
    yield


app = FastAPI(
    title="P2P Network API",
    description="API for managing nodes in a P2P network",
    version="1.0.0",
    contact={
        "name": "Victor Goubet",
        "email": "victorgoubet@orange.fr",
    },
    lifespan=lifespan,
)


@app.get(
    "/nodes",
    tags=["nodes"],
    response_model=list[Node],
    responses={
        200: {
            "description": "A list of nodes currently in the network",
            "content": {"application/json": {"example": [Node.get_example()]}},
        }
    },
)
async def get_nodes() -> list[Node]:
    """
    Get the list of nodes in the network.
    """
    return await network_service.list_nodes()


@app.post(
    "/nodes",
    tags=["nodes"],
    response_model=Node,
    status_code=201,
    responses={
        201: {
            "description": "The added node",
            "content": {"application/json": {"example": Node.get_example()}},
        },
        400: {
            "description": "Invalid request data",
            "content": {
                "application/json": {"example": {"detail": "Invalid request data"}}
            },
        },
        409: {
            "description": "A node with this id already exists.",
            "content": {
                "application/json": {"example": {"detail": "A node with this id already exists."}}
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {"example": {"detail": "Internal server error"}}
            },
        },
    },
)
async def add_node(node: Node) -> Node:
    """
    Add a new node to the network.

    :param Node node: The node to add.
    :return Node: The added node.
    """
    try:
        await network_service.add_node(node)
        return node
    except IntegrityError:
        raise HTTPException(status_code=409, detail="A node with this id already exists.")
    except (ValidationError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete(
    "/nodes",
    tags=["nodes"],
    status_code=204,
    responses={
        204: {
            "description": "Node removed",
        },
        400: {
            "description": "Invalid request data",
            "content": {
                "application/json": {"example": {"detail": "Invalid request data"}}
            },
        },
        404: {
            "description": "Node not found",
            "content": {
                "application/json": {"example": {"detail": "Node not found"}}
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {"example": {"detail": "Internal server error"}}
            },
        },
    },
)
async def remove_node(
    public_ip: IPvAnyAddress = Query(...),
    public_port: int = Query(...),
) -> None:
    """
    Remove a node from the network.
    """
    node = Node(public_ip=public_ip, public_port=public_port)
    try:
        await network_service.remove_node(node)
    except (ValidationError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put(
    "/nodes",
    tags=["nodes"],
    status_code=200,
    responses={
        200: {
            "description": "Node information updated successfully",
            "content": {
                "application/json": {"example": {"message": "Node information updated"}}
            },
        },
        400: {
            "description": "Invalid request data",
            "content": {
                "application/json": {"example": {"detail": "Invalid request data"}}
            },
        },
        404: {
            "description": "Node not found",
            "content": {
                "application/json": {"example": {"detail": "Node not found"}}
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {"example": {"detail": "Internal server error"}}
            },
        },
    },
)
async def update_node(node: Node) -> dict[str, str]:
    """
    Update node information.
    """
    try:
        await network_service.update_node(node)
        return {"message": "Node information updated"}
    except (ValidationError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
