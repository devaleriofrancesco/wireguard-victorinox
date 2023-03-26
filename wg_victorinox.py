# This is the Wireguard WG swiss army knife.
# You can add, remove, list wireguard clients and send configuration via email, or show QR code in terminal.

import argparse
import json
import smtplib
import subprocess
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import qrcode


def add_peer(ip_address, private_key_file, wg_interface, pubkey=None, output_dir=None, email=None):
    if not pubkey:
        # If no public key is provided, generate a new key pair
        privkey = subprocess.check_output(["wg", "genkey"]).decode().strip()
        pubkey = subprocess.check_output(["wg", "pubkey"], input=privkey.encode()).decode().strip()
        # Write the private key to a file
        with open(private_key_file, "w") as f:
            f.write(privkey)
    else:
        # If a public key is provided, read the private key from a file
        with open(private_key_file, "r") as f:
            privkey = f.read().strip()

    # Construct the command to add a new peer
    cmd = f"sudo wg set {wg_interface} peer {pubkey} allowed-ips {ip_address}/24"
    cmd += f" --private-key {private_key_file}"
    # Run the command using subprocess
    subprocess.run(cmd.split(), check=True)

    if email:
        # Export client configuration via email
        qr_data = f"interface {wg_interface}\n"
        qr_data += f"private_key {privkey}\n"
        qr_data += f"peer {pubkey}\n"
        qr_data += f"allowed_ips {ip_address}/32\n"
        qr_data += f"endpoint <server_ip_address>:51820\n"  # Modify this line to include the actual server IP address and port number
        # Construct the email message
        msg = MIMEMultipart()
        msg["Subject"] = "WireGuard client configuration"
        msg["From"] = "your_email@example.com"  # Modify this line to include your own email address
        msg["To"] = email
        msg_text = MIMEText(qr_data)
        msg.attach(msg_text)
        # Save the QR code to a file and attach it to the email message
        img = qrcode.make(qr_data)
        if output_dir:
            filename = f"{output_dir}/wg_client_{pubkey[:8]}.png"
        else:
            filename = f"wg_client_{pubkey[:8]}.png"
        img.save(filename)
        with open(filename, "rb") as f:
            msg_image = MIMEImage(f.read())
        msg.attach(msg_image)
        # Send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login("your_email@example.com",
                       "your_email_password")  # Modify these lines to include your own email address and password
            smtp.sendmail("your_email@example.com", email, msg.as_string())
    else:
        # Generate QR code containing client configuration
        qr_data = f"interface {wg_interface}\n"
        qr_data += f"private_key {privkey}\n"
        qr_data += f"peer {pubkey}\n"
        qr_data += f"allowed_ips {ip_address}/32\n"
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")


def remove_peer(pubkey, wg_interface):
    # Construct the command to remove a peer
    cmd = f"sudo wg set {wg_interface} peer {pubkey} remove"
    # Run the command using subprocess
    subprocess.run(cmd.split(), check=True)


def list_peers(wg_interface):
    # Construct the command to list the current peers
    cmd = f"sudo wg show {wg_interface} peers"
    # Run the command using subprocess and capture the output
    output = subprocess.check_output(cmd.split()).decode()
    # Parse the output and extract the public keys
    pubkeys = [line.split("\t")[1] for line in output.strip().split("\n")]
    # Return the list of public keys
    return pubkeys


def save_peers(wg_interface, filename):
    # Get the current peer list
    peer_list = list_peers(wg_interface)
    # Save the peer list to a JSON file
    with open(filename, "w") as f:
        json.dump(peer_list, f)


def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Manage WireGuard peers")
    # Add subparsers for each command
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add the "add" command
    add_parser = subparsers.add_parser("add", help="Add a new peer")
    add_parser.add_argument("pubkey", help="The public key of the new peer")
    add_parser.add_argument("ip_address", help="The IP address of the new peer")
    add_parser.add_argument("private_key_file", help="The path to the private key file")
    add_parser.add_argument("wg_interface", help="The name of the WireGuard interface")

    # Add the "remove" command
    remove_parser = subparsers.add_parser("remove", help="Remove an existing peer")
    remove_parser.add_argument("pubkey", help="The public key of the peer to remove")
    remove_parser.add_argument("wg_interface", help="The name of the WireGuard interface")

    # Add the "list" command
    list_parser = subparsers.add_parser("list", help="List the current peers")
    list_parser.add_argument("wg_interface", help="The name of the WireGuard interface")

    # Add the "save" command
    save_parser = subparsers.add_parser("save", help="Save the current peers to a file")
    save_parser.add_argument("wg_interface", help="The name of the WireGuard interface")
    save_parser.add_argument("filename", help="The name of the file to save the peer list to")

    # Parse the arguments
    args = parser.parse_args()

    # Dispatch to the appropriate function based on the command
    if args.command == "add":
        add_peer(args.pubkey, args.ip_address, args.private_key_file, args.wg_interface)
    elif args.command == "remove":
        remove_peer(args.pubkey, args.wg_interface)
    elif args.command == "list":
        peer_list = list


if __name__ == '__main__':
    main()
