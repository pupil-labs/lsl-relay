import pupil_labs.lsl_companion_relay as this_project


def test_package_metadata() -> None:
    assert hasattr(this_project, "__version__")
    assert this_project.__version__ != "unknown"
