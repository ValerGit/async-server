import argparse
import configparser
import os
import sys

from parser import SERVER_NAME
from server import Server

DEFAULT_CONFIG_PATH = 'config.ini'


def parse_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='{server_name} HTTP server'.format(server_name=SERVER_NAME))

    parser.add_argument(
        '-c', '--config', default=DEFAULT_CONFIG_PATH, help='Configuration file')
    parser.add_argument(
        '-r', '--root-dir', required=True, help='Root directory for reading files')
    parser.add_argument(
        '-n', '--cpu-num', default=3, type=int, help='Number of cpu')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    config = configparser.RawConfigParser()
    config.read(args.config)

    if not os.path.isdir(args.root_dir) or args.cpu_num < 1:
        print('Fatal error. Please enter right arguments!')
        sys.exit()

    serve = Server(config, args.cpu_num, args.root_dir)
    serve.start()
    try:
        while True:
            events = serve.selector.select()
            for key, mask in events:
                callback = key.data
                callback()
    except KeyboardInterrupt:
        serve.stop()
