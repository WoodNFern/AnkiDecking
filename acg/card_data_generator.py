#!/usr/bin/env python3

import argparse
import xml.sax
import re
import sys
import wikitextparser as wtp

RELEVANT_SECTIONS = tuple(['Adjective', 'Adverb', 'Conjunction', 'Determiner', 'Interjection', 'Noun', 'Number',
                    'Numeral', 'Ordinal number', 'Particle', 'Postposition', 'Preposition', 'Pronoun', 'Verb'])
IRRELEVANT_SECTIONS = tuple(['Abbreviations', 'Alternative forms', 'Anagrams', 'Antonyms', 'Compounds', 'Conjugation',
                        'Contraction', 'Coordinate terms', 'Declension', 'Derived terms', 'Descendants',
                        'External links', 'Further reading', 'Hypernyms', 'Hyponyms', 'Idiom', 'Idioms', 'Inflection',
                        'Participle', 'Phrases', 'Pronunciation', 'Proverbs', 'Quotations', 'References',
                        'Related terms', 'See also', 'Synonyms', 'Usage notes'])
IRRELEVANT_TEMPLATE_NAMES = tuple(['cln', 'definition', ' for', 'n-g', ' of', 'onlyusedin', 'q', 'taxlink'])

class CardDataGenerator(xml.sax.ContentHandler):

    def __init__(self, output_file, target_language = 'English'):
        xml.sax.ContentHandler.__init__(self)
        self.output_file = output_file
        self.target_language = target_language

        # Flag to determine our current position inside the XML file
        self.in_entry = False
        self.in_id = False
        self.in_title = False
        self.in_text = False

        # Variables to hold information about the processed element
        self.id = None
        self.title = None
        self.text = None

        self._init_regex_patterns()

    def _init_regex_patterns(self):
        """
        Initializes RegEx patterns for Wiki template processing
        """
        self.parenthesized_remark_pattern = re.compile(r"{{m\|.*\|(.*)\|\|(.*)}}")
        self.combining_parenthesizing_template_pattern = re.compile(r"{{(lb|label)\|[^\|\}]*\|([^\}]*)}}")
        self.omitting_template_pattern = re.compile(r"{{.*}}")
        self.parenthesizing_template_pattern = re.compile(r"{{(gloss|qualifier|qual)\|(.*)}}")
        self.unchanged_text_template_pattern = re.compile(r"{{(w|vern|l)\|(?:[^\}]*\|)?([^\}]*)}}")

    def startElement(self, name, attrs):
        if name == "entry":
            self.in_entry = True
        if self.in_entry and name == "id":
            self.in_id = True
        if self.in_entry and name == "title":
            self.in_title = True
        if self.in_entry and name == "text":
            self.in_text = True
            self.text = ""

    def characters(self, content):
        if self.in_title:
            self.title = content
        elif self.in_id:
            self.id = content
        elif self.in_text:
            self.text += content

    def endElement(self, name):
        if name == "entry":
            self._process()
        if self.in_entry and name == "title":
            self.in_title = False
        if self.in_entry and name == "id":
            self.in_id = False
        if self.in_entry and name == "text":
            self.in_text = False

    def _process(self):
        parsed_page = wtp.parse(self.text)

        # Only use contents of target language
        target_lang_section = [
            section.contents
            for section in parsed_page.sections
            if section.title == self.target_language
        ][0]
        subsections = wtp.parse(target_lang_section).get_sections(include_subsections=False, level=3) \
                    + wtp.parse(target_lang_section).get_sections(include_subsections=False, level=4)


        # Relevant subsections containing translations
        relevant_sections = [
            section
            for section in subsections
            if section.title is not None and section.title.startswith(RELEVANT_SECTIONS)
        ]

        print("Word: " + self.title)
        print(str(relevant_sections))



def generate_card_data(dictionary_filename, output_filename, target_language):
    with open(dictionary_filename, "r", encoding="utf-8") as dic_file:
        with open(output_filename, "w", encoding="utf-8") as output_file:
            output_file.write("<dictionary>\n")
            xml.sax.parse(dic_file, CardDataGenerator(output_file, target_language))
            output_file.write("</dictionary>\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Filter word entries from a Wiktionary dump by language.')
    parser.add_argument('--target-language', '-l', type=str,
                    default='English',
                    help='Language to filter words for. Use the English name of the language. '
                        + 'For example use "English", "German" or "Finnish" to filter English, '
                        + 'German or Finnish words respectively.')
    parser.add_argument('--dictionary-file', '-d', type=str,
                    default='filtered_dictionary.xml',
                    help='Filtered excerpt of Wiktionary dump.')
    parser.add_argument('--output-file', '-o', type=str,
                    default='filtered_dictionary.xml',
                    help='Filtered excerpt of Wiktionary dump.')
    args = parser.parse_args()

    # Read & filter the Wiktionary dump
    generate_card_data(args.dictionary_file, args.output_file, args.target_language)
