---
name: wikipedia
track: bonus
kind: live_api
provider: Wikipedia REST API (no key)
requires_env: []
inputs: [title, lang]
outputs: [found, title, description, summary, url, source, is_disambiguation]
side_effect: false
---
# wikipedia

Returns the lead summary of a Wikipedia article (`en` or `vi`). Free, no API key.
A missing article returns `found=false` (not an error). Empty `title` or HTTP
failures return an error dict. Summary is capped at 1500 chars.
