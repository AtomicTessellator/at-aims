import logging
from pydantic import ValidationError, BaseModel
from collections import defaultdict
from typing import Union, List
import traceback

from ataims.output_aims import OutputAims
from ataims.util import get_output_instance
from ataims.model import OutputData
from ataims.exceptions import FHIOutputParserError


logger = logging.getLogger(__name__)


def parse_outputfile(filename: str, as_set=True) -> Union[OutputData, List[BaseModel]]:
    """Given a filename, returns a set of pydantic classes with pertinent data from a .out file.

    Data can be serialized with .model_dump_json() or .model_dump()

    Args:
        filename (str): Path to the output file.
        as_set (bool, optional): If True, returns a list of pydantic classes. Defaults to True.

    Returns:
        Union[OutputData, List[BaseModel]]: 
            If as_set is False, returns an OutputData object.
            If as_set is True, returns a List of BaseModel objects.

    Raises:
        ValidationError: If the output data is not valid.
        Exception: If there is an unexpected error.
    """
    if not filename.endswith('.out'):
        raise ValueError("File must have a .out extension")

    with open(filename, 'r') as f:
        data = f.read()  # we have lots of memory

    files_data = [{'name': filename, 'type': 'text/plain', 'content': data}]
    output = get_output_instance(files_data)
    output.parse_output_file(filename)
    pydantic_class = _output_to_pydantic_class(output)
    if as_set:
        return [
            pydantic_class.results,
            pydantic_class.calculation_summary,
            pydantic_class.maximum_force_component,
            pydantic_class.change_of_sum_of_eigenvalues,
        ]
    else:
        return pydantic_class


def _output_to_pydantic_class(output: OutputAims) -> OutputData:
    """
    Converts the output of the outputparser (OutputAims instance) to a pydantic class.

    This function extracts various pieces of information from the OutputAims instance
    and organizes them into a structured format that can be validated using the
    OutputData pydantic model.

    Args:
        output (OutputAims): An instance of OutputAims containing parsed output data.

    Returns:
        OutputData: A validated pydantic model containing the structured output data.

    Raises:
        FHIOutputParserError: If there's an error during the extraction of FHI-aims data.
        ValidationError: If the extracted data fails to validate against the OutputData model.
        Exception: For any unexpected errors during the validation process.
    """
    data = defaultdict(dict)
    try:
        # System information
        data['system_information'] = output.system_information

        # Results 
        data['results'] = output.get_results_quantities()

        # Calculation summary
        output.get_calculation_info()
        data['calculation_summary']['code_version'] = output.calculation_info['codeVersion']['value']
        data['calculation_summary']['commit_number'] = output.calculation_info['commitNumber']['value']
        data['calculation_summary']['number_of_tasks'] = output.calculation_info['numberOfTasks']['value']
        # summary data can be missing due to the analysis not completing normally
        data['calculation_summary']['peak_memory_among_tasks_mb'] = output.memory['peakMemory']['value']
        data['calculation_summary']['largest_tracked_array_allocation_mb'] = output.memory['largestArray']['value']
        data['calculation_summary']['total_time'] = output.final_timings['totalTime']['value'] if output.final_timings else None

        # maxmimum force component
        data['maximum_force_component'] = output.relaxation_series if hasattr(output, 'relaxation_series') else None

        # eigenvalues, totalenergy, chargedensity
        output.get_data_series()
        data['change_of_sum_of_eigenvalues'] = output.data_series
        # errors
        terminated_normally_bool = output.exit_mode['normalTermination']
        data['calculation_summary']['calculation_exited_regularly'] = "Yes" if terminated_normally_bool else "No"
        if not terminated_normally_bool:
            output.scan_for_errors()  # added error parsing
            if output.errors_set:
                raise Exception("Critical errors detected in output file")
    except Exception as e:
        error_message = f"Error in FHI-aims extraction: {str(e)}\n"
        if output.errors_set:
            error_message += (max(len(k) for k in output.errors_set) * '*') + '\n'
            error_message += '\n'.join(output.errors_set)
            error_message += '\n' + (max(len(k) for k in output.errors_set) * '*') + '\n'
        error_message += f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
        raise FHIOutputParserError(error_message)

    # validation
    try:
        validated_data = OutputData.model_validate(data)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error validating output data: {e}")
        raise e
    return validated_data


__all__ = ['parse_outputfile', 'FHIOutputParserError']
