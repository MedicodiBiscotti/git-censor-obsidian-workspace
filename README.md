# Censor Obsidian workspace.json

Python script to censor specific file paths and search terms from Obsidian's `workspace.json` file. This file keeps track of what files you have open. I version control it to keep workspace synced between different machines, but some people gitignore it.

Script will output a callback you can use with [git filter-repo](https://github.com/newren/git-filter-repo). Change the censored terms before applying it to the repo.

By far the easiest and simplest solution is to just delete the file from history. Doing this and adding it to `.gitignore` has the added benefit of not leaking file names in the future, in the case you keep company notes in the same vault but gitignored.

But that's no fun. The more _eLeGaNt_ solution is the surgically remove only the exact information that needs censoring.

The 2nd easiest solution is to just remove anything that _could_ contain unwanted information. This would leave the file in a partial state, which is actually fine seeing as Obsidian is very good at just generating the missing stuff on startup. But it's not _eLeGaNt_.

## Usage

Needs either `-T` or `-P` to decide what operation to do, do censorship on **test files**, or **print** function body to console.

Optional parameters default to whatever the test scenario required.

`-p` is the list of file paths to censor. Must be supplied as **regex**. Don't escape the `\` for the file extension (`\.md`). Python does that itself.

`-w` is the list of search words to censor, i.e. if secret search term shows up in the search tab, remove it. If search term contains spaces, remember to quote that search term. Otherwise it's interpreted as separate words.

Currently, `-p` and `-w` are only used in `-P` mode because the test scenario is hard-coded. It would make sense to also use parameters there, though, since it can take different test file with `-f`.
