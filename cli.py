import argparse
from agents.react_agent import ReActAgent


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--symptom", required=True)
    parser.add_argument("--service", required=False)
    parser.add_argument("--llm", required=False)
    parser.add_argument("--debug", action="store_true")

    args = parser.parse_args()

    # agent = ReActAgent(model=args.llm)
    agent = ReActAgent(model=args.llm, debug=args.debug)
    result, trace = agent.run(args.symptom, args.service)

    print("\n=== TRACE ===")
    for t in trace:
        print("\n---\n", t)

    print("\n=== RESULT ===")
    print(result)


if __name__ == "__main__":
    main()
