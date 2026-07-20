"""Standalone Oracle Kerberos external-auth login for the Spider/PSGMGR schema."""

from .spider_login import connect, explain, load_config, preflight, verify

__all__ = ["connect", "explain", "load_config", "preflight", "verify"]
