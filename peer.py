import socket
import threading
import requests
import sys
import os


# --- CONFIGURATION ---
REGISTRY_URL = "http://127.0.0.1:5000" 
MY_IP = "127.0.0.1" 
# Change this for every peer you run (5001, 5002, etc.)
MY_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
MY_USERNAME = sys.argv[2] if len(sys.argv) > 2 else "Alice"

# --- GLOBAL VARIABLES ---
# Used to pass the incoming connection from the background thread to the main menu
PENDING_CONNECTION = None 
PENDING_ADDR = None
PENDING_NAME = None



def handle_incoming_messages(conn, user_name):
    print(f"\n[+] Listening for messages from {user_name}...")
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                print(f"\n[-] {user_name} disconnected.")
                break # Exit thread if connection dies
                
            decoded = data.decode('utf-8', errors='ignore')
            
            # 1. Handle Text Message
            if decoded.startswith("MSG:"):
                msg_content = decoded[4:]
                print(f"\n[{user_name}]: {msg_content}")
                print(f"You: ", end="", flush=True) # Restore input prompt
            
            # 2. Handle File Transfer (Bonus)
            elif decoded.startswith("FILE:"):
                # Header format: FILE:filename:filesize
                parts = decoded.split(":")
                filename = parts[1]
                filesize = int(parts[2])
                print(f"\n[!] Receiving file: {filename} ({filesize} bytes)")
                
                # Create a file to write to
                with open(f"received_{filename}", "wb") as f:
                    bytes_received = 0
                    while bytes_received < filesize:
                        # We read the raw chunks from the socket
                        chunk = conn.recv(1024)
                        if not chunk: break
                        f.write(chunk)
                        bytes_received += len(chunk)
                print(f"[+] File saved as 'received_{filename}'")
                print(f"You: ", end="", flush=True)

        except Exception as e:
            print(f"\n[-] Error receiving data: {e}")
            break
    conn.close()

def chat_session(sock, remote_name):
    # Start a thread to listen for incoming messages
    listener = threading.Thread(target=handle_incoming_messages, args=(sock, remote_name))
    listener.daemon = True
    listener.start()

    print(f"\n--- CHAT STARTED with {remote_name} ---")
    print("Type 'exit' to quit, 'file' to send a file.")
    
    # Send Loop
    while True:
        try:
            msg = input("You: ")
            
            if msg.lower() == 'exit':
                sock.close()
                print("[*] Chat ended.")
                break
                
            elif msg.lower() == 'file':
                filepath = input("Enter file path: ")
                if os.path.exists(filepath):
                    filename = os.path.basename(filepath)
                    filesize = os.path.getsize(filepath)
                    
                    # Send Header
                    header = f"FILE:{filename}:{filesize}"
                    sock.send(header.encode('utf-8'))
                    
                    # Send Body
                    with open(filepath, "rb") as f:
                        while True:
                            bytes_read = f.read(1024)
                            if not bytes_read: break
                            sock.send(bytes_read)
                    print(f"[+] Sent {filename}")
                else:
                    print("[-] File not found.")
            else:
                # Standard Message
                sock.send(f"MSG:{msg}".encode('utf-8'))
                
        except (BrokenPipeError, OSError):
            print("[-] Connection lost.")
            break

def listen_for_requests():
    
    global PENDING_CONNECTION, PENDING_ADDR, PENDING_NAME
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((MY_IP, MY_PORT))
    server_sock.listen(5)
    
    while True:
        conn, addr = server_sock.accept()
        try:
            # Peek/Read the handshake REQ
            data = conn.recv(1024).decode('utf-8')
            if data.startswith("REQ:"):
                requester_name = data.split(":")[1]
                
                # STORE IT IN GLOBAL VARS
                PENDING_CONNECTION = conn
                PENDING_ADDR = addr
                PENDING_NAME = requester_name
                
                # Just notify the user, don't block
                print(f"\n\n[!] INCOMING REQUEST from '{requester_name}'!")
                print(f"[!] Type 'y' and Enter to accept, or 'n' to reject.")
                print("Select: ", end="", flush=True) 
            else:
                conn.close()
        except Exception as e:
            print(e)

def main_menu():
    global PENDING_CONNECTION, PENDING_NAME
    
    # 1. Register with Server
    try:
        data = {"username": MY_USERNAME, "ip": MY_IP, "port": MY_PORT}
        requests.post(f"{REGISTRY_URL}/register", json=data)
        print(f"[+] Registered as {MY_USERNAME} on {MY_PORT}")
    except:
        print("[-] Could not connect to Registry Server.")

    # 2. Start Listening Thread
    threading.Thread(target=listen_for_requests, daemon=True).start()

    # 3. Main Loop
    while True:
        print("\n--- Menu ---")
        print("1. List Peers")
        print("2. Chat (Connect to someone)")
        print("3. Exit Program")
        
        # If there is a pending request, we remind the user
        if PENDING_CONNECTION:
            print(f"*** PENDING REQUEST FROM {PENDING_NAME} (Type 'y' to accept) ***")
            
        choice = input("Select: ")

        # --- HIDDEN OPTION: ACCEPT REQUEST ---
        if choice.lower() == 'y' and PENDING_CONNECTION:
            print(f"[+] Accepting connection from {PENDING_NAME}...")
            # Send YES
            PENDING_CONNECTION.send("YES".encode('utf-8'))
            # Enter Chat
            chat_session(PENDING_CONNECTION, PENDING_NAME)
            # Reset Global
            PENDING_CONNECTION = None
            PENDING_NAME = None
            
        # --- HIDDEN OPTION: REJECT REQUEST ---
        elif choice.lower() == 'n' and PENDING_CONNECTION:
            print(f"[-] Rejecting connection from {PENDING_NAME}...")
            PENDING_CONNECTION.send("NO".encode('utf-8'))
            PENDING_CONNECTION.close()
            PENDING_CONNECTION = None
            PENDING_NAME = None

        elif choice == '1':
            try:
                res = requests.get(f"{REGISTRY_URL}/peers")
                print("Online Users:", res.json())
            except:
                print("[-] Registry Error")

        elif choice == '2':
            target = input("Enter username to call: ")
            try:
                res = requests.get(f"{REGISTRY_URL}/peerinfo", params={"username": target})
                if res.status_code == 200:
                    info = res.json()
                    ip, port = info['ip'], int(info['port'])
                    
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((ip, port))
                    
                    # Handshake
                    s.send(f"REQ:{MY_USERNAME}".encode('utf-8'))
                    print("[*] Calling... Waiting for response...")
                    
                    resp = s.recv(1024).decode('utf-8')
                    if resp == "YES":
                        chat_session(s, target)
                    else:
                        print("[-] Connection Rejected.")
                        s.close()
                else:
                    print("[-] User not found.")
            except Exception as e:
                print(f"[-] Error: {e}")

        elif choice == '3':
            sys.exit()

if __name__ == "__main__":
    main_menu()
