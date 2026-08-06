# CLI entry: parse args, load config, render output.
import argparse

import config
import output


def main() -> None:
    args = argparse.ArgumentParser(description="portable")
    args.add_argument("--format", default="plain")
    ns = args.parse_args()
    data = config.load("config.ini")
    print(output.render(data, ns.format))


if __name__ == "__main__":
    main()
