"""
Application configuration file

Author: Iker Hurtado
"""

from typing import Dict, List, Any, Optional


class Conf:
    """Object storing the configuration"""

    # Default settings
    settings: Dict[str, Any] = {
        "decimalDigits": 6,
        "symmetryThreshold": 1e-5,
    }

    BASE_FOLDER: str = ''  # 'static/'

    # Species codes
    ELEMENT_NAMES: Dict[str, int] = {
        element: i for i, element in enumerate([
            'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si',
            'P', 'S', 'Cl', 'Ar', 'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni',
            'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb',
            'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe',
            'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho',
            'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg',
            'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np',
            'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Ha', 'Sg',
            'Ns', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn', 'Nh', 'Fl', 'Mc', 'Lv', 'Ts', 'Og'
        ])
    }

    # StructureViewer constants
    RADIUS_FACTOR: float = 0.5
    MISSING_RADIUS: float = 0.2

    ELEMENT_RADII: List[float] = [
        0.31, 0.28, 1.28, 0.96, 0.84, 0.76, 0.71, 0.66, 0.57, 0.58,
        1.66, 1.41, 1.21, 1.11, 1.07, 1.05, 1.02, 1.06, 2.03, 1.76, 1.7, 1.6, 1.53,
        1.39, 1.39, 1.32, 1.26, 1.24, 1.32, 1.22, 1.22, 1.2, 1.19, 1.2, 1.2, 1.16,
        2.2, 1.95, 1.9, 1.75, 1.64, 1.54, 1.47, 1.46, 1.42, 1.39, 1.45, 1.44, 1.42,
        1.39, 1.39, 1.38, 1.39, 1.4, 2.44, 2.15, 2.07, 2.04, 2.03, 2.01, 1.99, 1.98,
        1.98, 1.96, 1.94, 1.92, 1.92, 1.89, 1.9, 1.87, 1.87, 1.75, 1.7, 1.62, 1.51,
        1.44, 1.41, 1.36, 1.36, 1.32, 1.45, 1.46, 1.48, 1.4, 1.5, 1.5, 2.6, 2.21,
        2.15, 2.06, 2.0, 1.96, 1.9, 1.87, 1.8, 1.69, MISSING_RADIUS, MISSING_RADIUS,
        MISSING_RADIUS, MISSING_RADIUS, MISSING_RADIUS, MISSING_RADIUS, MISSING_RADIUS
    ]

    MISSING_COLOR: str = '#000000'

    ELEMENT_COLORS: List[str] = [
        '#ffffff', '#d9ffff', '#cc80ff', '#c2ff00', '#ffb5b5', '#909090', '#3050f8', 
        '#ff0d0d', '#90e050', '#b3e3f5', '#ab5cf2', '#8aff00', '#bfa6a6', '#f0c8a0', '#ff8000', 
        '#ffff30', '#1ff01f', '#80d1e3', '#8f40d4', '#3dff00', '#e6e6e6', '#bfc2c7', '#a6a6ab', 
        '#8a99c7', '#9c7ac7', '#e06633', '#f090a0', '#50d050', '#c88033', '#7d80b0', '#c28f8f', 
        '#668f8f', '#bd80e3', '#ffa100', '#a62929', '#5cb8d1', '#702eb0', '#00ff00', '#94ffff', 
        '#94e0e0', '#73c2c9', '#54b5b5', '#3b9e9e', '#248f8f', '#0a7d8c', '#006985', '#c0c0c0', 
        '#ffd98f', '#a67573', '#668080', '#9e63b5', '#d47a00', '#940094', '#429eb0', '#57178f', 
        '#00c900', '#70d4ff', '#ffffc7', '#d9ffc7', '#c7ffc7', '#a3ffc7', '#8fffc7', '#61ffc7', 
        '#45ffc7', '#30ffc7', '#1fffc7', '#00ff9c', '#00e675', '#00d452', '#00bf38', '#00ab24', 
        '#4dc2ff', '#4da6ff', '#2194d6', '#267dab', '#266696', '#175487', '#d0d0e0', '#ffd123', 
        '#b8b8d0', '#a6544d', '#575961', '#9e4fb5', '#ab5c00', '#754f45', '#428296', '#420066', 
        '#007d00', '#70abfa', '#00baff', '#00a1ff', '#008fff', '#0080ff', '#006bff', '#545cf2', 
        '#785ce3', '#8a4fe3', '#a136d4', '#b31fd4', '#b31fba', '#b30da6', '#bd0d87', '#c70066', 
        '#cc0059', '#d1004f', '#d90045', '#e00038', '#e6002e', '#eb0026'
    ]

    @staticmethod
    def get_species_color(species: Optional[str]) -> str:
        """
        Returns the species color code
        :param species: Element symbol
        :return: Color code as string
        """
        if species is None:
            return Conf.MISSING_COLOR
        return Conf.ELEMENT_COLORS[Conf.ELEMENT_NAMES[species]]

    @staticmethod
    def set_species_color(species: str, color: str) -> None:
        """
        Sets a species color code overwriting the original one
        :param species: Element symbol
        :param color: New color code
        """
        print(f'setSpeciesColor: {species}, {Conf.ELEMENT_NAMES[species]}, {Conf.ELEMENT_COLORS[Conf.ELEMENT_NAMES[species]]}, {color}')
        Conf.ELEMENT_COLORS[Conf.ELEMENT_NAMES[species]] = color

    @staticmethod
    def get_species_radius(species: Optional[str]) -> float:
        """
        Returns the species radius
        :param species: Element symbol
        :return: Radius as float
        """
        if species is None:
            return Conf.MISSING_RADIUS
        return Conf.ELEMENT_RADII[Conf.ELEMENT_NAMES[species]]

    @staticmethod
    def get_radius_and_color(species: Optional[str]) -> Dict[str, Any]:
        """
        Returns the species radius and color
        :param species: Element symbol
        :return: Dictionary with radius and color
        """
        if species is None:
            return {"radius": 0.5, "color": Conf.MISSING_COLOR}
        index = Conf.ELEMENT_NAMES[species]
        return {
            "radius": Conf.ELEMENT_RADII[index] * Conf.RADIUS_FACTOR,
            "color": Conf.ELEMENT_COLORS[index]
        }

    @staticmethod
    def get_species_atomic_number(species: str) -> int:
        """
        Returns the species atomic number
        :param species: Element symbol
        :return: Atomic number as integer
        """
        return Conf.ELEMENT_NAMES[species] + 1
