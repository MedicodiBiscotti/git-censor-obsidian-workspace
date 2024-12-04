import json


def read_and_write_back(input: str, output: str):
    with open(input) as infile:
        data = json.load(infile)
        write_json_string(data, output)


def write_json_file(data: dict, output: str):
    # newline="" or "\n" writes with LF. dump does \n by default, but open does os.linesep.
    with open(output, "w", newline="\n") as outfile:
        json.dump(data, outfile, indent=2)


def format_json_string(data: dict) -> str:
    return json.dumps(data, indent=2)


def write_json_string(data: dict, output: str):
    with open(output, "w", newline="\n") as outfile:
        outfile.write(format_json_string(data))


if __name__ == "__main__":
    read_and_write_back("workspace.json", "testdump.json")
