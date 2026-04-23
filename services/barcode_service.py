"""
services/barcode_service.py
 
Manages a single background thread that listens on the barcode scanner's
serial port. Other parts of the app (tabs) register callbacks to be notified
when a barcode is scanned.
 
Usage:
    # Start listening
    BarcodeService.start()
 
    # Register a callback — called with the barcode string when scanned
    BarcodeService.register(my_callback)
 
    # Unregister when no longer needed
    BarcodeService.unregister(my_callback)
 
    # Stop the listener
    BarcodeService.stop()
"""
 
import threading
import serial
import serial.tools.list_ports
from typing import Callable
 
# Configure listener for the Barcode
SERIAL_PORT = "COM9"
BAUD_RATE = 9600
 
 
class BarcodeService:
    _thread: threading.Thread = None
    _running: bool = False
    _serial: serial.Serial = None
    _callbacks: list[Callable] = []
    _lock = threading.Lock()
 
    # Whether the scanner is currently connected and working
    _connected: bool = False
    _status_callbacks: list[Callable] = []
 
    # ── Public API ────────────────────────────────────────────────────────────
 
    @classmethod
    def start(cls):
        """
        Start the background listener thread.
        Safe to call multiple times — does nothing if already running.
        """
        if cls._running:
            return
        cls._running = True
        cls._thread = threading.Thread(target=cls._listen, daemon=True)
        cls._thread.start()
 
    @classmethod
    def stop(cls):
        """Stop the background listener thread and close the serial port."""
        cls._running = False
        if cls._serial and cls._serial.is_open:
            cls._serial.close()
 
    @classmethod
    def register(cls, callback: Callable[[str], None]):
        """
        Register a callback to be called when a barcode is scanned.
        The callback receives the barcode string as its only argument.
        """
        with cls._lock:
            if callback not in cls._callbacks:
                cls._callbacks.append(callback)
 
    @classmethod
    def unregister(cls, callback: Callable[[str], None]):
        """Remove a previously registered callback."""
        with cls._lock:
            if callback in cls._callbacks:
                cls._callbacks.remove(callback)
 
    @classmethod
    def register_status(cls, callback: Callable[[bool], None]):
        """
        Register a callback to be notified when the scanner connects or disconnects.
        The callback receives True (connected) or False (disconnected).
        """
        with cls._lock:
            if callback not in cls._status_callbacks:
                cls._status_callbacks.append(callback)
        # Immediately notify with current status
        callback(cls._connected)
 
    @classmethod
    def unregister_status(cls, callback: Callable[[bool], None]):
        """Remove a previously registered status callback."""
        with cls._lock:
            if callback in cls._status_callbacks:
                cls._status_callbacks.remove(callback)
 
    @classmethod
    def is_connected(cls) -> bool:
        """Returns True if the scanner is currently connected."""
        return cls._connected
 
    # ── Internal listener ─────────────────────────────────────────────────────
 
    @classmethod
    def _listen(cls):
        """
        Background thread that continuously reads from the serial port.
        Automatically reconnects if the scanner is unplugged and plugged back in.
        """
        while cls._running:
            try:
                # Try to open the serial port
                cls._serial = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                cls._set_connected(True)
 
                # Read barcodes until the port closes or we stop
                while cls._running and cls._serial.is_open:
                    raw = cls._serial.readline().decode(errors="ignore").strip()
 
                    if not raw:
                        continue
 
                    # Strip everything except digits
                    barcode = "".join(filter(str.isdigit, raw))
 
                    if barcode:
                        cls._notify(barcode)
 
            except serial.SerialException:
                # Scanner disconnected or port not available
                cls._set_connected(False)
                # Wait before retrying so we don't spam reconnect attempts
                threading.Event().wait(timeout=3)
 
            finally:
                if cls._serial and cls._serial.is_open:
                    cls._serial.close()
                cls._set_connected(False)
 
    @classmethod
    def _notify(cls, barcode: str):
        """Call all registered callbacks with the scanned barcode."""
        with cls._lock:
            callbacks = list(cls._callbacks)
        for callback in callbacks:
            try:
                callback(barcode)
            except Exception as e:
                print(f"BarcodeService callback error: {e}")
 
    @classmethod
    def _set_connected(cls, connected: bool):
        """Update connection status and notify status callbacks."""
        if cls._connected == connected:
            return
        cls._connected = connected
        with cls._lock:
            callbacks = list(cls._status_callbacks)
        for callback in callbacks:
            try:
                callback(connected)
            except Exception as e:
                print(f"BarcodeService status callback error: {e}")