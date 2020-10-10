#!/usr/bin/env python3

import argparse
import json

from data.card import Card
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
    with open("resources/tts/" + filename + ".mp3", "wb") as out:
        out.write(response.audio_content)

def synthesize_dictionary(json_path: str):
    """
    Parse the contents of the JSON document containing the card data
    and synthesize each 'word' element in it.

    :param json_path: the file path of the JSON document file
    """
    with open(json_path, 'r') as f:
        json_content = f.read()
        doc = json.loads(json_content)

        for entry in [ Card.from_json(json_obj) for json_obj in list(doc) ]:
            if entry.has_definitions():
                synthesize_text(entry.word, entry.word)
            else:
                continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", "-t",
        help="The text from which to synthesize speech.")
    group.add_argument("--json-file", "-j",
        help="JSON file containing data with which to create cards")

    args = parser.parse_args()

    if args.text:
        synthesize_text(args.text, args.text)
    else:
        synthesize_dictionary(args.json_file)
