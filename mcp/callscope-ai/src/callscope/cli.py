import argparse
import json
import sys

from . import analyze
from .demo import DEMO_SEGMENTS


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="callscope", description="Analyze a customer-service call locally.")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="audio file, or a JSON file of segments")
    a.add_argument("path")
    a.add_argument("--model", default="small", help="faster-whisper model size (audio only)")
    a.add_argument("--language", default=None)
    sub.add_parser("demo", help="analyze a fictional call, no audio or model needed")
    args = p.parse_args(argv)
    if args.cmd == "demo":
        result = analyze(DEMO_SEGMENTS)
    elif args.path.endswith(".json"):
        with open(args.path, encoding="utf-8") as f:
            result = analyze(json.load(f))
    else:
        result = analyze(args.path, model_size=args.model, language=args.language)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
