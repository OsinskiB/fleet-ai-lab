# Learnings

## 2026-11-16 – API key almost pushed to GitHub
- Problem: .env (with the API key) was included in the first commit.
- Cause: .gitignore was edited but not saved before `git add .`.
- Fix: `git rm --cached .env`, `git commit --amend`, checked with `git show --stat HEAD` before pushing.
- Lesson: always run `git status` before committing.