"""Bounded read-only route audit plus one 1-MiB upload/download round trip."""
import hashlib
import json
import os
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLI = r"G:\vpn\EasyTier\bin\easytier-cli.exe"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
       "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=15",
       "-o", "ServerAliveCountMax=2"]
REMOTE = "/home/inspur/aic_video_work/network_verification/easytier_20261013_v1"


def run(args, timeout=60):
    result = subprocess.run(args, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"Command failed ({result.returncode}): " + result.stderr.decode(errors="replace")[:1000])
    return result.stdout.decode(encoding="utf-8", errors="replace")


def peers(port):
    values = json.loads(run([CLI, "-p", f"127.0.0.1:{port}", "-v", "-o", "json", "peer"]))
    clean = []
    for value in values:
        route = value["route"]
        clean.append({"hostname": route["hostname"], "peer_id": route["peer_id"],
                      "next_hop_peer_id": route["next_hop_peer_id"], "cost": route["cost"],
                      "connections": [{"id": c["conn_id"], "type": c["tunnel"]["tunnel_type"],
                                       "local": c["tunnel"].get("local_addr"),
                                       "remote": c["tunnel"].get("remote_addr"),
                                       "stats": c["stats"], "closed": c["is_closed"]}
                                      for c in value["peer"]["conns"]]})
    return clean


def tailscale_counters():
    data = json.loads(run([r"C:\Program Files\Tailscale\tailscale.exe", "status", "--json"]))
    return [{key: peer.get(key) for key in ("HostName", "CurAddr", "Relay", "TxBytes", "RxBytes")}
            for peer in data.get("Peer", {}).values()
            if "100.127.244.47" in peer.get("TailscaleIPs", [])]


def main():
    receipt = ROOT / "verification.json"
    if receipt.exists() or (ROOT / "probe.bin").exists():
        raise RuntimeError("Existing probe/receipt: inspect it, do not repeat file transfer")
    record = {"started_utc": datetime.now(timezone.utc).isoformat(), "payload_bytes_each_direction": 1048576,
              "permanent_configuration_changed": False, "service_restart_or_fault_injection": False}
    diagnostic = None
    try:
        with socket.socket() as available:
            available.bind(("127.0.0.1", 0))
            rpc_port = available.getsockname()[1]
        diagnostic = subprocess.Popen(SSH + ["-N", "-o", "ExitOnForwardFailure=yes", "-L",
                                              f"127.0.0.1:{rpc_port}:127.0.0.1:15889", "aic-inspur-home"],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                      creationflags=subprocess.CREATE_NO_WINDOW)
        ready = False
        for _ in range(60):
            if diagnostic.poll() is not None:
                raise RuntimeError("Diagnostic SSH forwarding exited before verification")
            with socket.socket() as check:
                check.settimeout(0.2)
                if check.connect_ex(("127.0.0.1", rpc_port)) == 0:
                    ready = True
                    break
            time.sleep(0.2)
        if not ready:
            raise RuntimeError("Diagnostic RPC forwarding did not become ready")
        record["before"] = {"windows": peers(15889), "linux": peers(rpc_port),
                            "bootstrap": peers(15891), "tailscale": tailscale_counters()}
        for side, target in (("windows", "linux-direct-test"), ("linux", "win-direct-test")):
            peer = next(p for p in record["before"][side] if p["hostname"] == target)
            if peer["cost"] != 1 or peer["next_hop_peer_id"] != peer["peer_id"] or not any(
                c["type"] == "udp" and not c["closed"] for c in peer["connections"]):
                raise RuntimeError(f"{side} does not currently show a direct UDP peer")
        local = ROOT / "probe.bin"
        local.write_bytes(os.urandom(1048576))
        expected_sha = hashlib.sha256(local.read_bytes()).hexdigest()
        run(SSH + ["aic-inspur-home", f"mkdir -p {REMOTE}; test ! -e {REMOTE}/probe.bin"], timeout=30)
        scp = ["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "ConnectTimeout=15", "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=2"]
        start = time.monotonic()
        run(scp + [str(local), f"aic-inspur-home:{REMOTE}/probe.bin"], timeout=60)
        record["upload_seconds"] = time.monotonic() - start
        remote_sha = run(SSH + ["aic-inspur-home", f"sha256sum {REMOTE}/probe.bin"], timeout=30).split()[0]
        downloaded = ROOT / "probe_roundtrip.bin"
        start = time.monotonic()
        run(scp + [f"aic-inspur-home:{REMOTE}/probe.bin", str(downloaded)], timeout=60)
        record["download_seconds"] = time.monotonic() - start
        actual_sha = hashlib.sha256(downloaded.read_bytes()).hexdigest()
        record["transfer"] = {"local_sha256": expected_sha, "linux_sha256": remote_sha,
                              "download_sha256": actual_sha, "download_bytes": downloaded.stat().st_size,
                              "all_equal": expected_sha == remote_sha == actual_sha}
        if not record["transfer"]["all_equal"] or downloaded.stat().st_size != 1048576:
            raise RuntimeError("Round-trip byte/SHA mismatch")
        record["after"] = {"windows": peers(15889), "linux": peers(rpc_port),
                           "bootstrap": peers(15891), "tailscale": tailscale_counters()}
        record["status"] = "PASS_ONE_ROUNDTRIP_SHA_AND_BOTH_ENDS_DIRECT_UDP_SNAPSHOTS"
        record["reboot_or_network_change_recovery_tested"] = False
        record["airport_billing_meter_obtained"] = False
    except Exception as exc:
        record["status"] = "FAILED"
        record["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if diagnostic is not None and diagnostic.poll() is None:
            diagnostic.terminate()
            diagnostic.wait(timeout=5)
        record["finished_utc"] = datetime.now(timezone.utc).isoformat()
        receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: record[key] for key in ("status", "payload_bytes_each_direction", "upload_seconds", "download_seconds", "transfer")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
