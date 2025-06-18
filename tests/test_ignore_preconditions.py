from os import fspath as _fsp
from pathlib import Path
import pytest
from qc_baselib import Configuration, IssueSeverity
from qc_opendrive.checks import basic
from test_setup import *

TEST_DATA_PATH = Path(__file__).parent / "data"


def patch_bundle_param(param, value):
    config = Configuration()
    config.load_from_file(CONFIG_FILE_PATH)
    config.set_checker_bundle_param(constants.BUNDLE_NAME, param, value)
    config.write_to_file(CONFIG_FILE_PATH)


def patch_checker_param(checker_id, param, value):
    config = Configuration()
    config.load_from_file(CONFIG_FILE_PATH)
    config.register_checker(
        constants.BUNDLE_NAME,
        checker_id,
        IssueSeverity.ERROR,
        IssueSeverity.INFORMATION,
    )
    config.set_checker_param(constants.BUNDLE_NAME, checker_id, param, value)
    config.write_to_file(CONFIG_FILE_PATH)


def test_checker_ignore_precondition(monkeypatch) -> None:
    target_file_path = (
        TEST_DATA_PATH / "valid_xml_document/xml.valid_xml_document.negative.xodr"
    )
    create_test_config(_fsp(target_file_path))
    patch_checker_param(
        basic.root_tag_is_opendrive.CHECKER_ID, "ignorePreconditions", 1
    )
    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    assert (
        result.get_checker_status(basic.root_tag_is_opendrive.CHECKER_ID)
        != StatusType.SKIPPED
    )
    assert (
        result.get_checker_status(basic.version_is_defined.CHECKER_ID)
        == StatusType.SKIPPED
    )
    cleanup_files()


def _verify_failed_version_check(err_info):
    """
    verify that a failure was due to attempting to run a checker that required a version check,
    without a version being set.
    SIDE EFFECT: reverses the traceback
    """
    assert "NoneType" in str(err_info.value)
    # Find the version check in the traceback
    err_info.traceback.reverse()
    tb_entry = next(e for e in err_info.traceback if e.name == "check_version")
    # Verify that the checker was not in "basic" category (basic checkers do not depend on version)
    checker_class = tb_entry.locals["checker"].__package__.split(".")[-1]
    assert checker_class != "basic"


def _get_result_from_bundle_traceback(traceback):
    """
    In cases where a bundle run is abended (e.g. due to disabling critical preconditions),
    a report is not saved to file.
    Therefore, we need to extract the live object from the failure traceback.
    """
    entry = next(e for e in traceback if e.name == "run_checks")
    return entry.locals["checker_data"].result


def test_bundle_ignore_precondition(monkeypatch) -> None:
    target_file_path = TEST_DATA_PATH / "root_tag_is_opendrive/negative.xodr"
    create_test_config(_fsp(target_file_path))
    patch_bundle_param("ignorePreconditions", 1)

    with pytest.raises(TypeError) as err_info:
        launch_main(monkeypatch)
    _verify_failed_version_check(err_info)

    result = _get_result_from_bundle_traceback(err_info.traceback)
    assert (
        result.get_checker_status(basic.root_tag_is_opendrive.CHECKER_ID)
        != StatusType.SKIPPED
    )
    assert (
        result.get_checker_status(basic.version_is_defined.CHECKER_ID)
        != StatusType.SKIPPED
    )
    # report was not generated because of the failure, so cannot use normal cleanup
    assert not Path(REPORT_FILE_PATH).is_file()
    os.remove(CONFIG_FILE_PATH)


def test_cli_ignore_precondition(monkeypatch) -> None:
    target_file_path = TEST_DATA_PATH / "root_tag_is_opendrive/negative.xodr"
    create_test_config(_fsp(target_file_path))

    with pytest.raises(TypeError) as err_info:
        launch_main(monkeypatch, ["--ignore_preconditions"])
    _verify_failed_version_check(err_info)

    result = _get_result_from_bundle_traceback(err_info.traceback)
    assert (
        result.get_checker_status(basic.version_is_defined.CHECKER_ID)
        != StatusType.SKIPPED
    )
    # report was not generated because of the failure, so cannot use normal cleanup
    assert not Path(REPORT_FILE_PATH).is_file()
    os.remove(CONFIG_FILE_PATH)
