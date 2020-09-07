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

        # Extract & format definition
        for pos_section in relevant_sections:
            items = [ wtp.WikiText(def_item) for def_list in pos_section.get_lists() for def_item in def_list.items ]
            formatted_items = [ item.plain_text(replace_templates=False).strip() for item in items ]
            templated_items = [ TemplateProcessor.process_templates(formatted_item) for formatted_item in formatted_items ]
            print("%s (%s): %s" % (self.title, pos_section.title, str(templated_items)))


class TemplateProcessor():

    @staticmethod
    def process_templates(wiki_text: str):
        processed_text = wiki_text
        p = re.compile(r"{{([^\|]*?)\|(.*?)}}")
        t_coordinates = TemplateProcessor.detect_template_coordinates(processed_text)

        while t_coordinates:
            # Extract template information
            start_index, end_index = t_coordinates.pop(0)
            m = p.search(processed_text[start_index:end_index])
            t_type, t_args = (m.group(1), m.group(2)) if m else ('', '')

            # Substitute template with processed text
            processed_template = TemplateProcessor.process_specific_template(t_type, t_args)
            processed_text = processed_text[:start_index] + processed_template + processed_text[end_index:]
            t_coordinates = TemplateProcessor.detect_template_coordinates(processed_text)

        return processed_text

    @staticmethod
    def detect_template_coordinates(wiki_text: str):
        t_coordinates = []
        stack = []

        i = 0
        while i < len(wiki_text) - 1:
            if wiki_text[i:i+2] == '{{':
                stack.append(i)
            elif wiki_text[i:i+2] == '}}':
                start_index = stack.pop()
                end_index = i + 2
                t_coordinates.append((start_index, end_index))
                i += 1  # next character is already processed -> skip
            else:
                pass
            i += 1

        return t_coordinates

    @staticmethod
    def process_specific_template(t_type: str, t_args: str):
        if t_type in ['m', 'mention']:
            return TemplateProcessor.unchanged_text_with_opt_remark(t_args)
        elif t_type in ['l', 'link']:
            return TemplateProcessor.get_second_arg(t_args)
        elif t_type in ['lb', 'label']:
            return TemplateProcessor.paranthesized_comma_list(t_args)
        elif t_type in ['gloss', 'qualifier', 'qual', 'q']:
            return TemplateProcessor.parenthesized_arg(t_args)
        elif t_type in ['taxlink', 'w', 'n-g', 'non-gloss definition', 'vern']:
            return TemplateProcessor.get_first_arg(t_args)
        elif any(particle in t_type for particle in ['for', 'form']) :
            return TemplateProcessor.leave_marked(t_type, t_args)
        elif t_type in ['cln']:
            return TemplateProcessor.omit_template()
        else:
            return TemplateProcessor.omit_template()

    @staticmethod
    def unchanged_text_with_opt_remark(t_args: str):
        """
        Produces the unprocessed mention from the first argument and appends an
        optional further remark in quotes and parentheses from the second
        argument, if present.
        """
        splits = re.split(r'\|+', t_args)

        mention = splits[1]
        if len(splits) == 3:
            mention += ' ("' + splits[2] + '")'

        return mention

    @staticmethod
    def get_first_arg(t_args: str):
        splits = re.split(r'\|+', t_args)

        return splits[0]

    @staticmethod
    def get_second_arg(t_args: str):
        splits = re.split(r'\|+', t_args)

        return splits[1]

    @staticmethod
    def parenthesized_arg(t_args: str):
        """
        Returns the provided arguments unchanged, put between parantheses.
        """
        return '(%s)' % t_args

    @staticmethod
    def paranthesized_comma_list(t_args: str):
        """
        Produces a comma seperated list of all arguments but the first one,
        which is a language specifier, in parantheses.
        """
        splits = re.split(r'\|+', t_args)[1:]
        label = ', '.join(splits)
        return '(%s)' % label

    @staticmethod
    def leave_marked(t_type: str, t_args: str):
        """
        Leave template marked to be detected later on such that the whole
        containing translation can be deleted instead of merely removing the
        template.
        """
        return '$$' + t_type + '|' + t_args + '$$'

    @staticmethod
    def omit_template():
        """
        Omit unknown templates with the assumption that new templates are not
        going to introduce fundamental new information.
        """
        return ''

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
