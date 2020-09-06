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

        # Extract & format definition
        for pos_section in relevant_sections:
            items = [ wtp.WikiText(def_item) for def_list in pos_section.get_lists() for def_item in def_list.items ]
            formatted_items = [ item.plain_text(replace_templates=False).strip() for item in items ]
            templated_items = self._replace_templates(formatted_items)
            print("%s (%s): %s" % (self.title, pos_section.title, str(templated_items)))

    def _replace_templates(self, items):
        # Subsitute templates, which produce argument text as result
        replaced_items = [ re.sub(self.unchanged_text_template_pattern, r'\2', item) for item in items]

        # Subsitute templates, which produce parenthesized text as result
        parenthesized_items = [ re.sub(self.parenthesizing_template_pattern, r'(\2)', item) for item in replaced_items]

        # Substitute remark templates with explanations in postposed parantheses
        remark_items = [ re.sub(self.parenthesized_remark_pattern, r'\1 ("\2")', item) for item in parenthesized_items]

        # Substitute patterns generating parenthesized lists
        fully_parenthesized_items = [ re.sub(self.combining_parenthesizing_template_pattern, r'(\2)', item) for item in remark_items]

        # Remove remaining templates
        cleaned_items = [ re.sub(self.omitting_template_pattern, '', item) for item in fully_parenthesized_items ]

        return cleaned_items


class TemplateProcessor():

    @staticmethod
    def process_templates(wiki_text: str):
        processed_text = wiki_text
        p = re.compile(r"{{([^\|]*?)\|(.*?)}}")
        m = p.search(processed_text)
        while m:
            template_type = m.group(1)
            template_args = m.group(2)
            processed_template = TemplateProcessor.process_specific_template(template_type, template_args)
            processed_text = processed_text[:m.start()] + processed_template + processed_text[m.end():]
            m = p.search(processed_text)
        return processed_text

    @staticmethod
    def process_specific_template(t_type: str, t_args: str):
        if t_type == 'm':
            return TemplateProcessor.process_remark_template(t_args)
        elif t_type in ['w', 'l', 'vern']:
            return TemplateProcessor.process_link_template(t_args)
        elif t_type in ['gloss', 'qualifier', 'qual']:
            return TemplateProcessor.process_qualifier_template(t_args)
        elif t_type in ['lb', 'label']:
            return TemplateProcessor.process_label_template(t_args)
        else:
            return TemplateProcessor.process_misc_template(t_args)

    @staticmethod
    def process_remark_template(t_args: str):
        splits = re.split(r'\|+', t_args)

        remark = splits[1]
        if len(splits) == 3:
            remark += ' ("' + splits[2] + '")'

        return remark

    @staticmethod
    def process_link_template(t_args: str):
        splits = re.split(r'\|+', t_args)

        return splits[-1]

    @staticmethod
    def process_qualifier_template(t_args: str):
        return '(%s)' % t_args

    @staticmethod
    def process_label_template(t_args: str):
        splits = re.split(r'\|+', t_args)[1:]
        label = ', '.join(splits)
        return '(%s)' % label

    @staticmethod
    def process_misc_template(t_args: str):
        return '(misc)'


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
