import io
import re
import zipfile
from pathlib import Path

from text2qti.config import Config
from text2qti.export import quiz_to_pandoc
from text2qti.qti import QTI
from text2qti.quiz import Quiz


FIXTURES = Path(__file__).parent / 'fixtures' / 'addition'

ADDITION = '''Quiz title: Addition
Quiz description: Checking addition.
shuffle answers: false

Title: An addition question
Points: 2
1. What is 2+3?
... General feedback.
+   Correct feedback.
-   Incorrect feedback.
a)  6
*c) 5
'''


def zip_texts(data):
    archive = zipfile.ZipFile(io.BytesIO(data))
    return {
        name: archive.read(name).decode('utf8')
        for name in archive.namelist()
        if not name.endswith('/')
    }


def test_addition_qti_matches_fixtures():
    quiz = Quiz(ADDITION, config=Config(), source_name='quiz.txt')
    files = zip_texts(QTI(quiz).zip_bytes())
    assessment_name = next(name for name in files if name.endswith('.xml') and not name.endswith('assessment_meta.xml') and name != 'imsmanifest.xml')
    meta_name = next(name for name in files if name.endswith('/assessment_meta.xml'))

    assert files[assessment_name] == (FIXTURES / 'assessment.xml').read_text(encoding='utf8')
    assert files[meta_name] == (FIXTURES / 'assessment_meta.xml').read_text(encoding='utf8')

    manifest = re.sub(
        r'<imsmd:dateTime>.*</imsmd:dateTime>',
        '<imsmd:dateTime>DATE</imsmd:dateTime>',
        files['imsmanifest.xml'],
    )
    assert manifest == (FIXTURES / 'imsmanifest.xml').read_text(encoding='utf8')


def test_solution_text_is_exported_and_omitted_from_qti():
    quiz = Quiz(
        '''
1. Write an essay about text2qti.
!   This is important information about what the essay should cover.
____
''',
        config=Config(),
        source_name='quiz.txt',
    )
    solutions = quiz_to_pandoc(quiz, solutions=True)
    assessment = next(
        text for name, text in zip_texts(QTI(quiz).zip_bytes()).items()
        if name.endswith('.xml') and 'assessment_meta' not in name and name != 'imsmanifest.xml'
    )
    assert 'important information about what the essay should cover' in solutions
    assert 'important information' not in assessment
