# Horama Port Scanner

Horama is a lightweight Python tool for checking which TCP ports are open on a
host. It has a desktop interface (version 1.0) built with Tkinter.

## Features

- Scan a hostname or IPv4 address using a single writable port field: a range
  (`1-65535`, the default), specific ports (`22,80,443`), or a mix (`20-25,80`).
- Multithreaded scanning with up to 2,000 simultaneous workers (fixed).
- Live progress bar and list of open ports, with the option to cancel a scan.
- Export open ports to a CSV file (`host`, `ip_address`, `port`, `state`).
- Customizable dark theme through `theme.yaml`.
- Horama window and taskbar icon (`Ico/Horama.ico`).

## Requirements

- Python 3 with Tkinter (included with the standard Windows installer).
- [PyYAML](https://pypi.org/project/PyYAML/) for loading the theme. The app
  falls back to its default theme if PyYAML or `theme.yaml` is missing.

```text
pip install -r requirements.txt
```

## Run

On Windows, double-click `Launch Horama Port Scanner.bat`.

Alternatively, launch it from a terminal:

```text
python HoramaPortScanner_v1.0.py
```

## Usage

1. Enter the host or IPv4 address to scan.
2. Type the ports to scan: `1-65535` (default), a range like `20-80`, or
   specific ports like `22,80,443`.
3. Click **Start scan**. Open ports appear in the results as they are found.
4. Click **Cancel** to stop early, or **Export CSV** to save the open ports.
   **Export CSV** is enabled once a scan has found at least one open port.

The default scan checks ports 1 through 65,535; use a smaller range or a few
specific ports for a quicker scan. The scan uses many simultaneous workers, so
it can use substantial system resources.

## Customize the theme

Edit `theme.yaml` to change colors and fonts, then restart the app. Any value
you remove falls back to its default.

## Disclaimer

Only scan hosts you own or have permission to test.
