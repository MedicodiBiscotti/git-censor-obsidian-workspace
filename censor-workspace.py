import json
import re

# str.encode should output needed bytes (byte string, I think).
# json.loads can read bytes in UTF which workspace should be in, I think.
# When testing censoring logic, we don't need to bother with bytes.
# If you can test whether bytes file is identical with Git object, please do so.


def read_and_write_back(input: str, output: str):
    data = read_data(input)
    write_json_string(data, output)


def read_and_write_back_bytes(input: str, output: str):
    data = read_data(input)
    write_json_bytes(data, output)


def read_data(input: str) -> dict:
    with open(input) as infile:
        data = json.load(infile)
        return data


def write_json_file(data: dict, output: str):
    # newline="" or "\n" writes with LF. dump does \n by default, but open does os.linesep.
    with open(output, "w", newline="\n") as outfile:
        json.dump(data, outfile, indent=2)


def format_json_string(data: dict) -> str:
    return json.dumps(data, indent=2)


def write_json_string(data: dict, output: str):
    data_str = format_json_string(data)
    with open(output, "w", newline="\n") as outfile:
        outfile.write(data_str)


def write_json_bytes(data: dict, output: str):
    data_str = format_json_string(data)
    data_bytes = data_str.encode()
    with open(output, "wb") as outfile:
        outfile.write(data_bytes)


def main(input: str, output: str):
    data = read_data(input)
    data = censor_sensitive_information(data)
    write_json_bytes(data, output)


def censor_sensitive_information(data: dict) -> dict:
    banned_file_patterns = [
        re.compile(pattern)
        for pattern in [
            r"Some company/.*\.md",
            r"Another company/.*\.md",
        ]
    ]

    data["lastOpenFiles"] = [
        f
        for f in data["lastOpenFiles"]
        if not any([p.match(f) for p in banned_file_patterns])
    ]

    banned_search_words = ["secret"]
    for tab in data["left"]["children"][0]["children"]:
        if tab["state"]["type"] == "search":
            for w in banned_search_words:
                if w in tab["state"]["state"]["query"]:
                    tab["state"]["state"]["query"] = ""
                    break

    # Absolutely nutty comprehension.
    data["right"]["children"][0]["children"] = [
        t
        for t in data["right"]["children"][0]["children"]
        if "file" not in t["state"]["state"]
        or not any([p.match(t["state"]["state"]["file"]) for p in banned_file_patterns])
    ]

    return data


if __name__ == "__main__":
    main("workspace.json", "workspace_filtered.json")


# Things I understand about workspace.json

# Windows can have multiple children if vertical split. Horizontal split gets weird, though.

# All windows have a "currentTab" in the "tabs" child.
# If out of bounds, corrects when opened.
# If first tab selected, removes property instead of setting 0.
# Best to adjust if tab is removed.

# "active" applies to all windows.

# Don't use list comprehension. You need the index and id to check if "currentTab" or "active" was removed.

# All windows, "left", "right", and "main" have the same general structure.
# split -> tabs -> leaf.
# If you have horizontal split windows, it's more complicated.
# Technically, you can move items between them, so each specific tab we look for could be either left or right.
# Maybe common code. In that case, use filter function.

# leaf id can be anything. Keeps id even if you open another file (in the same tab).
# If missing or empty string for "id" or "active", generated when Obsidian reopened.

# If no file opened, leaf node with "type": "empty" is created. Has "id" and possibly the "active" node.

# "left" and "right" sidebars have empty array children when everything is closed.
# "collapsed" true hides the sidebar. If not set and empty children, it's ugly but works.
# No children corrects to defaults when Obsidian reopened.

# Backlinks, outline, etc. don't always update to follow the current file.
# All seem to follow when clicking to different file, but not when keyboard navigating, e.g. ctrl+tab or ctrl+o.
# Backlinks and outline seem to follow. Outgoing links don't.

# Content of sidebar tabs isn't in file, e.g. search result, actual backlinks from other files.
