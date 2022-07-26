from __future__ import annotations

from enum import Enum
from logging import Logger

from typing_extensions import TypedDict

from ..gpio import GPIO
from ..logger.logger import create_logger
from ..singleton import AdaGPIOSingleton  # type: ignore

# Default Pins
FRONT_LIMIT_SWITCH_PIN = "P8_12"
REAR_LIMIT_SWITCH_PIN = "P8_10"
MOTOR_IN1_PIN = "P8_7"  # Drive backward (toward BBB)
MOTOR_IN2_PIN = "P8_9"  # Drive forward (away from BBB)

DEFAULT_LOGGER = create_logger("MotorDriver")


class MotorDriver(metaclass=AdaGPIOSingleton):
    class State(Enum):
        STOP = 0
        FORWARD = 1
        BACKWARD = 2
        BREAK = 3

    class Config(TypedDict, total=False):
        motorIN1Pin: str
        motorIN2Pin: str

    def __init__(self, config: MotorDriver.Config):
        self._motor_in1_pin: str = config.get("motorIN1Pin", MOTOR_IN1_PIN)
        self._motor_in2_pin: str = config.get("motorIN2Pin", MOTOR_IN2_PIN)
        self._state: MotorDriver.State = MotorDriver.State.STOP
        self._gpio_setup()

    def _gpio_setup(self) -> None:
        GPIO.setup(self._motor_in1_pin, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self._motor_in2_pin, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN)
        self.stop()

    def forward(self) -> None:
        self.set_state(MotorDriver.State.FORWARD)

    def backward(self) -> None:
        self.set_state(MotorDriver.State.BACKWARD)

    def stop(self) -> None:
        self.set_state(MotorDriver.State.STOP)

    def get_state(self) -> MotorDriver.State:
        return self._state

    def set_state(self, s: MotorDriver.State) -> None:
        if s == MotorDriver.State.FORWARD:
            GPIO.output(self._motor_in1_pin, GPIO.LOW)
            GPIO.output(self._motor_in2_pin, GPIO.HIGH)
            self._state = MotorDriver.State.FORWARD
        elif s == MotorDriver.State.BACKWARD:
            GPIO.output(self._motor_in2_pin, GPIO.LOW)
            GPIO.output(self._motor_in1_pin, GPIO.HIGH)
            self._state = MotorDriver.State.BACKWARD
        elif s == MotorDriver.State.BREAK:
            GPIO.output(self._motor_in2_pin, GPIO.HIGH)
            GPIO.output(self._motor_in1_pin, GPIO.HIGH)
            self._state = MotorDriver.State.BREAK
        else:
            GPIO.output(self._motor_in2_pin, GPIO.LOW)
            GPIO.output(self._motor_in1_pin, GPIO.LOW)
            self._state = MotorDriver.State.STOP


class MotorLimits(metaclass=AdaGPIOSingleton):
    class Config(TypedDict, total=False):
        logger: Logger
        frontLimitSwitchPin: str
        rearLimitSwitchPin: str

    def __init__(self, config: MotorLimits.Config):
        self._logger: Logger = config.get("logger", DEFAULT_LOGGER)
        self._front_limit_switch_pin: str = config.get(
            "frontLimitSwitchPin", FRONT_LIMIT_SWITCH_PIN
        )
        self._rear_limit_switch_pin: str = config.get(
            "rearLimitSwitchPin", REAR_LIMIT_SWITCH_PIN
        )
        self._gpio_setup()

    def _gpio_setup(self) -> None:
        GPIO.setup(self._front_limit_switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self._rear_limit_switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def is_front_limit_pressed(self) -> bool:
        return not GPIO.input(self._front_limit_switch_pin)

    def is_rear_limit_pressed(self) -> bool:
        return not GPIO.input(self._rear_limit_switch_pin)
