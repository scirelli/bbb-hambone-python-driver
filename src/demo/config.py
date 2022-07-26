from logging import Logger
from typing import List

from typing_extensions import TypedDict

from presenter_drivers.neopixel import writer


class WriterFileConfig(TypedDict, total=False):
    fileName: str
    fileMode: str


class WriterConfig(TypedDict, total=False):
    type: str
    config: WriterFileConfig


class NeoPixelPRUConfig(TypedDict, total=False):
    ledCount: int
    writerConfig: WriterConfig
    writer: writer.Writer
    logger: Logger


class CCKDisplayConfig(TypedDict, total=False):
    neoPixelPRUConfig: NeoPixelPRUConfig
    logger: Logger


class MotorConfig(TypedDict, total=False):
    motorIN1Pin: str
    motorIN2Pin: str


class MotorLimitsConfig(TypedDict, total=False):
    frontLimitSwitchPin: str
    rearLimitSwitchPin: str


class PawConfig(TypedDict, total=False):
    motorConfig: MotorConfig
    motorLimitsConfig: MotorLimitsConfig
    logger: Logger


class IRConfig(TypedDict, total=False):
    foreground: List[int]
    background: List[int]
    link: List[int]
    neoPixelPRUConfig: NeoPixelPRUConfig
    logger: Logger


class DoorConfig(TypedDict, total=False):
    doorSwitchPin: str
    foreground: List[int]
    background: List[int]
    neoPixelPRUConfig: NeoPixelPRUConfig
    logger: Logger


class CCKConfig(TypedDict, total=False):
    irConfig: IRConfig
    pawConfig: PawConfig
    cckDisplayConfig: CCKDisplayConfig
    doorConfig: DoorConfig
    logger: Logger


class Config(TypedDict, total=False):
    cckConfig: CCKConfig
