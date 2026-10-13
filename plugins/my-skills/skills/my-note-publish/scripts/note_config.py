"""Local note publisher configuration; secrets never enter CLI arguments."""

import base64
import ctypes
import getpass
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


class ConfigError(Exception):
    pass


def config_path():
    custom = os.environ.get("BLOG_NOTE_CONFIG")
    return Path(custom).expanduser() if custom else Path.home() / ".config/my-note-publish/config.json"


def normalize_origin(value):
    if not isinstance(value, str):
        raise ConfigError("Blog address must be text")
    value = value.strip().rstrip("/")
    if "://" not in value:
        value = "https://" + value
    parts = urlsplit(value)
    if (not parts.hostname or parts.username is not None or parts.password is not None
            or parts.query or parts.fragment or parts.path or any(c.isspace() for c in value)
            or (parts.scheme != "https" and not (parts.scheme == "http" and parts.hostname in {"localhost", "127.0.0.1", "::1"}))):
        raise ConfigError("Blog address must be an HTTPS origin (HTTP allowed only on localhost)")
    parts.port
    return value


def protect_secret(value, decrypt=False):
    """Use Windows DPAPI, scoped to the current user, without external packages."""
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = ctypes.create_string_buffer(value)
    source = Blob(len(value), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    operation = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    operation.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                          ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    operation.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not operation(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise ConfigError("Cannot encrypt/decrypt local credentials for this Windows user")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(ctypes.cast(target.data, ctypes.c_void_p))


def read_config():
    path = config_path()
    if not path.exists():
        return {}
    try:
        if os.name != "nt" and path.stat().st_mode & 0o077:
            raise ConfigError("Local credential file must have permissions 0600")
        record = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or record.get("version") != 1:
            raise ConfigError("Unsupported local config; run setup again")
        secret = record.get("password", "")
        if record.get("protection") == "windows-dpapi":
            if os.name != "nt":
                raise ConfigError("Windows credentials cannot be read on this platform")
            secret = protect_secret(base64.b64decode(secret, validate=True), decrypt=True).decode("utf-8")
        elif record.get("protection") != "file-0600":
            raise ConfigError("Unsupported credential storage; run setup again")
        return {"base_url": normalize_origin(record.get("base_url")), "password": secret}
    except (OSError, ValueError, TypeError):
        raise ConfigError("Cannot read local configuration; run setup again") from None


def resolve_config():
    base = os.environ.get("BLOG_BASE_URL", "")
    password = os.environ.get("BLOG_ADMIN_PASSWORD", "")
    # Fully configured environment must not depend on an obsolete local file.
    local = read_config() if not base or not password else {}
    base = base or local.get("base_url", "")
    password = password or local.get("password", "")
    missing = [name for name, value in [("blog_domain", base), ("blog_password", password)] if not value]
    if missing:
        return None, None, missing
    if not isinstance(password, str) or "\r" in password or "\n" in password:
        raise ConfigError("Invalid blog password; run setup again")
    return normalize_origin(base), password, []


def save_config(base, password):
    base = normalize_origin(base)
    if not isinstance(password, str) or not password or "\r" in password or "\n" in password:
        raise ConfigError("Blog password is required")
    record = {"version": 1, "base_url": base}
    if os.name == "nt":
        record.update(protection="windows-dpapi", password=base64.b64encode(protect_secret(password.encode("utf-8"))).decode("ascii"))
    else:
        record.update(protection="file-0600", password=password)
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".note-config-", dir=path.parent)
    try:
        if os.name != "nt":
            os.chmod(temporary, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            json.dump(record, target, ensure_ascii=False, indent=2)
            target.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"status": "configured", "baseUrl": base, "configFile": str(path), "protection": record["protection"]}


def gui_credentials(base):
    if os.name != "nt":
        raise ConfigError("--gui is available only on Windows; run setup in a terminal")
    # The subprocess output stays in memory; only non-secret setup status is printed.
    script = r'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$form = New-Object System.Windows.Forms.Form
$form.Text = 'Blog configuration'
$form.Size = New-Object System.Drawing.Size(480,220)
$form.StartPosition = 'CenterScreen'
$form.TopMost = $true
$domainLabel = New-Object System.Windows.Forms.Label
$domainLabel.Text = 'Blog domain / URL'
$domainLabel.Location = New-Object System.Drawing.Point(20,20)
$domainLabel.AutoSize = $true
$domain = New-Object System.Windows.Forms.TextBox
$domain.Location = New-Object System.Drawing.Point(20,45)
$domain.Size = New-Object System.Drawing.Size(420,25)
$domain.Text = $env:NOTE_SETUP_BASE
$passwordLabel = New-Object System.Windows.Forms.Label
$passwordLabel.Text = 'Blog ADMIN_PASSWORD'
$passwordLabel.Location = New-Object System.Drawing.Point(20,80)
$passwordLabel.AutoSize = $true
$password = New-Object System.Windows.Forms.TextBox
$password.Location = New-Object System.Drawing.Point(20,105)
$password.Size = New-Object System.Drawing.Size(420,25)
$password.UseSystemPasswordChar = $true
$ok = New-Object System.Windows.Forms.Button
$ok.Text = 'Save'
$ok.Location = New-Object System.Drawing.Point(280,145)
$ok.DialogResult = [System.Windows.Forms.DialogResult]::OK
$cancel = New-Object System.Windows.Forms.Button
$cancel.Text = 'Cancel'
$cancel.Location = New-Object System.Drawing.Point(365,145)
$cancel.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.Controls.AddRange(@($domainLabel,$domain,$passwordLabel,$password,$ok,$cancel))
$form.AcceptButton = $ok
$form.CancelButton = $cancel
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
if ($form.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
  @{base_url=$domain.Text;password=$password.Text} | ConvertTo-Json -Compress
} else { exit 2 }
'''
    done = subprocess.run(["powershell.exe", "-NoProfile", "-STA", "-Command", script],
                          capture_output=True, text=True, encoding="utf-8",
                          env={**os.environ, "NOTE_SETUP_BASE": base})
    if done.returncode == 2:
        raise ConfigError("Setup cancelled; nothing saved")
    if done.returncode:
        raise ConfigError("Cannot open Windows setup dialog; run setup in a terminal")
    value = json.loads(done.stdout)
    return value["base_url"], value["password"]


def setup(gui=False):
    try:
        local = read_config()
    except ConfigError:
        local = {}
    base = os.environ.get("BLOG_BASE_URL") or local.get("base_url", "")
    if gui:
        base, password = gui_credentials(base)
    else:
        if not sys.stdin.isatty():
            raise ConfigError("Setup needs an interactive terminal; on Windows use setup --gui")
        base = input(f"博客域名 [{base}]: ").strip() or base
        password = getpass.getpass("博客 ADMIN_PASSWORD（隐藏输入）: ")
    return save_config(base, password)
