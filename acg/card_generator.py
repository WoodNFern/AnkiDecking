#!/usr/bin/env python3

import argparse
import glob
import json
import os
import shutil
import sys

from anki.decks import Deck
from anki.notes import Note
from anki.storage import Collection
from data.card import Card


def fill(collection: Collection, deck: Deck, json_path: str):
    """
    Parse and fill the contents of the JSON document containing the card data
    into the collection.

    :param json_path: the file path of the JSON document file
    """
    with open(json_path, 'r') as f:
        json_content = f.read()
        doc = json.loads(json_content)

        for entry in [ Card.from_json(json_obj) for json_obj in list(doc) ]:
            if entry.has_definitions():
                empty_note = collection.newNote()
                empty_note.model()['did'] = deck['id']
                filled_note = entry.fill_into_note(empty_note)

                collection.add_note(filled_note, deck['id'])
            else:
                continue


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--anki-home",
        help="Home of your Anki installation. Usually, this is one of the following:\n"\
            + " * '%APPDATA%\\Anki2' (on Windows)"\
            + " * '~/Library/Application Support/Anki2' (on Mac)"\
            + " * '~/.local/share/Anki2' (on Linux)")
    parser.add_argument("-d", "--deck-name", default="Default",
        help="Name of the card deck into which to add cards")
    parser.add_argument("-j", "--json-file",
        help="JSON file containing data with which to create cards")
    parser.add_argument("-m", "--model-name",
        help="Name of the note type (model) to be used for new cards")
    parser.add_argument("-p", "--anki-profile", default="User 1",
        help="Name of the profile for which the collection should be created")
    args = parser.parse_args()

    # Load the anki collection
    collection_path = os.path.join(args.anki_home, args.anki_profile, "collection.anki2")
    json_file = os.path.abspath(args.json_file)
    collection = Collection(collection_path, log=True)

    # Set the model
    model = collection.models.byName(args.model_name)
    deck = collection.decks.byName(args.deck_name)
    collection.decks.select(deck['id'])
    collection.decks.current()['mid'] = model['id']

    # Load JSON into collection
    fill(collection, deck, json_file)

    # Save the changes to DB
    collection.save()
    collection.close()
