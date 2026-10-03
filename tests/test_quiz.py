import pytest

from text2qti.config import Config
from text2qti.err import Text2qtiError
from text2qti.quiz import GroupStart, Question, Quiz, TextRegion


def parse(text, **overrides):
    config = Config()
    if overrides:
        config.update(overrides)
    return Quiz(text, config=config, source_name='quiz.txt')


def questions(quiz):
    return [item for item in quiz.questions_and_delims if isinstance(item, Question)]


def test_multiple_choice_and_true_false():
    quiz = parse('''
1. What is 2+3?
a) 6
b) 1
*c) 5

1. Ready?
*a) true
b) false
''')
    multiple_choice, true_false = questions(quiz)
    assert multiple_choice.type == 'multiple_choice_question'
    assert [choice.correct for choice in multiple_choice.choices] == [False, False, True]
    assert multiple_choice.choices[2].choice_raw == '5'
    assert true_false.type == 'true_false_question'
    assert quiz.points_possible == 2


def test_multiple_answers_short_answer_essay_and_upload():
    quiz = parse('''
1. Which of the following are dinosaurs?
[ ] Woolly mammoth
[*] Tyrannosaurus rex
[*] Triceratops

1. Who lives at the North Pole?
*   Santa
*   Santa Claus

1. Write an essay.
____

1. Upload a file.
^^^^
''')
    multiple_answers, short_answer, essay, upload = questions(quiz)
    assert multiple_answers.type == 'multiple_answers_question'
    assert multiple_answers.correct_choices == 2
    assert short_answer.type == 'short_answer_question'
    assert [choice.choice_raw for choice in short_answer.choices] == ['Santa', 'Santa Claus']
    assert essay.type == 'essay_question'
    assert upload.type == 'file_upload_question'


def test_numerical_forms():
    quiz = parse('''
1. Square root of 2?
=   1.4142 +- 0.0001

2. Cube root of 2?
=   [1.2598, 1.2600]

3. Five plus ten percent?
=   5 +- 10%

4. What is 2+3?
=   5
''')
    margin, bounds, percent, exact = questions(quiz)
    assert margin.numerical_exact == pytest.approx(1.4142)
    assert margin.numerical_min == pytest.approx(1.4141)
    assert margin.numerical_max == pytest.approx(1.4143)
    assert bounds.numerical_exact is None
    assert bounds.numerical_min == pytest.approx(1.2598)
    assert bounds.numerical_max == pytest.approx(1.2600)
    assert percent.numerical_min == pytest.approx(4.5)
    assert percent.numerical_max == pytest.approx(5.5)
    assert exact.numerical_exact == 5
    assert exact.numerical_min == 5
    assert exact.numerical_max == 5


def test_title_points_feedback_text_region_and_comments():
    quiz = parse('''
Quiz title: Addition
Quiz description: Checking addition.

% This line is ignored.
COMMENT
This block is ignored.
END_COMMENT

Text title: Instructions
Text: Read this first.

Title: An addition question
Points: 2
1. What is 2+3?
... General feedback.
+   Correct feedback.
-   Incorrect feedback.
a)  6
... Not this one.
*c) 5

Points: 1.5
2. Half points.
*a) yes
b)  no
''')
    assert quiz.title_raw == 'Addition'
    assert 'Checking addition.' in quiz.description_raw
    text_region = quiz.questions_and_delims[0]
    assert isinstance(text_region, TextRegion)
    assert text_region.title_raw == 'Instructions'
    assert text_region.text_raw == 'Read this first.'
    scored, half = questions(quiz)
    assert scored.title_raw == 'An addition question'
    assert scored.points_possible == 2
    assert scored.feedback_raw == 'General feedback.'
    assert scored.correct_feedback_raw == 'Correct feedback.'
    assert scored.incorrect_feedback_raw == 'Incorrect feedback.'
    assert scored.choices[0].feedback_raw == 'Not this one.'
    assert 'ignored' not in scored.question_raw
    assert half.points_possible == 1.5
    assert quiz.points_possible == 3.5


def test_group_points_use_pick_not_every_question():
    quiz = parse('''
GROUP
pick: 1
points per question: 2

1. A question.
*a) true
b) false

2. Another question.
*a) true
b) false

END_GROUP

1. Outside the group.
*a) true
b) false
''')
    group = quiz.questions_and_delims[0]
    assert isinstance(group, GroupStart)
    assert group.group.pick == 1
    assert len(group.group.questions) == 2
    assert quiz.points_possible == 3


def test_group_pick_may_equal_group_size():
    quiz = parse('''
GROUP
pick: 2

1. A question.
*a) true
b) false

2. Another question.
*a) true
b) false

END_GROUP
''')
    assert quiz.points_possible == 2


def test_repeated_group_options_are_rejected():
    with pytest.raises(Text2qtiError, match='"Pick" has already been set'):
        parse('''
GROUP
pick: 1
pick: 2
1. A question.
*a) true
b) false
END_GROUP
''')
    with pytest.raises(Text2qtiError, match='"solutions pick" has already been set'):
        parse('''
GROUP
solutions pick: 1
solutions pick: 2
1. A question.
*a) true
b) false
END_GROUP
''')
    with pytest.raises(Text2qtiError, match='"Points per question" has already been set'):
        parse('''
GROUP
points per question: 1
points per question: 2
1. A question.
*a) true
b) false
END_GROUP
''')


def test_short_group_reports_pick_as_the_minimum():
    with pytest.raises(Text2qtiError, match='needs at least 2'):
        parse('''
GROUP
pick: 2
1. A question.
*a) true
b) false
END_GROUP
''')


def test_parse_errors():
    with pytest.raises(Text2qtiError, match='Duplicate choice'):
        parse('''
1. Same choice twice.
*a) yes
b) yes
''')
    with pytest.raises(Text2qtiError, match='Duplicate question'):
        parse('''
1. Same question.
*a) yes
b) no

1. Same question.
*a) yes
b) no
''')
    with pytest.raises(Text2qtiError, match='must specify a response type'):
        parse('1. No answer.\n')
    with pytest.raises(Text2qtiError, match='Question group never ended'):
        parse('''
GROUP
1. A question.
*a) true
b) false
''')
    with pytest.raises(Text2qtiError, match='missing valid exec attributes'):
        parse('''
```python
print("no")
```
1. A question.
*a) true
b) false
''')


def test_quiz_flags_share_validation():
    quiz = parse('''
shuffle answers: True
show correct answers: false
one question at a time: true
can't go back: true
feedback is solution: true
solutions sample groups: false
solutions randomize groups: False

1. A question.
*a) true
b) false
''')
    assert quiz.shuffle_answers_xml == 'true'
    assert quiz.show_correct_answers_xml == 'false'
    assert quiz.one_question_at_a_time_xml == 'true'
    assert quiz.cant_go_back_xml == 'true'
    assert quiz.feedback_is_solution is True
    assert quiz.solutions_sample_groups is False
    assert quiz.solutions_randomize_groups is False

    with pytest.raises(Text2qtiError, match='Shuffle answers" has already been set'):
        parse('''
shuffle answers: true
shuffle answers: false
1. A question.
*a) true
b) false
''')
    with pytest.raises(Text2qtiError, match='before setting "Can\'t go back"'):
        parse('''
can't go back: true
1. A question.
*a) true
b) false
''')
    with pytest.raises(Text2qtiError, match='Expected option value "true" or "false"'):
        parse('''
shuffle answers: yes
1. A question.
*a) true
b) false
''')


def test_resource_path_accepts_a_directory(tmp_path):
    quiz = parse('1. A question.\n*a) true\nb) false\n')
    assert quiz.resource_path is None
    located = Quiz(
        '1. A question.\n*a) true\nb) false\n',
        config=Config(),
        source_name='quiz.txt',
        resource_path=tmp_path,
    )
    assert located.resource_path == tmp_path.resolve()
    with pytest.raises(TypeError):
        Quiz('1. Q\n*a) true\nb) false\n', config=Config(), resource_path=1)
    missing = tmp_path / 'missing'
    with pytest.raises(Text2qtiError, match='does not exist'):
        Quiz('1. Q\n*a) true\nb) false\n', config=Config(), resource_path=missing)
