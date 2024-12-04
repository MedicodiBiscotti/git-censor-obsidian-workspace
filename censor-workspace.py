import json

# str.encode should output needed bytes (byte string, I think).
# json.loads can read bytes in UTF which workspace should be in, I think.
# When testing censoring logic, we don't need to bother with bytes.
# If you can test whether bytes file is identical with Git object, please do so.


def read_and_write_back(input: str, output: str):
    with open(input) as infile:
        data = json.load(infile)
        write_json_string(data, output)


def read_and_write_back_bytes(input: str, output: str):
    with open(input) as infile:
        data = json.load(infile)
        data_str = format_json_string(data)
        data_bytes = data_str.encode()
        with open(output, "wb") as outfile:
            outfile.write(data_bytes)


def write_json_file(data: dict, output: str):
    # newline="" or "\n" writes with LF. dump does \n by default, but open does os.linesep.
    with open(output, "w", newline="\n") as outfile:
        json.dump(data, outfile, indent=2)


def format_json_string(data: dict) -> str:
    return json.dumps(data, indent=2)


def write_json_string(data: dict, output: str):
    with open(output, "w", newline="\n") as outfile:
        data_str = format_json_string(data)
        outfile.write(data_str)


if __name__ == "__main__":
    read_and_write_back("workspace.json", "testdump.json")
    read_and_write_back_bytes("workspace.json", "testdump.bin")
