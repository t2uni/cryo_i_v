"""Control and measurement of cryostat temperature."""

from PyQt5.QtCore import QMutex, QThread, pyqtSignal
import math
from threading import Event
import time
from typing import Optional


class TempControl(QThread):
    """Controls temperature and sends signals when target is reached.

    Attributes:
        _target_temp  Currently targeted temperature in Kelvins.
        _target_temp_mutex
        _should_run_event
    Properties:
        target_temp
    """

    min_temp = 0.0  # type: float
    max_temp = 400  # type: float
    temp_tolerance = 5.0  # type: float  # Absolute tolerance when comparing temperatures
    measure_interval_secs = 30  # type: int

    temp_delta_stable = 2.0  # type: float  # Threshold of temperature fluctuation when stablising,
    # ... below which temperature is considered stable.
    stabilise_interval_secs = 5  # type: int
    stabilise_count = 10  # type: int  # Amount of cycles during which temperaure fluctuation must
    # ... remain below 'temp_delta_stable', before temperature is considered stable.
    
    def __init__(self, should_run_event: Event, target_temp: float) -> None:
        # TODO: Initialise GPIB temperature controller.
        self._should_run = should_run_event
        self._target_temp = target_temp  # type: float
        self._target_temp_mutex = QMutex()

    @property
    def target_temp(self) -> float:
        """Return target temperature in kelvins."""
        self._target_temp_mutex.lock()
        value = self._target_temp  # type: float
        self._target_temp_mutex.unlock()
        return value

    @target_temp.setter
    def target_temp(self, value: float) -> None:
        assert self.min_temp <= value <= self.max_temp
        self._target_temp_mutex.lock()
        self._target_temp = value
        self._target_temp_mutex.unlock()

    def run(self) -> None:
        """Periodically check temperature, control it and signal target events.

        Override of QThread's 'run'.
        """

        def _stablilize_temp() -> None:
            """Wait until temperature is stablilised."""
            stable_cycles = 0  # type: int
            previous_temp = self._read_temp()  # type: float

            while stable_cycles < self.stabilise_count:
                time.sleep(self.stabilise_interval_secs)

                current_temp = self._read_temp()  # type: float
                temp_delta = current_temp - previous_temp  # type: float
                if abs(temp_delta) < self.temp_delta_stable:
                    stable_cycles += 1
                else:
                    stable_cycles = 0

                previous_temp = current_temp


        while self._should_run.is_set():
            # Is temperature in target range?
            if math.isclose(self._read_temp(), self.target_temp):
                _stablilize_temp()
                self.temperature_reached.emit(self._read_temp())

            self._write_target_temp()

            time.sleep(self.measure_interval_secs)

    def _read_temp(self) -> float:
        """Return kelvins read from GPIB device."""
        raise NotImplementedError()

    def _write_target_temp(self) -> None:
        """Write present target_temp to controller over GPIB."""
        raise NotImplementedError()

    # Arguments: current temperature
    temperature_reached = pyqtSignal(float)
