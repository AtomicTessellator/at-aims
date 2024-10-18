import numpy as np

# import output_parser.UserMsgBox as UserMsgBox
from .mathlib import matrix_dot, tensor_dot, add_arrays, invert33, minmax, determinant33
from .structure import Structure
# from .conf import Conf


def get_tokenized_lines(text):
    """
    Divides a text into lines and returns them in a list
    :param text: str
    :return: list of str
    """
    return text.replace(r'[ \t]+', ' ').split('\n')

# rewrite
# async def load_data_file(file_name, file_type, handler):
#     """
#     Loads a file from the application data folder and passes the content to a handler
#     :param file_name: str
#     :param file_type: str
#     :param handler: function
#     """
#     data = None
#     try:
#         response = requests.get(Conf.BASE_FOLDER + 'data/' + file_name)
#         if file_type == 'text':
#             data = response.text
#     except Exception as err:
#         print('loadDataFile error:', err)
#     handler(data)


def generate_supercell(dim_array, source_struct):
    """
    Generates a supercell of the given structure.
    :param dim_array: list of str
    :param source_struct: Structure
    :return: Structure, new structure representing the supercell
    """
    supercell_matrix = np.zeros((3, 3), dtype=int)
    if len(dim_array) == 9:
        for i in range(len(dim_array)):
            supercell_matrix[i // 3, i % 3] = int(dim_array[i])
    elif len(dim_array) == 3:
        for i in range(len(dim_array)):
            supercell_matrix[i % 3, i % 3] = int(dim_array[i])

    lattice = source_struct.lat_vectors
    super_lattice = matrix_dot(supercell_matrix, lattice, np.zeros_like(lattice))
    frac_points = lattice_points_in_supercell(supercell_matrix)

    new_struct = Structure()
    new_struct.file_source = source_struct.file_source + " (supercell)"
    new_struct.update_lattice_vectors(super_lattice, True)

    points = matrix_dot(frac_points, super_lattice, np.zeros_like(frac_points))
    for p in points:
        for atom in source_struct.atoms:
            new_cart = add_arrays(atom['position'], p)
            new_fract = [x + 1 if x < 0 else x - 1 if x >= 1 else x for x in new_struct.get_fractional_coordinates(new_cart)]
            new_position = new_struct.get_cartesian_coordinates(new_fract)
            new_struct.add_atom_data(new_position, atom['species'], False, atom['initMoment'], atom['constraint'], atom['charge'])
    return new_struct


def lattice_points_in_supercell(supercell_matrix):
    """
    Returns all lattice points of the old unit cell within the new supercell.
    :param supercell_matrix: list of lists
    :return: list of lists
    """
    diags = [[0, 0, 0], [0, 0, 1], [0, 1, 0], [1, 0, 0], [0, 1, 1], [1, 0, 1], [1, 1, 0], [1, 1, 1]]
    d_points = np.zeros_like(diags)

    matrix_dot(diags, supercell_matrix, d_points)
    mins = minmax(d_points, 0, np.min)
    maxs = [x + 1 for x in minmax(d_points, 0, np.max)]

    ranges = [np.arange(mins[i], maxs[i]) for i in range(3)]

    ar = tensor_dot(ranges[0], [[1, 0, 0]])
    br = tensor_dot(ranges[1], [[0, 1, 0]])
    cr = tensor_dot(ranges[2], [[0, 0, 1]])

    all_points = [add_arrays(ar[i], add_arrays(br[j], cr[k])) for i in range(len(ar)) for j in range(len(br)) for k in range(len(cr))]
    frac_points = matrix_dot(all_points, invert33(supercell_matrix), np.zeros_like(all_points))

    result = [p for p in frac_points if all(-1e-10 < x < 1 - 1e-10 for x in p)]
    assert len(result) == determinant33(supercell_matrix), 'We are missing some lattice points. Check precision of supercell matrix'
    return result

# async def generate_slab(slab_data, structure):
#     """
#     Generates a slab on the backend
#     :param slab_data: dict
#     :param structure: Structure
#     :return: Structure, slab structure
#     """
#     if not structure.atoms:
#         return
#     send_structure = {
#         'cell': structure.lat_vectors,
#         'positions': structure.atoms,
#         'slab_data': slab_data,
#         'fileName': structure.file_source
#     }
#     end_point = Conf.BASE_URL + ('/terminate-slab' if 'terminations' in slab_data else '/get-slab')
#     response = requests.post(end_point, headers={'Content-Type': 'application/json;charset=utf-8'}, json=send_structure)

#     if not response.ok:
#         UserMsgBox.setError('Unknown server ERROR')
#         return

#     slab_json = response.json()
#     slab_structure = get_structure_from_json(slab_json)
#     slab_structure.extraData['terminations'] = slab_json['terminations']
#     return slab_structure

# async def get_structure_info(structure):
#     """
#     Gets structure information from the backend
#     :param structure: Structure
#     :return: dict, JSON with structure information
#     """
#     structure_data = None
#     if structure.atoms:
#         send_structure = {
#             'cell': structure.lat_vectors,
#             'positions': structure.atoms,
#             'symThresh': Conf.settings['symmetryThreshold']
#         }
#         response = requests.post(Conf.BASE_URL + '/update-structure-info', headers={'Content-Type': 'application/json;charset=utf-8'}, json=send_structure)
#         if not response.ok:
#             UserMsgBox.setError('Unknown server ERROR')
#             raise Exception(f"HTTP error: {response.status}")
#         structure_data = response.json()
#     return structure_data.get('structureInfo') if structure_data else None


def get_structure_from_json(json_data):
    """
    Returns a Structure from a JSON object
    :param json_data: dict
    :return: Structure
    """
    structure = Structure()
    structure.file_source = json_data['fileName']
    structure.structure_info = json_data['structureInfo']
    structure.lat_vectors = json_data['lattice'] if json_data['lattice'] is not None else None
    for atom in json_data['atoms']:
        structure.add_atom_data(atom[0], atom[1], False, atom[3], atom[4], atom[5])  # cartesian coordinates
    return structure


def get_structure_from_file_content(file_name, file_content):
    """
    Returns a Structure from text content in a file (FHIaims geometry file)
    :param file_name: str
    :param file_content: str
    :return: Structure
    """
    file_ext = file_name.split('.')[-1]
    structure = parse_geometry_in_file_format(file_content) if file_ext == 'in' else None
    structure.file_source = file_name
    return structure


def parse_geometry_in_file_format(text):
    """
    Parses the FHIaims geometry file format and returns a Structure.
    :param text: str
    :return: Structure
    """
    VECTOR_KEYWORD = 'lattice_vector'
    ATOM_CART_KEYWORD = 'atom'
    ATOM_FRAC_KEYWORD = 'atom_frac'
    ATOM_INIT_MOMENT_KEYWORD = 'initial_moment'
    ATOM_INIT_CHARGE_KEYWORD = 'initial_charge'

    lines = get_tokenized_lines(text)
    structure = Structure()
    structure.lat_vectors = [] if VECTOR_KEYWORD in text else None

    for line in lines:
        tokens = line.strip().split(' ')
        if tokens[0] == VECTOR_KEYWORD:
            structure.lat_vectors.append([float(tokens[1]), float(tokens[2]), float(tokens[3])])
        elif tokens[0] in {ATOM_CART_KEYWORD, ATOM_FRAC_KEYWORD}:
            atom_pos = [float(tokens[1]), float(tokens[2]), float(tokens[3])]
            structure.add_atom_data(atom_pos, tokens[4], tokens[0] == ATOM_FRAC_KEYWORD)
        elif tokens[0] == ATOM_INIT_MOMENT_KEYWORD:
            structure.set_last_atom_init_moment(float(tokens[1]))
        elif tokens[0] == ATOM_INIT_CHARGE_KEYWORD:
            structure.set_last_atom_charge(float(tokens[1]))

    return structure


def get_geometry_in_texts(structure):
    # Implementation needed
    pass


def get_input_xml_texts(structure):
    # Implementation needed
    pass


def get_input_text_files_url(structure, fhi_aims=True):
    # Implementation needed
    pass


def get_geometry_files_testing(structure, fhi_aims=True):
    # Implementation needed
    pass


def deep_clone(obj):
    from copy import deepcopy
    return deepcopy(obj)


def int_validator(value):
    try:
        return int(value)
    except ValueError:
        return ''


def int_input_validator(value):
    if value in ["0", "-"]:
        return value
    try:
        return int(value)
    except ValueError:
        return ''


def float_validator(value):
    try:
        return float(value)
    except ValueError:
        return ''


def float_input_validator(value):
    if value in [".", "0", "-"]:
        return value
    try:
        return float(value)
    except ValueError:
        return ''
