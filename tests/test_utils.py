import pytest

from glinet_router.utils import decode_firmware_version


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("4.8.0", (4, 8, 0, 0)),
        ("v4.7.2-release6", (4, 7, 2, 6)),
        ("3", (3, 0, 0, 0)),
        ("snapshot", (0, 0, 0, 0)),
    ],
)
def test_decode_firmware_version_normalizes_to_four_numbers(
    version: str,
    expected: tuple[int, int, int, int],
) -> None:
    assert decode_firmware_version(version) == expected
