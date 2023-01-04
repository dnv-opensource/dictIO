from pathlib import Path

from dictIO import DictParser, DictReader


def test_parse_dict():
    # sourcery skip: avoid-builtin-shadow, class-extract-method
    # Prepare
    source_file = Path("test_dictParser_dict")
    parsed_dict = Path(f"parsed.{source_file.name}")
    parsed_param_dict = Path("parsed.test_dictParser_paramDict")  # must NOT exist !
    parsed_dict.unlink(missing_ok=True)
    parsed_param_dict.unlink(missing_ok=True)

    # Execute
    _ = DictParser.parse(source_file)
    # Assert
    assert parsed_dict.exists()
    assert not parsed_param_dict.exists()
    # Clean up
    parsed_dict.unlink()


def test_reread_parsed_dict():
    # sourcery skip: avoid-builtin-shadow, class-extract-method
    # Prepare
    source_file = Path("test_dictParser_dict")
    parsed_dict = Path(f"parsed.{source_file.name}")
    parsed_param_dict = Path("parsed.test_dictParser_paramDict")  # must NOT exist !
    parsed_dict.unlink(missing_ok=True)
    parsed_param_dict.unlink(missing_ok=True)

    # Execute
    dict = DictParser.parse(source_file)
    dict_reread = DictReader.read(parsed_dict)
    # Assert
    assert dict == dict_reread
    # Assert the prefix 'parsed.' does not get piped (i.e. 'parsed.parsed.')
    assert not Path("parsed.parsed.test_dictParser_dict").exists()
    assert not Path("parsed.parsed.test_dictParser_paramDict").exists()
    # Clean up
    parsed_dict.unlink()


def test_parse_dict_foam_format():
    # Prepare
    source_file = Path("test_dictParser_dict")
    parsed_file = Path(f"parsed.{source_file.name}")
    parsed_file_foam = Path(f"{parsed_file.name}.foam")
    parsed_file.unlink(missing_ok=True)
    parsed_file_foam.unlink(missing_ok=True)
    # Execute
    _ = DictParser.parse(source_file, output="foam")
    # Assert
    assert not parsed_file.exists()
    assert parsed_file_foam.exists()
    # Clean up
    parsed_file_foam.unlink()
