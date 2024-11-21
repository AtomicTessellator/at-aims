from pathlib import Path
import re
from typing import Union
from collections import defaultdict


# these patterns do not account for case sensitivity. that is specified later.
ERROR_PATTERNS = [
    r".*\*.*error.*" ,  # at least one asterisk followed by [stuff]error[more stuff]
    r".*syntax error.*" ,
    r".*killed by signal.*" ,

    r".*no species in .*" ,
    r".*an error led .*" ,
    r".*error reading keyword .*" ,
    r".*please correct file .*" ,
    r".*no kernel image .*" ,
    r".*\* ill-conditioned overlap matrix .*" ,
]

COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in ERROR_PATTERNS]


def match_error_patterns(line: str) -> bool:
    """Check if a line matches any of the error patterns."""
    return any(pattern.search(line) for pattern in COMPILED_PATTERNS)


def parse_error_file(filename: Union[str, Path]) -> dict[str, list[int]]:
    """Parse a file for error patterns and return a dict of errors with their line numbers."""
    error_dict = defaultdict(list)

    with open(filename, "r") as file:
        for line_num, line in enumerate(file, 1):
            if match_error_patterns(line):
                line = line.strip()
                error_dict[line].append(line_num)

    return error_dict
