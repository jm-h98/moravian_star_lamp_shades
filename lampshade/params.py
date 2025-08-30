import math
from dataclasses import dataclass

from .utils import clamp


@dataclass
class Params:
    # Mount assembly fixed dimensions
    mountCylinderOuterDiameter: float = 13.0
    mountCylinderHeight: float = 5.5
    transitionHeight: float = 15.0
    transitionWidth: float = 0.0
    overhangAngle: int = 30

    # Slider ranges
    topDiameterMin: int = 16
    topDiameterMax: int = 100
    middleDiameterMin: int = 30
    middleDiameterMax: int = 120
    bottomDiameterMin: int = 30
    bottomDiameterMax: int = 120
    overhangAngleMin: int = 30
    overhangAngleMax: int = 80
    cylinderHeightMin: int = 50
    cylinderHeightMax: int = 120
    featureCountMin: int = 1
    featureCountMax: int = 10
    detailMin: int = 25
    detailMax: int = 300
    featureDepthMin: float = 0.0
    featureDepthMax: float = 4.0

    # Main shape parameters
    topDiameter: int = 30
    middleDiameter: int = 70
    bottomDiameter: int = 60
    cylinderHeight: int = 80

    # Design parameters
    featureCount: int = 6
    featureDepth: float = 2.0

    # Design mode and interpolation
    designMode: int = 1      # 1..12 patterns, 0 = none
    interpolation: int = 0   # 0=bezier, 1=lagrange, 2=linear

    # Mesh detail
    detail: int = 120

    def update_transition(self) -> None:
        """Update transitional geometry (mount to main body) from current params."""
        self.transitionWidth = (self.topDiameter - self.mountCylinderOuterDiameter) / 2.0
        self.transitionHeight = max(0.0, self.transitionWidth) * math.tan(math.radians(self.overhangAngle))

    def update_feature_depth_max(self) -> None:
        """Limit feature depth to ensure it never inverts or pierces the mount cylinder."""
        outerRadius = self.mountCylinderOuterDiameter / 2.0
        smallestMainCylinderRadius = (
            min(
                self.topDiameter + self.transitionWidth,
                self.bottomDiameter,
                self.middleDiameter,
            )
            / 2.0
        )
        self.featureDepthMax = min(
            max(0.0, smallestMainCylinderRadius - outerRadius),
            self.featureDepthMax,
        )
        self.featureDepth = clamp(
            self.featureDepth,
            self.featureDepthMin,
            max(self.featureDepthMin, self.featureDepthMax),
        )

    def name(self) -> str:
        return "{}_{}_{}_{}_{}_{}_{}_{}".format(
            self.designMode,
            self.topDiameter,
            self.middleDiameter,
            self.bottomDiameter,
            self.cylinderHeight,
            self.featureCount,
            f"{self.featureDepth:.02f}",
            self.detail,
        )