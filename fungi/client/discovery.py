from fungi.client.nat import NATDetector
from fungi.models.discovery import DiscoveryResult
from fungi.utils.logger import get_logger


class DiscoveryService:
    """
    Service to discover public IP, port, and NAT type using NATDetector.
    """

    def __init__(
        self,
        stun_host: str = "stun.l.google.com",
        stun_port: int = 19302,
    ) -> None:
        """
        Initialize the DiscoveryService.

        :param str stun_host: The STUN server host.
        :param int stun_port: The STUN server port.
        """
        self._nat_detector = NATDetector(stun_host, stun_port)
        self._logger = get_logger("DiscoveryService")

    async def discover(self, local_port: int = 54320) -> DiscoveryResult:
        """
        Discover the public IP, port, and NAT type.

        :param int local_port: The local port to use for the STUN request.
        :return DiscoveryResult: The result of the NAT discovery operation.
        :raises RuntimeError: If discovery fails or NAT type is not supported.
        """
        self._logger.info(" 💡 Starting discovery of public IP, port, and NAT type...")
        return await self._nat_detector.detect(local_port)
