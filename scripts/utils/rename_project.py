#!/usr/bin/env python3
"""
Project Rename Script: transcribe_mcp → transcribe_mcp

This script systematically renames all occurrences of 'transcribe_mcp' to 'transcribe_mcp'
across the codebase, excluding certain directories and handling special cases.

BACKUP CREATED: backup-before-rename-20251001-054433
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Directories to exclude
EXCLUDE_DIRS = {
    'transcribe_mcp_env',
    'transcribe_mcp_env',
    '.git',
    'htmlcov',
    '.mypy_cache',
    '__pycache__',
    '.pytest_cache',
    'node_modules',
    '.venv',
    'venv',
    'tests/outputs',  # Test outputs - will be regenerated
}

# File patterns to process
INCLUDE_PATTERNS = {
    '*.py',
    '*.md',
    '*.toml',
    '*.cfg',
    '*.sh',
    '*.yaml',
    '*.yml',
    '*.json',
    '*.txt',
    '*.ini',
}

# Replacement mappings
REPLACEMENTS = [
    # Exact matches (case-sensitive)
    ('transcribe_mcp', 'transcribe_mcp'),
    ('TranscribeMCP', 'TranscribeMCP'),
    ('TRANSCRIBE_MCP', 'TRANSCRIBE_MCP'),

    # Command names
    ('transcribe_mcp-mcp', 'transcribe-mcp'),

    # URLs and domains
    ('transcribe_mcp.com', 'transcribe-mcp.com'),
    ('github.com/transcribe_mcp', 'github.com/karlsoro/transcribe_mcp'),

    # Environment variable prefixes
    ('TRANSCRIBE_MCP_', 'TRANSCRIBE_MCP_'),
]


def should_process_file(file_path: Path) -> bool:
    """Check if file should be processed."""
    # Check if in excluded directory
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in file_path.parts:
            return False

    # Check if matches include pattern
    for pattern in INCLUDE_PATTERNS:
        if file_path.match(pattern):
            return True

    return False


def find_files_to_process(root_dir: Path) -> List[Path]:
    """Find all files that need processing."""
    files = []

    for file_path in root_dir.rglob('*'):
        if file_path.is_file() and should_process_file(file_path):
            try:
                # Check if file contains 'transcribe_mcp' (case-insensitive)
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if 'transcribe_mcp' in content.lower():
                    files.append(file_path)
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")

    return sorted(files)


def process_file(file_path: Path, dry_run: bool = False) -> Tuple[int, List[str]]:
    """Process a single file and return count of replacements made."""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        changes = []
        total_replacements = 0

        for old, new in REPLACEMENTS:
            if old in content:
                count = content.count(old)
                content = content.replace(old, new)
                total_replacements += count
                changes.append(f"  {old} → {new}: {count} occurrence(s)")

        if content != original_content:
            if not dry_run:
                file_path.write_text(content, encoding='utf-8')
            return total_replacements, changes

        return 0, []

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0, []


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description='Rename project from transcribe_mcp to transcribe_mcp')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    args = parser.parse_args()

    root_dir = Path(__file__).parent.parent.parent

    print("=" * 70)
    print("Project Rename: transcribe_mcp → transcribe_mcp")
    print("=" * 70)
    print()

    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
        print()

    # Find files
    print("📂 Finding files to process...")
    files = find_files_to_process(root_dir)
    print(f"   Found {len(files)} files containing 'transcribe_mcp'")
    print()

    # Process files
    print("🔄 Processing files...")
    total_changes = 0
    files_changed = 0

    for file_path in files:
        rel_path = file_path.relative_to(root_dir)
        replacements, changes = process_file(file_path, dry_run=args.dry_run)

        if replacements > 0:
            files_changed += 1
            total_changes += replacements

            if args.verbose or args.dry_run:
                print(f"\n📝 {rel_path}")
                for change in changes:
                    print(change)
            else:
                print(f"   ✓ {rel_path} ({replacements} replacements)")

    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Files processed: {files_changed}")
    print(f"Total replacements: {total_changes}")

    if args.dry_run:
        print()
        print("⚠️  This was a DRY RUN - No files were modified")
        print("   Run without --dry-run to apply changes")
    else:
        print()
        print("✅ Rename complete!")
        print()
        print("Next steps:")
        print("   1. Test the renamed project")
        print("   2. Update virtual environment")
        print("   3. Verify imports and MCP server")
        print("   4. Generate test evidence")

    print()


if __name__ == "__main__":
    main()
