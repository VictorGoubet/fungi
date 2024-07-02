import json
from typing import List

from fastapi import FastAPI, HTTPException
from node import Node
from pydantic import ValidationError
from service import NetworkService

app = FastAPI(
    title="P2P Network API",
    description="API for managing nodes in a P2P network",
    version="1.0.0",
    contact={
        "name": "Victor Goubet",
        "email": "victorgoubet@orange.fr",
    },
)

network_service = NetworkService()


@app.get(
    "/nodes",
    response_model=List[Node],
    responses={
        200: {
            "description": "A list of nodes currently in the network",
            "content": {
                "application/json": {
                    "example": [
                        {"public_ip": "192.168.1.1", "public_port": 8080},
                        {"public_ip": "192.168.1.2", "public_port": 9090},
                    ]
                }
            },
        }
    },
)
async def get_nodes() -> List[Node]:
    """Get the list of nodes in the network"""
    return await network_service.list_nodes()


@app.post(
    "/nodes",
    response_model=Node,
    status_code=201,
    responses={
        201: {
            "description": "The added node",
            "content": {"application/json": {"example": {"public_ip": "192.168.1.1", "public_port": 8080}}},
        },
        400: {
            "description": "Invalid request data",
            "content": {"application/json": {"example": {"detail": "Invalid request data"}}},
        },
    },
)
async def add_node(node: Node) -> Node:
    """Add a new node to the network"""
    try:
        await network_service.add_node(node)
        return node
    except (ValidationError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete(
    "/nodes",
    status_code=204,
    responses={
        204: {
            "description": "Node removed",
        },
        400: {
            "description": "Invalid request data",
            "content": {"application/json": {"example": {"detail": "Invalid request data"}}},
        },
    },
)
async def remove_node(node: Node) -> None:
    """Remove a node from the network"""
    try:
        await network_service.remove_node(node)
    except (ValidationError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
