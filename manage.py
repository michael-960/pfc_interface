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

parse_collect.add_argument('-n', '--no-highlight', action='store_true')


args = parser.parse_args()

if args.command == 'status':
    utils.show_status()


if args.command == 'collect':
    d = utils.collect(args.root)

    s = json.dumps(d, indent=4)

    if args.no_highlight:
        print(s)
    else:
        console.print(s)


