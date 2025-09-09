"""Unit tests for wyoming_speaker_recognition.speaker_recognition."""
import pytest

from wyoming_speaker_recognition.speaker_recognition import SpeakerRecognizer


@pytest.fixture(scope="session")
def recognizer(tmp_path_factory):
    """Fixture to create a SpeakerRecognizer instance."""
    model = "speechbrain/spkrec-ecapa-voxceleb"
    savedir = tmp_path_factory.mktemp("models")
    audiodir = "tests/data/audio"
    recognizer = SpeakerRecognizer(model=model, savedir=str(savedir), audiodir=audiodir)
    return recognizer

def test_recognizer_initialization(recognizer):
    """Test the initialization of the SpeakerRecognizer."""
    recognizer.initialize_recognizer()

    assert recognizer._initialized is True
    assert len(recognizer._known_speakers) == 2
    assert "Hugo" in recognizer._known_speakers
    assert "Radio" in recognizer._known_speakers
    assert recognizer._known_embeddings.shape[0] == 2

@pytest.mark.parametrize("audio_file,expected_speaker", [
    ("tests/data/audio/Hugo.wav", "Hugo"),
    ("tests/data/audio/Radio.wav", "Radio"),
])
def test_recognize_known_speaker(recognizer, audio_file, expected_speaker):
    """Test the recognition of known speakers."""
    result = recognizer.recognize(audio_file)
    assert result == expected_speaker

def test_recognize_unknown_speaker(recognizer):
    """Test the recognition of unknown speakers."""
    result = recognizer.recognize("tests/data/audio/__unknown.wav")
    assert result == "Unknown"
