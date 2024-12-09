import argparse
import json
import re
import secrets
import textwrap

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


# Not abstracted into more functions because I need to ultimately output a single function body, so this is easier.
def censor_sensitive_information(data: dict) -> dict:
    banned_file_patterns = [
        re.compile(pattern)
        for pattern in [
            r"Some company/.*\.md",
            r"Another company/.*\.md",
        ]
    ]
    banned_search_words = ["secret"]

    data["lastOpenFiles"] = [
        f
        for f in data["lastOpenFiles"]
        if not any([p.match(f) for p in banned_file_patterns])
    ]

    # Windows have same structure, and any specific tab could be on either side.
    for split in map(data.get, ["main", "left", "right"]):
        # ignore horizontal split but respect vertical
        for tabs in split["children"]:
            # Reset active index. We need to know if the active tab is getting closed, and what the new active should be.
            # When going through other windows, it needs to know the active wasn't there.
            active_idx = None
            # Mask makes filtering and calculating new indices slightly more efficient and intuitive. Also allows numpy refactor.
            # Alternative is list of indices to remove.
            to_remove_mask = [False] * len(tabs["children"])
            for idx, tab in enumerate(tabs["children"]):
                if tab["id"] == data["active"]:
                    active_idx = idx
                if tab["state"]["type"] == "search":
                    for w in banned_search_words:
                        if w in tab["state"]["state"]["query"]:
                            # Delete search query.
                            tab["state"]["state"]["query"] = ""
                            break

                elif "file" in tab["state"]["state"] and any(
                    [
                        p.match(tab["state"]["state"]["file"])
                        for p in banned_file_patterns
                    ]
                ):
                    to_remove_mask[idx] = True

            # currentTab can never get lower by removing tabs. If already 0, it won't be in object either before or after.
            # But we might still need idx to adjust active node to different id.
            current_idx = tabs.get("currentTab", 0)
            if active_idx is not None and active_idx != current_idx:
                raise IndexError(
                    "very odd that current and active indices didn't match"
                )
            current_idx = max(0, current_idx - sum(to_remove_mask[: current_idx + 1]))
            if current_idx > 0:
                tabs["currentTab"] = current_idx
            # could also else: split.pop("currentTab", None)
            elif "currentTab" in tabs:
                del tabs["currentTab"]

            tabs["children"] = [
                tabs["children"][i]
                for i, remove in enumerate(to_remove_mask)
                if not remove
            ]

            # If main window and no tabs after filtering, inject node type "empty". Id can be anything.
            # Technically, regenerate tabs. Don't see much reason, but Obsidian does that when closing last tab.
            if split["id"] == data["main"]["id"] and len(tabs["children"]) == 0:
                tabs["id"] = secrets.token_hex(8)
                tabs["children"].append(
                    {
                        "id": secrets.token_hex(8),
                        "type": "leaf",
                        "state": {
                            "type": "empty",
                            "state": {},
                            "icon": "lucide-file",
                            "title": "New tab",
                        },
                    }
                )

            # If active_idx was found, it should equal current tab.
            # If left or right and all children closed, focus main.
            if active_idx is not None:
                if len(tabs["children"]) != 0:
                    data["active"] = tabs["children"][current_idx]["id"]
                else:
                    main_tabs = data["main"]["children"][0]
                    main_idx = main_tabs.get("currentTab", 0)
                    data["active"] = main_tabs["children"][main_idx]["id"]

    return data


def print_command(paths: list[str], words: list[str]):
    print(
        textwrap.dedent(
            # not raw so we can escape leading newline. \\ instead in the code.
            f"""\
            if not filename != r".obsidian/workspace.json":
                return (filename, mode, blob_id)
            
            import json
            import re
            import secrets

            contents = value.get_contents_by_identifier(blob_id)
            data = json.loads(contents)

            banned_file_patterns = [
                re.compile(pattern)
                for pattern in [
                    {paths}
                ]
            ]
            banned_search_words = {words}

            data["lastOpenFiles"] = [
                f
                for f in data["lastOpenFiles"]
                if not any([p.match(f) for p in banned_file_patterns])
            ]

            for split in map(data.get, ["main", "left", "right"]):
                for tabs in split["children"]:
                    active_idx = None
                    to_remove_mask = [False] * len(tabs["children"])
                    for idx, tab in enumerate(tabs["children"]):
                        if tab["id"] == data["active"]:
                            active_idx = idx
                        if tab["state"]["type"] == "search":
                            for w in banned_search_words:
                                if w in tab["state"]["state"]["query"]:
                                    tab["state"]["state"]["query"] = ""
                                    break

                        elif "file" in tab["state"]["state"] and any(
                            [
                                p.match(tab["state"]["state"]["file"])
                                for p in banned_file_patterns
                            ]
                        ):
                            to_remove_mask[idx] = True

                    current_idx = tabs.get("currentTab", 0)
                    if active_idx is not None and active_idx != current_idx:
                        raise IndexError(
                            "very odd that current and active indices didn't match"
                        )
                    current_idx = max(0, current_idx - sum(to_remove_mask[: current_idx + 1]))
                    if current_idx > 0:
                        tabs["currentTab"] = current_idx
                    elif "currentTab" in tabs:
                        del tabs["currentTab"]

                    tabs["children"] = [
                        tabs["children"][i]
                        for i, remove in enumerate(to_remove_mask)
                        if not remove
                    ]

                    if split["id"] == data["main"]["id"] and len(tabs["children"]) == 0:
                        tabs["id"] = secrets.token_hex(8)
                        tabs["children"].append(
                            {{
                                "id": secrets.token_hex(8),
                                "type": "leaf",
                                "state": {{
                                    "type": "empty",
                                    "state": {{}},
                                    "icon": "lucide-file",
                                    "title": "New tab",
                                }},
                            }}
                        )

                    if active_idx is not None:
                        if len(tabs["children"]) != 0:
                            data["active"] = tabs["children"][current_idx]["id"]
                        else:
                            main_tabs = data["main"]["children"][0]
                            main_idx = main_tabs.get("currentTab", 0)
                            data["active"] = main_tabs["children"][main_idx]["id"] 

            data_str = json.dumps(data, indent=2)
            data_bytes = data_str.encode()
            new_blob_id = value.insert_file_with_contents(data_bytes)

            return (filename, mode, new_blob_id)
            """
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    exclusive_group = parser.add_mutually_exclusive_group(required=True)
    exclusive_group.add_argument(
        "--print",
        "-P",
        action="store_true",
        help="print method body to give to git filter-repo --file-info-callback",
    )
    exclusive_group.add_argument(
        "--test",
        "-T",
        action="store_true",
        help="perform test censoring operation on files",
    )
    parser.add_argument(
        "--file",
        "-f",
        dest="input",
        default="workspace.json",
        help="input file to censor",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="workspace_filtered.json",
        help="output file after censoring",
    )
    parser.add_argument(
        "--paths",
        "-p",
        nargs="*",
        default=[
            r"Some company/.*\.md",
            r"Another company/.*\.md",
        ],
        help="list of file paths to censor",
    )
    parser.add_argument(
        "--words",
        "-w",
        nargs="*",
        default=["secret"],
        help="list of file paths to censor",
    )

    args = parser.parse_args()
    if args.test:
        main(args.input, args.output)
    elif args.print:
        print_command(args.paths, args.words)


# Things I understand about workspace.json
# Also this documentation: https://docs.obsidian.md/Plugins/User+interface/Workspace

# Split can have multiple children if vertical split. Horizontal split gets weird, though.

# All windows have a "currentTab" in the "tabs" child.
# If out of bounds, corrects when opened.
# If first tab selected, removes property instead of setting 0.
# Best to adjust if tab is removed.

# When current tab is closed, current index moves down.

# "active" applies to all windows.

# Don't use list comprehension. You need the index and id to check if "currentTab" or "active" was removed.

# All splits, "left", "right", and "main" have the same general structure.
# split -> tabs -> leaf.
# If you have horizontal split windows, it's more complicated.
# Technically, you can move items between them, so each specific tab we look for could be either left or right.
# Maybe common code. In that case, use filter function.

# leaf id can be anything. Keeps id even if you open another file (in the same tab).
# Obsidian uses 16 chars. uuid is 32. secrets with 8 bytes is 16 and also sufficiently random.
# If missing or empty string for "id" or "active", generated when Obsidian reopened.

# If no file opened, leaf node with "type": "empty" is created. Has "id" and possibly the "active" node.
# If instead children is empty, it will open most recent file and generate node. Also regenerate split and tabs.
# If no children and no recent files, generate empty node when opened.
# Regeneration of tabs also happens when closing last tab naturally.

# "left" and "right" sidebars have empty array children when everything is closed.
# "collapsed" true hides the sidebar. If not set and empty children, it's ugly but works.
# No children corrects to defaults when Obsidian reopened.

# Backlinks, outline, etc. don't always update to follow the current file.
# All seem to follow when clicking to different file, but not when keyboard navigating, e.g. ctrl+tab or ctrl+o.
# Backlinks and outline seem to follow. Outgoing links don't.

# Content of sidebar tabs isn't in file, e.g. search result, actual backlinks from other files.
