import json
from pprint import pprint
from ataims import parse_outputfile


# parse FHI aims output file into a pydantic class
output = parse_outputfile(
    'tests/test_files/d7ef4d09-9db2-40bf-bcdb-079c20700c58.out',
    as_set=False)  # as_set returns a list of each section of data

pprint(output.dump())  # dumps json
# output.model_dump()  # dumps a dict

with open('output.json', 'w') as f:
    json.dump(output.model_dump(), f)
