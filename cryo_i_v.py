"""Measure current-voltage characteristics in the cryostat."""

from easy2point.i_v_measurement import MeasureGPIB
from easy2point.easy2probe import MeasureWrapper
from easy2point.MainWindow import Mode
import math
from temp_control import TempControl
from threading import Event


class Constants:
    """Constants for this module."""

    INITIAL_TARGET_TEMP = 100.0  # type: float
    FINAL_TARGET_TEMP = 5.0  # type: float
    TEMP_STEP_WIDTH = 10.0  # type: float

def measure_i_v_once(temp_measured: float, temp_ctrl: TempControl,
                     temp_ctrl_should_run: Event, log_file_path: str,
                     comment: str, max_voltage: float, current_limit: float,
                     number_iterations: int) -> None:
    # Terminate temperature control when final temperature is reached:
    if math.isclose(Constants.FINAL_TARGET_TEMP,
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
        temp_ctrl.target_temp += Constants.TEMP_STEP_WIDTH
    

def main() -> None:
    # Start the temperature thread:
    temp_ctrl_should_run = Event()
    temp_ctrl_should_run.set()
    temp_ctrl = TempControl(temp_ctrl_should_run, Constants.INITIAL_TARGET_TEMP)

    temp_ctrl.temperature_reached.connect(
        lambda temp_measured: measure_i_v_once(temp_ctrl, temp_ctrl_should_run,
                                               temp_ctrl_should_run)
    )

    temp_ctrl.start()
    temp_ctrl.join()


if __name__ == "__main__":
    main()
