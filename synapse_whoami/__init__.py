from typing import Any, Dict

import attr
from synapse.module_api import ModuleApi
from .who_am_i import WhoAmIResource


@attr.s(auto_attribs=True, frozen=True)
class WhoAmIConfig:
    pass


class WhoAmI:
    def __init__(self, config: WhoAmIConfig, api: ModuleApi):
        # Keep a reference to the config and Module API
        self._api = api
        self._config = config

        # Initiate resources
        self.whoami = WhoAmIResource(api)

        # Register the HTTP endpoint
        api.register_web_resource("/_synapse/client/whoami", self.whoami)

    @staticmethod
    def parse_config(config: Dict[str, Any]) -> WhoAmIConfig:
        # Parse the module's configuration here.
        # If there is an issue with the configuration, raise a
        # synapse.module_api.errors.ConfigError.
        #
        # Example:
        #
        #     some_option = config.get("some_option")
        #     if some_option is None:
        #          raise ConfigError("Missing option 'some_option'")
        #      if not isinstance(some_option, str):
        #          raise ConfigError("Config option 'some_option' must be a string")
        #
        return WhoAmIConfig()
