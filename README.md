# Censor Obsidian workspace.json

Python script to censor specific file paths and search terms from Obsidian's `workspace.json` file. This file keeps track of what files you have open. I version control it to keep workspace synced between different machines, but some people gitignore it.

Script will output a callback you can use with [git filter-repo](https://github.com/newren/git-filter-repo). Change the censored terms before applying it to the repo.

By far the easiest and simplest solution is to just delete the file from history. Doing this and adding it to `.gitignore` has the added benefit of not leaking file names in the future, in the case you keep company notes in the same vault but gitignored.

But that's no fun. The more _eLeGaNt_ solution is the surgically remove only the exact information that needs censoring.

The 2nd easiest solution is to just remove anything that _could_ contain unwanted information. This would leave the file in a partial state, which is actually fine seeing as Obsidian is very good at just generating the missing stuff on startup. But it's not _eLeGaNt_.
