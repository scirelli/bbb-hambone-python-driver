#!/usr/bin/env python3
from collections import defaultdict
from logging import Logger
from time import sleep
from typing import Any, Tuple, cast

from tabulate import tabulate

from demo.motor import runMotorDemo
from demo.neopixel import runNeoPixelDemo
from hambone.logger.logger import create_logger
from hambone.neopixel import writer
from hambone.neopixel.NeoPixelPRU import NeoPixelPRU
from hambone.sensors.CCKIR import CCKIR
from hambone.sensors.ir import MinMax

TWO_SECONDS = 2
FIVE_SECONDS = 5
TEN_SECONDS = 10
TOTAL_FLASH_TIME = TEN_SECONDS
TOTAL_ANIMATION_TIME = TEN_SECONDS

DEFAULT_CONFIG = {
    "cckConfig": {
        "displayConfig": {
            "neoPixelConfig": {
                "ledCount": 42,
                "writerConfig": {
                    "type": "PRUDeviceWriter",
                    "config": {
                        "_fileName": "/dev/rpmsg_pru30",
                        "fileName": "/tmp/rpmsg_pru30.txt",
                        "fileMode": "a",
                    },
                },
                "writer": None,
            },
        },
        "pawConfig": {
            "motorConfig": {
                "motorIN1Pin": "P8_7",
                "motorIN2Pin": "P8_9",
            },
            "motorLimitsConfig": {
                "frontLimitSwitchPin": "P8_12",
                "rearLimitSwitchPin": "P8_10",
            },
        },
        "irConfig": {
            "foreground": [0, 128, 0],
            "background": [128, 0, 0],
            "link": [0xB7, 0xD7, 0x00],
            "neoPixelConfig": {
                "ledCount": 42,
                "writerConfig": {
                    "type": "PRUDeviceWriter",
                    "config": {
                        "_fileName": "/dev/rpmsg_pru30",
                        "fileName": "/tmp/rpmsg_pru30.txt",
                        "fileMode": "a",
                    },
                },
                "writer": None,
            },
        },
    },
    "demo": {"which": "all"},
}

logger = create_logger("HAMBoneDemo")


def main(config: dict[str, Any]) -> None:
    config = defaultdict(
        dict, {**DEFAULT_CONFIG, **config}
    )  # Need to fix this for nesting
    logger.info("\n\nConfig: %s\n\n", config)

    demoConfig = config.get("demo", {})
    cckConfig = config.get("cckConfig", {})
    cckConfig["pawConfig"]["logger"] = logger
    cckConfig["displayConfig"]["logger"] = logger
    cckConfig["irConfig"]["logger"] = logger

    match demoConfig.get("which", "all"):
        case "display":
            logger.info("Running display dmeo only")
            runNeoPixelDemo(cckConfig["displayConfig"]["neoPixelConfig"])
        case "motor":
            logger.info("Running motor dmeo only")
            runMotorDemo(cckConfig["pawConfig"])
        case "ir":
            logger.info("Running IR demo only")
            irDemo(cckConfig["irConfig"])
        case _:
            logger.info("Running all dmeos")
            runNeoPixelDemo(cckConfig["displayConfig"])
            runMotorDemo(cckConfig["pawConfig"])
            irDemo(cckConfig["irConfig"])


def irDemo(config: dict[str, Any]) -> None:  # pylint: disable = too-many-locals
    log: Logger = create_logger("IRDemo")

    # Add a logger instance and the writer instance to the CCKDisplay config
    config["logger"] = log
    neoPixelConfig = config["neoPixelConfig"]
    neoPixelConfig["logger"] = log
    writerConfig = neoPixelConfig.get("writerConfig", {})
    neoPixelConfig["writerConfig"] = writerConfig
    fg_color = config.get("foreground", [0, 128, 0])
    bg_color = config.get("background", [128, 0, 0])
    link_color = config.get("link", [0xB7, 0xD7, 0x00])

    wr = writer.__dict__[writerConfig.get("type", "STDOutWriter")](
        writerConfig.get("config", {}).get("fileName", "")
    )

    lights = [
        16,  # LEFT_FRONT
        6,  # LEFT_MIDDLE
        0,  # LEFT_REAR
        21,  # RIGHT_FRONT, 41
        11,  # RIGHT_MIDDLE, 15
        5,  # RIGHT_REAR, 5
    ]

    with wr as f:
        neoPixelConfig["writer"] = f
        neopixel_controller: NeoPixelPRU = NeoPixelPRU(
            cast(NeoPixelPRU.Config, neoPixelConfig)
        )
        cckIR = CCKIR(cast(CCKIR.Config, config))
        calibrator = MinMax({"sensors": cckIR.get_sensors()})

        input(
            "\n\nPress enter when ready to calibrate. Remember to move paper around.\n"
        )
        minMaxes = _ir_demo_calibration(calibrator, neopixel_controller)
        log.debug("\n%s\n\n", _ir_calibration_results_to_string(minMaxes))
        # At least 10% greater than mid point to turn on.
        onThresholds = [
            (z[0] + (z[1][1] - z[0]) * 0.1)
            for z in zip(
                [v[0] + ((v[1] - v[0]) / 2) for v in minMaxes],
                minMaxes,
            )
        ]
        input("\n\nCalibration complete. Press a key to run demo.\n\n")
        print("Demo engaged\n")
        print("Press ctrl+c to exit IR demo.")

        try:
            while True:
                for values in [
                    cckIR.read_front(),
                    cckIR.read_middle(),
                    cckIR.read_rear(),
                ]:
                    _ir_demo_light_link(
                        values, lights, onThresholds, neopixel_controller, link_color
                    )

                for sensor in CCKIR.Sensor:
                    if cckIR.read_sensor(sensor) > onThresholds[sensor.value]:
                        # log.info("Under %s", sensor.name)
                        neopixel_controller.set_color_buffer(
                            lights[sensor.value], *fg_color
                        )
                    else:
                        neopixel_controller.set_color_buffer(
                            lights[sensor.value], *bg_color
                        )

                neopixel_controller.draw()
        except KeyboardInterrupt:
            pass
        neopixel_controller.clear()


def _ir_demo_light_link(
    values: CCKIR.SensorPair,
    lights: list[int],
    onThresholds: list[float],
    neopixel_controller: NeoPixelPRU,
    link_color: list[int],
) -> None:
    left, right = values.keys()
    if (
        values[left] > onThresholds[left.value]
        and values[right] > onThresholds[right.value]
    ):
        for x in range(lights[left.value], lights[right.value] + 1):
            neopixel_controller.set_color_buffer(x, *link_color)
    else:
        for x in range(lights[left.value], lights[right.value] + 1):
            neopixel_controller.set_color_buffer(x, 0, 0, 0)


def _ir_demo_calibration(
    calibrator: MinMax, neopixel_controller: NeoPixelPRU
) -> Tuple[Tuple[int, int], ...]:
    for i in range(21):
        neopixel_controller.set_color_buffer(i + 16, 0, 128, 0)
    neopixel_controller.draw()

    calibrator.start()
    for i in range(20, -1, -1):
        sleep(1)
        neopixel_controller.set_color(i + 16, 0, 0, 0)
    neopixel_controller.clear()
    return calibrator.stop()


def _ir_calibration_results_to_string(results: Tuple[Tuple[int, int], ...]) -> str:
    data = [
        (
            CCKIR.Sensor(sensor).name,
            v[0],
            v[0] + ((v[1] - v[0]) / 2),
            v[1],
            f"{((abs(v[0] - v[1]) / ((v[0] + v[1]) / 2)) * 100):.2f}%",
            (v[1] - v[0]),
        )
        for sensor, v in enumerate(results)
    ]

    return tabulate(data, headers=["Name", "Min", "Mid", "Max", "% Diff", "Diff"])


if __name__ == "__main__":
    import argparse
    from json import decoder, load
    from sys import stdin

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config",
        default=stdin,
        type=argparse.FileType("r"),
        nargs="?",
        help="The config file.",
    )

    args = parser.parse_args()

    try:
        main(load(args.config))
    except decoder.JSONDecodeError:
        logger.warning("Unable to parse config file.")