from ataims.error_parser import match_error_patterns


def test_match_error_patterns():
    error_lines = [
        ("** ERROR **", "Error in simulation output - see logs"),
        ("* Error: k-grid not specified!", "k-grid not specified"),
        ("*** parse_control: ! No species in control.in.", "No species in control.in"),
        ("An error led to a call to aims_stop", "An error led to a call to aims_stop - see logs"),
        ("Error reading keyword argument in control.in", "Error reading keyword argument in control.in"),
        ("Syntax error reading 'control.in'", "Syntax error reading 'control.in'"),
        ("Please correct file control.in", "Please correct file control.in - see logs for specifics"),
        ("* Error:", "Error detected in simulation output - see logs for specifics"),
        ("no kernel image is available for execution on the device", "CUDA compatibility error - unsupported architecture"),
        ("*** CUDA Error", "CUDA Error detected in simulation output"),
        ("list-directed I/O syntax error", "list-directed I/O syntax error"),
        ("KILLED BY SIGNAL: 9 (Killed)", "Killed by signal 9"),
        ("*** Ill-conditioned overlap matrix found.", "Ill-conditioned overlap matrix found"),

        ("*** CUBLAS Error in /workspaces/fhi-aims-build/FHIaims2024/src/gpu/CUDA/gpuDensity.cu at line 371", "CUBLAS Error")
    ]

    for error_text, _ in error_lines:
        assert match_error_patterns(error_text), f"Failed to match pattern: {error_text}"


def test_false_positive_errors():
    false_positive_errors = [
        """Use the "compensate_multipole_errors" flag to change this behaviour.""",
        """  | Charge integration error                      :      -0.0045741909""",
        """  | error in Hartree potential    :           0.00000000 Ha           0.00000000 eV""",
        """Preferred method for the eigenvalue solver ('KS_method') not specified in 'control.in'.""",
        """The contents of geometry.in will be repeated verbatim below""",
    ]

    for error_text in false_positive_errors:
        assert not match_error_patterns(error_text), f"False positive error matched: {error_text}"
