#!/usr/bin/env python3

import argparse
import xml.sax
import codecs
import sys

from typing import TextIO

class LanguageFilter(xml.sax.ContentHandler):

    def __init__(self, output_file: TextIO, frequency_list: dict = {}, target_language: str = 'English'):
        xml.sax.ContentHandler.__init__(self)
        self.output_file = output_file
        self.frequency_list = frequency_list
        self.language_marker = "==" + target_language + "=="

        # Flag to determine our current position inside the XML file
        self.in_page = False
        self.in_id = False
        self.in_title = False
        self.in_text = False

        # Variables to hold information about the processed element
        self.id = None
        self.title = None
        self.text = None

        # Counter to count the number of English word found
        self.filtered_words = 0
        self.all_words = 0

    def startElement(self, name, attrs):
        if name == "page":
            self.in_page = True
        if self.in_page and name == "id":
            self.in_id = True
        if self.in_page and name == "title":
            self.in_title = True
        if self.in_page and name == "text":
            self.in_text = True
            self.text = ""

    def characters(self, content):
        if self.in_title:
            self.title = content
        elif self.in_id:
            self.id = content
        elif self.in_text:
            self.text += content

    def _append_word(self):
        self.filtered_words += 1
        rank, pos = self.frequency_list.get(self.title, (None, None))

        self.output_file.write("  <entry>\n")
        self.output_file.write("    <id>%s</id>\n" % self.id)
        self.output_file.write("    <title>%s</title>\n" % self.title)
        self.output_file.write("    <pos>%s</pos>\n" % pos)
        self.output_file.write("    <rank>%s</rank>\n" % rank)
        self.output_file.write("    <text xml:space=\"preserve\"><![CDATA[\n")
        self.output_file.write("%s\n" % self.text)
        self.output_file.write("    ]]></text>\n")
        self.output_file.write("  </entry>\n")

    def _should_append_word(self):
        is_in_target_language = self.language_marker in self.text[:200]
        is_no_category_page = not ":" in self.title
        is_original_page = self.title != self.title.title()
        should_take_all = not self.frequency_list
        is_in_freq_list = self.title in self.frequency_list

        return is_in_target_language \
            and is_no_category_page \
            and is_original_page \
            and (should_take_all or is_in_freq_list)

    def endElement(self, name):
        if name == "page":
            self.in_page = False
            self.all_words += 1
            
            if self._should_append_word():
                    self._append_word()
                    print("Appending " + self.title)
    
        if self.in_page and name == "title":
            self.in_title = False
        if self.in_page and name == "id":
            self.in_id = False
        if self.in_page and name == "text":
            self.in_text = False

def read_frequency_list(frequency_file: str) -> dict:
    """
    Read a word frequency file and return a dictionary mapping word to their
    rank.
    """
    frequency_list = {}
    with open(frequency_file, "r", encoding="utf-8") as freq_file:
        for line in freq_file.readlines():
            (rank, word, part_of_speech) = line.strip().split(',')
            frequency_list[word] = (int(rank), part_of_speech)
    return frequency_list

def filter_wiki_dump(wiki_dump_file: str, frequency_list: dict, output_file: str, target_language: str):
    with open(output_file, "w", encoding="utf-8") as output_file:
        with open(wiki_dump_file, "r") as wiki_dump_file:
            output_file.write("<dictionary>\n")
            xml.sax.parse(wiki_dump_file, LanguageFilter(output_file, frequency_list, target_language))
            output_file.write("</dictionary>\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Filter word entries from a Wiktionary dump by language.')
    parser.add_argument('--target-language', '-l', type=str,
                    default='English',
                    help='Language to filter words for. Use the English name of the language. '
                        + 'For example use "English", "German" or "Finnish" to filter English, '
                        + 'German or Finnish words respectively.')
    parser.add_argument('--frequency-file', '-f', type=str,
                    required=True,
                    help='CSV file containing words of a language sorted by their frequency.')
    parser.add_argument('--wiki-dump-file', '-w', type=str,
                    required=True,
                    help='Dump of a Wiktionary.')
    parser.add_argument('--output-file', '-o', type=str,
                    default='filtered_dictionary.xml',
                    help='Filtered excerpt of Wiktionary dump.')
    args = parser.parse_args()

    # Read the frequency list to filter the words
    frequency_list = read_frequency_list(args.frequency_file)

    # Read & filter the Wiktionary dump
    filter_wiki_dump(args.wiki_dump_file, frequency_list, args.output_file, args.target_language)
