from pytest import fixture, raises

from ataims import parse_outputfile, OutputData
from ataims.output_aims import OutputAims
from ataims.exceptions import FHIOutputParserError
from tests.test_files import expected


@fixture
def filename() -> str:
    return 'd7ef4d09-9db2-40bf-bcdb-079c20700c58.out'


@fixture
def output_file(filename) -> str:
    return f'tests/test_files/{filename}'


@fixture
def output_file_with_errors() -> str:
    return 'tests/test_files/04f18ef0-9686-44c3-b447-38780479188b.out'


@fixture
def output_instance(output_file: str) -> OutputData:
    return parse_outputfile(output_file, as_set=False)


def test_get_results_quantities(output_instance: OutputData):
    assert output_instance.results.model_dump() == expected.results


def test_calculation_summary(output_instance: OutputData):
    assert output_instance.calculation_summary.model_dump() == expected.calculation_summary

    # assert output.calculation_summary.code_version == '240507'
    # assert output.calculation_summary.commit_number == '7e80a0c21'
    # assert output.calculation_summary.number_of_tasks == 36
    # assert isinstance(output.calculation_summary.total_time, float)
    # assert output.calculation_summary.peak_memory_among_tasks_mb == 326.687
    # assert output.calculation_summary.largest_tracked_array_allocation_mb == 42.804
    # assert output.calculation_summary.calculation_exited_regularly == 'Yes'


def test_change_of_sum_of_eigenvalues(output_instance: OutputAims):
    assert len(output_instance.change_of_sum_of_eigenvalues) == 11
    assert output_instance.change_of_sum_of_eigenvalues[0].charge_density.data[0] == expected.change_of_sum_of_eigenvalues['charge_density']['data'][0]
    assert output_instance.change_of_sum_of_eigenvalues[0].eigen_values.data[0] == expected.change_of_sum_of_eigenvalues['eigen_values']['data'][0]
    assert output_instance.change_of_sum_of_eigenvalues[0].total_energy.data[0] == expected.change_of_sum_of_eigenvalues['total_energy']['data'][0]


def test_maximum_force_component(output_instance: OutputAims):
    assert output_instance.maximum_force_component.forces.data[0] == expected.maximum_force_component['forces']['data'][0]
    assert output_instance.maximum_force_component.energy.data[0] == expected.maximum_force_component['energy']['data'][0]


def test_file_with_errors(output_file_with_errors: str):
    with raises(FHIOutputParserError):
        parse_outputfile(output_file_with_errors, as_set=False)