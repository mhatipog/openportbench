"""Generate reproducible Markdown scorecard from archived JSON."""
import argparse
from openportbench.matrix_report import render_file


def main():
    p=argparse.ArgumentParser()
    p.add_argument("source")
    p.add_argument("--output",required=True)
    args=p.parse_args()
    render_file(args.source,args.output)


if __name__=="__main__":
    main()
