import pytest

from text2qti.config import Config
from text2qti.err import Text2qtiError


def test_missing_config_file_is_created(tmp_path):
    path = tmp_path / 'text2qti.bespon'
    config = Config(config_path=path)
    config.load()
    written = path.read_text(encoding='utf8')
    assert 'latex_render_url' in written
    assert config['latex_render_url'] == '/equation_images/'
    assert config['run_code_blocks'] is False
    assert config.loaded_config_file is False


def test_config_file_overrides_defaults(tmp_path):
    path = tmp_path / 'text2qti.bespon'
    path.write_text('run_code_blocks = true\n', encoding='utf8')
    config = Config(config_path=path)
    config.load()
    assert config['run_code_blocks'] is True
    assert config['pandoc_mathml'] is False


def test_unknown_config_key_is_rejected(tmp_path):
    path = tmp_path / 'text2qti.bespon'
    path.write_text('nope = 1\n', encoding='utf8')
    config = Config(config_path=path)
    with pytest.raises(Text2qtiError, match='Invalid configuration option "nope"'):
        config.load()
