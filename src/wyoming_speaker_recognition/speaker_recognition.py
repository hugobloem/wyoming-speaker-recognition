"""Speaker recognizer."""

import io
import logging
import os
from glob import glob

import torch
from speechbrain.inference.speaker import SpeakerRecognition

_LOGGER = logging.getLogger(__name__)

class SpeakerRecognizer:
    """Class for recognizing speakers in audio."""

    def __init__(self, model:str, savedir:str, audiodir:str, threshold:float=0.75) -> None:
        """Initialize the speaker recognizer."""
        self.model = model
        self.savedir = savedir
        self.audiodir = audiodir
        self.threshold = threshold
        self.similarity = torch.nn.CosineSimilarity(dim=-1, eps=1e-6)
        self._known_speakers = []
        self._known_embeddings = torch.empty((0, 192))
        self._initialized = False

    def initialize_recognizer(self):
        """Initialize the recognizer by loading the model and processing known speakers."""
        self._load_model(self.model, self.savedir)
        audiofiles = self._get_audio_files()
        _LOGGER.debug(f"Found {len(audiofiles)} audio files for known speakers: {audiofiles}")

        if not audiofiles:
            raise ValueError(f"No audio files found in the {self.audiodir} directory.")

        speaker_names, embeddings = self._process_known_speakers(audiofiles)
        self._known_speakers = speaker_names
        self._known_embeddings = embeddings
        self._initialized = True

    def recognize(self, fhandle: io.BytesIO|str) -> str:
        """Recognize the speaker in the given audio file."""
        if not self._initialized:
            _LOGGER.warning("Recognizer not initialized. Initializing now.")
            self.initialize_recognizer()
        audio = self._open_file(fhandle)
        embedding = self._generate_embedding(audio)

        score = self.similarity(embedding, self._known_embeddings)
        val, idx = torch.max(score, dim=0)
        if val < self.threshold:
            _LOGGER.info(f"Unknown speaker detected with confidence {val.item()}")
            return "Unknown"
        _LOGGER.info(f"Recognized speaker: {self._known_speakers[idx]} with confidence {val.item()}")
        return self._known_speakers[idx]


    def _load_model(self, model:str, savedir:str):
        """Load the speaker recognition model."""
        _LOGGER.info(f"Loading model {model} into {savedir}")
        self._model = SpeakerRecognition.from_hparams(source=model, savedir=os.path.join(savedir, model.split("/")[-1]))

    def _get_audio_files(self) -> list[str]:
        """Get a list of audio files in the audio directory."""
        audiofiles = glob(os.path.join(self.audiodir, "*.wav"))
        return [af for af in audiofiles if not os.path.basename(af).startswith("__")]

    def _process_known_speakers(self, audiofiles: list[str]) -> tuple[list[str], torch.Tensor]:
        audio = [self._open_file(audiofile) for audiofile in audiofiles]
        embeddings = torch.vstack([self._generate_embedding(a) for a in audio])
        speaker_names = [os.path.basename(af).replace(".wav", "") for af in audiofiles]
        return speaker_names, embeddings

    def _open_file(self, audiofile: str| io.BytesIO) -> torch.Tensor:
        """Open an audio file."""
        return self._model.load_audio(audiofile)


    def _generate_embedding(self, audio: torch.Tensor) -> torch.Tensor:
        """Generate speaker embeddings for a given audio file."""
        return self._model.encode_batch(audio, normalize=False)
