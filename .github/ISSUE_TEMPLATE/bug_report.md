---
name: Bug report
about: Report a problem with the glinet Python client
title: "[Bug] "
labels: ["bug"]
---

### Summary

<!-- What happened? -->

### Reproduction

<!-- Minimal code snippet that reproduces the issue. -->

```python
import asyncio
from glinet import GLinetApiClient


async def main() -> None:
    async with GLinetApiClient("http://192.168.8.1/rpc") as client:
        ...


asyncio.run(main())
```

### Expected behavior

### Actual behavior

### Environment

- Library version: e.g. `glinet==0.0.1`
- Python version: e.g. `Python 3.12.4`
- Router model: e.g. `GL.iNet Beryl (GL-MT1300)`
- Router firmware version: e.g. `4.5.0`

### Logs

```
Paste the relevant traceback or logs here.
```
