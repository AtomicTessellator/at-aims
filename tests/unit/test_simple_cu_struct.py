import pytest
from unittest.mock import Mock, patch
from ataims import parse_outputfile, FHIOutputParserError
from ataims.output_aims import OutputAims


def test_parse_cu_out_file_with_missing_memory_attribute():
    """Test that parsing cu.out fails due to validation errors, but NOT due to memory attribute issues."""
    cu_out_path = "tests/test_files/cu.out"
    
    # The cu.out file has incomplete data, so it should fail validation
    # But it should NOT fail due to memory attribute access issues
    with pytest.raises(FHIOutputParserError) as exc_info:
        parse_outputfile(cu_out_path, as_set=False)
    
    # Verify that the error is NOT about memory attribute access
    error_message = str(exc_info.value)
    assert "'NoneType' object has no attribute 'get'" not in error_message
    # The error should be about validation, not AttributeError
    assert "validation error" in error_message.lower() or "field required" in error_message.lower()


@patch('ataims.parser.parse_error_file')
def test_parse_cu_out_file_with_mocked_complete_data(mock_parse_error):
    """Test that parsing works when all required data is provided."""
    cu_out_path = "tests/test_files/cu.out"
    
    # Mock the error file parsing
    mock_parse_error.return_value = {}
    
    # Mock the output to provide all required data
    with patch('ataims.parser.get_output_instance') as mock_get_output:
        # Create a mock output object with complete data
        mock_output = Mock(spec=OutputAims)
        mock_output.system_information = {}
        
        # Mock complete results data
        mock_output.get_results_quantities.return_value = {
            'Total Energy (eV)': -100.5,
            'Fermi Energy (eV)': -5.2,
            'Highest occupied state (eV)': -5.0,
            'Lowest unoccupied state (eV)': -3.0,
            'Estimated HOMO-LUMO gap (eV)': 2.0
        }
        
        mock_output.get_calculation_info.return_value = None
        mock_output.calculation_info = {
            'codeVersion': {'value': '240920'},
            'commitNumber': {'value': 'c0120a398'},
            'numberOfTasks': {'value': 16}
        }
        
        # Mock memory data to test the fix
        mock_output.memory = {'peakMemory': {'value': 100.5}, 'largestArray': {'value': 50.2}}
        mock_output.final_timings = {'totalTime': {'value': 123.45}}
        mock_output.relaxation_series = None
        mock_output.get_data_series.return_value = None
        mock_output.data_series = [{
            'eigenvalues': {'data': [1.0, 2.0], 'label': 'eigenvalues'},
            'totalEnergy': {'data': [-100.0, -100.5], 'label': 'totalEnergy'}
        }]
        mock_output.exit_mode = {'normalTermination': True}
        mock_output.errors = []
        mock_output.errors_set = set()
        mock_output.files = {'output': {'test_file': 'content'}}
        mock_output.parse_output_file.return_value = None
        
        mock_get_output.return_value = mock_output
        
        # This should work and return memory values
        result = parse_outputfile(cu_out_path, as_set=False)
        assert result is not None
        assert result.calculation_summary.peak_memory_among_tasks_mb == 100.5
        assert result.calculation_summary.largest_tracked_array_allocation_mb == 50.2


@patch('ataims.parser.parse_error_file')
def test_parse_cu_out_file_handles_none_memory_gracefully(mock_parse_error):
    """Test that we can handle None memory attribute gracefully without AttributeError."""
    cu_out_path = "tests/test_files/cu.out"
    
    # Mock the error file parsing
    mock_parse_error.return_value = {}
    
    # Mock the output with None memory but complete other data
    with patch('ataims.parser.get_output_instance') as mock_get_output:
        mock_output = Mock(spec=OutputAims)
        mock_output.system_information = {}
        
        # Mock complete results data
        mock_output.get_results_quantities.return_value = {
            'Total Energy (eV)': -100.5,
            'Fermi Energy (eV)': -5.2,
            'Highest occupied state (eV)': -5.0,
            'Lowest unoccupied state (eV)': -3.0,
            'Estimated HOMO-LUMO gap (eV)': 2.0
        }
        
        mock_output.get_calculation_info.return_value = None
        mock_output.calculation_info = {
            'codeVersion': {'value': '240920'},
            'commitNumber': {'value': 'c0120a398'},
            'numberOfTasks': {'value': 16}
        }
        
        # Set memory to None to test the fix
        mock_output.memory = None
        mock_output.final_timings = {'totalTime': {'value': 123.45}}
        mock_output.relaxation_series = None
        mock_output.get_data_series.return_value = None
        mock_output.data_series = [{
            'eigenvalues': {'data': [1.0, 2.0], 'label': 'eigenvalues'},
            'totalEnergy': {'data': [-100.0, -100.5], 'label': 'totalEnergy'}
        }]
        mock_output.exit_mode = {'normalTermination': True}
        mock_output.errors = []
        mock_output.errors_set = set()
        mock_output.files = {'output': {'test_file': 'content'}}
        mock_output.parse_output_file.return_value = None
        
        mock_get_output.return_value = mock_output
        
        # This should work now that memory can be None
        result = parse_outputfile(cu_out_path, as_set=False)
        assert result is not None
        assert result.calculation_summary.peak_memory_among_tasks_mb is None
        assert result.calculation_summary.largest_tracked_array_allocation_mb is None


@patch('ataims.parser.parse_error_file')
def test_memory_attribute_access_directly(mock_parse_error):
    """Test the specific memory attribute access fix directly."""
    from ataims.parser import _output_to_pydantic_class
    
    # Mock the error file parsing
    mock_parse_error.return_value = {}
    
    # Test with None memory
    mock_output = Mock(spec=OutputAims)
    mock_output.system_information = {}
    mock_output.get_results_quantities.return_value = {
        'Total Energy (eV)': -100.5,
        'Fermi Energy (eV)': -5.2,
        'Highest occupied state (eV)': -5.0,
        'Lowest unoccupied state (eV)': -3.0,
        'Estimated HOMO-LUMO gap (eV)': 2.0
    }
    mock_output.get_calculation_info.return_value = None
    mock_output.calculation_info = {
        'codeVersion': {'value': '240920'},
        'commitNumber': {'value': 'c0120a398'},
        'numberOfTasks': {'value': 16}
    }
    mock_output.memory = None  # This should not cause AttributeError anymore
    mock_output.final_timings = {'totalTime': {'value': 123.45}}
    mock_output.relaxation_series = None
    mock_output.get_data_series.return_value = None
    mock_output.data_series = [{
        'eigenvalues': {'data': [1.0, 2.0], 'label': 'eigenvalues'},
        'totalEnergy': {'data': [-100.0, -100.5], 'label': 'totalEnergy'}
    }]
    mock_output.exit_mode = {'normalTermination': True}
    mock_output.errors = []
    mock_output.errors_set = set()
    mock_output.files = {'output': {'test_file': 'content'}}
    
    # This should work now - no AttributeError about memory.get()
    result = _output_to_pydantic_class(mock_output)
    assert result is not None
    assert result.calculation_summary.peak_memory_among_tasks_mb is None
    assert result.calculation_summary.largest_tracked_array_allocation_mb is None
