# Firewall

The `client.firewall` module is the largest of the modules. It wraps
five logically distinct surfaces that the GL.iNet API exposes under a
single `firewall` namespace.

## 1. Custom firewall rules

```python
rules = await client.firewall.get_rule_list()
await client.firewall.add_rule({"name": "Allow SSH from LAN", "proto": "tcp",
                                "src": "lan", "dest_port": 22, "enabled": True})
await client.firewall.set_rule({"id": "…", "name": "Updated name"})
await client.firewall.remove_rule({"id": "…"})
```

The exact parameter shape depends on the firmware version. See the
GL.iNet developer docs (`dev-docs.docx`) for the full schema; the
library forwards whatever you pass.

## 2. Access-control rules (ACLs)

ACLs are per-client allow/deny entries:

```python
acls = await client.firewall.get_acl_rule_list()   # list of dicts
await client.firewall.add_acl_rule({"src_mac": "…", "action": "accept"})
await client.firewall.edit_acl_rule({"id": "…", "src_mac": "…", "action": "deny"})
await client.firewall.delete_acl_rule({"id": "…"})
await client.firewall.order_acl_rule(id_list=["…", "…", "…"])
```

`order_acl_rule` takes an explicit list of ids in the desired priority
order; the router reorders them in a single call.

## 3. Port forwards

```python
forwards = await client.firewall.get_port_forward_list()
await client.firewall.add_port_forward({
    "name": "Web server",
    "proto": "tcp",
    "src": "wan",
    "src_port": 80,
    "dest_ip": "192.168.8.10",
    "dest_port": 80,
})
await client.firewall.set_port_forward({"id": "…", "enabled": False})
await client.firewall.remove_port_forward({"id": "…"})
await client.firewall.order_port_forward(id_list=["…", "…", "…"])
```

## 4. DMZ

```python
dmz = await client.firewall.get_dmz()    # {"enabled": bool, "dest_ip": str}
await client.firewall.set_dmz(enabled=True, dest_ip="192.168.8.10")
await client.firewall.set_dmz(enabled=False)
```

`dest_ip` is optional when disabling; pass it when enabling.

## 5. WAN access

```python
wan = await client.firewall.get_wan_access()       # dict
await client.firewall.set_wan_access({"https": True, "ssh": False})
```

## Zones (informational)

```python
zones = await client.firewall.get_zone_list()
acl_zones = await client.firewall.get_acl_zone_list()
```

These are read-only; the GL.iNet API does not expose zone creation
endpoints.

## See also

- [Errors](errors.md) — what happens when a rule id does not exist.
- [Architecture](architecture.md) — how module methods share the
  `_call` helper.
