from argparse import ArgumentParser
import utils


parser = ArgumentParser()


parser.add_argument('command', 
                    choices=['unit_cell', 'gen_interface', 'run_interface'],
                    type=str)

parser.add_argument('-c', '--config', 
                    help='config file',
                    required=True)


args = parser.parse_args()



if args.command == 'unit_cell':
    utils.unit_cell.run(args.config)

elif args.command == 'gen_interface':
    utils.gen_interface.run(args.config)

elif args.command == 'run_interface':
    utils.run_interface.run(args.config)

