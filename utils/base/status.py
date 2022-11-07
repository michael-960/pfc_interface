from pathlib import Path

import rich
from .. import global_cfg as G



def show_status():

    console = rich.get_console()
    
    data_path = Path(G.DATA_DIR)

    running = list(data_path.rglob('.running'))

    console.print(f'[bold orange1] {len(running)} Running: [/bold orange1]') 

    for r in running:
        console.print('    ' + str(r.parent), highlight=False)

