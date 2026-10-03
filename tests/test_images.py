import io
import zipfile

from text2qti.config import Config
from text2qti.qti import QTI
from text2qti.quiz import Quiz


def test_relative_image_is_read_from_resource_path(tmp_path, monkeypatch):
    image_bytes = b'\x89PNG\r\n\x1a\n'
    (tmp_path / 'dot.png').write_bytes(image_bytes)
    elsewhere = tmp_path / 'elsewhere'
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    quiz = Quiz(
        '1. See ![dot](dot.png)\n*a) yes\nb) no\n',
        config=Config(),
        source_name='quiz.txt',
        resource_path=tmp_path,
    )
    archive = zipfile.ZipFile(io.BytesIO(QTI(quiz).zip_bytes()))
    assert archive.read('images/dot.png') == image_bytes
