"""Wyoming Speaker Recognition entrypoint."""

import argparse
import asyncio
import contextlib
import logging
import os
import signal
from functools import partial

from wyoming.info import Info
from wyoming.server import AsyncServer

from . import WyomingSpeakerRecognitionConfig
from .handler import EventHandler
from .passthrough import Passthrough
from .speaker_recognition import SpeakerRecognizer

_LOGGER = logging.getLogger(__name__)

stop_event = asyncio.Event()


def handle_stop_signal(*args):
    """Handle shutdown signal and set the stop event."""
    _LOGGER.info("Received stop signal. Shutting down...")
    exit()


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--uri", default="tcp://0.0.0.0:10300", help="unix:// or tcp://"
    )
    parser.add_argument(
        "--passthrough-uri",
        required=True,
        help="unix:// or tcp:// URI for speech recognition.",
    )
    parser.add_argument(
        "--model-name",
        default="speechbrain/spkrec-ecapa-voxceleb",
        help="Name of the pre-trained model to use (default: speechbrain/spkrec-ecapa-voxceleb)",
    )
    parser.add_argument(
        "--training-mode",
        action="store_true",
        help="Enable training mode",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Similarity threshold for speaker recognition (default: 0.75)",
    )
    parser.add_argument(
        "--model-dir",
        default="pretrained_models/",
        help="Directory to store pre-trained models (default: pretrained_models/)",
    )
    parser.add_argument(
        "--audio-dir",
        default="audio/",
        help="Directory to save audio files (default: audio/)",
    )
    parser.add_argument("--debug", action="store_true", help="Log DEBUG messages")
    return parser.parse_args()


async def main() -> None:
    """Start Wyoming Microsoft STT server."""
    args = parse_arguments()

    os.makedirs(args.audio_dir, exist_ok=True)
    os.makedirs(args.model_dir, exist_ok=True)

    config = WyomingSpeakerRecognitionConfig(
        passthrough_uri=args.passthrough_uri,
        model=args.model_name,
        savedir=args.model_dir,
        audiodir=args.audio_dir,
        training_mode=args.training_mode,
        threshold=args.threshold,
    )

    passthrough = Passthrough(uri=config.passthrough_uri)
    recognizer = SpeakerRecognizer(model=config.model, savedir=config.savedir, audiodir=config.audiodir, threshold=config.threshold)

    # Set up logging
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    _LOGGER.debug("Arguments parsed successfully.")
    _LOGGER.debug(args)

    wyoming_info = Info(
        asr=await passthrough.get_asr_information(),
    )

    _LOGGER.info("Loading Speech Recognition model.")
    recognizer.initialize_recognizer()

    # Initialize server and run
    server = AsyncServer.from_uri(args.uri)
    _LOGGER.info("Ready")
    try:
        await server.run(
            partial(
                EventHandler,
                wyoming_info,
                args,
                passthrough,
                recognizer,
            )
        )
    except Exception as e:
        _LOGGER.error(f"An error occurred while running the server: {e}")


if __name__ == "__main__":
    # Set up signal handling for graceful shutdown
    signal.signal(signal.SIGTERM, handle_stop_signal)
    signal.signal(signal.SIGINT, handle_stop_signal)

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
