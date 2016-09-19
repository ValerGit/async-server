import argparse
import configparser
import os
import sys

from server import Server

DEFAULT_CONFIG_PATH = 'config.ini'


def parse_arguments():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Morelia HTTP server')

    parser.add_argument(
        '-c', '--config', default=DEFAULT_CONFIG_PATH, help='Configuration file')
    parser.add_argument(
        '-r', '--root-dir', required=True, help='Root directory for reading files')
    parser.add_argument(
        '-n', '--cpu-num', default=4, choices=[1, 2, 3, 4], help='Number of cpu to use')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_arguments()
    config = configparser.RawConfigParser()
    config.read(args.config)

    if not os.path.isdir(args.root_dir):
        print('Fatal. Root directory is wrong!')
        sys.exit()

    serve = Server(config, args.cpu_num, args.root_dir)
    serve.start()

    while True:
        events = serve.selector.select()
        for key, mask in events:
            callback = key.data
            callback()
