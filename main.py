import argparse
from ping import verbose_ping, parse_arguments
from utils import validate_ip, validate_hostname


def main():
    args = parse_arguments()

    if not validate_ip(args.destination) and not validate_hostname(args.destination):
        print("Invalid IP address or hostname.")
        return

    verbose_ping(args.destination, count=args.count)


if __name__ == '__main__':
    main()
