# Examples

Runnable scripts that demonstrate `glinet` outside the Home Assistant
context.

| Script | Purpose | Requires |
| --- | --- | --- |
| [`print_router_info.py`](print_router_info.py) | Authenticate and dump router model, firmware, status, and the list of online clients. | `glinet[auth]` |
| [`send_sms.py`](send_sms.py) | Send an SMS via the router's SIM card (cellular models only). | `glinet[auth]` |
| [`raw_rpc.py`](raw_rpc.py) | Make a raw JSON-RPC call without installing `passlib`. Useful for scripting and ad-hoc queries. | `glinet` only |

## Running an example

```bash
# From the repository root:
pip install -e '.[auth]'
python examples/print_router_info.py --host http://192.168.8.1 --password your-password
```

## Adding a new example

1. Add the script under this folder.
2. Make it executable directly (`chmod +x`) and add a `#!/usr/bin/env python3`
   shebang if you want.
3. Document what it does in the table above.
4. Use only the public `glinet` API (`from glinet_router import ...`) — do not reach
   into the package internals.
