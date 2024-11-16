
# CToDNS - Command and Control Server Over DNS

CToDNS is a Command and Control (C2) server that communicates with remote beacons over DNS, leveraging DNS TXT records for command transmission and DNS queries for response delivery.

---

## Features
- Communicate with remote machines using DNS TXT records.
- Support for splitting large responses into manageable chunks.
- Automatically decodes and displays responses from beacons.
- Built-in nsupdate integration for dynamic DNS updates.
- Interactive and color-coded CLI for seamless operation.

---

## Prerequisites

### Install Required Software
1. **Python 3.x**  
   Ensure Python 3.x is installed on your machine.
   
2. **Required Python Libraries**  
   Install the necessary Python libraries using pip:
   ```bash
   pip install scapy termcolor
   ```
3. DNS Server
A Bind9 DNS server configured to handle dynamic updates for the communication domain.


## Setting Up the DNS Server

Step 1: Install Bind9
 ```bash
sudo apt update
sudo apt install bind9 bind9utils
```

Step 2: Configure the Zone
Edit /etc/bind/named.conf.local to add the zone configuration:
 ```bash
zone "your_domain.co.il" {
    type master;
    file "/etc/bind/db.your_domain.co.il";
    allow-update { localhost; };
};
```

Step 3: Create the Zone File
Create the zone file /etc/bind/db.your_domain.co.il:
```bash
$TTL 3600
@   IN  SOA ns1.your_domain.co.il. admin.your_domain.co.il. (
        1       ; Serial
        3600    ; Refresh
        1800    ; Retry
        604800  ; Expire
        86400 ) ; Minimum TTL

@       IN  NS      ns1.your_domain.co.il.
ns1     IN  A       <YOUR_SERVER_IP>
```

Step 4: Set Permissions for Bind Updates
Ensure Bind has permissions to write to the zone file:
```bash
sudo chown bind:bind /etc/bind/db.connect.menorraitdev.net
sudo chmod 660 /etc/bind/db.connect.menorraitdev.net
```

Step 5: Start and Enable Bind9
Start and enable Bind9:
```bash
sudo systemctl start bind9
sudo systemctl enable bind9

```

## Running the CToDNS Tool
```bash
git clone https://github.com/ShudW/CToDNS.git
cd CToDNS
python3 CToDNS.py
```

## Usage Instructions
```bash
Enter command to execute: whoami
```


## DNS Configuration Validation
Test the Zone
Run the following command to ensure the zone is valid:
```bash
named-checkzone connect.menorraitdev.net /etc/bind/db.connect.menorraitdev.net
```

Test DNS Updates
Test dynamic updates using nsupdate:
```bash
nsupdate
> server 127.0.0.1
> update add test.connect.menorraitdev.net 60 TXT "hello world"
> send
```

Verify the record:
```bash
dig -t TXT test.connect.menorraitdev.net
```
