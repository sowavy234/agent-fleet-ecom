import socket
import ssl
from datetime import datetime
from typing import Dict, Any

try:
    import whois
except Exception:
    whois = None


def get_ssl_info(hostname: str, port: int = 443, timeout: float = 5.0) -> Dict[str, Any]:
    out = {"valid": False, "notBefore": None, "notAfter": None, "issuer": None, "error": None}
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                not_before = cert.get("notBefore")
                not_after = cert.get("notAfter")
                issuer = cert.get("issuer")
                if not_before:
                    out["notBefore"] = not_before
                if not_after:
                    out["notAfter"] = not_after
                out["issuer"] = issuer
                out["valid"] = True
    except Exception as e:
        out["error"] = str(e)
    return out


def get_whois(domain: str) -> Dict[str, Any]:
    out = {"available": None, "creation_date": None, "expiration_date": None, "registrar": None, "nameservers": None, "raw": None, "error": None}
    if whois is None:
        out["error"] = "whois package not installed"
        return out
    try:
        w = whois.whois(domain)
        out["raw"] = str(w)
        # whois lib sometimes returns lists
        cd = w.creation_date
        if isinstance(cd, (list, tuple)) and cd:
            cd = cd[0]
        ed = w.expiration_date
        if isinstance(ed, (list, tuple)) and ed:
            ed = ed[0]
        if isinstance(cd, datetime):
            out["creation_date"] = cd.isoformat()
        if isinstance(ed, datetime):
            out["expiration_date"] = ed.isoformat()
        out["registrar"] = getattr(w, "registrar", None)
        out["nameservers"] = getattr(w, "name_servers", None)
    except Exception as e:
        out["error"] = str(e)
    return out
