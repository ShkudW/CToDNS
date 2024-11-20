
# CToDNS - Command and Control Server Over DNS

CToDNS (Client To DNS) is a Command and Control (C2) server that communicates with remote beacons over DNS, leveraging DNS TXT records for command transmission and DNS CNAME queries for response delivery.

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
3. **DNS Server**
A Bind9 DNS server configured to handle dynamic updates for the communication domain.


## Setting Up the DNS Server

Step 1: Set up a server with an external address, preferably with a Debian Linux operating system
        I really like DigitalOcean
        https://cloud.digitalocean.com/

Step 2: Buy a domain name.
        For the demonstration, I purchased the domain name - mydomain.net

Step 3: Configure your DNS server in Digitalocean.

         NS        mydomain.net                  ns1.digitalocean.com.           -> NS Record for my Domain Name.
         A         mydomain.net                  X.X.X.X (IPv4)                  -> A Record for my Domain Name.

         A         ns1.connect.mydomain.net      X.X.X.X (IPv4)                  -> A Record for my DNS Domain name.
         NS        connect.mydomain.net          ns1.connect.mydomain.net   -> NS Record for my DNS Domain Name.

Step 4: Install Bind9
 ```bash
sudo apt update
sudo apt install bind9 bind9utils
```

Step 5: Create the Zone File ->  /etc/bind/db.connect.mydomain.net

```bash
$ORIGIN .
$TTL 3600       ; 1 hour
connect.mydomain.net IN SOA ns1.connect.mydomain.net. admin.mydomain.net. (
                                2024111723 ; serial
                                1800       ; refresh (30 minutes)
                                1800       ; retry (30 minutes)
                                1209600    ; expire (2 weeks)
                                86400      ; minimum (1 day)
                                )
                        NS      ns1.connect.mydomain.net.
                        A       X.X.X.X - > your IP_Address
$ORIGIN connect.mydomain.net.
$TTL 60 ; 1 minute
command                 TXT     "default"
$TTL 3600       ; 1 hour
ns1                     A       X.X.X.X (You IPv4 //Remove this comment after configuration)
```

Step 6: Configure the Zone: edit the file ->  /etc/bind/named.conf.local
 ```bash
zone "connect.mydomain.net" {
    type master;
    file "/etc/bind/db.connect.mydomain.net";
    allow-update { localhost; };
};
```
Step 7: Configura /etc/bind/named.conf.options file:
 ```bash
logging {
    channel update_debug {
        file "/var/log/named.update.log" versions 3 size 5m;
        severity debug 3;
        print-time yes;
    };
};

options {
    // If there is a firewall between you and nameservers you want
    // to talk to, you may need to fix the firewall to allow multiple
    // ports to talk.  See http://www.kb.cert.org/vuls/id/800113

    // If your ISP provided one or more IP addresses for stable
    // nameservers, you probably want to use them as forwarders.
    // Uncomment the following block, and insert the addresses replacing
    // the all-0's placeholder.

    // forwarders {
    //      0.0.0.0;
    // };

    //========================================================================
    // If BIND logs error messages about the root key being expired,
    // you will need to update your keys.  See https://www.isc.org/bind-keys
    //========================================================================
    dnssec-validation yes;

    listen-on-v6 { any; };
};
```

Step 8: Set Permissions for Bind Updates
```bash
sudo chown bind:bind /etc/bind/db.connect.mydomain.net
sudo chmod 660 /etc/bind/db.connect.mydomain.net
```

Step 9: Set Permissions for Bind Folder
```bash
sudo chown -R bind:bind /etc/bind
sudo chmod 755 /etc/bind
```

Step 10: Canceling AppArmor's limitation on the named service
```bash
sudo ln -s /etc/apparmor.d/usr.sbin.named /etc/apparmor.d/disable/
sudo apparmor_parser -R /etc/apparmor.d/usr.sbin.named
```

Step 11: Checking the Zone (Need to Get 'OK')
```bash
named-checkzone connect.mydomain.net /etc/bind/db.connect.mydomain.net
```

Step 12: Start and Enable Bind9
Start and enable Bind9:
```bash
sudo systemctl start bind9
sudo systemctl enable bind9

```

## Running the CToDNS Tool
```bash
python3 -m venv CToDNS
Source CToDNS/bin/active
git clone https://github.com/ShudW/CToDNS.git
cd CToDNS
pip install scapy termcolor
python3 CToDNS.py
```

## Usage Instructions
```bash
Enter command to execute: whoami
```

