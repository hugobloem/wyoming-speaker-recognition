"""Pass events through to the ASR program."""
import logging

from wyoming.asr import Transcribe
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.client import AsyncClient
from wyoming.event import Event
from wyoming.info import AsrProgram, Describe, Info

_LOGGER = logging.getLogger(__name__)


class Passthrough:
    """Pass events through to the ASR program."""

    def __init__(self, uri: str):
        self.uri = uri

    def set_callback(self, callback: callable):
        """Set the callback function to be called on events."""
        self.callback = callback

    async def get_asr_information(self) -> list[AsrProgram]:
        """Get information from the request."""
        async with AsyncClient.from_uri(self.uri) as client:
            await client.write_event(Describe().event())
            response = await client.read_event()

        if Info.is_type(response.type):
            asr = [AsrProgram.from_dict(asr) for asr in response.data['asr']]
            return asr

        raise ValueError("Invalid response from passthrough" \
        "please check if you have configured the passthrough uri correctly.")

    async def handle_event(self, event: Event) -> bool:
        """Handle an event."""

        if Describe.is_type(event.type):
            await self.repeat_event(event, get_response=True)
            return True

        if Transcribe.is_type(event.type):
            await self.repeat_event(event, get_response=False)
            return True

        if AudioStart.is_type(event.type):
            await self.repeat_event(event, get_response=False)
            return True

        if AudioChunk.is_type(event.type):
            await self.repeat_event(event, get_response=False)
            return True

        if AudioStop.is_type(event.type):
            await self.repeat_event(event, get_response=True)

            # Reset
            return False

        return True

    async def repeat_event(self, event: Event, get_response: bool = False) -> bool:
        """Repeat an event."""
        _LOGGER.debug(f"Repeating event: {event.type}")

        async with AsyncClient.from_uri(self.uri) as client:
            await client.write_event(event)
            if get_response:
                response = await client.read_event()
                _LOGGER.debug(f"Received response: {response.type}")
                await self.callback(response)
