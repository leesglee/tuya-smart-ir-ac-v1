from tuya_connector import TuyaOpenAPI
from .const import VALID_MODES
from homeassistant.core import HomeAssistant

import logging
from pprint import pformat

_LOGGER = logging.getLogger("tuya_hack")


class TuyaAPI:
    def __init__(
        self_v1,
        hass: HomeAssistant,
        access_id_v1,
        access_secret_v1,
        thermostat_device_id_v1,
        ir_remote_device_id_v1,
    ):
        self_v1.access_id_v1 = access_id_v1
        self_v1.access_secret_v1 = access_secret_v1
        self_v1.thermostat_device_id_v1 = thermostat_device_id_v1
        self_v1.ir_remote_device_id_v1 = ir_remote_device_id_v1
        self_v1.hass = hass

        openapi = TuyaOpenAPI("https://openapi.tuyaus.com", access_id_v1, access_secret_v1)
        openapi.connect()
        self_v1.openapi = openapi

        self_v1._temperature = "0"
        self_v1._mode = "0"
        self_v1._power = "0"
        self_v1._wind = "0"

    async def async_init(self_v1):
        await self_v1.update()

    async def async_update(self_v1):
        status = await self_v1.get_status()
        if status:
            self_v1._temperature = status.get("temp")
            self_v1._mode = status.get("mode")
            self_v1._power = status.get("power")
            self_v1._wind = status.get("wind")
        _LOGGER.info(pformat("ASYNC_UPDATE " + str(status)))

    async def async_set_fan_speed(self_v1, fan_speed):
        _LOGGER.info(fan_speed)
        await self_v1.send_command("wind", str(fan_speed))

    async def async_set_temperature(self_v1, temperature):
        await self_v1.send_command("temp", str(temperature))

    async def async_turn_on(self_v1):
        await self_v1.send_command("power", "1")

    async def async_turn_off(self_v1):
        await self_v1.send_command("power", "0")

    async def async_set_hvac_mode(self_v1, hvac_mode):
        _LOGGER.info(hvac_mode)
        for mode, mode_name in VALID_MODES.items():
            if hvac_mode == mode_name:
                _LOGGER.info(mode)
                await self_v1.send_command("mode", mode)
                break

    async def get_status(self_v1):
        url = f"/v2.0/infrareds/{self_v1.ir_remote_device_id_v1}/remotes/{self_v1.thermostat_device_id_v1}/ac/status"
        _LOGGER.info(url)
        try:
            data = await self_v1.hass.async_add_executor_job(self_v1.openapi.get, url)
            if data.get("success"):
                _LOGGER.info(pformat("GET_STATUS " + str(data.get("result"))))
                return data.get("result")
        except Exception as e:
            _LOGGER.error(f"Error fetching status: {e}")
        return None

    async def send_command(self_v1, code, value):
        url = f"/v2.0/infrareds/{self_v1.ir_remote_device_id_v1}/air-conditioners/{self_v1.thermostat_device_id_v1}/command"
        _LOGGER.info(url)
        try:
            _LOGGER.info(pformat("SEND_COMMAND_CODE_THEN_VAL " + code + " " + value))
            data = await self_v1.hass.async_add_executor_job(
                self_v1.openapi.post,
                url,
                {
                    "code": code,
                    "value": value,
                },
            )
            _LOGGER.info(pformat("SEND_COMMAND_END " + str(data)))
            return data
        except Exception as e:
            _LOGGER.error(f"Error sending command: {e}")
            return False
