from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails
import tinytuya
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)


class T2276TinyTuyaDevice:
    """Custom TinyTuya-based device for T2276 (X8 Pro SES)"""
    
    def __init__(self, model_details, device_id: str, host: str, timeout: float, ping_interval: float, update_entity_state, local_key: str = None, port: int = 6668, gateway_id: str = None, version: tuple = (3, 5), **kwargs):
        """Initialize the TinyTuya device"""
        self.device_id = device_id
        self.host = host
        self.local_key = local_key
        self.state = {}
        self._dps = {}  # Add _dps attribute for compatibility
        self.model_details = model_details
        self.version = version
        
        # Create TinyTuya device
        self._tinytuya_device = tinytuya.OutletDevice(device_id, host, local_key)
        self._tinytuya_device.set_version(3.5)
        
    async def async_get(self) -> None:
        """Get device status using TinyTuya"""
        try:
            # Run TinyTuya status in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            status = await loop.run_in_executor(None, self._tinytuya_device.status)
            
            if status and 'dps' in status:
                self.state = status['dps']
                self._dps = status['dps']  # Update _dps for compatibility
                _LOGGER.debug(f"T2276 status updated: {self.state}")
            else:
                _LOGGER.warning("No DPS data received from T2276")
                
        except Exception as e:
            _LOGGER.error(f"Error getting T2276 status: {e}")
            raise
            
    async def async_set(self, dps: dict) -> None:
        """Set device state using TinyTuya"""
        try:
            # Use TinyTuya set_value for individual DPS values
            for dps_key, dps_value in dps.items():
                _LOGGER.debug(f"Setting T2276 DPS {dps_key} to {dps_value}")
                result = self._tinytuya_device.set_value(int(dps_key), dps_value)
                if not result:
                    _LOGGER.warning(f"Set_value failed for DPS {dps_key}")
                    
            # Update state after setting
            await asyncio.sleep(1)
            await self.async_get()
            
        except Exception as e:
            _LOGGER.error(f"Error setting T2276 state: {e}")
            raise


class T2276(RobovacModelDetails):
    homeassistant_features = (
        VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
    )
    robovac_features = (
        RoboVacEntityFeature.DO_NOT_DISTURB
        | RoboVacEntityFeature.BOOST_IQ
    )
    # X8 Pro SES uses protocol version 3.5
    protocol_version = (3, 5)
    
    # Custom payload format for X8 Pro SES
    @staticmethod
    def get_status_payload(device_id: str, gateway_id: str) -> dict:
        """Get the custom status payload for X8 Pro SES.
        
        The X8 Pro SES requires a different payload format than standard Tuya devices.
        Based on TinyTuya analysis, it uses an empty payload for status requests.
        """
        # TinyTuya uses empty payload for status requests - this works!
        return {}
    
    # Don't use PING for status - use GET with empty payload
    use_ping_for_status = False
    
    commands = {
        RobovacCommand.START_PAUSE: {
            "code": "1",
            "values": {
                "start": True,
                "stop": False,
            },
        },
        RobovacCommand.STATUS: {
            "code": "15",
        },
        RobovacCommand.MODE: {
            "code": "5",
            "values": {
                "auto": "auto",
                "spot": "spot",
                "edge": "edge",
            },
        },
        RobovacCommand.RETURN_HOME: {
            "code": "7",
            "values": {
                "return_home": True,
            }
        },
        RobovacCommand.FAN_SPEED: {
            "code": "102",
            "values": {
                "max": "Max",
                "mid": "Mid",
                "min": "Min",
            }
        },
        RobovacCommand.BATTERY: {
            "code": "104",
        },
        RobovacCommand.ERROR: {
            "code": "2",
        },
    }
    
    @staticmethod
    def get_device_class():
        """Return the custom device class for T2276"""
        return T2276TinyTuyaDevice
