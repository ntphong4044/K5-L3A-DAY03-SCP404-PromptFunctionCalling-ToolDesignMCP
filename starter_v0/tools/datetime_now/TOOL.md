---
name: datetime_now
track: bonus
kind: local_knowledge
provider: Python stdlib (no network, no key)
requires_env: []
inputs: [timezone_name]
outputs: [timezone, iso, date, time, weekday, utc_offset]
side_effect: false
---
# datetime_now

Current date/time in a timezone: `UTC`, a known name (`Asia/Ho_Chi_Minh`, ...)
or an offset like `UTC+7`. Uses fixed offsets (no DST, no tzdata needed on
Windows). Unknown timezone returns an error dict. The param is
`timezone_name` so it does not shadow `datetime.timezone`.
