# Parental control

The `client.parental_control` module exposes the GL.iNet
`parental-control` JSON-RPC namespace. The API is split into three
logical surfaces: global enable/config, time-window "brief" rules, and
per-client groups.

## Global state

```python
config = await client.parental_control.get_config()
await client.parental_control.set_config(enable=True)
status = await client.parental_control.get_status()
await client.parental_control.update()      # ask the router to reload
```

`update()` triggers a router-side reload after you change group
membership or filtering mode.

## Filtering mode

```python
mode = await client.parental_control.get_mode()    # {"mode": 0/1}
await client.parental_control.set_mode(mode=0)     # 0 = whitelist, 1 = blacklist
```

The exact mode numbering is firmware-specific; check your router's
admin UI for the current values.

## Time-window "brief" rules

Brief rules attach a time window (e.g. "block between 22:00 and 07:00")
to a specific group. The router returns the rule id when you create
one — pass it back to update.

```python
result = await client.parental_control.set_brief(
    enable=True,
    time="22:00-07:00",
    rule_id="…",          # from a previous call
    group_id="…",
    manual_stop=False,
)
```

`get_brief(group_id)` returns the current brief for a group:

```python
brief = await client.parental_control.get_brief(group_id="…")
```

## Groups

```python
await client.parental_control.set_group(
    id="…",
    name="Kids",
    mac=["aa:bb:cc:dd:ee:ff"],
    # any other group fields the firmware accepts
)
```

The library forwards unknown keys as-is. Use the router's admin UI to
discover the supported field names for your firmware version.

## Companion: black/white list

The `client.black_white_list` module is the older access-control
surface that some firmwares still expose alongside parental control:

```python
await client.black_white_list.set_config(mode="black", mac=["aa:bb:cc:dd:ee:ff"])
await client.black_white_list.set_single_mac(mode="white", operate="add",
                                             mac="aa:bb:cc:dd:ee:ff")
config = await client.black_white_list.get_config()
```

If your firmware exposes both, prefer parental control — the API is
richer and more stable across versions.

## See also

- [Errors](errors.md) — what happens when a group id does not exist.
- [Architecture](architecture.md) — how module methods share the
  `_call` helper.
