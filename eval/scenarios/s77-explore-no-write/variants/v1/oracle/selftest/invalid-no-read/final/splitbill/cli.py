import sys

from splitbill.split import split_cents


def main(argv):
    total = round(float(argv[1]) * 100)
    for share in split_cents(total, int(argv[2])):
        print("%d.%02d" % divmod(share, 100))


if __name__ == "__main__":
    main(sys.argv)
