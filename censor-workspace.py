import json


def read_and_write_back(input: str, output: str):
    with open(input) as infile:
        data = json.load(infile)
        write_json_text_file(data, output)


def write_json_text_file(data: dict, output: str):
    with open(output, "w", newline="\n") as outfile:
        json.dump(data, outfile, indent=2)
