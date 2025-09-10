# Wyoming Speaker Recognition
Wyoming protocol server for Speaker Recognition

This Python package provides a Wyoming integration for Speaker Recognition and can be directly used with [Home Assistant](https://www.home-assistant.io/) voice and [Rhasspy](https://github.com/rhasspy/rhasspy).

## Speaker Recognition
Speaker recognition is a technology that identifies or verifies a person based on their voice. It analyzes unique vocal characteristics—such as pitch, accent, speaking style, and frequency patterns.

There are two main types:

- Speaker Identification: Determines who is speaking from a group of known voices.
- Speaker Verification: Confirms if a person is who they claim to be by comparing their voice to a stored sample.

Speaker recognition is used in security systems, voice assistants, call centers, and more, providing a convenient and secure way to authenticate users or personalize experiences. This program allows you to integrate these capabilities easily.

## Installation
Depending on your use case there are different installation options.

- **Using pip**
  Clone the repository and install the package using pip or run using uv. Please note that you require `ffmpeg` for this package to work.
  ```sh
  pip install .
  ```
  ```sh
  uv run -m  wyoming_speaker_recognition
  ```

- **Home Assistant Add-On**
  Add the following repository as an add-on repository to your Home Assistant, or click the button below.
  [https://github.com/hugobloem/homeassistant-addons](https://github.com/hugobloem/homeassistant-addons)

  [![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fhugobloem%2Fhomeassistant-addons)

- **Docker container**
  To run as a Docker container use the following command:
  ```bash
  docker run ghcr.io/hugobloem/wyoming-speaker-recognition-noha:latest --<key> <value>
  ```
  For the relevant keys please look at [the table below](#usage)

- **docker compose**

  Below is a sample for a docker compose file. You need to change the command for your specific use case.

  ```yaml
  wyoming-proxy-azure-tts:
    image: ghcr.io/hugobloem/wyoming-speaker-recognition-noha
    container_name: wyoming-speaker-recognition
    ports:
      - "10300:10300"
    environment:
    command: --uri=tcp://0.0.0.0:10300 --passthrough-uri ...
  ```

## Usage
Depending on the installation method parameters are parsed differently. However, the same options are used for each of the installation methods and can be found in the table below. 

For the bare-metal Python install the program is run as follows:
```python
python -m wyoming-speaker-recognition --<key> <value>
```

| Key | Optional | Description |
|---|---|---|
| `uri` | No | Uri where the server will be broadcasted e.g., `tcp://0.0.0.0:10300` |
| `passthrough-uri` | No | Uri where the speech-to-text service is available e.g., `tcp://0.0.0.0:10301` |
| `training-mode` | Yes | Enable training mode where voice samples are saved to disk |
| `model-dir` | Yes | Directory to download neural network models into (default: /tmp/) |
| `audio-dir` | Yes | Directory to store and retrieve audio data (default: /tmp/) |
| `debug` | Yes | Log debug messages |

First you'll want to run the service in `training-mode`. In training mode audio data is saved to disk under your `audio-dir` folder. So to use this service with your own audio data, follow these steps:

### 1. Prepare your audio data
- Create a directory to store your audio files (e.g., `~/audio-data`).
- Place your audio samples in this directory. Ensure that the files are in a format supported by `ffmpeg` (e.g., WAV).

### 2. Run the service in training mode
- Use the `--training-mode` flag and specify the `audio-dir` where your audio files are stored:
  ```sh
  python -m wyoming-speaker-recognition --training-mode --audio-dir=~/audio-data --uri=tcp://0.0.0.0:10300
  ```
- The service will save processed voice data into the `audio-dir`.

### 3. Train the system
- Once training mode is active, the service will collect and process audio samples for speaker recognition. Monitor the logs for progress.

### 4. Use the trained data
- After training, you can disable `training-mode` and run the service normally:
  ```sh
  python -m wyoming-speaker-recognition --audio-dir=~/audio-data --uri=tcp://0.0.0.0:10300
  ```
- The system will now use the trained data to recognize or verify speakers.

Ensure the `model-dir` is specified if custom models are needed, and adjust other parameters as required.