#!/usr/bin/env python3

#   dic.html puts simple dictionary search into one self-contained HTML file.
#   Copyright 2024 Yorwba

#   dic.html is free software: you can redistribute it and/or
#   modify it under the terms of the GNU Affero General Public License
#   as published by the Free Software Foundation, either version 3 of
#   the License, or (at your option) any later version.

#   dic.html is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.

#   You should have received a copy of the GNU Affero General Public License
#   along with dic.html.  If not, see <https://www.gnu.org/licenses/>.

import html
import pathlib
import sqlite3
import unicodedata as ud


def main(argv):
    db_path = argv[0]
    packed_path = argv[1]

    dictionary = load_dictionary(db_path)
    json_db = {
        'dictionary': dictionary,
        'index': build_index(dictionary),
    }
    packed_db = pack(json_db)
    with open(packed_path, 'w') as f:
        f.write(html.escape(packed_db))


def load_dictionary(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    dictionary = sorted(map(clean_entry, cur.execute('SELECT word, definition FROM dictionary')))
    return dictionary


def clean_entry(entry):
    word, definition = entry
    split_definition = definition.split('\n', 1)
    if len(split_definition) != 2:
        return entry
    definition_head, definition_rest = split_definition
    definition_head = definition_head.replace('·', '').replace('◊', '')
    if definition_head.startswith(word):
        definition_head = definition_head[len(word):].lstrip(', ')
    if definition_head:
        definition_head += '\n'
    definition = definition_head + definition_rest
    return (word, definition)


def build_index(dictionary):
    search_strings = [ud.normalize('NFKD', word) for word, definition in dictionary]
    def suffix(word_suffix_index):
        word_index, suffix_index = word_suffix_index
        return search_strings[word_index][suffix_index:]
    suffix_array = sorted(
        ((word_index, suffix_index)
         for word_index, word in enumerate(search_strings)
         for suffix_index in range(len(word))),
        key=suffix)
    return {
        'searchStrings': search_strings,
        'suffixArray': suffix_array,
    }


def pack(json_db):
    dictionary_indices = []
    packed_dictionary = []
    packed_dictionary_len = 0
    for word, definition in json_db['dictionary']:
        packed_entry = pack_single(packed_len(word)) + word + definition
        dictionary_indices.append(packed_dictionary_len)
        packed_dictionary.append(packed_entry)
        packed_dictionary_len += packed_len(packed_entry)
    dictionary_indices.append(packed_dictionary_len)
    packed_dictionary = ''.join(packed_dictionary)
    assert packed_len(packed_dictionary) == packed_dictionary_len

    packed_dictionary_indices = []
    packed_dictionary_indices_len = 0
    for dictionary_index in dictionary_indices:
        assert packed_dictionary_indices_len == 2 * len(packed_dictionary_indices)
        packed_entry = pack_double(dictionary_index)
        packed_dictionary_indices.append(packed_entry)
        packed_dictionary_indices_len += packed_len(packed_entry)
    packed_dictionary_indices = ''.join(packed_dictionary_indices)
    assert packed_len(packed_dictionary_indices) == packed_dictionary_indices_len

    search_string_indices = []
    packed_search_strings = []
    packed_search_strings_len = 0
    for search_string in json_db['index']['searchStrings']:
        search_string_indices.append(packed_search_strings_len)
        packed_search_strings.append(search_string)
        packed_search_strings_len += packed_len(search_string)
    search_string_indices.append(packed_search_strings_len)
    packed_search_strings = ''.join(packed_search_strings)
    assert packed_len(packed_search_strings) == packed_search_strings_len

    packed_search_string_indices = []
    packed_search_string_indices_len = 0
    for search_string_index in search_string_indices:
        assert packed_search_string_indices_len == 2 * len(packed_search_string_indices)
        packed_entry = pack_double(search_string_index)
        packed_search_string_indices.append(packed_entry)
        packed_search_string_indices_len += packed_len(packed_entry)
    packed_search_string_indices = ''.join(packed_search_string_indices)
    assert packed_len(packed_search_string_indices) == packed_search_string_indices_len

    packed_suffix_array = []
    packed_suffix_array_len = 0
    for word_index, suffix_index in json_db['index']['suffixArray']:
        assert packed_suffix_array_len == 3 * len(packed_suffix_array)
        packed_entry = pack_double(word_index) + pack_single(suffix_index)
        packed_suffix_array.append(packed_entry)
        packed_suffix_array_len += packed_len(packed_entry)
    packed_suffix_array = ''.join(packed_suffix_array)
    assert packed_len(packed_suffix_array) == packed_suffix_array_len

    dictionary_len = len(json_db['dictionary'])
    suffix_array_len = len(json_db['index']['suffixArray'])
    packed_db = []
    packed_db.append(pack_double(dictionary_len))
    packed_db.append(pack_double(packed_dictionary_len))
    packed_db.append(pack_double(packed_search_strings_len))
    packed_db.append(pack_double(suffix_array_len))
    packed_db.append(packed_dictionary_indices)
    packed_db.append(packed_search_string_indices)
    packed_db.append(packed_dictionary)
    packed_db.append(packed_search_strings)
    packed_db.append(packed_suffix_array)
    packed_db = ''.join(packed_db)
    left = packed_len(packed_db)
    right = 8 + 4 * (dictionary_len + 1) + packed_dictionary_len + packed_search_strings_len + 3 * suffix_array_len
    assert left == right, (left, right)

    return packed_db


def packed_len(string):
    return len(string.encode('utf-16')) // 2 - 1

SINGLE_UTF16_LOWER_LIMIT = 0x20
SINGLE_UTF16_UPPER_LIMIT = 0xd800
SINGLE_UTF16_RANGE = SINGLE_UTF16_UPPER_LIMIT - SINGLE_UTF16_LOWER_LIMIT


def pack_single(value):
    assert 0 <= value < SINGLE_UTF16_RANGE, value
    return chr(value + SINGLE_UTF16_LOWER_LIMIT)


def pack_double(value):
    assert 0 <= value < SINGLE_UTF16_RANGE**2, value
    low = value % SINGLE_UTF16_RANGE
    high = value // SINGLE_UTF16_RANGE
    return pack_single(high) + pack_single(low)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
