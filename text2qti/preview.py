# -*- coding: utf-8 -*-
#
# Copyright (c) 2026, Geoffrey M. Poore
# All rights reserved.
#
# Licensed under the BSD 3-Clause License:
# http://opensource.org/licenses/BSD-3-Clause
#


import json

from .quiz import Quiz, Question




def quiz_to_preview_json(quiz: Quiz, *, solutions=False) -> str:
    '''
    Create a JSON representation of a quiz, with all elements represented in
    HTML format, suitable for HTML previewing.
    '''
    quiz_json = []

    in_group = False
    for question_or_delim in quiz.questions_and_delims:
        if isinstance(question_or_delim, Question):
            if in_group:
                continue
            question_data = {
                'type': 'question',
                'lines': [question_or_delim.linenum_start, question_or_delim.linenum_end],
                'text': question_or_delim.md.md_to_html(question_or_delim.question_raw),
            }
            if question_or_delim.choices:
                if question_or_delim.choices[0].shortans:
                    question_data['choices'] = [choice.choice_xml for choice in question_or_delim.choices]
                else:
                    question_data['choices'] = [question_or_delim.md.md_to_html(choice.choice_raw, True)
                                                for choice in question_or_delim.choices]
            quiz_json.append(question_data)
            continue

    return json.dumps(quiz_json)
