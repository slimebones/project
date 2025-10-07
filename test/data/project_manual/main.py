import sys
import module_a


def main():
    check = module_a.Check(a=10, b="hello")
    print(check.a, check.b, file=sys.stdout)


if __name__ == "__main__":
    main()