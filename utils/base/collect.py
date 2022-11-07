from pathlib import Path
import json
from .. import global_cfg as G
from .data import put_val

def collect(root: str):


    data_path = Path(G.DATA_DIR)
    root_path = Path(root)

    if not root_path.is_relative_to(data_path):
        raise ValueError(f'Invalid data root: {str(root_path)}')

    d = {}

    calcs = root_path.rglob(G.CALC_FILE)

    for calc_path in calcs:


        with open(calc_path, 'r') as f:
            calc_data = json.load(f)

        rel_path = calc_path.relative_to(root_path)
        affixes = [s.split('_')[-1] for s in rel_path.parent.parts]

        put_val(d, *affixes, val=calc_data)


    return d


