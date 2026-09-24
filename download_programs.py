"""Download and install official Windows programs.

The installers are saved in a ``downloads`` folder next to this script and
then run with unattended-install options. Windows may ask for permission.
"""

from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DOWNLOADS = {
    "DiscordSetup.exe": "https://discord.com/api/download?platform=win",
    "FirefoxSetup.exe": (
        "https://download.mozilla.org/?product=firefox-latest-ssl"
        "&os=win64&lang=en-US"
    ),
    "VSCodeUserSetup-x64.exe": (
        "https://code.visualstudio.com/sha/download"
        "?build=stable&os=win32-x64-user"
    ),
    "MedalSetup.exe": "https://install.medal.tv/MedalSetup.exe",
    "VencordInstaller.exe": (
        "https://github.com/Vencord/Installer/releases/latest/download/"
        "VencordInstaller.exe"
    ),
}

INSTALL_ARGUMENTS = {
    "DiscordSetup.exe": ("--silent",),
    "FirefoxSetup.exe": ("-ms",),
    "VSCodeUserSetup-x64.exe": ("/VERYSILENT", "/MERGETASKS=!runcode"),
    "MedalSetup.exe": (),
}
DOWNLOAD_ONLY = {"VencordInstaller.exe"}


def download_file(url: str, destination: Path) -> None:
    """Download a URL to destination while displaying progress."""
    request = Request(url, headers={"User-Agent": "Windows-program-downloader/1.0"})

    with urlopen(request, timeout=60) as response:
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0

        with destination.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                downloaded += len(chunk)

                if total:
                    percent = downloaded * 100 // total
                    print(
                        f"\r    {downloaded / 1048576:.1f}/"
                        f"{total / 1048576:.1f} MB ({percent}%)",
                        end="",
                        flush=True,
                    )
                else:
                    print(
                        f"\r    {downloaded / 1048576:.1f} MB",
                        end="",
                        flush=True,
                    )

    print()


def install_file(installer: Path, arguments: tuple[str, ...]) -> None:
    """Run an installer and raise an error if it does not complete successfully."""
    print(f"Installing {installer.name}...")
    result = subprocess.run(
        (str(installer), *arguments),
        check=False,
        shell=False,
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, installer)
    print(f"    Installed {installer.name}")


def show_vencord_prompt(installer: Path) -> None:
    """Show a prompt that opens Vencord only when the user clicks its button."""
    window = tk.Tk()
    window.title("Installation complete")
    window.resizable(False, False)
    window.attributes("-topmost", True)

    message = tk.Label(
        window,
        text=(
            "All main softwares have been downloaded.\n"
            "Press the button below to open the Vencord installer."
        ),
        padx=30,
        pady=20,
    )
    message.pack()

    def open_vencord() -> None:
        try:
            subprocess.Popen((str(installer),), shell=False)
        except OSError as error:
            messagebox.showerror("Unable to open Vencord", str(error), parent=window)
            return
        window.destroy()

    button = tk.Button(
        window,
        text="Open Vencord installer",
        command=open_vencord,
        padx=12,
        pady=6,
    )
    button.pack(pady=(0, 20))
    window.mainloop()


def main() -> int:
    if sys.platform != "win32":
        print("This script must be run on Windows because it launches .exe installers.")
        return 1

    output_dir = Path(__file__).resolve().parent / "downloads"
    output_dir.mkdir(exist_ok=True)

    print(f"Saving installers to: {output_dir}")

    failed = False
    downloaded_installers: list[tuple[Path, tuple[str, ...]]] = []
    for filename, url in DOWNLOADS.items():
        destination = output_dir / filename
        print(f"\nDownloading {filename}...")

        try:
            download_file(url, destination)
            print(f"    Saved: {destination}")
            if filename not in DOWNLOAD_ONLY:
                downloaded_installers.append((destination, INSTALL_ARGUMENTS[filename]))
            else:
                print(f"    {filename} was downloaded only; it will not be run.")
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            failed = True
            destination.unlink(missing_ok=True)
            print(f"    Failed: {error}")

    if failed:
        print("\nSome downloads failed. Check your connection and try again.")
        return 1

    print("\nAll installers downloaded successfully. Starting installation...")
    for installer, arguments in downloaded_installers:
        try:
            install_file(installer, arguments)
        except (OSError, subprocess.CalledProcessError) as error:
            failed = True
            print(f"    Installation failed for {installer.name}: {error}")

    if failed:
        print("\nSome installations failed. You can retry them from the downloads folder.")
        return 1

    print("\nAll programs were installed successfully.")
    show_vencord_prompt(output_dir / "VencordInstaller.exe")
    print("Restarting Windows in 30 seconds. Use 'shutdown /a' to cancel.")
    subprocess.run(
        (
            "shutdown",
            "/r",
            "/t",
            "30",
            "/c",
            "Program installation completed",
        ),
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
