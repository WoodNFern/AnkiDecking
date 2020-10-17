import json

from anki.notes import Note
from typing import List, Final

class Card():

    WIKI_LINK_TEMPLATE: Final = "https://en.wiktionary.org/wiki/%s#Finnish"

    def __init__(self, word: str, pos: str, rank: int, definitions: List[str]):
        self.word = word
        self.pos = pos
        self.rank = rank
        self.definitions = definitions

    def fill_into_note(self, note: Note):
        note['Front'] = self.word
        note['PartOfSpeech'] = self.pos
        note['Back'] = Card.parsed_definitions(self.get_first_few_definitions())
        note['Rank'] = str(self.rank)
        note['WikiLink'] = Card.WIKI_LINK_TEMPLATE % self.word
        note['Audio'] = "[sound:%s.mp3]" % self.word
        return note

    def has_definitions(self):
        return any(definition for definition in self.definitions)

    @staticmethod
    def parsed_definitions(definitions: List[str]):
        parsed_string = "<ol>\n"

        for definition in definitions:
            if len(definition) > 0:
                parsed_string += "<li>%s</li>\n" % definition

        parsed_string += "</ol>"
        return parsed_string

    def get_first_few_definitions(self):
        """
        Selects a limited number of definitions to avoid information overload.
        """
        count = len(self.definitions)
        max_count = min(3, int(count / 2))
        return self.definitions[:max_count]

    @staticmethod
    def from_json(json_obj: dict):
        word = json_obj['word']
        pos = json_obj['pos']
        rank = json_obj['rank']
        definitions = json_obj['definitions']

        return Card(word, pos, rank, definitions)

    def __repr__(self):
        return json.dumps(self.__dict__, separators=(',', ': '), indent=4)