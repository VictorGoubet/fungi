from pydantic_settings import BaseSettings
from pydantic import Field


class AppConfig(BaseSettings):
    """
    Application configuration for P2P client.
    """

    server_url: str = Field(
        "http://192.168.1.4:8000",
        description="URL of the signaling server",
    )
    stun_server_host: str = Field(
        "stun.l.google.com",
        description="STUN server hostname",
    )
    stun_server_port: int = Field(
        19302,
        description="STUN server port",
    )
    sqlite_db_url: str = Field(
        "sqlite+aiosqlite:///./nodes.db",
        description="SQLite database URL for node storage",
    )


# Singleton config instance
config = AppConfig()
