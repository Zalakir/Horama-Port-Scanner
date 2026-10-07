# Horama Port Scanner

Horama is a lightweight Python tool for checking which TCP ports are open on a
host. Its desktop interface lets you enter a hostname or IPv4 address, choose a
port range and worker count, monitor scan progress, and cancel a scan.

## Run

On Windows, double-click `Launch Horama Port Scanner.bat`.

Alternatively, launch it from a terminal:

```text
python HoramaPortScanner_v0.2.py
```

The application uses Python's built-in Tkinter library. The default scan checks
ports 1 through 65,535; use a smaller range for a quicker scan. Only scan hosts
you own or have permission to test.
