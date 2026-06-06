Review $ARGUMENTS for quality, correctness, and security.

Check for:
- Logic bugs or edge cases that could cause failures (especially Playwright selectors)
- Security issues (hardcoded secrets, unvalidated input)
- Error handling gaps — what happens when Playwright times out or Telegram fails?
- Unnecessary complexity — is there a simpler way?
- Python best practices (type hints, naming, structure)

For each issue found:
1. Quote the relevant line(s)
2. Explain what the problem is
3. Show the fix

End with: overall quality, biggest risk, one thing done well.
Keep it direct — no filler, no praise padding.
