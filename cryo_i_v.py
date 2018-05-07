"""Measure current-voltage characteristics in the cryostat."""

from configparser import ConfigParser
from easy2point.i_v_measurement import MeasureGPIB
from easy2point.MainWindow import MainWindow
Mode = MainWindow.Mode
import math
import os
from temp_control import TempControl
from threading import Event


def _load_configuration(config_file: str) -> ConfigParser:
    """Load user configuration from a file."""
    if not os.path.isfile(config_file):
        raise FileNotFoundError("Config file {} not found.".format(config_file))

    config = ConfigParser()
    config.read(config_file)
    return config["temp_ctrl"]

TEMP_CONFIG = _load_configuration("cryo_i_v.conf")


def measure_i_v_once(temp_measured: float, temp_ctrl: TempControl,
                     temp_ctrl_should_run: Event, log_file_path: str,
                     comment: str, max_voltage: float, current_limit: float,
                     number_iterations: int) -> None:
    # Terminate temperature control when final temperature is reached:
    if math.isclose(TEMP_CONFIG["FINAL_TARGET_TEMP"],
                    temp_measured,
                    abs_tol=TempControl.temp_tolerance):
        temp_ctrl_should_run.clear()

    measurement_should_run = Event()
    measurement_should_run.set()
    # TODO: allow aborting the measurement, e.g. on CTRL-C
    
    i_v_measurement = MeasureGPIB(measurement_should_run, log_file_path, comment,
                                  max_voltage, current_limit, number_iterations,
                                  ("", ""), ("", ""), Mode.FOUR_WIRE, None)
    i_v_measurement.run()

    # Set next target temperature for controller:
    if temp_ctrl_should_run.is_set():
        temp_ctrl.target_temp += TEMP_CONFIG["TEMP_STEP_WIDTH"]


def main() -> None:
    # Start the temperature thread:
    temp_ctrl_should_run = Event()
    temp_ctrl_should_run.set()
    temp_ctrl = TempControl(temp_ctrl_should_run, TEMP_CONFIG["INITIAL_TARGET_TEMP"])

    temp_ctrl.temperature_reached.connect(
        lambda temp_measured: measure_i_v_once(temp_ctrl, temp_ctrl_should_run,
                                               temp_ctrl_should_run)
    )

    temp_ctrl.start()
    temp_ctrl.join()


if __name__ == "__main__":
    main()
