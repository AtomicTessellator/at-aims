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
from ataims.error_parser import parse_error_file


logger = logging.getLogger(__name__)


def parse_outputfile(
    filename: Union[str, Path], as_set: bool = False
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
    if path.suffix != ".out":
        raise ValueError(f"File must have a .out extension, got: {path}")

    # Resolve to absolute path to handle relative paths
    path = path.resolve()

    try:
        with path.open("r", encoding="utf-8") as f:
            data = f.read()
    except (FileNotFoundError, PermissionError, IOError) as e:
        raise

    files_data = [{"name": str(filename), "type": "text/plain", "content": data}]
    output = get_output_instance(files_data)
    output.parse_output_file(str(filename))

    try:
        pydantic_class = _output_to_pydantic_class(output)
    except Exception as e:
        error_message = f"Error in FHI-aims extraction: {str(e)}\n"
        if output.errors_set:
            error_message += (max(len(k) for k in output.errors_set) * "*") + "\n"
            error_message += "\n".join(output.errors_set)
            error_message += "\n" + (max(len(k) for k in output.errors_set) * "*") + "\n"
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
    data["system_information"] = output.system_information

    # Results
    data["results"] = output.get_results_quantities()

    # Calculation summary
    output.get_calculation_info()
    # Handle case where calculation_info is None or missing
    calculation_info = getattr(output, "calculation_info", None) or {}
    data["calculation_summary"]["code_version"] = calculation_info.get("codeVersion", {}).get(
        "value"
    )
    data["calculation_summary"]["commit_number"] = calculation_info.get("commitNumber", {}).get(
        "value"
    )
    data["calculation_summary"]["number_of_tasks"] = calculation_info.get("numberOfTasks", {}).get(
        "value"
    )
    # summary data can be missing due to the analysis not completing normally
    # Handle case where memory attribute is None or missing
    memory_data = getattr(output, "memory", None) or {}
    data["calculation_summary"]["peak_memory_among_tasks_mb"] = memory_data.get(
        "peakMemory", {}
    ).get("value")
    data["calculation_summary"]["largest_tracked_array_allocation_mb"] = memory_data.get(
        "largestArray", {}
    ).get("value")
    # Handle case where final_timings is None or missing
    final_timings = getattr(output, "final_timings", None) or {}
    data["calculation_summary"]["total_time"] = final_timings.get("totalTime", {}).get("value")

    # maxmimum force component
    data["maximum_force_component"] = (
        output.relaxation_series if hasattr(output, "relaxation_series") else None
    )

    # eigenvalues, totalenergy, chargedensity
    output.get_data_series()
    data["change_of_sum_of_eigenvalues"] = getattr(output, "data_series", None)

    # errors - handle missing exit_mode
    exit_mode = getattr(output, "exit_mode", None) or {}
    terminated_normally_bool = exit_mode.get("normalTermination", False)
    data["calculation_summary"]["calculation_exited_regularly"] = (
        "Yes" if terminated_normally_bool else "No"
    )
    if not terminated_normally_bool:
        parser_errors = set()
        # Handle case where errors is None or missing
        errors = getattr(output, "errors", None) or []
        [parser_errors.add(error[0]) for error in errors if error]
        logger.debug(f"Simulation did not terminate normally!")
        logger.debug(f"Parsing errors: {parser_errors}")
        output.scan_for_errors()  # added error parsing
        # Handle case where errors_set is None or missing
        errors_set = getattr(output, "errors_set", None) or set()
        if errors_set:
            raise Exception("Critical errors detected in output file")

    # errors that fhiaims writes - handle missing files
    files = getattr(output, "files", None) or {}
    output_files = files.get("output", {})
    if output_files:
        filename = next(iter(output_files))
        error_lines = parse_error_file(filename)
    else:
        error_lines = {}
    data["errors"] = error_lines

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
