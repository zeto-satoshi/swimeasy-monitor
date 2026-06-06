Create a git commit for the current changes.

Steps:
1. Run `git diff` (staged + unstaged) and `git status`
2. Summarize what changed and why (infer from the diff)
3. Write a commit message: one concise subject line + optional body if needed
4. Stage relevant files — NEVER: .env, *.log, __pycache__
5. Commit and confirm

Follow existing commit style in `git log`.
Co-author line: Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
