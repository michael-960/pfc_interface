import utils
from argparse import ArgumentParser
import rich
import json

console = rich.get_console()


parser = ArgumentParser()

subparsers = parser.add_subparsers(dest='command')

parse_status = subparsers.add_parser('status')

parse_collect = subparsers.add_parser('collect')
parse_collect.add_argument('root')

args = parser.parse_args()

if args.command == 'status':
    utils.show_status()


if args.command == 'collect':
    d = utils.collect(args.root)
    console.print(json.dumps(d, indent=4))

