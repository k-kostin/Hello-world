import argparse
from azs_prices.parsers import get_parser


def main():
    parser = argparse.ArgumentParser(description="Parse gas station prices.")
    parser.add_argument("network", help="Name of the gas station network (e.g., bashneft, lukoil, gazprom, tatneft, yandex)")
    parser.add_argument("--output", "-o", help="Optional output filename (CSV)")
    parser.add_argument("--pages", "-p", type=int, help="Max pages (for Russiabase-based networks)")
    args = parser.parse_args()

    ParserClass = get_parser(args.network)

    if hasattr(ParserClass, "_brand_id"):
        # For Russiabase concrete classes
        parser_instance = ParserClass(max_pages=args.pages)
    else:
        parser_instance = ParserClass()

    path = parser_instance.run()
    print(f"Saved data to {path}")


if __name__ == "__main__":
    main()