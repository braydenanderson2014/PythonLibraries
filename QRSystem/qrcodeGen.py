import os
import sys
import qrcode


def make_url_qr(url: str, filename: str = "qr_url.png") -> str:
    img = qrcode.make(url)
    img.save(filename)
    return os.path.abspath(filename)


def make_wifi_qr(
    ssid: str,
    password: str,
    auth_type: str = "WPA",
    hidden: bool = False,
    filename: str = "qr_wifi.png",
) -> str:
    """
    Generate a Wi-Fi QR code.

    auth_type: "WPA", "WEP", or "nopass"
    hidden: True if SSID is hidden
    """
    # Build Wi-Fi QR payload
    # Note: double semicolon at the end is intentional and part of the spec.
    wifi_str = f"WIFI:T:{auth_type};S:{ssid};P:{password};"
    if hidden:
        wifi_str += "H:true;"
    wifi_str += ";"  # closing semicolon

    img = qrcode.make(wifi_str)
    img.save(filename)
    return os.path.abspath(filename)


def ask(prompt: str) -> str:
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print("\nCanceled.")
        sys.exit(0)


def main():
    print("=== Local QR Generator (no server, no account) ===")
    print("1) URL QR code")
    print("2) Wi-Fi QR code")
    choice = ask("Choose an option (1 or 2): ").strip()

    if choice == "1":
        url = ask("Enter the URL (e.g. https://example.com): ").strip()
        if not url:
            print("No URL provided. Exiting.")
            return
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        outfile = ask("Output filename [qr_url.png]: ").strip() or "qr_url.png"
        path = make_url_qr(url, outfile)
        print(f"\n✅ URL QR code generated: {path}")

    elif choice == "2":
        ssid = ask("Wi-Fi SSID (network name): ").strip()
        if not ssid:
            print("No SSID provided. Exiting.")
            return

        password = ask("Wi-Fi password (leave blank only for open networks): ")

        if password:
            auth_type = ask("Auth type [WPA/WEP] (default WPA): ").strip().upper() or "WPA"
        else:
            auth_type = "nopass"

        hidden_in = ask("Is the SSID hidden? [y/N]: ").strip().lower()
        hidden = hidden_in == "y"

        outfile = ask("Output filename [qr_wifi.png]: ").strip() or "qr_wifi.png"
        path = make_wifi_qr(ssid, password, auth_type, hidden, outfile)
        print(f"\n✅ Wi-Fi QR code generated: {path}")

    else:
        print("Invalid choice. Exiting.")
        return

    print("\nYou can now open/print that PNG and scan it with your phone.")
    print("Done. Program will now exit.")


if __name__ == "__main__":
    main()
