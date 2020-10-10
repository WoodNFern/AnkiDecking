#!/usr/bin/env python3

import argparse

from google.cloud import texttospeech

def synthesize_text(text: str, filename: str, language_code: str = 'fi-FI'):
    """
    Synthesizes speech from the input string of text.
    """

    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=language_code + "-Wavenet-A",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )

    # The response's audio_content is binary.
    with open(filename + ".mp3", "wb") as out:
        out.write(response.audio_content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", help="The text from which to synthesize speech.", required=True)

    args = parser.parse_args()

    synthesize_text(args.text, args.text)