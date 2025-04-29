from asyncio import get_running_loop
from fungi.utils.logger import get_logger
from fungi.models.nat_type import NatType
from fungi.models.discovery import DiscoveryResult
from stun import get_nat_type


class NATDetector:
    """
    Detects the NAT type and discovers the public IP and port using a STUN server.
    """

    def __init__(
        self,
        stun_host: str = "stun.l.google.com",
        stun_port: int = 19302,
    ) -> None:
        """
        Initialize the NATDetector.

        :param str stun_host: The STUN server host.
        :param int stun_port: The STUN server port.
        """
        self.stun_host = stun_host
        self.stun_port = stun_port
        self._logger = get_logger("NATDetector")

    async def detect(self, local_port: int = 54320) -> DiscoveryResult:
        """
        Detect the NAT type and discover the public IP and port.

        :param int local_port: The local port to use for the STUN request.
        :return DiscoveryResult: The result of the NAT discovery operation.
        :raises RuntimeError: If detection fails or NAT type is not supported.
        """
        loop = get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: get_nat_type(
                self.stun_host,
                self.stun_port,
                source_port=local_port,
            ),
        )
        nat_type, external_ip, external_port = result
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
