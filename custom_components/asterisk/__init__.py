"""Astisk Component."""
import logging
import json
from typing import Any

import asterisk.manager
import voluptuous as vol
from time import sleep

from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5038
DEFAULT_USERNAME = "manager"
DEFAULT_PASSWORD = "manager"

DATA_ASTERISK = "asterisk_manager"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_PORT): cv.port,
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["sensor"]

_LOGGER = logging.getLogger(__name__)

def handle_asterisk_event(event, manager, hass, entry):
    _LOGGER.error("event.headers: " + json.dumps(event.headers))
    _extension = event.get_header("ObjectName")
    # entry.async_set_unique_id(f"{entry.entry_id}_{_extension}")


    hass.data[DOMAIN][entry.entry_id]["devices"].append(_extension)
    # device_registry = dr.async_get(hass)

    # device = device_registry.async_get_or_create(
        # config_entry_id=entry.entry_id,
        # identifiers={(DOMAIN, f"{entry.entry_id}_{_extension}")},
        # manufacturer="Asterisk",
        # model="SIP",
        # name=f"Asterisk Extension {_extension}",
    # )



    #hass.async_setup_platforms(entry, PLATFORMS)


async def async_setup_entry(hass, entry):
    """Your controller/hub specific code."""

    _LOGGER.error("SETTING UP FROM ENTRY")

    manager = asterisk.manager.Manager()

    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    _LOGGER.info("Asterisk component is now set up")
    try:
        manager.connect(host, port)
        manager.login(username, password)
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
            "devices": [],
            "manager": manager
        }
        # hass.data[DOMAIN]["manager"] = manager
        _LOGGER.info("Successfully connected to Asterisk server")
        manager.register_event("PeerEntry", lambda event, manager=manager, hass=hass, entry=entry: handle_asterisk_event(event, manager, hass, entry))
        manager.sippeers()

        sleep(5)
        
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(
                entry, "sensor"
            )
        )

        return True
    except asterisk.manager.ManagerException as exception:
        _LOGGER.error("Error connecting to Asterisk: %s", exception.args[1])
        _LOGGER.error(f"Host: {host}, Port: {port}, Username: {username}, Password: {password}")
        return False