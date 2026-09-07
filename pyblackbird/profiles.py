"""Protocol profiles for Monoprice Blackbird matrices."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BlackbirdProfile:
    """Defines the routable input and output range of a matrix model."""

    name: str
    sources: int
    zones: int

    def validate_source(self, source: int) -> int:
        """Validate a one-based source identifier."""
        if not 1 <= source <= self.sources:
            raise ValueError(f"source must be between 1 and {self.sources}")
        return source

    def validate_zone(self, zone: int) -> int:
        """Validate a one-based zone identifier."""
        if not 1 <= zone <= self.zones:
            raise ValueError(f"zone must be between 1 and {self.zones}")
        return zone


BLACKBIRD_8X8 = BlackbirdProfile("8x8", sources=8, zones=8)
BLACKBIRD_4X4 = BlackbirdProfile("4x4", sources=4, zones=4)
