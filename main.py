from argparse import ArgumentParser
import utils


parser = ArgumentParser()

parser.add_argument('command', 
                    choices=[
                        'uc', 'unit_cell',
                        'gi', 'gen_interface',
                        'ri', 'run_interface',
                        'cg', 'calc_gamma',
                        'cw', 'calc_width'],
                    type=str)

parser.add_argument('-c', '--config', 
                    help='config file',
                    required=True)

group = parser.add_mutually_exclusive_group()

group.add_argument('-d', '--dry', 
                    help='dry run',
                    action='store_true')

group.add_argument('-O', '--overwrite',
                    help='overwrite existing data',
                    action='store_true')


parser.add_argument('-p', '--plot',
                    help='field plotting',
                    action='store_true')


args = parser.parse_args()


CC = utils.CommandLineConfig(args)

if args.command in ['uc' ,'unit_cell']:
    utils.unit_cell.run(args.config, CC)

if args.command in ['gi', 'gen_interface']:
    utils.gen_interface.run(args.config, CC)

if args.command in ['ri', 'run_interface']:
    utils.run_interface.run(args.config, CC)

if args.command in ['cg', 'calc_gamma']:
    utils.calc.gamma.run(args.config, CC)

if args.command in ['cw', 'calc_width']:
    utils.calc.width.run(args.config, CC)


