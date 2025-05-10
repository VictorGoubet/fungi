import asyncio
import socket
from fungi.utils.logger import get_logger
from fungi.models.node import NatType
from fungi.models.discovery import DiscoveryResult
import stun


class NATDetector:
    """
    Finds your public IP, port, and NAT type using a STUN server.
    """

    def __init__(
        self,
        stun_host: str = "stun.l.google.com",
        stun_port: int = 19302,
    ) -> None:
        """
        Set up the NAT detector with a STUN server.
        :param str stun_host: The STUN server host.
        :param int stun_port: The STUN server port.
        """
        self.stun_host = stun_host
        self.stun_port = stun_port
        self._logger = get_logger("NATDetector")

    def _get_nat_info(self, local_port: int) -> tuple[str, str, int]:
        """
        Uses pystun3 to get NAT type, public IP, and port.
        :param int local_port: The local port to use for the STUN request.
        :return tuple[str, str, int]: NAT type, public IP, public port.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("0.0.0.0", local_port))
        try:
            nat_type, result = stun.get_nat_type(
                s,
                "0.0.0.0",
                local_port,
                self.stun_host,
                self.stun_port
            )
            external_ip = result.get("ExternalIP")
            external_port = result.get("ExternalPort")
        finally:
            s.close()
        return nat_type, external_ip, external_port

    async def detect(self, local_port: int = 54320) -> DiscoveryResult:
        """
        Runs NAT detection and returns the result. Raises if unsupported NAT.
        :param int local_port: The local port to use for the STUN request.
        :return DiscoveryResult: The result of the NAT discovery operation.
        :raises RuntimeError: If detection fails or NAT type is not supported.
        """
        loop = asyncio.get_running_loop()
        nat_type, external_ip, external_port = await loop.run_in_executor(
            None,
            lambda: self._get_nat_info(local_port)
        )
        self._logger.info(
            f" 💡 NAT type: {nat_type}, Public IP: {external_ip}, Public Port: {external_port}"
        )
        if nat_type not in {
            NatType.FULL_CONE,
            NatType.RESTRICTED_CONE,
            NatType.PORT_RESTRICTED_CONE,
        }:
            self._logger.error(f" ❌ Unsupported NAT type: {nat_type}")
            raise RuntimeError(f"Unsupported NAT type: {nat_type}")
        return DiscoveryResult(
            nat_type=NatType(nat_type),
            public_ip=external_ip,
            public_port=external_port,
        )
 