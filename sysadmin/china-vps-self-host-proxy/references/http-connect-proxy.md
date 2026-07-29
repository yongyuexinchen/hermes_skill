# HTTP CONNECT Proxy (Python)

The simplest possible proxy that bypasses GFW DPI entirely. ISP sees plain HTTP traffic on port 80.

## Server-side script

Save as `/usr/local/bin/http-proxy.py` on VPS:

```python
import socket, select, threading

def relay(a, b):
    """Bidirectional TCP relay between two sockets."""
    try:
        while True:
            r, _, _ = select.select([a, b], [], [], 30)
            if not r:
                break
            for s in r:
                d = s.recv(8192)
                if not d:
                    return
                (b if s is a else a).sendall(d)
    except:
        pass

def handle(client):
    """Handle one client connection."""
    remote = None
    try:
        data = client.recv(8192)
        if not data:
            return
        line = data.split(b'\r\n')[0].decode()
        if line.startswith('CONNECT'):
            # HTTPS tunnel
            host, port = line.split()[1].split(':')
            remote = socket.create_connection((host, int(port)), 10)
            client.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            relay(client, remote)
    except:
        pass
    finally:
        client.close()
        if remote:
            remote.close()

def main():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 80))
    s.listen(50)
    print('HTTP CONNECT Proxy listening on :80')
    while True:
        c, addr = s.accept()
        threading.Thread(target=handle, args=(c,), daemon=True).start()

if __name__ == '__main__':
    main()
```

## Usage

### Start (on VPS)
```bash
# Free up port 80
systemctl stop nginx

# Start proxy in background
nohup python3 /usr/local/bin/http-proxy.py > /dev/null 2>&1 &
```

### Client (Windows)
Settings → Network → Proxy → Manual:
- Address: `VPS_IP`
- Port: `80`

## Limitations
- No authentication (VPS IP is the only secret)
- No encryption on the HTTP CONNECT channel (but HTTPS sites are end-to-end encrypted anyway)
- Single-threaded relay per connection (fine for personal use)
