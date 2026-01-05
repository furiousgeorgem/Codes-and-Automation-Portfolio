# archived_scripts

This folder holds older or superseded versions of scripts that were deliberately removed from the main project tree to keep `main` focused on the current, maintained versions.

Why these files are here
- Preserve history: files are moved (with `git mv`) so their full git history is retained.
- Keep main tidy: reduce confusion by keeping only the actively maintained scripts at the top level.
- Make it easy to restore: files can be moved back into place if needed.

Contents (examples)
- amazon_songs.py — older version moved from `amazon_songs/`
- furious_multi_matcher2.py — older version moved from `furious_multi_matcher/`
- furious_reporter2.py — older version moved from `furious_reporter/`

How to restore a file
1. Create a branch from `main`:
   git checkout -b restore/<file-name>
2. Move the file back to its original location:
   git mv archived_scripts/<file> <original/path>/<file>
3. Commit and push:
   git commit -m "Restore <file> from archived_scripts/"
   git push -u origin HEAD
4. Open a PR to merge the restore branch into `main`.
