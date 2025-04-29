from enum import Enum


class NatType(str, Enum):
    """
    Represents the type of NAT (Network Address Translation) a node is behind.
    """

    FULL_CONE = "Full Cone"
    RESTRICTED_CONE = "Restricted Cone"
    PORT_RESTRICTED_CONE = "Port Restricted Cone"
    SYMMETRIC = "Symmetric"
