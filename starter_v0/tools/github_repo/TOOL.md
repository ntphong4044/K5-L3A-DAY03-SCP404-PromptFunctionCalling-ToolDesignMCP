---
name: github_repo
track: bonus
kind: live_api
provider: GitHub REST API (no key)
requires_env: []
inputs: [repo]
outputs: [found, repo, description, stars, forks, open_issues, language, license, topics, archived, last_push, url]
side_effect: false
---
# github_repo

Public metadata of one GitHub repo. `repo` accepts `owner/name` or a full
github.com URL. Unknown repo returns `found=false`. Rate limit (60 req/hour
without a token) and malformed input return an error dict.
