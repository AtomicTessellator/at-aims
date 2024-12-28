from pytest import fixture, raises

from ataims import parse_outputfile


@fixture
def filename() -> str:
    return "tests/test_files/water.out"


def test_nonperiodic(filename: str):
    output = parse_outputfile(filename)

    # Make sure the fact that the simulation terminated normally is correctly parsed
    assert len(output.errors.keys()) == 0
    assert output.calculation_summary.calculation_exited_regularly == "Yes"

    # Make sure the cell volume is not present (non-periodic simulations do not have a cell volume)
    assert output.results.cell_volume is None
