#!/usr/bin/env python3
from time import sleep

from tabulate import tabulate

from presenter_drivers.sensors.CCKIR import CCKIR
from presenter_drivers.sensors.ir import MinMax as MinMaxCalibrator

cckir = CCKIR({})
calibrator = MinMaxCalibrator({"sensors": cckir.get_sensors()})
data = []

for i in range(5):
    calibrator.start()
    sleep(10)
    results = calibrator.stop()
    data.extend(
        [
            (
                (i + 1),
                CCKIR.Sensor(sensor).name,
                v[0],
                v[1],
                f"{((abs(v[0] - v[1]) / ((v[0] + v[1]) / 2)) * 100):.2f}%",
                (v[1] - v[0]),
            )
            for sensor, v in enumerate(results)
        ]
    )
    data.extend([[""] * 6])
    sleep(2)

print(tabulate(data, headers=["Run", "Name", "Min", "Max", "% Diff", "Diff"]))
