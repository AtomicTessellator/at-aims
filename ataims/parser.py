import logging
from collections import defaultdict
from typing import Union, List
import traceback
from pathlib import Path

from pydantic import BaseModel, ValidationError

from ataims.output_aims import OutputAims
from ataims.util import get_output_instance
from ataims.model import OutputData
from ataims.exceptions import FHIOutputParserError


logger = logging.getLogger(__name__)


def parse_outputfile(
    filename: Union[str, Path], 
    as_set: bool = False
) -> Union[OutputData, List[BaseModel]]:
    """Parse an FHI-aims output file and return structured data.

    Args:
        filename: Path to the FHI-aims output file. Can be either a string path
            or Path object. Both absolute and relative paths are supported.
            Example paths:
                - "calculation.out"
                - "./results/calculation.out"
                - "/home/user/aims/calculation.out"
                - "C:\\Users\\name\\aims\\calculation.out"
        as_set: If True, returns a list of individual data models.
            If False, returns a single combined OutputData object.
            Defaults to True.

    Returns:
        Union[OutputData, List[BaseModel]]: 
            If as_set is False, returns an OutputData object containing all parsed data.
            If as_set is True, returns a List of individual BaseModel objects.

    Raises:
        ValueError: If the file doesn't have a .out extension
        FileNotFoundError: If the specified file doesn't exist
        PermissionError: If the file can't be accessed due to permissions
        IOError: If there's an error reading the file
        FHIOutputParserError: If there's an error parsing the FHI-aims output

    Examples:
        >>> data = parse_outputfile("calculation.out")
        >>> # Using pathlib
        >>> from pathlib import Path
        >>> path = Path("aims/outputs/calculation.out")
        >>> data = parse_outputfile(path)
    """
    # Convert to Path object for OS-independent handling
    path = Path(filename)

    # Check extension
    if path.suffix != '.out':
        raise ValueError(f"File must have a .out extension, got: {path}")

    # Resolve to absolute path to handle relative paths
    path = path.resolve()

    try:
        with path.open('r', encoding='utf-8') as f:
            data = f.read()
    except (FileNotFoundError, PermissionError, IOError) as e:
        raise


    files_data = [{'name': str(filename), 'type': 'text/plain', 'content': data}]
    output = get_output_instance(files_data)
    output.parse_output_file(str(filename))

    try:
        pydantic_class = _output_to_pydantic_class(output)
    except Exception as e:
        error_message = f"Error in FHI-aims extraction: {str(e)}\n"
        if output.errors_set:
            error_message += (max(len(k) for k in output.errors_set) * '*') + '\n'
            error_message += '\n'.join(output.errors_set)
            error_message += '\n' + (max(len(k) for k in output.errors_set) * '*') + '\n'
        error_message += f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
        raise FHIOutputParserError(error_message)

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
    data['calculation_summary']['largest_tracked_array_allocation_mb'] = output.memory.get('largestArray', {}).get('value')
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
