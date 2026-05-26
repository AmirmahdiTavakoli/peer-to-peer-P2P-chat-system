
# P2P Chat System (LAN‑based)

A minimal **peer‑to‑peer chat application** built as a university networking project.  
Peers register with a central HTTP registry (STUN‑like directory), discover each other, and then communicate directly over **TCP** – text messages **and files**.

> ⚠️ Works **only on a local network** (or with public, directly reachable IPs). No NAT traversal.

---

## 🚀 Features

- **HTTP registry server** (Flask) that stores `username` → `(IP, port)`
- **Direct TCP connection** between peers after discovery
- **Real‑time text messaging** (prefix `MSG:`)
- **Accept / reject incoming calls** (interactive menu)
- **File transfer** (bonus) – send any file; receiver saves as `received_<filename>`
- **Multi‑threaded** – background listener for incoming requests while in main menu
- **Basic error handling** – disconnections, registry failures

---

## 📦 Project Structure

```
.
├── registry_server.py      # Flask directory server
├── peer.py                 # Peer client (run multiple instances)
└── README.md
```

---

## 🛠️ Requirements

- Python 3.7+
- `flask`, `requests` (install via pip)

```bash
pip install flask requests
```

---

## ▶️ How to Run

### 1. Start the Registry Server

```bash
python registry_server.py
```

- Runs on `http://127.0.0.1:5000`
- Keeps a simple in‑memory list of online peers.

### 2. Start Peer Clients (two or more terminals)

Each peer needs a **unique port** and **username**:

```bash
python peer.py 5001 Alice
python peer.py 5002 Bob
python peer.py 5003 Charlie
```

The arguments are:  
`python peer.py <listening_port> <username>`

Upon start, each peer:
- Registers itself with the registry.
- Starts a TCP server on its given port.
- Shows a text menu.

### 3. Use the Chat

From any peer’s menu:
- `1` – List all online users
- `2` – Call another user (enter their username)
- `3` – Exit

When someone calls you, you’ll see:
```
[!] INCOMING REQUEST from 'Bob'!
Type 'y' to accept, 'n' to reject.
```
Then in the menu, type `y` or `n`.

Once connected:
- Type normal messages and press Enter.
- Type `file` to send a file (will ask for file path).
- Type `exit` to close the chat.

---

## 📁 File Transfer Details

- Sender triggers with `file` command.
- Protocol:  
  - Header: `FILE:<filename>:<filesize>`  
  - Body: raw binary chunks.
- Receiver saves as `received_<original_filename>` in the peer’s working directory.

---

## ⚠️ Limitations (Important)

| Limitation | Explanation |
|------------|-------------|
| **LAN only** | No NAT hole punching – both peers must be on the same local network or have publicly reachable IPs (e.g., `127.0.0.1` / direct VPN). |
| **No re‑registration** | If a peer’s IP changes, it must be restarted. |
| **Single pending request** | Only one incoming call can be queued; later requests overwrite the pending one. |
| **Plaintext protocol** | No encryption (not suitable for production). |
| **In‑memory registry** | All peers lost when registry restarts. |
| **No IPv6** | Hardcoded for IPv4. |

---

## 🧪 Example (local machine)

**Terminal 1**
```bash
python registry_server.py
```

**Terminal 2**
```bash
python peer.py 5001 Alice
```

**Terminal 3**
```bash
python peer.py 5002 Bob
```

From Bob’s menu:
- `1` → sees `['Alice']`
- `2` → call `Alice`
- Alice sees incoming request, types `y`
- Chat starts!

---

## 📚 Educational Purpose

This project was created for a **Computer Networks** course to demonstrate:
- Socket programming (`TCP`)
- Multithreading for concurrent I/O
- HTTP client/server interaction (Flask + `requests`)
- Peer discovery with a central directory
- Simple file transfer over sockets

It deliberately avoids external libraries like `asyncio` or `pynat` to keep the core concepts clear.

