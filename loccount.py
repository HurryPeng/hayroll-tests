#!/usr/bin/env python3
"""Generate cloc command to count lines of code for filtered CBench programs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def load_metadata(path: Path) -> dict:
    """Load the metadata JSON file."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_cloc_command(metadata: dict) -> list[str]:
    """Build cloc command with specific directories from metadata."""
    programs = metadata.get("programs", [])
    if not programs:
        raise ValueError("No programs found in metadata")
    
    # Build list of CBench subdirectories to include
    directories = []
    for program in programs:
        path = program.get("path")
        if path:
            directories.append(f"CBench/{path}")
            
    print(len(directories), "directories to analyze")
    
    if not directories:
        raise ValueError("No valid program paths found in metadata")
    
    # Build cloc command
    cmd = [
        "cloc",
        "--exclude-dir=build,c2rust_out,hayroll_out",
        "--include-ext=c,h",
    ] + directories
    
    return cmd


def main() -> int:
    """Main entry point."""
    metadata_path = Path("metadata-filtered.json")
    
    if not metadata_path.exists():
        print(f"Error: {metadata_path} not found", file=sys.stderr)
        return 1
    
    try:
        metadata = load_metadata(metadata_path)
        cmd = build_cloc_command(metadata)
        
        print("Running command:")
        print(" ".join(cmd))
        print()
        
        # Execute the cloc command
        result = subprocess.run(cmd, check=False)
        return result.returncode
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())