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
    banned_search_words = ["secret"]

    data["lastOpenFiles"] = [
        f
        for f in data["lastOpenFiles"]
        if not any([p.match(f) for p in banned_file_patterns])
    ]

    adjusted_active = False
    # Windows have same structure, and any specific tab could be on either side.
    for window in map(data.get, ["main", "left", "right"]):
        # ignore horizontal split but respect vertical
        for split in window["children"]:
            adjusted_current = False
            # Reset active index. We need to know if the active tab is getting closed, and what the new active should be.
            # When going through other windows, it needs to know the active wasn't there.
            active_idx = None
            # Mask makes filtering and calculating new indices slightly more efficient and intuitive. Also allows numpy refactor.
            # Alternative is list of indices to remove.
            to_remove_mask = [False] * len(split["children"])
            for idx, tab in enumerate(split["children"]):
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
            current_idx = split.get("currentTab", 0)
            if active_idx is not None and active_idx != current_idx:
                raise IndexError(
                    "very odd that current and active indices didn't match"
                )
            current_idx = current_idx - max(0, sum(to_remove_mask[: current_idx + 1]))
            if current_idx > 0:
                split["currentTab"] = current_idx
            # could also else: split.pop("currentTab", None)
            elif "currentTab" in split:
                del split["currentTab"]

            split["children"] = [
                split["children"][i]
                for i, remove in enumerate(to_remove_mask)
                if not remove
            ]

            # If active_idx was found, it should equal current tab.
            if active_idx is not None:
                data["active"] = split["children"][current_idx]["id"]

    return data


if __name__ == "__main__":
    main("workspace.json", "workspace_filtered.json")


# Things I understand about workspace.json

# Windows can have multiple children if vertical split. Horizontal split gets weird, though.

# All windows have a "currentTab" in the "tabs" child.
# If out of bounds, corrects when opened.
# If first tab selected, removes property instead of setting 0.
# Best to adjust if tab is removed.

# When current tab is closed, current index moves down.

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
# If instead children is empty, it will generate empty node when opened. Also regenerate split and tabs.

# "left" and "right" sidebars have empty array children when everything is closed.
# "collapsed" true hides the sidebar. If not set and empty children, it's ugly but works.
# No children corrects to defaults when Obsidian reopened.

# Backlinks, outline, etc. don't always update to follow the current file.
# All seem to follow when clicking to different file, but not when keyboard navigating, e.g. ctrl+tab or ctrl+o.
# Backlinks and outline seem to follow. Outgoing links don't.

# Content of sidebar tabs isn't in file, e.g. search result, actual backlinks from other files.
