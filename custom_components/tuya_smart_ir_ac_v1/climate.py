import voluptuous as vol

import logging

from pprint import pformat

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate.const import (
    HVACMode,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_FAN_MODE,
)
from homeassistant.const import UnitOfTemperature, STATE_UNKNOWN
from homeassistant.components.climate import ClimateEntity

from .const import VALID_MODES
from .api import TuyaAPI

_LOGGER = logging.getLogger("tuya_hack")

ACCESS_ID = "access_id_v1"
ACCESS_SECRET = "access_secret_v1"
REMOTE_ID = "remote_id_v1"
AC_ID = "ac_id_v1"
NAME = "name_v1"
SENSOR = "sensor_v1"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(ACCESS_ID): cv.string,
        vol.Required(ACCESS_SECRET): cv.string,
        vol.Required(REMOTE_ID): cv.string,
        vol.Required(AC_ID): cv.string,
        vol.Required(NAME): cv.string,
        vol.Required(SENSOR): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    climate = {
        "access_id_v1": config[ACCESS_ID],
        "access_secret_v1": config[ACCESS_SECRET],
        "remote_id_v1": config[REMOTE_ID],
        "ac_id_v1": config[AC_ID],
        "name_v1": config[NAME],
        "sensor_v1": config[SENSOR]
    }

    add_entities([TuyaThermostat(climate, hass)])


class TuyaThermostat(ClimateEntity):
    def __init__(self_v1, climate, hass):
        _LOGGER.info(pformat(climate))
        self_v1._api = TuyaAPI(
            hass,
            climate[ACCESS_ID],
            climate[ACCESS_SECRET],
            climate[AC_ID],
            climate[REMOTE_ID],
        )
        self_v1._sensor_name = climate[SENSOR]
        self_v1._name = climate[NAME]

    @property
    def name(self_v1):
        return self_v1._name

    @property
    def unique_id(self_v1):
        return "tuya_hack_01"

    @property
    def temperature_unit(self_v1):
        return UnitOfTemperature.CELSIUS

    @property
    def supported_features(self_v1):
        return SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE

    @property
    def min_temp(self_v1):
        return 15

    @property
    def max_temp(self_v1):
        return 30

    @property
    def current_temperature(self_v1):
        sensor_state = self_v1.hass.states.get(self_v1._sensor_name)
        _LOGGER.info("SENSOR STATE ", sensor_state)
        if sensor_state and sensor_state.state != STATE_UNKNOWN:
            return float(sensor_state.state)
        return float(self_v1._api._temperature) if self_v1._api._temperature else None

    @property
    def target_temperature(self_v1):
        return float(self_v1._api._temperature) if self_v1._api._temperature else None

    @property
    def hvac_mode(self_v1):
        if self_v1._api._power == "0":
            return HVACMode.OFF
        return VALID_MODES.get(str(self_v1._api._mode), None)

    @property
    def hvac_modes(self_v1):
        return list(VALID_MODES.values())

    @property
    def fan_mode(self_v1):
        return (
            "Low"
            if self_v1._api._wind == "1"
            else "Medium"
            if self_v1._api._wind == "2"
            else "High"
            if self_v1._api._wind == "3"
            else "Automatic"
            if self_v1._api._wind == "1"
            else None
        )

    @property
    def fan_modes(self_v1):
        return list(["Low", "Medium", "High", "Automatic"])

    async def async_set_fan_mode(self_v1, fan_mode):
        if fan_mode == "Low":
            await self_v1._api.send_command("wind", "1")
        elif fan_mode == "Medium":
            await self_v1._api.send_command("wind", "2")
        elif fan_mode == "High":
            await self_v1._api.send_command("wind", "3")
        elif fan_mode == "Automatic":
            await self_v1._api.send_command("wind", "0")
        else:
            await self_v1._api.send_command("wind", "0")
            _LOGGER.warning("Invalid fan mode.")

    async def async_update(self_v1):
        await self_v1._api.async_update()
        self_v1.async_write_ha_state()

    async def async_set_temperature(self_v1, **kwargs):
        temperature = kwargs.get("temperature")
        if temperature is not None:
            await self_v1._api.async_set_temperature(float(temperature))

    async def async_set_hvac_mode(self_v1, hvac_mode):
        _LOGGER.info("SETTING HVAC MODE TO " + hvac_mode)
        for mode, mode_name in VALID_MODES.items():
            if hvac_mode == mode_name:
                if mode == "5":
                    await self_v1._api.async_turn_off()
                else:
                    if self_v1._api._power == "0":
                        await self_v1._api.async_turn_on()
                    await self_v1._api.async_set_fan_speed(0)
                    await self_v1._api.async_set_hvac_mode(mode)
                break
