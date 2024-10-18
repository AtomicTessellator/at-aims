from typing import Dict, List, Optional, Any


class Output:
    def __init__(self):
        self.files: Dict[str, Dict[str, Any]] = {
            'dos': {},
            'absorption': {},
            'dielectric': {},
            'output': {},
            'input': {}
        }
        
        self.filled_up: bool = False
        self.inputs: Dict[str, Any] = {}
        self.results: List[Any] = []
        self.run_time_choices: Dict[str, Any] = {
            'calculationType': 'singlePoint',  # 'singlePoint', 'relaxation'
            'spin': 'none',  # 'none', 'collinear'
            'hasForces': False,
            'isPeriodic': False,
            'hasStress': False,
            'outputLevel': 'normal',  # 'normal', 'MD_light'
            'hasSOC': False,
            'hasHirshfeld': False,
            'hasMulliken': False,
            'hasMBD': False
        }
        self.system_information: Dict[str, Any] = {
            'nAtoms': 0,
            'formulaUnit': None,
            'volume': None
        }
        self.control_in: Optional[str] = None
        self.structure_in: Optional[Any] = None
        self.errors: List[str] = []
        self.ks_ev: Optional[Any] = None
        self.workflows: List[Any] = []

    def parse_files(self, files_data: List[Dict[str, Any]]) -> None:
        pass

    def is_filled_up(self) -> bool:
        return self.filled_up

    def is_relaxation(self) -> bool:
        return self.run_time_choices['calculationType'] == 'relaxation'

    def parse_output_file(self, file_name: Optional[str] = None) -> None:
        pass

    def parse_file(self, file_name: str, file_text: str) -> None:
        pass

    def get_structure(self) -> Optional[Any]:
        return self.structure_in

    def get_first_file_dos_data(self) -> Optional[Any]:
        return next(iter(self.files['dos'].values()), None)

    def get_bs_info(self) -> Any:
        # not all of these methods are even implemented
        pass
