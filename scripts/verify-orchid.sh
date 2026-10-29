#!/bin/sh
cd "$(dirname "$0")/.."
exec python scripts/verify_orchid.py
