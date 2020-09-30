import json

from typing import List

class Card():

    def __init__(self, word: str, pos: str, definitions: List[str]):
        self.word = word
        self.pos = pos
        self.definitions = definitions

    @staticmethod
    def from_json(json_obj: dict):
        word = json_obj['word']
        pos = json_obj['pos']
        definitions = json_obj['definitions']

        return Card(word, pos, definitions)

    def __repr__(self):
        return json.dumps(self.__dict__, separators=(',', ': '), indent=4)