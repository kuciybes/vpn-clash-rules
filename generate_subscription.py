#!/usr/bin/env python3
"""Convert Clash Meta config.yaml to base64 subscription for Streisand/V2Box/Shadowrocket."""

import yaml
import base64
import urllib.parse
import sys


def proxy_to_vless_uri(proxy: dict) -> str:
    """Convert a single Clash Meta proxy dict to a VLESS share link."""
    uuid = proxy["uuid"]
    server = proxy["server"]
    port = proxy["port"]
    name = proxy.get("name", "").strip().strip("'\"")

    params = {
        "encryption": "none",
        "type": proxy.get("network", "tcp"),
    }

    # Flow (XTLS)
    flow = proxy.get("flow")
    if flow:
        params["flow"] = flow

    # Packet encoding
    if proxy.get("packet-encoding"):
        params["packetEncoding"] = proxy["packet-encoding"]

    # Reality
    reality_opts = proxy.get("reality-opts")
    if reality_opts:
        params["security"] = "reality"
        params["sni"] = proxy.get("servername", server)
        params["fp"] = proxy.get("client-fingerprint", "chrome")
        params["pbk"] = reality_opts["public-key"]
        if reality_opts.get("short-id"):
            params["sid"] = reality_opts["short-id"]
    elif proxy.get("tls"):
        params["security"] = "tls"
        params["sni"] = proxy.get("servername", server)
        params["fp"] = proxy.get("client-fingerprint", "chrome")
        alpn = proxy.get("alpn")
        if alpn:
            params["alpn"] = ",".join(alpn)

    # WebSocket
    if proxy.get("network") == "ws":
        ws_opts = proxy.get("ws-opts", {})
        if ws_opts.get("path"):
            params["path"] = ws_opts["path"]
        headers = ws_opts.get("headers", {})
        if headers.get("Host"):
            params["host"] = headers["Host"]

    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    encoded_name = urllib.parse.quote(name)
    return f"vless://{uuid}@{server}:{port}?{query}#{encoded_name}"


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "subscription.txt"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    proxies = config.get("proxies", [])
    uris = []
    for proxy in proxies:
        if proxy.get("type") != "vless":
            continue
        uri = proxy_to_vless_uri(proxy)
        uris.append(uri)

    plain = "\n".join(uris)
    encoded = base64.b64encode(plain.encode("utf-8")).decode("utf-8")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(encoded)

    print(f"Generated {len(uris)} VLESS links -> {output_path}")


if __name__ == "__main__":
    main()
