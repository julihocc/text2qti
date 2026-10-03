import sys

import pytest

from text2qti.cmdline import main
from text2qti.convert import export_solutions, read_quiz_text
from text2qti.err import Text2qtiError


def test_read_quiz_text_reports_a_missing_file(tmp_path):
    missing = tmp_path / 'quiz.txt'
    with pytest.raises(Text2qtiError, match='does not exist'):
        read_quiz_text(missing)


def test_main_prints_parse_errors_without_a_traceback(tmp_path, monkeypatch, capsys):
    quiz_path = tmp_path / 'quiz.txt'
    quiz_path.write_text('% only a comment\n', encoding='utf8')
    monkeypatch.setattr(sys, 'argv', ['text2qti', str(quiz_path)])
    monkeypatch.setattr('text2qti.cmdline.Config.load', lambda self: None)

    with pytest.raises(SystemExit) as caught:
        main()

    assert caught.value.code == 1
    error = capsys.readouterr().err
    assert 'No questions were found' in error
    assert 'Traceback' not in error


def test_export_solutions_writes_markdown(tmp_path):
    from text2qti.config import Config
    from text2qti.quiz import Quiz

    quiz = Quiz(
        '1. Write.\n!   Covered in solutions.\n____\n',
        config=Config(),
        source_name='quiz.txt',
    )
    destination = tmp_path / 'solutions.md'
    export_solutions(quiz, [destination])
    assert 'Covered in solutions.' in destination.read_text(encoding='utf8')
