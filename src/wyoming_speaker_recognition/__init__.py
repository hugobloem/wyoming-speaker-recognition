"""Wyoming Speaker Recognition."""

from pydantic import BaseModel, DirectoryPath


class WyomingSpeakerRecognitionConfig(BaseModel):
    """Configuration for speaker recognition service."""

    passthrough_uri: str
    model: str = "speechbrain/spkrec-ecapa-voxceleb"
    savedir: DirectoryPath = DirectoryPath("pretrained_models/")
    audiodir: DirectoryPath = DirectoryPath("audio/")
    training_mode: bool = False
