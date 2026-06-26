#!/usr/bin/env python3
"""
Aura Neo4j instance manager for DryDocs.

Usage:
    python scripts/aura_manage.py list
    python scripts/aura_manage.py status <instance_id>
    python scripts/aura_manage.py create --name <name> --type free-db --cloud gcp --region us-east1
    python scripts/aura_manage.py pause <instance_id>
    python scripts/aura_manage.py resume <instance_id>
    python scripts/aura_manage.py delete <instance_id> [--yes]

Credentials are read from AURA_CLIENT_ID and AURA_CLIENT_SECRET environment variables
(or from .env in the project root).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Load .env from project root before anything else
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

import requests


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class AuraClient:
    BASE = "https://api.neo4j.io"

    def __init__(self, client_id: str, client_secret: str, session: requests.Session | None = None):
        self._id = client_id
        self._secret = client_secret
        self._session = session or requests.Session()
        self._token: str | None = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _get_token(self) -> str:
        r = self._session.post(
            f"{self.BASE}/oauth/token",
            auth=(self._id, self._secret),
            data={"grant_type": "client_credentials"},
        )
        r.raise_for_status()
        return r.json()["access_token"]

    def _headers(self) -> dict[str, str]:
        if not self._token:
            self._token = self._get_token()
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    # ------------------------------------------------------------------
    # Instances
    # ------------------------------------------------------------------

    def list_instances(self) -> list[dict]:
        r = self._session.get(f"{self.BASE}/v1/instances", headers=self._headers())
        r.raise_for_status()
        return r.json().get("data", [])

    def get_instance(self, instance_id: str) -> dict:
        r = self._session.get(f"{self.BASE}/v1/instances/{instance_id}", headers=self._headers())
        r.raise_for_status()
        return r.json()["data"]

    def create_instance(
        self,
        *,
        name: str,
        type_: str,
        cloud: str,
        region: str,
        tenant_id: str | None = None,
        memory: str | None = None,
    ) -> dict:
        payload: dict = {
            "name": name,
            "type": type_,
            "cloud_provider": cloud,
            "region": region,
            "version": "5",
        }
        if tenant_id:
            payload["tenant_id"] = tenant_id
        if memory:
            payload["memory"] = memory

        r = self._session.post(f"{self.BASE}/v1/instances", headers=self._headers(), json=payload)
        r.raise_for_status()
        return r.json()["data"]

    def pause_instance(self, instance_id: str) -> dict:
        r = self._session.post(
            f"{self.BASE}/v1/instances/{instance_id}/pause", headers=self._headers()
        )
        r.raise_for_status()
        return r.json().get("data", {})

    def resume_instance(self, instance_id: str) -> dict:
        r = self._session.post(
            f"{self.BASE}/v1/instances/{instance_id}/resume", headers=self._headers()
        )
        r.raise_for_status()
        return r.json().get("data", {})

    def delete_instance(self, instance_id: str) -> None:
        r = self._session.delete(
            f"{self.BASE}/v1/instances/{instance_id}", headers=self._headers()
        )
        r.raise_for_status()

    def poll_status(
        self,
        instance_id: str,
        target: str,
        timeout: int = 600,
        interval: int = 10,
    ) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            instance = self.get_instance(instance_id)
            status = instance.get("status", "unknown")
            print(f"  status={status}", flush=True)
            if status == target:
                return
            if status == "destroying":
                raise RuntimeError(f"Instance {instance_id} is being destroyed unexpectedly")
            time.sleep(interval)
        raise TimeoutError(
            f"Instance {instance_id} did not reach '{target}' within {timeout}s"
        )


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _print_instances(instances: list[dict], as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(instances, indent=2))
        return
    if not instances:
        print("No instances found.")
        return
    cols = ["id", "name", "status", "type", "region", "cloud_provider"]
    widths = {c: max(len(c), max((len(str(i.get(c, ""))) for i in instances), default=0)) for c in cols}
    header = "  ".join(c.upper().ljust(widths[c]) for c in cols)
    print(header)
    print("-" * len(header))
    for inst in instances:
        print("  ".join(str(inst.get(c, "")).ljust(widths[c]) for c in cols))


def _print_instance(inst: dict, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(inst, indent=2))
        return
    for k, v in inst.items():
        print(f"  {k:<20} {v}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aura Neo4j instance manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # list
    sub.add_parser("list", help="List all instances")

    # status
    p = sub.add_parser("status", help="Show instance status and details")
    p.add_argument("instance_id")

    # create
    p = sub.add_parser("create", help="Create a new Aura instance")
    p.add_argument("--name", required=True, help="Instance name")
    p.add_argument(
        "--type",
        dest="type_",
        default="free-db",
        choices=["free-db", "professional-db", "business-critical", "enterprise-db",
                 "professional-ds", "enterprise-ds"],
        help="Instance tier (default: free-db)",
    )
    p.add_argument("--cloud", default="gcp", choices=["gcp", "aws", "azure"])
    p.add_argument("--region", default="us-east1", help="Cloud region (default: us-east1)")
    p.add_argument("--tenant-id", help="Aura tenant/project ID (required for paid tiers)")
    p.add_argument("--memory", help="Memory size e.g. 4GB (Professional+ only)")
    p.add_argument("--no-wait", action="store_true", help="Return immediately without polling")

    # pause
    p = sub.add_parser("pause", help="Pause a running instance")
    p.add_argument("instance_id")

    # resume
    p = sub.add_parser("resume", help="Resume a paused instance")
    p.add_argument("instance_id")

    # delete
    p = sub.add_parser("delete", help="Delete an instance (IRREVERSIBLE)")
    p.add_argument("instance_id")
    p.add_argument("--yes", action="store_true", help="Skip confirmation prompt")

    return parser


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"ERROR: {name} environment variable is not set.", file=sys.stderr)
        print("       Set it in .env or export it before running this script.", file=sys.stderr)
        sys.exit(1)
    return value


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    client_id = _require_env("AURA_CLIENT_ID")
    client_secret = _require_env("AURA_CLIENT_SECRET")
    client = AuraClient(client_id, client_secret)
    as_json = args.json

    if args.command == "list":
        instances = client.list_instances()
        _print_instances(instances, as_json)

    elif args.command == "status":
        inst = client.get_instance(args.instance_id)
        _print_instance(inst, as_json)

    elif args.command == "create":
        print(f"Creating instance '{args.name}' (type={args.type_}, {args.cloud}/{args.region})...")
        data = client.create_instance(
            name=args.name,
            type_=args.type_,
            cloud=args.cloud,
            region=args.region,
            tenant_id=args.tenant_id,
            memory=args.memory,
        )
        print(f"\nInstance created: {data.get('id')}")
        print(f"  Connection URI : neo4j+s://{data.get('id')}.databases.neo4j.io")
        print(f"  Username       : neo4j")
        print(f"  Password       : {data.get('password')}  <-- SAVE THIS NOW (shown once)")
        if not args.no_wait:
            print("\nPolling until running...")
            client.poll_status(data["id"], "running")
            print("Instance is running.")
        if as_json:
            print(json.dumps(data, indent=2))

    elif args.command == "pause":
        print(f"Pausing {args.instance_id}...")
        client.pause_instance(args.instance_id)
        print("Polling until paused...")
        client.poll_status(args.instance_id, "paused")
        print("Instance paused.")

    elif args.command == "resume":
        print(f"Resuming {args.instance_id}...")
        client.resume_instance(args.instance_id)
        print("Polling until running...")
        client.poll_status(args.instance_id, "running")
        print("Instance running.")

    elif args.command == "delete":
        if not args.yes:
            confirm = input(
                f"Delete instance {args.instance_id}? This is IRREVERSIBLE. Type 'yes' to confirm: "
            )
            if confirm.strip().lower() != "yes":
                print("Cancelled.")
                sys.exit(0)
        print(f"Deleting {args.instance_id}...")
        client.delete_instance(args.instance_id)
        print("Instance deleted.")


if __name__ == "__main__":
    main()
