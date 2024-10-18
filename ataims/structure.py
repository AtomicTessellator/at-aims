from typing import List, Dict, Optional, Union, Any
import numpy as np

from ataims.mathlib import multiply_scalar, add_arrays
from ataims.conf import Conf


def solve33(lattice_vectors: List[List[float]], cartesian_coords: List[float]) -> List[float]:
    """
    Solves the linear system to get the fractional coordinates from Cartesian coordinates
    :param lattice_vectors: 3x3 list of lattice vectors
    :param cartesian_coords: 1x3 list of Cartesian coordinates
    :return: 1x3 list of fractional coordinates
    """
    lattice_matrix = np.array(lattice_vectors)
    cartesian_coords = np.array(cartesian_coords)
    # Solve for fractional coordinates: lattice_matrix * fractional = cartesian_coords
    fractional_coords = np.linalg.solve(lattice_matrix.T, cartesian_coords)
    return fractional_coords.tolist()


class Structure:
    """
    A class modeling an atomic structure, either a periodic or non-periodic system.
    It's usually gotten from a file.
    """

    def __init__(self) -> None:
        self.lat_vectors: Optional[List[List[float]]] = None  # List of lists (3x3)
        self.atoms: List[Dict[str, Union[List[float], str, float, bool]]] = []
        self.file_source: str = ""
        self.structure_info: Dict[str, Any] = {}
        self.extra_data: Dict[str, Any] = {}
        self.id: Optional[str] = None

    def reset(self) -> None:
        """Reset the structure"""
        self.lat_vectors = None
        self.atoms = []
        self.file_source = None
        self.structure_info = None
        self.extra_data = None

    def is_a_periodic_system(self) -> bool:
        """Returns if it's a periodic system or not"""
        return self.lat_vectors is not None

    def remove_lattice_vectors(self) -> None:
        """Removes the lattice vectors becoming a non-periodic system"""
        self.lat_vectors = None

    def update_lattice_vectors(self, vectors: List[List[float]], scale_atoms_position: bool) -> None:
        """
        Updates the lattice vectors and scales the atoms positions if specified
        :param vectors: List of lists
        :param scale_atoms_position: bool
        """
        fract_positions = []
        if scale_atoms_position:
            fract_positions = [self.get_fractional_coordinates(atom['position']) for atom in self.atoms]

        self.lat_vectors = vectors

        if scale_atoms_position:
            for i, fract_pos in enumerate(fract_positions):
                self.atoms[i]['position'] = self.get_cartesian_coordinates(fract_pos)

    def create_atom(self, cart_coords: List[float], species: str, moment: float, constraint: bool, charge: float) -> Dict[str, Union[List[float], str, float, bool]]:
        """
        Creates a new atom object (it's not added to the structure)
        :return: dict
        """
        return {
            'position': cart_coords,
            'species': species,
            'initMoment': moment,
            'constraint': constraint,
            'charge': charge,
            'radius': Conf.get_species_radius(species)
        }

    def add_atom_data(self, pos: List[float], species: str, is_fractional: bool = False, moment: float = 0, constraint: bool = False, charge: float = 0, index: Optional[int] = None) -> None:
        """
        Creates and add a new atom object
        """
        c_coors = self.get_cartesian_coordinates(pos) if is_fractional else pos
        atom = self.create_atom(c_coors, species, moment, constraint, charge)
        if index is None:
            self.atoms.append(atom)
        else:
            self.atoms.insert(index, atom)

    def add_undefined_atom(self) -> int:
        """
        Creates an undefined atom.
        :return: int, new atom position in the structure
        """
        self.add_atom_data([0, 0, 0], None)
        return len(self.atoms) - 1

    def update_atom_species(self, atom_index: int, species: str) -> None:
        """Updates a structure atom species"""
        self.atoms[atom_index]['species'] = species

    def update_atom_init_moment(self, atom_index: int, init_moment: float) -> None:
        """Updates a structure atom initialization moment"""
        self.atoms[atom_index]['initMoment'] = init_moment

    def update_atom_constraint(self, atom_index: int, constraint: bool) -> None:
        """Updates a structure atom constrain"""
        self.atoms[atom_index]['constraint'] = constraint

    def update_atom_charge(self, atom_index: int, charge: float) -> None:
        """Updates a structure atom charge"""
        self.atoms[atom_index]['charge'] = charge

    def update_atom_position(self, atom_index: int, values: List[float], is_fract: bool = False) -> None:
        """Updates a structure atom position"""
        for i in range(3):
            self.update_atom_coor_value(atom_index, i, values[i], is_fract)

    def update_atom_coor_value(self, atom_index: int, coor_index: int, value: float, is_fract: bool = False) -> None:
        """Updates a coordinate of a structure atom"""
        if atom_index >= len(self.atoms):
            atom = self.create_atom([0, 0, 0], None, 0, False, 0)
            self.atoms.append(atom)  
        if is_fract:
            self.atoms[atom_index]['position'][coor_index] = self.get_cartesian_coordinates([value if i == coor_index else 0 for i in range(3)])[coor_index]
        else:
            self.atoms[atom_index]['position'][coor_index] = value

    async def update_info(self) -> None:
        """Updates information on this structure"""
        # looks like network requests
        from util import get_structure_info
        self.structure_info = await get_structure_info(self)

    def set_last_atom_init_moment(self, moment: float) -> None:
        """Sets the initialization moment to the last atom"""
        self.atoms[-1]['initMoment'] = moment

    def set_last_atom_charge(self, charge: float) -> None:
        """Sets the initialization charge to the last atom"""
        self.atoms[-1]['charge'] = charge

    def get_cartesian_coordinates(self, fract_coors: List[float]) -> List[float]:
        """
        Returns the cartesian coordinates corresponding to the
        fractional coordinates passed as the argument.
        """
        if not self.is_a_periodic_system():
            return fract_coors
        cart_pos = multiply_scalar(self.lat_vectors[0], fract_coors[0])
        cart_pos = add_arrays(cart_pos, multiply_scalar(self.lat_vectors[1], fract_coors[1]))
        cart_pos = add_arrays(cart_pos, multiply_scalar(self.lat_vectors[2], fract_coors[2]))
        return cart_pos

    def is_magnetic(self) -> bool:
        """
        Finds if the structure is magnetic, that is, if any of initial moments has been set
        :return: bool
        """
        return any(atom['initMoment'] != 0 for atom in self.atoms)

    def get_atom_fract_position(self, i: int) -> Optional[List[float]]:
        """Returns a structure atom fractional coordinates"""
        return self.get_fractional_coordinates(self.atoms[i]['position'])

    def get_fractional_coordinates(self, cart_coors: List[float]) -> Optional[List[float]]:
        """
        Returns the fractional coordinates corresponding to the
        cartesian coordinates passed as the argument.
        """
        return solve33(self.lat_vectors, cart_coors) if self.is_a_periodic_system() else None
