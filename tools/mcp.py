import json, sys, urllib.request, socket

PORTS = [29292, 29293, 29294, 29295]
_id = [0]
_active = [None]


def _post(port, body, timeout=25):
    req = urllib.request.Request(
        "http://127.0.0.1:%d/mcp" % port,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8", "replace")
    try:
        return json.loads(raw)
    except Exception:
        for line in raw.splitlines():
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        raise


def rpc(method, params=None, timeout=25):
    _id[0] += 1
    body = {"jsonrpc": "2.0", "id": _id[0], "method": method}
    if params is not None:
        body["params"] = params
    cands = [_active[0]] if _active[0] else PORTS
    last = None
    for port in cands:
        try:
            res = _post(port, body, timeout)
            if _active[0] != port:
                _active[0] = port
            return res
        except Exception as e:
            last = e
            continue
    raise last


def call(name, args, timeout=25):
    return rpc("tools/call", {"name": name, "arguments": args}, timeout)


if __name__ == "__main__":
    if sys.argv[1] == "list":
        print(json.dumps(rpc("tools/list"), ensure_ascii=False)[:2000])
    else:
        name = sys.argv[1]
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        print(json.dumps(call(name, args), ensure_ascii=False)[:3000])
