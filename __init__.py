"""The Extended Conversation Client integration."""
from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.exceptions import HomeAssistantError, ConfigEntryNotReady
import aiohttp
import asyncio
import logging
from typing import Optional

from .ServerInterface.Helpers.shared_models import (
    ProcessRequest,
    UserInput,
    ProcessResponse,
    ErrorDetails
)

from .const import (
    DOMAIN,
    CONF_SERVER_URL,
    DEFAULT_SERVER_URL,
    CONF_SERVER_ENABLED,
    DEFAULT_SERVER_ENABLED
)

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config) -> bool:
    """Set up Extended Conversation Client."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Extended Conversation Client from a config entry."""
    try:
        # Test server connection
        server_url = entry.options.get(CONF_SERVER_URL, DEFAULT_SERVER_URL)
        _LOGGER.info("Attempting to connect to server at %s", server_url)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{server_url}/health", timeout=10) as response:
                    if response.status != 200:
                        _LOGGER.error("Server returned status %s", response.status)
                        raise ConfigEntryNotReady(f"Server returned status {response.status}")
                    _LOGGER.info("Successfully connected to server")
            except aiohttp.ClientError as err:
                _LOGGER.error("Connection error: %s", str(err))
                raise ConfigEntryNotReady(f"Connection error: {err}")
            except asyncio.TimeoutError:
                _LOGGER.error("Connection timeout")
                raise ConfigEntryNotReady("Connection timeout")
            
    except Exception as err:
        _LOGGER.error("Failed to connect to server: %s", str(err), exc_info=True)
        raise ConfigEntryNotReady(f"Failed to connect to server: {err}")

    agent = ExternalServerAgent(hass, entry)
    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})
    conversation.async_set_agent(hass, entry, agent)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Extended Conversation Client."""
    hass.data[DOMAIN].pop(entry.entry_id)
    conversation.async_unset_agent(hass, entry)
    return True

class ExternalServerAgent(conversation.AbstractConversationAgent):
    """Agent that delegates processing to external server."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self.server_enabled = entry.options.get(CONF_SERVER_ENABLED, DEFAULT_SERVER_ENABLED)
        self.server_url = entry.options.get(CONF_SERVER_URL, DEFAULT_SERVER_URL)

    @property
    def supported_languages(self) -> list[str]:
        """Return all languages."""
        return ["en"]

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence by delegating to external server."""
        try:
            if not self.server_enabled:
                _LOGGER.info("Server is disabled, using local processing")
                return await self._process_locally(user_input)

            return await self._process_with_server(user_input)

        except Exception as err:
            _LOGGER.error("Error processing request: %s", err)
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                f"Internal error: {str(err)}"
            )
            return conversation.ConversationResult(
                response=intent_response,
                conversation_id=None
            )

    async def _process_with_server(
                self, user_input: conversation.ConversationInput
            ) -> conversation.ConversationResult:
                """Process request using external server."""
                try:
                    # Get current states of entities
                    states = {
                        state.entity_id: state.state
                        for state in self.hass.states.async_all()
                    }

                    # Create request using shared models
                    request = ProcessRequest(
                        user_input=UserInput(
                            text=user_input.text,
                            language=user_input.language,
                            conversation_id=user_input.conversation_id,
                            device_id=user_input.device_id
                        ),
                        states=states,
                        config={"server_url": self.server_url}
                    )

                    _LOGGER.info("Attempting server request to: %s", self.server_url)
                    _LOGGER.debug("Request data: %s", request.dict())

                    async with aiohttp.ClientSession() as session:
                        try:
                            async with session.post(
                                f"{self.server_url}/process",
                                json=request.dict(),
                                timeout=30
                            ) as response:
                                if response.status != 200:
                                    _LOGGER.error("Server returned error status: %s", response.status)
                                    text = await response.text()
                                    _LOGGER.error("Server error response: %s", text)
                                    return await self._process_locally(user_input)
                                    
                                result = await response.json()
                                if result is None:
                                    _LOGGER.error("Server returned None response")
                                    return await self._process_locally(user_input)
                                    
                                _LOGGER.debug("Received response from server: %s", result)

                                response_obj = ProcessResponse(**result)
                                
                                # Check for error in response
                                if response_obj.error:
                                    error_details = response_obj.error
                                    _LOGGER.error("Server error: %s", error_details.traceback)
                                    return await self._process_locally(user_input)

                                # Execute any commands returned by server
                                if response_obj.commands:
                                    for command in response_obj.commands:
                                        _LOGGER.debug("Executing command: %s", command.dict())
                                        await self.hass.services.async_call(
                                            command.domain,
                                            command.service,
                                            command.data,
                                            blocking=True
                                        )

                                # Return the response
                                intent_response = intent.IntentResponse(language=user_input.language)
                                intent_response.async_set_speech(response_obj.response)
                                return conversation.ConversationResult(
                                    response=intent_response,
                                    conversation_id=response_obj.conversation_id
                                )

                        except aiohttp.ClientError as err:
                            _LOGGER.error("Failed to communicate with server: %s", str(err))
                            return await self._process_locally(user_input)
                        except asyncio.TimeoutError:
                            _LOGGER.error("Server request timed out")
                            return await self._process_locally(user_input)
                        except ValueError as err:
                            _LOGGER.error("Failed to parse server response: %s", str(err))
                            return await self._process_locally(user_input)

                except Exception as err:
                    _LOGGER.error("Server processing failed: %s", str(err), exc_info=True)
                    return await self._process_locally(user_input)

    async def _process_locally(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Fallback local processing."""
        try:
            if "turn on helix" in user_input.text.lower():
                await self.hass.services.async_call(
                    "light", 
                    "turn_on",
                    {"entity_id": "light.helix"},
                    blocking=True,
                )
                response_text = "Turned on Helix light"
            else:
                response_text = "Hello World local"

            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_speech(response_text)
            return conversation.ConversationResult(
                response=intent_response,
                conversation_id=None
            )
        except Exception as err:
            _LOGGER.error("Local processing failed: %s", str(err), exc_info=True)
            raise