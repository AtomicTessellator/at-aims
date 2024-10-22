from typing import List, Dict, Any, Optional, Tuple, Generator, Union
import re
import logging

from ataims.output import Output
from ataims.structure import Structure
from ataims import common_util as util
# import output_parser.user_msg_box as UserMsgBox


logger = logging.getLogger(__name__)


class OutputAims(Output):
    def __init__(self):
        super().__init__()
        __slots__ = [
            'inputs',
            'output',
            'no_soc',
            'is_gw',
            'segments_map',
            'band_names',
            'float_regex',
            'errors_set'
        ]

        self.inputs: Dict[str, List[str]] = {'controlIn': [], 'geometryIn': []}
        self.output: Dict[str, List[str]] = {'body': [], 'finale': []}
        self.no_soc: bool = False
        self.is_gw: bool = False
        self.segments_map: Dict[str, Any] = {}
        self.band_names: List[str] = []
        self.float_regex = r'-?\d+\.\d+(?:[eE][-+]?\d+)?'
        # error lines are redundant
        self.errors_set = set()

    def parse_files(self, files_data: List[Dict[str, Any]]) -> 'OutputAims':
        if len(files_data) == 1 and 'gzip' in files_data[0]['type']:
            # TODO: replace this method
            pass
            # data = await self.prepare_workflow_outputs(files_data[0])
            # return self._parse(data, True)
        else:
            return self._parse(files_data, False)

    async def prepare_workflow_outputs(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        response = await util.fetch('/upload-workflow', method='POST', body=file_data['content'])
        if not response.ok:
            # UserMsgBox.set_error('Unknown server ERROR')
            return {}
        text = await response.text()
        return util.json_loads(text)

    def _parse(self, files_data: List[Dict[str, Any]], is_workflow: bool = False) -> 'OutputAims':
        import os
        for file_data in files_data:
            file_name = file_data['name']
            is_band_file = 'band' in file_name if is_workflow else file_name.startswith('band')
            is_gw_band_file = 'GW_band' in file_name if is_workflow else file_name.startswith('GW_band')
            if is_band_file and file_name.endswith('.out'):
                self.band_names.append(file_name)
            if is_band_file and file_name.endswith('.no_soc'):
                self.band_names.append(file_name)
                self.no_soc = True
            if is_gw_band_file and file_name.endswith('.out'):
                self.is_gw = True
                self.band_names.append(file_name)

        logger.info(f"{self.band_names}: no SOC - {self.no_soc}, is GW - {self.is_gw}")

        for file_data in files_data:
            file_name = file_data['name']
            workflow_idx = None
            if is_workflow:
                workflow = os.path.dirname(file_name)
                if workflow not in self.workflows:
                    self.workflows.append(workflow)
                workflow_idx = self.workflows.index(workflow)
            is_band_file = 'band' in file_name if is_workflow else file_name.startswith('band')
            is_gw_band_file = 'GW_band' in file_name if is_workflow else file_name.startswith('GW_band')
            lines = util.get_tokenized_lines(file_data['content'])

            if re.match(r'KS_DOS_total(_tetrahedron)?.dat', file_name) or \
               re.match(r'_proj_dos(_tetrahedron)?\.dat(\.no_soc)?', file_name) or \
               re.match(r'atom_proj(ected)?_dos(_tetrahedron)?_[A-Z][a-z]?[0-9]{4}\.dat(\.no_soc)?', file_name):
                self.files['dos'][file_name] = self.get_tabulated_data_fhi_aims(lines)
                self.filled_up = True
            elif re.match(r'_proj_dos(_tetrahedron)?_spin_(up|dn)\.dat(\.no_soc)?', file_name):
                alt_file_name = file_name.replace('_spin_up', '').replace('_spin_dn', '')
                if alt_file_name in self.files['dos']:
                    data = self.files['dos'][alt_file_name]
                    data_new = self.get_tabulated_data_fhi_aims(lines)
                    for i, line in enumerate(data_new):
                        if 'spin_up' in file_name:
                            data[i][1] = line[1]
                        else:
                            data[i][2] = line[1]
                else:
                    data = []
                    for line in self.get_tabulated_data_fhi_aims(lines):
                        if 'spin_up' in file_name:
                            data.append([line[0], line[1], 0.0])
                        else:
                            data.append([line[0], 0.0, line[1]])
                    self.files['dos'][alt_file_name] = data
                self.filled_up = True
                self.run_time_choices['has_spin'] = True
            elif re.match(r'absorption(_soc)?(_Lorentzian)?(_Tetrahedron)?_[0-9].[0-9]{4}(_x_x)?(_y_y)?(_z_z)?.out', file_name):
                self.files['absorption'][file_name] = self.get_tabulated_data_fhi_aims(lines)
                self.filled_up = True
            elif re.match(r'dielectric_function(_soc)?(_Lorentzian)?(_Tetrahedron)?_[0-9].[0-9]{4}(_x_x)?(_y_y)?(_z_z)?(_x_y)?(_x_z)?(_y_z)?.out', file_name):
                self.files['dielectric'][file_name] = self.get_tabulated_data_fhi_aims(lines)
                self.filled_up = True
            elif (is_band_file or is_gw_band_file) and file_name.endswith('.out'):
                self.add_bs_file_data(file_name, self.segments_map, lines, is_gw_band_file, workflow_idx)
                self.filled_up = True
            elif 'control.in' in file_name:
                self.files['input'][file_name] = file_data['content']
                self.control_in = lines
            elif 'geometry.in' in file_name:
                self.files['input'][file_name] = file_data['content']
            elif 'Invoking FHI-aims ...' in file_data['content']:
                self.files['output'][file_name] = file_data['content']
                self.filled_up = True

        return self

    @staticmethod
    def get_tabulated_data_fhi_aims(lines: List[str]) -> List[List[float]]:
        data = []
        for line in lines:
            if not line.startswith('#') and len(line.strip()) > 1:
                a = [float(x) for x in line.strip().split()]
                data.append(a)
        return data

    @staticmethod
    def add_bs_file_data(full_file_name: str, segments_map: Dict[str, Any], lines: List[str], is_gw: bool, index: Optional[int] = None) -> None:
        import os
        file_name = os.path.basename(full_file_name)
        segment_num_ind = [5, 8] if not is_gw else [8, 11]
        spin_index_ind = 4 if not is_gw else 7
        segment_num = file_name[segment_num_ind[0]:segment_num_ind[1]]
        spin_index = 0
        if index is None:
            if file_name.endswith(".no_soc"):
                spin_index = int(file_name[spin_index_ind])
            elif file_name.endswith(".out"):
                spin_index = int(file_name[spin_index_ind]) - 1
        else:
            spin_index = index

        if segment_num not in segments_map:
            segments_map[segment_num] = {
                'segment_num': int(segment_num),
                'band_k_points': [],
                'band_energies': [[], [], []],
                'bs_name': [[], [], []],
                'segment_name': [[], [], []]
            }
        segment_data = segments_map[segment_num]

        file_name_token = file_name[:segment_num_ind[0]] + '***' + file_name[segment_num_ind[1]:]
        segment_data['bs_name'][spin_index].append(file_name_token)
        segment_data['segment_name'][spin_index].append(file_name)

        k_point_flag = spin_index if len(segment_data['band_k_points']) == 0 else None
        for line in lines:
            if len(line.strip()) > 1:
                a = [float(x) for x in line.strip().split()]
                if spin_index == k_point_flag:
                    segment_data['band_k_points'].append(a[1:4])
                segment_data['band_energies'][spin_index].append([e for i, e in enumerate(a[4:]) if i % 2 == 1])

    def get_bs_info(self) -> Dict[str, Any]:
        if not hasattr(self, 'bs_info'):
            if self.control_in:
                self.bs_info = self.find_lacking_segments(self.control_in, self.segments_map)
            else:
                self.bs_info = self.find_lacking_segments(None, self.segments_map)
        self.bs_info['has_spin'] = (self.run_time_choices['spin'] == "collinear")
        self.bs_info['has_soc'] = self.run_time_choices['has_soc']
        return self.bs_info

    def parse_output_file(self, file_name: Optional[str] = None) -> None:
        if len(self.files['output']) == 0:
            return

        control_in_lines = self.control_in

        if not file_name:
            file_name = next(iter(self.files['output']))

        file_text = self.files['output'][file_name]
        self.parse_file(file_name, file_text)

        if not control_in_lines:
            control_in_lines = self.inputs['controlIn']   
        # this finds and passes "'  # FHI-aims relaxation template'", unclear if it matters for our purposes
        self.bs_info = self.find_lacking_segments(control_in_lines, self.segments_map)

    @staticmethod
    def find_lacking_segments(control_in: Optional[List[str]], segments_map: Dict[str, Any]) -> Dict[str, Any]:
        lacking_segments = []
        bs_data = []

        if control_in:
            lacking_segments = OutputAims.add_segment_labels_to_bs(control_in, segments_map)

        segment_nums = sorted(segments_map.keys())
        for segment_num in segment_nums:
            bs_data.append(segments_map[segment_num])

        # Find missing segments
        if segment_nums:
            max_num = int(segment_nums[-1])
            for i in range(1, max_num + 1):
                code = OutputAims.get_file_code_from_number(i)
                if code not in segment_nums:
                    lacking_segments.append(code)

        return {'lacking_segments': lacking_segments, 'bs_data': bs_data}

    @staticmethod
    def add_segment_labels_to_bs(lines: List[str], segments_map: Dict[str, Any]) -> List[str]:
        segments_labels = []
        lacking_segments = []

        for line in lines:
            a = line.strip().split()
            if len(a) >= 4 and a[0] == 'output' and a[1] == 'band':
                segments_labels.append(a[-2:])

        for i, label in enumerate(segments_labels):
            key = OutputAims.get_file_code_from_number(i + 1)
            if key in segments_map:
                segments_map[key]['band_segm_labels'] = label
            else:
                lacking_segments.append(key)

        return lacking_segments

    @staticmethod
    def get_file_code_from_number(n: int) -> str:
        return f'00{n}' if n < 10 else f'0{n}'

    def parse_file(self, file_name: str, file_text: str) -> None:
        self.normal_parser(file_text)
        self.ks_ev = self.get_ks_ev(file_text)
        self.get_data_series()
        if self.run_time_choices['calculationType'] == 'relaxation':
            self.get_relaxation_series()

    def get_data_series(self) -> None:
        data_series = []

        for loop in self.scf_loops:
            has_iter = loop.get('iterations') and len(loop['iterations']) > 0
            if has_iter:
                data_series_iteration = {
                    'eigenvalues': {'label': 'Change of Eigenvalues', 'color': 'rgb(0,157,220)', 'data': []},
                    'totalEnergy': {'label': 'Change of Total Energy', 'color': 'rgb(242,100,48)', 'data': []},
                }
                if self.run_time_choices['spin'] == 'collinear':
                    data_series_iteration['chargeDensityUp'] = {'label': 'Change of Charge Density', 'color': 'rgb(42,45,52)', 'data': []}
                    data_series_iteration['chargeDensityDown'] = {'label': 'Change of Spin Density', 'color': 'rgb(84,45,52)', 'data': []}
                else:
                    data_series_iteration['chargeDensity'] = {'label': 'Change of Charge Density', 'color': 'rgb(42,45,52)', 'data': []}

                for iteration in loop['iterations']:
                    for key, entry in data_series_iteration.items():
                        entry['data'].append(iteration['convergenceAccuracy'][key])

                data_series.append(data_series_iteration)

        self.data_series = data_series

    def get_relaxation_series(self) -> None:
        iters, data_i, force_i = [], [], []
        d_end = 0.0
        logging.debug(f"Number of SCF loops: {len(self.scf_loops)}")
        for i, loop in enumerate(self.scf_loops, 1):
            logging.debug(f"Processing loop {i}")
            logging.debug(f"Loop keys: {loop.keys()}")
            logging.debug(f"isConverged: {loop.get('isConverged', 'Not found')}")
            if loop.get('isConverged', False):
                iters.append(i)
                if 'finalScfEnergies' in loop and 'totalEnergy' in loop['finalScfEnergies']:
                    energy = loop['finalScfEnergies']['totalEnergy']
                    data_i.append(energy)
                    if i == len(self.scf_loops):  # Last iteration
                        d_end = energy
                else:
                    logging.warning(f"Missing 'finalScfEnergies' or 'totalEnergy' in loop {i}")
                if 'maxForceComponent' in loop:
                    force_i.append(loop['maxForceComponent'])
                else:
                    logging.warning(f"Missing 'maxForceComponent' in loop {i}")
        logging.debug(f"Processed {len(iters)} converged iterations")

        if not iters:
            logging.warning("No converged iterations found. Check if this is a relaxation calculation.")
            return

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
                "data": [abs(force) for force in force_i],
                "yAxisID": 'ymaxforce',
                "fill": False,
                "borderColor": "rgb(0,157,220)",
                "lineTension": 0.1
            }
        }

    def get_structure(self) -> Optional[Structure]:
        from .util import line_array_to_text
        geometry_in_text = None
        if self.inputs['geometryIn']:
            geometry_in_text = line_array_to_text(self.inputs['geometryIn'])
        elif self.files['input'].get('geometry.in'):
            geometry_in_text = self.files['input']['geometry.in']

        if geometry_in_text:
            return util.get_structure_from_file_content('geometry.in', geometry_in_text)
        return None

    def get_results_quantities(self) -> Dict[str, Any]:
        quantities = {}
        last_converged = -1
        for loop in self.scf_loops:
            if loop['isConverged']:
                last_converged += 1

        if last_converged >= 0:
            last_loop = self.scf_loops[last_converged]
            last_iter = last_loop['iterations'][-1]
            quantities['Total Energy (eV)'] = last_loop['finalScfEnergies']['totalEnergy']

            for entry in last_iter['electronInfo'].values():
                quantities[entry['info']] = entry['value']

            if self.run_time_choices['is_periodic']:
                from .util import get_parallelepiped_volume
                quantities['Cell Volume (&#197;<sup>3</sup>)'] = float(get_parallelepiped_volume(self.structure_in.lat_vectors))

            if self.run_time_choices['calculationType'] == 'relaxation':
                from .util import geo_text_from_structure
                final_structure_text = geo_text_from_structure(last_loop['structure'])
                # not needed for now
                # href = util.create_blob_url(final_structure_text, 'text/plain')
                # quantities['download-link'] = href

        return quantities

    def get_input_files_map(self) -> Dict[str, str]:
        from .util import line_array_to_text
        input_files_map = {}
        if self.inputs['geometryIn']:
            input_files_map['geometry.in'] = line_array_to_text(self.inputs['geometryIn'])
        if self.inputs['controlIn']:
            input_files_map['control.in'] = line_array_to_text(self.inputs['controlIn'])

        for name, content in self.files['input'].items():
            if name not in input_files_map:
                input_files_map[name] = content

        return input_files_map

    def get_run_time_choices(self) -> None:
        rtc = self.run_time_choices
        rtc['output_level'] = 'normal'  # Set a default value
        for line in self.inputs['controlIn']:
            trim_line = line.strip()

            if trim_line.startswith('relax_geometry'):
                rtc['calculationType'] = 'relaxation'
                rtc['has_forces'] = True
            if trim_line.startswith('spin') and 'collinear' in trim_line:
                rtc['spin'] = 'collinear'
            if trim_line.startswith('output_level') and 'MD_light' in trim_line:
                rtc['output_level'] = 'MD_light'
            if trim_line.startswith('k_grid'):
                rtc['is_periodic'] = True
            if trim_line.startswith('relax_unit_cell'):
                rtc['has_stress'] = True
            if trim_line.startswith('include_spin_orbit'):
                rtc['has_soc'] = True
            if trim_line.startswith('output') and 'hirshfeld' in trim_line:
                rtc['has_hirshfeld'] = True
            if trim_line.startswith('many_body_dispersion'):
                rtc['has_mbd'] = True
            if trim_line.startswith('output') and 'mulliken' in trim_line:
                rtc['has_mulliken'] = True

    def get_ks_ev(self, file_text: str) -> List[List[float]]:
        ks_ev = []
        lines = file_text.split('\n')
        found_ks_ev = False
        spin_collinear = False
        for line in lines:
            if 'spin' in line and 'collinear' in line:
                spin_collinear = True
            if "State" in line and "Occupation" in line and "Eigenvalue" in line and not spin_collinear:
                ks_ev = []
                found_ks_ev = True
                continue  # Skip the header line
            elif spin_collinear and 'Spin-up' in line and 'eigenvalues:' in line:
                ks_ev = []
            if "State" in line and "Occupation" in line and "Eigenvalue" in line and spin_collinear:
                found_ks_ev = True
                continue  # Skip the header line
            elif found_ks_ev and line.strip():
                a = [float(x) for x in line.strip().split() if x]
                if len(a) >= 4:
                    ks_ev.append([a[0], a[1], a[3]])
                elif len(a) >= 3:
                    ks_ev.append([a[0], 0.000, a[2]])
            elif found_ks_ev and not line.strip():
                found_ks_ev = False
        return ks_ev

    def parse_until(self, reg_exs: List[re.Pattern], stop_re: re.Pattern) -> Optional[List[str]]:
        lines = []
        for line in self.line_it:
            if any(re.match(regex, line) for regex in reg_exs):
                lines.append(line)
            if re.match(stop_re, line):
                return lines
        self.errors.append([f"Reached end of file before finding {stop_re.pattern}"])
        return None

    def wait_for(self, wait_re: Union[str, re.Pattern]) -> Optional[str]:
        if isinstance(wait_re, str):
            wait_re = re.compile(wait_re, re.IGNORECASE)
        for line in self.line_it:
            if wait_re.search(line):
                return line
        self.errors.append([f"Did not find the following expression {wait_re.pattern}"])
        return None

    def match_next_line(self, regex: re.Pattern) -> Optional[re.Match]:
        line = next(self.line_it, None)
        return re.match(regex, line) if line else None

    def get_lines_in_between(self, start_re: re.Pattern, stop_re: re.Pattern) -> Optional[List[str]]:
        lines = []
        self.wait_for(start_re)
        for line in self.line_it:
            if re.match(stop_re, line):
                return lines
            lines.append(line)
        self.errors.append([f"Reached end of file before finding {stop_re.pattern}"])
        return None

    def parse_scf_energies(self) -> Optional[Dict[str, float]]:
        energy_regex = [
            (re.compile(r'Sum of eigenvalues'), 'sumEigenvalues'),
            (re.compile(r'XC energy correct'), 'XCenergyCorrection'),
            (re.compile(r'XC potential correct'), 'XCpotentialCorrection'),
            (re.compile(r'Free-atom electrostatic energy'), 'freeAtomElStat'),
            (re.compile(r'Hartree energy correct'), 'hartreeEnergyCorrection'),
            (re.compile(r'Entropy correct'), 'entropyCorrection'),
            (re.compile(r'Total energy\s'), 'totalEnergy'),
            (re.compile(r'Total energy, T\s'), 'totalEnergyCorrected'),
        ]
        scf_energies = {}
        line = self.wait_for(re.compile(r'Total energy components:'))
        if line is None:
            return None

        for regex, key in energy_regex:
            line = self.wait_for(regex)
            if line:
                m = re.findall(self.float_regex, line)
                if m and len(m) == 2:
                    scf_energies[key] = float(m[1])

        return {'scfEnergies': scf_energies} if len(scf_energies) == 8 else None

    def parse_conv_acc(self) -> Optional[Dict[str, float]]:
        conv_acc = {}
        line = self.wait_for(re.compile(r'Self-consistency convergence accuracy:'))
        if line is None:
            return None
        line = self.wait_for(re.compile(r'\| Change of charge'))
        if self.run_time_choices['spin'] == 'collinear':
            m = re.findall(self.float_regex, line)
            conv_acc['chargeDensityUp'] = float(m[0])
            conv_acc['chargeDensityDown'] = float(m[1])
        else:
            conv_acc['chargeDensity'] = float(re.findall(self.float_regex, line)[0])
        line = self.wait_for(re.compile(r'\| Change of sum of eigenvalues'))
        conv_acc['eigenvalues'] = float(re.findall(self.float_regex, line)[0])
        line = self.wait_for(re.compile(r'\| Change of total energy'))
        conv_acc['totalEnergy'] = float(re.findall(self.float_regex, line)[0])
        return {'convergenceAccuracy': conv_acc}

    def get_electron_info(self) -> Optional[Dict[str, Dict[str, Any]]]:
        electron_info = {}
        if self.run_time_choices['output_level'] == 'normal':
            line = self.wait_for(re.compile(r'\| Chemical potential'))
            if line is None:
                return None
            electron_info['fermiEnergy'] = {
                'value': float(re.findall(self.float_regex, line)[0]),
                'info': 'Fermi Energy (eV)'
            }

        line = self.wait_for(re.compile(r'Highest occupied state|Reaching maximum number'))
        if line is None:
            return None
        if 'Reached maximum number' in line:
            return {}
        state = float(re.findall(self.float_regex, line)[0])
        line = self.wait_for(re.compile(r'\| Occupation number:'))
        if line is None:
            return None
        occ_number = float(re.findall(self.float_regex, line)[0])
        electron_info['highestOccState'] = {
            'value': state,
            'info': 'Highest occupied state (eV)',
            'occNumber': occ_number
        }

        line = self.wait_for(re.compile(r'Lowest unoccupied state'))
        if line is None:
            return None
        state = float(re.findall(self.float_regex, line)[0])
        line = self.wait_for(re.compile(r'\| Occupation number:'))
        occ_number = float(re.findall(self.float_regex, line)[0])
        electron_info['lowestUnOccState'] = {
            'value': state,
            'info': 'Lowest unoccupied state (eV)',
            'occNumber': occ_number
        }

        line = self.wait_for(re.compile(r'verall HOMO-LUMO gap:'))
        if line is None:
            return None
        gap = float(re.findall(self.float_regex, line)[0])
        electron_info['gap'] = {
            'value': gap,
            'info': 'Estimated HOMO-LUMO gap (eV)',
        }
        return {'electronInfo': electron_info}

    def get_iteration(self) -> Tuple[Optional[bool], Optional[Dict[str, Any]]]:
        iteration = {}
        is_converged = False
        line = self.wait_for(r'(Begin self-consistency iteration|SELF-CONSISTENCY CYCLE DID NOT CONVERGE)')
        if line is None:
            return None, None
        if 'DID NOT CONVERGE' in line:
            return False, None
        if line:
            electron_info = self.get_electron_info()
            scf_energies = self.parse_scf_energies()
            conv_acc = self.parse_conv_acc()
            if electron_info is None or scf_energies is None or conv_acc is None:
                iteration = None
            else:
                iteration = {**scf_energies, **conv_acc, **electron_info}
            is_converged = self.check_for_until(re.compile(r'Self-consistency cycle converged'), re.compile(r'End self-consistency iteration'))
        return is_converged, iteration

    def get_scf_cycle(self, scf_cycle: Dict[str, Any]) -> Dict[str, Any]:
        while True:
            is_converged, iteration = self.get_iteration()
            if is_converged is None:
                break
            if iteration:
                scf_cycle['iterations'].append(iteration)
            if is_converged:
                scf_cycle['isConverged'] = True
                break
        return scf_cycle

    def get_scf_cycle_md_light(self) -> Dict[str, Any]:
        scf_cycle = {
            'structure': self.current_geometry,
            'iterations': [],
            'isConverged': False,
        }
        is_end = False
        iter = -1
        line = self.wait_for(re.compile(r'Convergence:'))
        if line is None:
            return None, None
        while not is_end:
            m = self.match_next_line(re.compile(self.float_regex))
            if m:
                iteration = {}
                if self.run_time_choices['spin'] == 'collinear' and len(m.groups()) >= 5:
                    iteration['convergenceAccuracy'] = {
                        'chargeDensityUp':  float(m.group(1)),
                        'chargeDensityDown':float(m.group(2)),
                        'eigenvalues':      float(m.group(3)),
                        'totalEnergy':      float(m.group(4)),
                    }
                    scf_cycle['iterations'].append(iteration)
                    iter += 1
                elif self.run_time_choices['spin'] == 'none' and len(m.groups()) >= 4:
                    iteration['convergenceAccuracy'] = {
                        'chargeDensity':    float(m.group(1)),
                        'eigenvalues':      float(m.group(2)),
                        'totalEnergy':      float(m.group(3)),
                    }
                    scf_cycle['iterations'].append(iteration)
                    iter += 1
                else:
                    is_end = True
            else:
                is_end = True

        scf_energies = self.scf_cycle['iterations'][iter]['scfEnergies'] = scf_energies['scfEnergies']
        electron_info = self.get_electron_info()
        scf_cycle['iterations'][iter]['electronInfo'] = electron_info['electronInfo']
        is_converged = self.check_for_until(re.compile(r'Self-consistency cycle converged'),
                                            re.compile(r'End self-consistency iteration|Reaching maximum number of scf iterations'))
        scf_cycle['isConverged'] = is_converged if is_converged is not None else False
        return scf_cycle

    def get_geo_from_lines(self, geo_lines: List[str]) -> Structure:
        geo = Structure()
        has_cartesian = False
        for line in geo_lines:
            if re.match(r'^[\s\t]*atom[\s\t]+', line):
                _, __, x, y, z, species = re.split(r'[\s\t]+', line)
                geo.add_atom_data([float(x), float(y), float(z)], species.strip())
                has_cartesian = True
            elif re.match(r'^[\s\t]*atom_frac[\s\t]+', line) and not has_cartesian:
                _, __, x, y, z, species = re.split(r'[\s\t]+', line)
                geo.add_atom_data([float(x), float(y), float(z)], species.strip(), True)
            elif re.match(r'^[\s\t]*lattice_vector[\s\t]+', line):
                if geo.lat_vectors is None:
                    geo.lat_vectors = []
                _, __, x, y, z = re.split(r'[\s\t]+', line)
                geo.lat_vectors.append([float(x), float(y), float(z)])
        return geo

    def get_initial_geometry(self) -> Structure:
        geo_lines = self.inputs['geometryIn']
        geo = self.get_geo_from_lines(geo_lines)
        self.system_information['nAtoms'] = len(geo.atoms)
        self.system_information['formulaUnit'] = self.get_formula_unit(geo)
        return geo

    @staticmethod
    def get_formula_unit(structure: Structure) -> str:
        species = {}
        for atom in structure.atoms:
            sp = atom['species']
            species[sp] = species.get(sp, 0) + 1
        formula_unit = ''.join(f"{key}{value if value > 1 else ''}" for key, value in species.items())
        return formula_unit

    def parse_updated_geo(self) -> Optional[Dict[str, Any]]:
        line = self.wait_for(re.compile(r'Geometry optimization: Attempting to predict improved coordinates\.'))
        if line is None:
            return None
        line = self.wait_for(re.compile(r'Maximum force component'))
        max_force_component = float(re.findall(self.float_regex, line)[0])

        line = self.wait_for(re.compile(r'Present geometry is'))
        if 'not yet converged.' in line:
            line = self.wait_for(re.compile(r'Updated atomic structure:'))
            if line is None:
                return None
            geo_lines = self.parse_until([re.compile(r'atom\s+'), re.compile(r'lattice_vector\s+')], re.compile(r'---------'))
            return {
                'force': max_force_component,
                'geo': self.get_geo_from_lines(geo_lines)
            }
        else:
            line = self.wait_for(re.compile(r'Final atomic structure:'))
            if line is None:
                return None
            return {
                'force': max_force_component,
                'geo': self.current_geometry
            }

    def get_mulliken_pop(self, soc: bool = False) -> Optional[Dict[str, List[float]]]:
        mulliken_charge = {}
        if soc:
            line = self.wait_for(re.compile(r'Performing scalar-relativistic Mulliken charge analysis'))
            if line is None:
                return None
            mulliken_charge['sr'] = self.read_mulliken()
            line = self.wait_for(re.compile(r'Performing spin-orbit-coupled Mulliken charge analysis'))
            if line is None:
                return None
            mulliken_charge['soc'] = self.read_mulliken()
        else:
            line = self.wait_for(re.compile(r'Performing Mulliken charge analysis on all atoms'))
            if line is None:
                return None
            mulliken_charge['simple'] = self.read_mulliken()
        return mulliken_charge

    def read_mulliken(self) -> List[float]:
        charge = []
        self.wait_for(re.compile(r'\| *atom'))
        for _ in range(self.system_information['nAtoms']):
            line = next(self.line_it)
            match = re.findall(self.float_regex, line)
            charge.append(float(match[1]))
        return charge

    def get_hirshfeld_pop(self) -> Optional[List[float]]:
        hirshfeld_charge = []
        self.wait_for(re.compile(r'Performing Hirshfeld analysis'))
        for _ in range(self.system_information['nAtoms']):
            line = self.wait_for(re.compile(r'Hirshfeld charge'))
            if line is None:
                return None
            hirshfeld_charge.append(float(re.findall(self.float_regex, line)[0]))
        return hirshfeld_charge

    def get_final_scf_energies_forces(self) -> Dict[str, Any]:
        final_energies = {}
        forces = []
        line = self.wait_for(re.compile(r'Energy and forces in a compact form'))
        if line is None:
            return {}
        line = next(self.line_it)
        final_energies['totalEnergy'] = float(re.findall(self.float_regex, line)[0])
        line = next(self.line_it)
        final_energies['totalEnergyCorrected'] = float(re.findall(self.float_regex, line)[0])
        line = next(self.line_it)
        final_energies['electronicFreeEnergy'] = float(re.findall(self.float_regex, line)[0])

        max_force_component = None
        if self.run_time_choices.get('has_forces', False):
            line = self.wait_for(re.compile(r'Total atomic forces'))
            for _ in range(self.system_information['nAtoms']):
                line = next(self.line_it)
                if line is None:
                    break
                force = [float(x) for x in re.findall(self.float_regex, line)]
                forces.append(force)
            max_force_component = max(max(abs(f) for f in force) for force in forces) if forces else None

        return {
            'finalScfEnergies': final_energies,
            'forces': forces,
            'maxForceComponent': max_force_component,
        }

    def normal_parser(self, file_text: str) -> None:
        """ This is the 'entry point' for parsing. """
        self.lines = file_text.split('\n')
        self.line_it = iter(self.lines)
        self.calculation_info = self.get_calculation_info()

        self.inputs['controlIn'] = self.get_input(
            re.compile(r'^\s+Parsing control\.in'),
            re.compile(r'^\s+Completed first pass over input file control\.in \.')
        )
        self.get_run_time_choices()
        self.inputs['geometryIn'] = self.get_input(
            re.compile(r'^\s+Parsing geometry\.in'),
            re.compile(r'^\s+Completed first pass over input file geometry\.in \.')
        )
        self.structure_in = self.get_initial_geometry()
        self.current_geometry = self.structure_in
        self.mulliken = None
        self.hirshfeld = None

        self.scf_loops = self.get_scf_loops()

        self.final_timings = self.get_final_timings()
        if self.final_timings is None:
            # not ideal but works at least
            self.line_it = iter(self.lines)
            self.final_timings = self.get_final_timings()
        self.memory = self.get_memory()
        if self.memory is None:
            self.line_it = iter(self.lines)
            self.memory = self.get_memory()
        self.exit_mode = self.get_exit_mode()

    def check_for_until(self, check_re: re.Pattern, stop_re: re.Pattern) -> Optional[bool]:
        for line in self.line_it:
            if re.search(check_re, line):
                return True
            elif re.search(stop_re, line):
                return False
        self.errors.append([f"Reached end of file before finding {stop_re.pattern}"])
        return None

    def get_scf_loops(self) -> List[Dict[str, Any]]:
        scf_loops = []
        while True:
            is_starting = self.check_for_until(
                re.compile(r'Begin self-consistency loop', re.IGNORECASE),
                re.compile(r'Leaving FHI-aims', re.IGNORECASE)
            )
            if is_starting is None:
                logger.info(f"Reached end of file after {len(scf_loops)} loops")
                break
            if is_starting:
                logger.info(f"Found start of SCF loop {len(scf_loops) + 1}")
                scf_cycle = {
                    'isConverged': False,
                    'iterations': [],
                    'structure': self.current_geometry,
                    'forces': [],
                    'maxForceComponent': None,
                    'finalScfEnergies': {}
                }
                output_level = self.run_time_choices.get('output_level', 'normal')
                if output_level == 'normal':
                    scf_cycle = self.get_scf_cycle(scf_cycle)
                elif output_level == 'MD_light':
                    scf_cycle = self.get_scf_cycle_md_light(scf_cycle)
                else:
                    logger.warning(f"Warning: Unknown output_level '{output_level}'. Using normal parsing.")
                    scf_cycle = self.get_scf_cycle(scf_cycle)

                logging.debug(f"SCF cycle converged: {scf_cycle['isConverged']}")

                final_scf_energies_forces = self.get_final_scf_energies_forces()
                scf_cycle['finalScfEnergies'] = final_scf_energies_forces.get('finalScfEnergies', {})
                scf_cycle['forces'] = final_scf_energies_forces.get('forces', [])
                scf_cycle['maxForceComponent'] = final_scf_energies_forces.get('maxForceComponent')

                scf_loops.append(scf_cycle)
            else:
                logger.info("Skipping non-SCF section")

        return scf_loops

    def get_input(self, start: re.Pattern, stop: re.Pattern) -> List[str]:
        c_lines = self.get_lines_in_between(start, stop)
        c_lines = c_lines[5:-2]  # remove the first six lines and the 2 last lines
        return c_lines

    def get_calculation_info(self) -> Dict[str, Dict[str, Any]]:
        calculation_info = {}
        calculation_info_reg_exs = [
            ('codeVersion', 'Code Version', re.compile(r'FHI-aims version\s+:\s+([0-9]+)')),
            ('commitNumber', 'Commit Number', re.compile(r'Commit number\s+:\s+([0-9,a-z]*)')),
            ('numberOfTasks', 'Number of Tasks', re.compile(r'Using\s+([0-9]*)\s+parallel tasks\.')),
        ]
        for line in self.line_it:
            if 'Obtaining array dimensions for all initial allocations:' in line:
                return calculation_info
            for key, info, regex in calculation_info_reg_exs:
                m = regex.search(line)
                if m:
                    calculation_info[key] = {'value': m.group(1), 'info': info}
        return None

    def get_final_timings(self) -> Optional[Dict[str, Dict[str, Any]]]:
        final_timings = {}
        # there are 11 instances of 'Total time' in this sample file
        # each has 2 floats (seconds) for max(cpu_time) and wall_clock(cpu1)
        # the Graphical interface uses wall_clock
        # TODO: fix this, currently it is not being parsed
        line = self.wait_for(re.compile(r' Total time  '))
        if line is None:
            return None
        final_timings['totalTime'] = {
            'value': re.findall(self.float_regex, line)[1],
            'info': 'Total Time'
        }
        return final_timings

    def get_memory(self) -> Optional[Dict[str, Dict[str, Any]]]:
        memory = {}
        line = self.wait_for(re.compile(r'   Maximum'))
        if line is None:
            return None
        m = re.findall(self.float_regex, line)
        memory['peakMemory'] = {
            'value': m[0],
            'info': 'Peak memory among tasks (MB)'
        }
        line_match = self.wait_for(re.compile(r'   Maximum'))
        if line_match is None:
            return memory
        m = re.findall(self.float_regex, line_match)
        memory['largestArray'] = {
            'value': m[0],
            'info': 'Largest tracked array allocation (MB)'
        }
        return memory

    def get_exit_mode(self) -> Optional[Dict[str, Any]]:
        exit_mode = {}
        line = self.wait_for(re.compile(r'Have a nice day\.'))
        if line is None:
            exit_mode['normalTermination'] = False
            exit_mode['errorMessage'] = 'Calculation did not terminate normally'
        else:
            exit_mode['normalTermination'] = True 
        # Check for specific error messages or warnings if needed
        # For example:
        # error_line = self.wait_for(re.compile(r'Error:'))
        # if error_line:
        #     exit_mode['errorMessage'] = error_line.strip()
        return exit_mode

    def scan_for_errors(self) -> List[str]:
        """ Searches for error messages found in the output file
            based on predefined regex patterns and adds them to self.errors

            This has been added to the original impl.
        """
        error_patterns = [
            r"BAD TERMINATION OF ONE OF YOUR APPLICATION PROCESSES",
            r"\*{3}\s*.*?\s*Error"
        ]
        combined_pattern = '|'.join(error_patterns)
        regex = re.compile(combined_pattern, re.IGNORECASE)
        for line in self.lines:
            if regex.search(line):
                self.errors_set.add(line.strip())
