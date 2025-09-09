"""Event handler for clients of the server."""
import argparse
import io
import logging
import os
import time
import wave

from wyoming.audio import AudioChunk, AudioChunkConverter, AudioStart, AudioStop
from wyoming.event import Event
from wyoming.info import Info
from wyoming.server import AsyncEventHandler

from .passthrough import Passthrough
from .speaker_recognition import SpeakerRecognizer

_LOGGER = logging.getLogger(__name__)


class EventHandler(AsyncEventHandler):
    """Event handler for clients."""

    def __init__(
        self,
        wyoming_info: Info,
        cli_args: argparse.Namespace,
        passthrough_asr: Passthrough,
        recognizer: SpeakerRecognizer,
        *args,
        **kwargs,
    ) -> None:
        """Initialize."""
        super().__init__(*args, **kwargs)

        self.cli_args = cli_args
        self.training_mode: bool = cli_args.training_mode
        self.wyoming_info_event = wyoming_info.event()
        self.passthrough_asr = passthrough_asr
        self.recognizer = recognizer

        self.passthrough_asr.set_callback(self.write_event)

        self.audio_converter = AudioChunkConverter(
            rate=16000,
            width=2,
            channels=1,
        )

    async def handle_event(self, event: Event) -> bool:
        """Handle an event."""
        status = await self.passthrough_asr.handle_event(event)

        if AudioStart.is_type(event.type):
            self.initialize_buffer()

        if AudioChunk.is_type(event.type):
            self.receive_chunk(event)

        if AudioStop.is_type(event.type):
            self.audio_complete()

        return status

    def audio_complete(self):
        """Process the received audio."""
        if self.training_mode:
            wav, filename = self._get_wavefile()
        else:
            wav, fhandle = self._get_io_wavefile()
        self.save_audio(wav)

        if self.training_mode:
            _LOGGER.info(f"Saved training audio to {filename}")
            return

        self.recognizer.recognize(fhandle)

    def initialize_buffer(self):
        """Initialize the audio buffer."""
        _LOGGER.debug("Initializing audio buffer...")
        self.audio = b""

    def receive_chunk(self, event: Event) -> None:
        """Save a chunk of audio."""
        _LOGGER.debug("Receiving audio chunk...")
        try:
            chunk = AudioChunk.from_event(event)
            chunk = self.audio_converter.convert(chunk)
            self.audio += chunk.audio
        except Exception as e:
            _LOGGER.error(f"Error receiving audio chunk: {e}")

    def save_audio(self, fhandle):
        """Save the received audio to a file."""
        _LOGGER.debug("Saving audio...")
        try:
            self.write_file(fhandle, self.audio)
        except Exception as e:
            _LOGGER.error(f"Failed to write audio to file: {e}")

    def _get_wavefile(self)-> tuple[wave.Wave_write, str]:
        """Get a waveform from a file."""
        filename = os.path.join(self.cli_args.audio_dir, f"__{time.monotonic_ns()}.wav")
        wav_file = wave.open(filename, "wb")
        return wav_file, filename

    def _get_io_wavefile(self) -> tuple[wave.Wave_write, io.BytesIO]:
        """Get a waveform from the received audio."""
        fhandle = io.BytesIO()
        wav_file = wave.open(fhandle, "wb")
        return wav_file, fhandle

    def write_file(self, fhandle: wave.Wave_write , data: bytes):
        """Write data to a wav file."""
        try:
            with fhandle:
                fhandle.setnchannels(1)
                fhandle.setsampwidth(2)
                fhandle.setframerate(16000)
                fhandle.writeframes(data)
            _LOGGER.debug("Audio written to file handle.")
        except Exception as e:
            _LOGGER.error(f"Failed to write wav file handle: {e}")
