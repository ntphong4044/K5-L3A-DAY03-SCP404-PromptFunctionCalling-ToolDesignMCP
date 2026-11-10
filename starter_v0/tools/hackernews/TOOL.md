---
name: hackernews
track: bonus
kind: live_api
provider: Hacker News Algolia API (no key)
requires_env: []
inputs: [limit, kind]
outputs: [items]
side_effect: false
---
# hackernews

Lists Hacker News stories: `kind=top` (front page) or `kind=new` (latest).
`limit` is clamped to 1..10. Items use the same `title/url/source/summary`
shape as other tools, so they can be passed straight to `format`.
Free, no API key.
