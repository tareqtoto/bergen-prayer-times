# Bergen prayer timetable data

This public repository contains the currently verified Bergen Moske monthly
prayer timetable used by a Home Assistant dashboard.

`current.json` is the only live data file. It must contain exactly one complete
calendar month. When a new month is verified, it replaces the prior month;
historical months are not retained here and old-month data must never be shown
as current.

Run the deterministic, network-free validator before publishing an update:

```sh
python3 validate.py
```

The repository contains public timetable data only. It contains no Home
Assistant configuration, credentials, tokens, addresses, personal data,
workflows, JavaScript, executable web code, or inbound Home Assistant access.
