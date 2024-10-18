from typing import List, Dict, Any, Optional, Generator, Match, Tuple
import re
import logging

from ataims.output import Output
from ataims.structure import Structure
from ataims import common_util as util


HARTREE = 27.211386245988
BOHR = 0.529177249

float_regex = r'[-+]?[0-9]+[.][0-9]*([eE][-+]?[0-9]+)?'

logger = logging.getLogger(__name__)


def parse_float_2_aa(float_string: str) -> float:
    return BOHR * float(float_string)


def parse_float_2_ev(float_string: str) -> float:
    return HARTREE * float(float_string)


class OutputExciting(Output):
    # warning: untested
    def __init__(self):
        super().__init__()
        self.inputs: Dict[str, List[str]] = {'InputXML': []}
        self.structure_in = Structure()
        self.structure_in.lat_vectors = []
        self.system_information: Dict[str, Any] = {'formula_unit': '', 'n_atoms': 0}
        self.output: Dict[str, List[str]] = {'preamble': [], 'initialization': [], 'groundstate': [], 'finale': []}
        self.bs_data: List[Dict[str, Any]] = []

    def parse_files(self, files_data: List[Dict[str, Any]]) -> None:
        for file_data in files_data:
            if file_data['type'] in ['application/gzip', 'application/x-gzip']:
                logger.info('Workflow output for Exciting is not yet implemented')
                return
            file_name = file_data['name']
            lines = util.get_tokenized_lines(file_data['content'])

            if file_name == 'dos.xml':
                self.files.dos[file_name] = get_dos_data_exciting(file_data['content'])
                self.filled_up = True
            elif file_name == 'bandstructure.xml':
                self.bs_data = get_bs_data_exciting(file_data['content'])
                self.filled_up = True
            elif file_name == 'INFO.OUT':
                self.files.output[file_name] = file_data['content']
                self.filled_up = True
            elif file_name == 'input.xml':
                self.files.input[file_name] = file_data['content']

    def get_bs_info(self) -> Dict[str, Any]:
        return {'bs_data': self.bs_data, 'lacking_segments': []}

    def get_relaxation_series(self) -> None:
        iters, data_i, force_i, d_end, ev_i = [], [], [], 0.0, []
        for i, loop in enumerate(self.scf_loops, 1):
            if loop['is_converged']:
                iters.append(i)
                d_end = loop['final_scf_energies']['total_energy']
                data_i.append(loop['final_scf_energies']['total_energy'])
                force_i.append(loop['max_force_component'])

        self.relaxation_series = {
            'labels': iters,
            'energy': {
                "label": "Total Energy",
                "data": [abs(value - d_end) for value in data_i],
                "yAxisID": 'yscenergy',
                "fill": False,
                "borderColor": "rgb(42,45,52)",
                "lineTension": 0.1
            },
            'forces': {
                "label": "Maximum Force Component",
                "data": [abs(value) for value in force_i],
                "yAxisID": 'ymaxforce',
                "fill": False,
                "borderColor": "rgb(0,157,220)",
                "lineTension": 0.1
            }
        }

    def get_data_series(self) -> None:
        data_series = []
        for loop in self.scf_loops:
            if loop.get('iterations'):
                data_series_iteration = {
                    'effective_potential': {'label': 'Change of effective Potential', 'color': 'rgb(0,157,220)', 'data': []},
                    'total_energy': {'label': 'Change of Total Energy', 'color': 'rgb(242,100,48)', 'data': []},
                    'charge_distance': {'label': 'Charge Distance', 'color': 'rgb(42,45,52)', 'data': []},
                }
                if self.run_time_choices.get('has_forces'):
                    data_series_iteration['forces'] = {
                        'label': 'Forces', 'color': 'rgb(42,45,104)', 'data': []
                    }

                for iteration in loop['iterations']:
                    for key, entry in data_series_iteration.items():
                        if iteration.get('convergence_accuracy'):
                            entry['data'].append(iteration['convergence_accuracy'][key])

                data_series.append(data_series_iteration)

        self.data_series = data_series

    def get_results_quantities(self) -> Dict[str, float]:
        from util import get_parallelepiped_volume
        quantities = {}
        last_converged = -1
        for i, loop in enumerate(self.scf_loops):
            if loop['is_converged']:
                last_converged = i

        if last_converged >= 0:
            last_loop = self.scf_loops[last_converged]
            quantities['Total Energy (eV)'] = last_loop['final_scf_energies']['total_energy']

            if self.run_time_choices['calculation_type'] != 'relaxation':
                last_iter = last_loop['iterations'][-1]
                for key, entry in last_iter['electron_info'].items():
                    quantities[entry['info']] = entry['value']

            if self.run_time_choices.get('is_periodic'):
                quantities['Cell Volume (Å³)'] = get_parallelepiped_volume(self.structure_in.lat_vectors)

            if self.run_time_choices['calculation_type'] == 'relaxation':
                from util import geo_text_from_structure
                final_structure_text = geo_text_from_structure(last_loop['structure'])
                href = util.create_object_url(final_structure_text, 'text/plain')
                quantities['download-link'] = href

        return quantities

    def get_calculation_info(self) -> Dict[str, Dict[str, Any]]:
        quantities = {}
        info_objects = [self.calculation_info, self.final_timings, self.exit_mode]
        for info_object in info_objects:
            if info_object:
                for key, entry in info_object.items():
                    quantities[entry['info']] = entry['value']
        return quantities

    def get_input_files_map(self) -> Dict[str, str]:
        return self.files.input

    def parse_output_file(self, file_name: Optional[str] = None) -> None:
        if not self.files.output:
            return

        if not file_name:
            file_name = next(iter(self.files.output))

        file_text = self.files.output[file_name]
        self.parse_file(file_name, file_text)

    def parse_file(self, file_name: str, file_text: str) -> None:
        self.normal_parser(file_name, file_text)
        self.get_system_information()
        self.get_data_series()
        if self.run_time_choices['calculation_type'] == 'relaxation':
            self.get_relaxation_series()

    def normal_parser(self, file_name: str, file_text: str) -> None:
        # Implementation of normal_parser goes here
        # This function is quite long, so I'll provide a skeleton and you can fill in the details

        def lines_iterator(body: List[str]) -> Generator[str, None, None]:
            for line in body:
                yield line

        def parse_until(regexs: List[re.Pattern], stop_re: re.Pattern) -> Optional[List[str]]:
            lines = []
            for line in line_it:
                for regex in regexs:
                    if regex.search(line):
                        lines.append(line)
                if stop_re.search(line):
                    return lines
            self.errors.append([f"Reached end of file before finding {stop_re.pattern}"])
            return None

        def wait_for(wait_re: re.Pattern) -> Optional[str]:
            for line in line_it:
                if wait_re.search(line):
                    return line
            self.errors.append([f"Did not find the following expression {wait_re.pattern}"])
            return None

        def check_for_until(check_re: re.Pattern, stop_re: re.Pattern) -> Optional[bool]:
            for line in line_it:
                if check_re.search(line):
                    return True
                elif stop_re.search(line):
                    return False
            self.errors.append([f"Reached end of file before finding {stop_re.pattern}"])
            return None

        def match_next_line(regex: re.Pattern) -> Optional[re.Match]:
            line = next(line_it, None)
            if line is not None:
                return regex.search(line)
            return None

        def get_lines_in_between(start_re: re.Pattern, stop_re: re.Pattern) -> Optional[List[str]]:
            lines = []
            line = wait_for(start_re)
            if line is None:
                return None
            for line in line_it:
                if stop_re.search(line):
                    return lines
                lines.append(line)
            self.errors.append([f"Reached end of file before finding {stop_re.pattern}"])
            return None

        def get_calculation_info() -> Optional[Dict[str, Dict[str, str]]]:
            line = wait_for(re.compile(r'\sEXCITING'))
            if line is None:
                return None
            version = line.split()[2]
            line = wait_for(re.compile(r'version hash id'))
            if line is None:
                return None
            hash_id = line.split()[4]
            return {
                'version': {'value': version, 'info': 'Version'},
                'hashID': {'value': hash_id[:9], 'info': 'Hash Id'}
            }

        def get_calculation_type() -> None:
            rtc = self.run_time_choices
            rtc['is_periodic'] = True
            lines = parse_until(
                [re.compile(r'Ground-state run'), re.compile(r'Structural optimisation')],
                re.compile(r'Starting initialization')
            )
            if lines is None:
                return
            if re.search(r'Ground-state run', lines[0]):
                rtc['calculation_type'] = 'singlePoint'
            elif re.search(r'Structural optimisation', lines[0]):
                rtc['calculation_type'] = 'relaxation'
            if rtc['calculation_type'] == 'relaxation':
                rtc['has_forces'] = True

        def parse_initialization() -> None:
            nonlocal current_structure
            line = wait_for(re.compile(r'\s+Lattice vectors'))
            if line is None:
                return
            init_structure = Structure()
            init_structure.lat_vectors = []
            for _ in range(3):
                match = match_next_line(re.compile(float_regex))
                if match:
                    init_structure.lat_vectors.append([parse_float_2_aa(x) for x in match.groups()])

            lines = get_lines_in_between(re.compile(r'Brillouin zone volume'), re.compile(r'Total number of atoms per unit cell'))
            if lines is None:
                return

            is_position_block = False
            is_fract = False
            species = ''

            for line in lines:
                if re.search(r'Species\s', line):
                    species = re.search(r'\((.*)\)', line).group(1)
                elif re.search(r'atomic positions', line) and not is_position_block:
                    is_fract = re.search(r'\(([^)]+)\)', line).group(1) == "lattice"
                    is_position_block = True
                elif is_position_block:
                    position = re.findall(float_regex, line)
                    if position:
                        if is_fract:
                            init_structure.add_atom_data([float(x) for x in position], species.strip(), is_fract)
                        else:
                            init_structure.add_atom_data([parse_float_2_aa(x) for x in position], species.strip(), is_fract)
                    else:
                        is_position_block = False

            self.structure_in = init_structure
            current_structure = init_structure

            line = wait_for('Spin treatment')
            if line:
                spin = line.split()[4]
                if spin == 'spin-unpolarised':
                    self.run_time_choices['spin'] = 'none'
                if spin == 'spin-polarised':
                    self.run_time_choices['spin'] = 'collinear'

            line = wait_for('Ending initialization')
            if line is None:
                return

        def parse_until(regexs: List[re.Pattern], stop_re: re.Pattern) -> Optional[List[str]]:
            lines = []
            for line in line_it:
                for regex in regexs:
                    if regex.search(line):
                        lines.append(line)
                if stop_re.search(line):
                    return lines
            self.errors.append([f"Reached end of file before finding {stop_re.pattern}"])
            return None

        def wait_for(wait_re: re.Pattern) -> Optional[str]:
            for line in line_it:
                if wait_re.search(line):
                    return line
            self.errors.append([f"Did not find the following expression {wait_re.pattern}"])
            return None

        def check_for_until(check_re: re.Pattern, stop_re: re.Pattern) -> Optional[bool]:
            for line in line_it:
                if check_re.search(line):
                    return True
                elif stop_re.search(line):
                    return False
            self.errors.append([f"Reached end of file before finding {stop_re.pattern}"])
            return None

        def match_next_line(regex: re.Pattern) -> Optional[Match[str]]:
            line = next(line_it, None)
            if line is not None:
                return regex.search(line)
            return None

        def get_lines_in_between(start_re: re.Pattern, stop_re: re.Pattern) -> Optional[List[str]]:
            lines = []
            line = wait_for(start_re)
            if line is None:
                return None
            for line in line_it:
                if stop_re.search(line):
                    return lines
                lines.append(line)
            self.errors.append([f"Reached end of file before finding {stop_re.pattern}"])
            return None

        def get_calculation_info() -> Optional[Dict[str, Dict[str, Any]]]:
            line = wait_for(re.compile(r'\sEXCITING'))
            if line is None:
                return None
            version = line.split()[2]
            line = wait_for(re.compile(r'version hash id'))
            if line is None:
                return None
            hash_id = line.split()[4]
            return {
                'version': {'value': version, 'info': 'Version'},
                'hashID': {'value': hash_id[:9], 'info': 'Hash Id'}
            }

        def get_calculation_type() -> None:
            rtc = self.run_time_choices
            rtc['is_periodic'] = True
            lines = parse_until(
                [re.compile(r'Ground-state run'), re.compile(r'Structural optimisation')],
                re.compile(r'Starting initialization')
            )
            if lines is None:
                return
            if re.search(r'Ground-state run', lines[0]):
                rtc['calculation_type'] = 'singlePoint'
            elif re.search(r'Structural optimisation', lines[0]):
                rtc['calculation_type'] = 'relaxation'
            if rtc['calculation_type'] == 'relaxation':
                rtc['has_forces'] = True

        def parse_initialization() -> None:
            global current_structure
            line = wait_for(re.compile(r'\s+Lattice vectors'))
            if line is None:
                return
            init_structure = Structure()
            init_structure.lat_vectors = []
            for _ in range(3):
                match = match_next_line(re.compile(float_regex))
                if match:
                    init_structure.lat_vectors.append([parse_float_2_aa(x) for x in match.groups()])

            lines = get_lines_in_between(re.compile(r'Brillouin zone volume'), re.compile(r'Total number of atoms per unit cell'))
            if lines is None:
                return

            is_position_block = False
            is_fract = False
            species = ''

            for line in lines:
                if re.search(r'Species\s', line):
                    species = re.search(r'\((.*)\)', line).group(1)
                elif re.search(r'atomic positions', line) and not is_position_block:
                    is_fract = re.search(r'\(([^)]+)\)', line).group(1) == "lattice"
                    is_position_block = True
                elif is_position_block:
                    position = re.findall(float_regex, line)
                    if position:
                        if is_fract:
                            init_structure.add_atom_data([float(x) for x in position], species.strip(), is_fract)
                        else:
                            init_structure.add_atom_data([parse_float_2_aa(x) for x in position], species.strip(), is_fract)
                    else:
                        is_position_block = False

            self.structure_in = init_structure
            current_structure = init_structure

            line = wait_for('Spin treatment')
            if line:
                spin = line.split()[4]
                if spin == 'spin-unpolarised':
                    self.run_time_choices['spin'] = 'none'
                if spin == 'spin-polarised':
                    self.run_time_choices['spin'] = 'collinear'

            line = wait_for('Ending initialization')
            if line is None:
                return

        def get_scf_loops(run_time_choices: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
            line = wait_for('Self-consistent loop started')
            if line is None:
                return None
            is_converged, iterations = get_iterations(run_time_choices)
            first_scf_loop = {
                'is_converged': is_converged,
                'iterations': iterations,
                'structure': current_structure,
                'final_scf_energies': {}
            }
            if not is_converged:
                return [first_scf_loop]
            last_iteration = get_last_iteration()
            if not last_iteration:
                return [first_scf_loop]
            first_scf_loop['iterations'].append(last_iteration)
            first_scf_loop['final_scf_energies']['total_energy'] = last_iteration['scf_energies']['total_energy']
            if run_time_choices['calculation_type'] == 'relaxation':
                line = wait_for(re.compile(r'Maximum force magnitude'))
                if line is None:
                    return [first_scf_loop]
                first_scf_loop['max_force_component'] = float(re.search(float_regex, line).group()) * HARTREE / BOHR
            scf_loops = [first_scf_loop]
            if run_time_choices['calculation_type'] == 'relaxation':
                is_converged, relaxation_scf_loops = get_relaxation_scf_loops()
                scf_loops = [first_scf_loop] + relaxation_scf_loops
            return scf_loops
        
        def get_relaxation_scf_loops() -> Tuple[bool, List[Dict[str, Any]]]:
            """
            Get the relaxation SCF loops from the output.

            Returns:
                Tuple[bool, List[Dict[str, Any]]]: A tuple containing:
                    - bool: True if the relaxation converged, False otherwise
                    - List[Dict[str, Any]]: List of optimization steps
            """
            relaxation_scf_loops: List[Dict[str, Any]] = []
            is_not_converged = True
            while is_not_converged:
                is_not_converged = check_for_until(r'Optimization step', r'Force convergence target achieved')
                if is_not_converged is False:
                    return True, relaxation_scf_loops
                elif is_not_converged is None:
                    return False, relaxation_scf_loops
                else:
                    optimization_step = get_optimization_step()
                    if not optimization_step:
                        return False, relaxation_scf_loops
                    relaxation_scf_loops.append(optimization_step)
            
            # This line should never be reached, but we include it for completeness
            return False, relaxation_scf_loops

        def get_optimization_step() -> Optional[Dict[str, Any]]:
            """
            Get the optimization step information from the output.

            Returns:
                Optional[Dict[str, Any]]: A dictionary containing optimization step information,
                or None if the required information is not found.
            """
            optimization_step: Dict[str, Any] = {
                'final_scf_energies': {},
                'max_force_component': None,
                'is_converged': True
            }

            line = wait_for(re.compile(r'Maximum force magnitude'))
            if not line:
                return None
            optimization_step['max_force_component'] = float(re.search(float_regex, line).group()) * HARTREE / BOHR

            line = wait_for(re.compile(r'Total energy at this optimization step'))
            if not line:
                return None
            optimization_step['final_scf_energies']['total_energy'] = float(re.search(float_regex, line).group())

            lines = get_lines_in_between(re.compile(r'Atomic positions at this step'), re.compile(r'Total atomic forces'))
            if not lines:
                return None

            updated_structure = Structure()
            updated_structure.lat_vectors = current_structure.lat_vectors
            for line in lines:
                if 'atom' in line:
                    position = re.findall(float_regex, line)
                    species = line.split()[2]
                    updated_structure.add_atom_data([float(pos) for pos in position], species.strip(), True)

            optimization_step['structure'] = updated_structure
            return optimization_step

        def get_iterations(run_time_choices: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
            """
            Get iterations from the output.

            Args:
                run_time_choices (Dict[str, Any]): Runtime choices for the calculation.

            Returns:
                Tuple[bool, List[Dict[str, Any]]]: A tuple containing a boolean indicating convergence
                and a list of iteration data.
            """
            iterations: List[Dict[str, Any]] = []
            is_not_converged = True
            while is_not_converged:
                is_not_converged = check_for_until(re.compile(r'SCF iteration number'), re.compile(r'Convergence targets achieved\.'))
                if is_not_converged is False:
                    return True, iterations
                elif is_not_converged is None:
                    return False, iterations
                else:
                    iteration = get_iteration(run_time_choices)
                    if not iteration:
                        return False, iterations
                    iterations.append(iteration)
            return False, iterations  # This line should never be reached

        def get_iteration(run_time_choices: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            """
            Get data for a single iteration.

            Args:
                run_time_choices (Dict[str, Any]): Runtime choices for the calculation.

            Returns:
                Optional[Dict[str, Any]]: A dictionary containing iteration data, or None if required information is not found.
            """
            iteration: Dict[str, Any] = {
                'scf_energies': {},
                'electron_info': {}
            }

            line = wait_for(re.compile(r'Total energy'))
            if not line:
                return None
            iteration['scf_energies']['total_energy'] = parse_float_2_ev(re.search(float_regex, line).group())

            line = wait_for(re.compile(r'Fermi energy'))
            if not line:
                return None
            iteration['electron_info']['fermi_energy'] = {
                'value': parse_float_2_ev(re.search(float_regex, line).group()),
                'info': 'Fermi Energy (eV)'
            }

            conv_acc = get_conv_acc(run_time_choices)
            if not conv_acc:
                return None
            iteration['convergence_accuracy'] = conv_acc

            return iteration

        def get_last_iteration() -> Optional[Dict[str, Any]]:
            """
            Get data for the last iteration.

            Returns:
                Optional[Dict[str, Any]]: A dictionary containing the last iteration data,
                or None if required information is not found.
            """
            iteration: Dict[str, Any] = {
                'scf_energies': {},
                'electron_info': {}
            }

            line = wait_for(re.compile(r'Total energy'))
            if not line:
                return None
            iteration['scf_energies']['total_energy'] = parse_float_2_ev(re.search(float_regex, line).group())

            line = wait_for(re.compile(r'Fermi energy'))
            if not line:
                return None
            iteration['electron_info']['fermi_energy'] = {
                'value': parse_float_2_ev(re.search(float_regex, line).group()),
                'info': 'Fermi Energy (eV)'
            }

            line = wait_for(re.compile(r'Estimated fundamental gap'))
            if not line:
                return None
            iteration['electron_info']['gap'] = {
                'value': parse_float_2_ev(re.search(float_regex, line).group()),
                'info': 'Estimated fundamental gap (eV)'
            }

            return iteration

        def get_conv_acc(run_time_choices: Dict[str, Any]) -> Optional[Dict[str, float]]:
            """
            Get convergence accuracy data.

            Args:
                run_time_choices (Dict[str, Any]): Runtime choices for the calculation.

            Returns:
                Optional[Dict[str, float]]: A dictionary containing convergence accuracy data,
                or None if required information is not found.
            """
            conv_acc: Dict[str, float] = {}

            line = wait_for(re.compile(r'RMS change in effective potential'))
            if not line:
                return None
            conv_acc['effective_potential'] = float(re.search(float_regex, line).group())

            line = wait_for(re.compile(r'Absolute change in total energy'))
            if not line:
                return None
            conv_acc['total_energy'] = float(re.search(float_regex, line).group())

            line = wait_for(re.compile(r'Charge distance'))
            if not line:
                return None
            conv_acc['charge_distance'] = float(re.search(float_regex, line).group())

            if run_time_choices.get('has_forces'):
                line = wait_for(re.compile(r'Abs. change in max-nonIBS-force'))
                if not line:
                    return None
                conv_acc['forces'] = float(re.search(float_regex, line).group())

            return conv_acc

        def get_final_timings() -> Optional[Dict[str, Dict[str, Any]]]:
            line = wait_for(re.compile(r'Total time spent'))
            if line is None:
                return None
            return {
                'total_time': {
                    'value': float(re.search(float_regex, line).group()),
                    'info': 'Total Time (s)'
                }
            }

        def get_exit_mode() -> Dict[str, Dict[str, str]]:
            line = wait_for(re.compile(r'EXCITING.*stopped'))
            value = 'yes' if line else 'no'
            return {
                'exit_mode': {
                    'value': value,
                    'info': 'Calculation exited regularly'
                }
            }

        current_structure = None
        lines = file_text.split('\n')
        line_it = lines_iterator(lines)

        self.calculation_info = get_calculation_info()
        get_calculation_type()
        parse_initialization()
        self.scf_loops = get_scf_loops(self.run_time_choices)

        self.final_timings = get_final_timings()
        self.exit_mode = get_exit_mode()

    def get_system_information(self) -> None:
        n_atoms = len(self.structure_in.atoms)
        species = {}
        for atom in self.structure_in.atoms:
            sp = atom.species
            species[sp] = species.get(sp, 0) + 1
        
        formula_unit = ''.join(f"{key}{num}" if num > 1 else key for key, num in species.items())
        
        self.system_information['n_atoms'] = n_atoms
        self.system_information['formula_unit'] = formula_unit

def get_dos_data_exciting(xml_text: str) -> List[List[float]]:
    # Implementation goes here
    pass

def get_bs_data_exciting(xml_text: str) -> List[Dict[str, Any]]:
    # Implementation goes here
    pass

def get_kpoint_coords(vertexes: List[Dict[str, Any]], index: int, dist_per_unit: float) -> List[float]:
    # Implementation goes here
    pass
