import json
import sys

from lf_toolkit.shared.params import Params

from .evaluation import evaluation_function


def dev():
    """Run the evaluation function from the command line for development purposes.

    Usage: python -m evaluation_function.dev <response> <answer> [params]

    Each argument is JSON, e.g. '[["L", "50 cm"]]' '[["L", "0.001 m < L < 1 m"]]'.
    """
    if len(sys.argv) < 3:
        print("Usage: python -m evaluation_function.dev <response> <answer> [params]")
        return

    response = json.loads(sys.argv[1])
    answer = json.loads(sys.argv[2])
    params = Params(json.loads(sys.argv[3]) if len(sys.argv) > 3 else {})

    result = evaluation_function(response, answer, params)

    print(result.to_dict())


if __name__ == "__main__":
    dev()
