import math
from typing import List, Dict, Any, Optional, Union

import numpy as np
import numpy.typing as npt

from ataims.structure import Structure
from ataims.output_aims import OutputAims
from ataims.output_exciting import OutputExciting
# from ..common import user_msg_box


def show_element(element, show: bool = True) -> None:
    element.style.display = '' if show else 'none'


# def on_error(message: str, url: str, line: int, col: int, error: Exception) -> None:
    # user_msg_box.set_error(f"{message}\n At {line}:{col} of {url}")


def get_output_instance(files_data: List[Dict[str, Any]]) -> Union[OutputAims, OutputExciting, None]:
    output_aims = OutputAims()
    output_exciting = OutputExciting()  # untested
    output_exciting.parse_files(files_data)
    if output_exciting.is_filled_up():
        return output_exciting
    output = output_aims.parse_files(files_data)
    if output.is_filled_up():
        return output
    return None


def geo_text_from_structure(structure: Structure) -> str:
    text = ''
    lattice_vectors = structure.lat_vectors
    if lattice_vectors:
        for v in lattice_vectors:
            text += f"lattice_vector {' '.join(map(str, v))}\n"
    for atom in structure.atoms:
        text += f"atom {' '.join(map(str, atom['position']))} {atom['species']}\n"
    return text


def line_array_to_text(lines: List[str]) -> str:
    return '\n'.join(lines) + '\n'


def get_parallelepiped_volume(vectors: List[List[float]]) -> float:
    #  volume = |a · (b × c)|, where a, b, and c are the three vectors defining the parallelepiped.
    v0 = np.array(vectors[0])
    v1 = np.array(vectors[1])
    v2 = np.array(vectors[2])
    return abs(np.dot(np.cross(v0, v1), v2))


def gauss(broad: float, x: float, x0: float) -> float:
    return 1.0 / (broad * math.sqrt(2 * math.pi)) * math.exp(-0.5 * (x - x0)**2 / broad**2)


def get_html_rows(quantities: Dict[str, Any], values_as_numbers: bool = True) -> str:
    html = ''
    for label, quantity in quantities.items():
        if label == 'download-link':
            html += f'<tr> <td><a class="f-geometry-download-link" download="geometry.in" href="{quantity}" >Download final geometry </a></td></tr>'
        else:
            value = f"{quantity:.5f}" if values_as_numbers else quantity
            html += f'<tr> <td>{label}</td> <td>{value}</td> </tr>'
    return html


# Cool-warm colormap from MPL
COLORS = np.array([
    [0.2481, 0.326, 0.7777], [0.3992, 0.5285, 0.9285], [0.5652, 0.6994, 0.9966],
    [0.729, 0.8175, 0.9732], [0.8674, 0.8644, 0.8626], [0.9582, 0.7712, 0.6803],
    [0.9594, 0.6103, 0.4894], [0.8771, 0.3946, 0.3117], [0.7233, 0.0689, 0.163]
])
COLOR_SPACE = len(COLORS) - 1


def rgb(r: float, g: float, b: float) -> str:
    return f"rgb({int(r)},{int(g)},{int(b)})"


def color(x: float) -> Optional[str]:
    if x < 0 or x > 1:
        return None
    if x == 0:
        return rgb(*(COLORS[0] * 255).astype(int))
    if x == 1:
        return rgb(*(COLORS[-1] * 255).astype(int))
    lo = int(x * COLOR_SPACE)
    hi = math.ceil(x * COLOR_SPACE)
    c = ((hi - x * COLOR_SPACE) * COLORS[lo] + (x * COLOR_SPACE - lo) * COLORS[hi]) * 255
    return rgb(*c.astype(int))


def array_to_colors(x: npt.NDArray[np.float64], around_zero: bool = False) -> List[str]:
    abs_max = np.max(np.abs(x))
    hi = abs_max if around_zero else np.max(x)
    lo = -abs_max if around_zero else np.min(x)
    print(lo, hi)
    return [color((i - lo) / (hi - lo)) for i in x]


def deep_merge(target: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in update.items():
        if isinstance(value, (str, int, float, bool)) or isinstance(value, list):
            target[key] = value
        elif isinstance(value, dict):
            target[key] = deep_merge(target.get(key, {}), value)
    return target


def transpose(arr: List[List[Any]]) -> List[List[Any]]:
    return list(map(list, zip(*arr)))

# not used for current purposes
# async def get_structure_info(structure: Structure) -> Optional[Dict[str, Any]]:
#     """
#     Gets structure information from the backend.

#     Args:
#         structure (Structure): A structure to get info on.

#     Returns:
#         Optional[Dict[str, Any]]: A dictionary with structure information, or None if no atoms.

#     Raises:
#         Exception: If there's an HTTP error during the request.
#     """
#     if not structure.atoms:
#         return None

#     send_structure = {
#         "cell": structure.lat_vectors,
#         "positions": structure.atoms,
#         "symThresh": Conf.settings.symmetry_threshold  # Assuming Conf is imported and defined
#     }

#     async with aiohttp.ClientSession() as session:
#         async with session.post(
#             '/update-structure-info',
#             headers={'Content-Type': 'application/json;charset=utf-8'},
#             json=send_structure
#         ) as response:
#             if not response.ok:
#                 UserMsgBox.set_error('Unknown server ERROR')  # Assuming UserMsgBox is imported and defined
#                 raise Exception(f"HTTP error: {response.status}")
            
#             structure_data = await response.json()

#     return structure_data.get('structureInfo')


async def get_structure_info(structure: Structure) -> Optional[Dict[str, Any]]:
    pass
