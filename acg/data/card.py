import json

class Card():

    def __init__(self, word: str, pos: str, definitions: list):
        self.word = word
        self.pos = pos
        self.definitions = definitions

    def __repr__(self):
        return json.dumps(self.__dict__, separators=(',', ': '), indent=4)