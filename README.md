# at-aims - Ad hoc parser for FHI-aims output files.

This parser is designed to be a simple way to extract data from the output files of FHI-aims.

## Installation
```pip install ataims```

## Usage
FHI-aims typically outputs a single file, `aims.out`.

To parse the file, use the `parse_outputfile` function:
```python
from ataims import parse_outputfile

output = parse_outputfile('aims.out')  # returns a single OutputData object
# or
output_list = parse_outputfile('aims.out', as_set=True)  # returns a list of parsed data
```

You can access the data in the output object:
```python
# Result summary
print(output.results)
{
    'cell_volume': 572.2999274955883,
    'estimated_homo_lumo_gap': 0.01002036,
    'fermi_energy': -5.04135398,
    'highest_occupied_state': -5.04446227,
    'lowest_unoccupied_state': -5.03444191,
    'total_energy': -3013017.92658861,
}

# Calculation summary
print(output.calculation_summary)
{
    'calculation_exited_regularly': 'Yes',
    'code_version': '240507',
    'commit_number': '7e80a0c21',
    'largest_tracked_array_allocation_mb': 42.804,
    'number_of_tasks': 36,
    'peak_memory_among_tasks_mb': 326.687,
    'total_time': 10285.059,
}

# Dump entire output object to json string
print(output.dump())
# same with nested objects
print(output.results.dump())

# or a dictionary
print(output.model_dump())
print(output_list[0].model_dump())  # with `as_set=True`
```

For an example of a full output file see [examples/example_output.json](examples/example_output.json)


## Testing
```pytest```

<br/>
<br/>
<hr/>
<br/>
Development of this parser was possible thanks to the support of
<br/>
<br/>
<a href="https://atomictessellator.com">
    <img width="400" src="docs/at_logo.png" alt="Atomic Tessellator">
</a>
<br/>
<hr/>
<br/>
This project was inspired by some other brilliant FHI-aims tools:

- [aimstools](https://github.com/romankempt/aimstools/)
- [Atomic Simulation Environment (ASE)](https://gitlab.com/ase/ase)

