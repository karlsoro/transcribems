#!/usr/bin/env python3
"""
Folder Reorganization Script for TranscribeMCP
This script reorganizes the chaotic folder structure into a clean, logical layout.
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Tuple

def create_new_structure():
    """Create the new organized directory structure."""
    directories = [
        "config",
        "docs/api",
        "docs/development",
        "docs/research",
        "test_data/audio",
        "test_data/fixtures",
        "test_data/expected_results",
        "test_reports/coverage",
        "test_reports/execution",
        "test_reports/validation",
        "test_reports/metrics",
        "scripts/setup",
        "scripts/validation",
        "scripts/performance",
        "data/jobs",
        "data/results",
        "data/uploads",
        "data/transcriptions",
        "data/logs",
        "deploy/docker",
        "deploy/k8s/manifests",
        ".cache"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}/")

def safe_move(source: str, destination: str, description: str = "") -> bool:
    """Safely move files/directories with error handling."""
    try:
        source_path = Path(source)
        dest_path = Path(destination)

        if not source_path.exists():
            print(f"⚠️  Source not found: {source}")
            return False

        # Create destination directory if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if source_path.is_file():
            shutil.move(str(source_path), str(dest_path))
        else:
            # For directories, merge if destination exists
            if dest_path.exists():
                # Move contents
                for item in source_path.iterdir():
                    item_dest = dest_path / item.name
                    if item.is_file():
                        shutil.move(str(item), str(item_dest))
                    else:
                        shutil.move(str(item), str(item_dest))
                # Remove empty source directory
                source_path.rmdir()
            else:
                shutil.move(str(source_path), str(dest_path))

        print(f"✅ Moved: {source} → {destination} {description}")
        return True

    except Exception as e:
        print(f"❌ Failed to move {source} → {destination}: {e}")
        return False

def cleanup_redundant_directories():
    """Remove redundant and unnecessary directories."""
    redundant_dirs = [
        "venv",  # Keep transcribe_mcp_env
        "transcribe_mcp",  # Duplicate project structure
        ".mypy_cache",
        ".pytest_cache",
    ]

    for directory in redundant_dirs:
        try:
            if Path(directory).exists():
                if directory in ["venv", "transcribe_mcp"]:
                    # Ask for confirmation for major deletions
                    response = input(f"⚠️  Delete redundant directory '{directory}'? (y/N): ")
                    if response.lower() != 'y':
                        print(f"⏭️  Skipped: {directory}")
                        continue

                shutil.rmtree(directory)
                print(f"🗑️  Removed: {directory}/")
        except Exception as e:
            print(f"❌ Failed to remove {directory}: {e}")

def reorganize_documentation():
    """Move documentation to proper docs/ structure."""
    doc_moves = [
        ("README.md", "docs/README.md"),
        ("TESTING_GUIDE.md", "docs/TESTING_GUIDE.md"),
        ("GPU_TESTING_REQUIREMENTS.md", "docs/GPU_TESTING_REQUIREMENTS.md"),
        ("SYSTEM_OVERVIEW.md", "docs/SYSTEM_OVERVIEW.md"),
        ("FOLDER_STRUCTURE_ANALYSIS.md", "docs/development/FOLDER_STRUCTURE_ANALYSIS.md"),
        ("docs/fastapi-research-findings.md", "docs/research/fastapi-research-findings.md"),
    ]

    print("\n📚 Reorganizing Documentation...")
    for source, dest in doc_moves:
        safe_move(source, dest, "(documentation)")

def reorganize_tests():
    """Move scattered test files to proper test structure."""
    test_moves = [
        # Validation tests
        ("test_gpu_validation.py", "scripts/validation/test_gpu_validation.py"),
        ("integration_test.py", "scripts/validation/integration_test.py"),
        ("validate_implementation.py", "scripts/validation/validate_implementation.py"),
        ("system_demo.py", "scripts/validation/system_demo.py"),

        # Performance tests
        ("performance_benchmark.py", "scripts/performance/performance_benchmark.py"),

        # Setup scripts
        ("create_test_audio.py", "scripts/setup/create_test_audio.py"),

        # Test data
        ("test_audio", "test_data/audio"),

        # Remove scattered test files from root
        ("test_real_audio.py", "tests/manual/test_real_audio.py"),
        ("test_real_speaker_service.py", "tests/manual/test_real_speaker_service.py"),
        ("test_whisperx_fixed_format.py", "tests/manual/test_whisperx_fixed_format.py"),
        ("test_correct_whisperx_diarization.py", "tests/manual/test_correct_whisperx_diarization.py"),
        ("test_real_whisperx_diarization.py", "tests/manual/test_real_whisperx_diarization.py"),
        ("test_real_audio_optimized.py", "tests/manual/test_real_audio_optimized.py"),
        ("test_simple_diarization.py", "tests/manual/test_simple_diarization.py"),
    ]

    print("\n🧪 Reorganizing Tests...")
    Path("tests/manual").mkdir(parents=True, exist_ok=True)

    for source, dest in test_moves:
        safe_move(source, dest, "(test file)")

def reorganize_test_results():
    """Move test results and evidence to proper locations."""
    # Test results already created in test_reports/
    result_moves = [
        ("integration_test_results.json", "test_reports/execution/integration_test_results.json"),
        ("performance_benchmark_report.json", "test_reports/metrics/performance_benchmark_report.json"),
        ("optimized_audio_test_results.json", "test_reports/execution/optimized_audio_test_results.json"),
        ("system_demo_report.json", "test_reports/validation/system_demo_report.json"),
        (".coverage", "test_reports/coverage/.coverage"),
        ("coverage.xml", "test_reports/coverage/coverage.xml"),
    ]

    print("\n📊 Reorganizing Test Results...")
    for source, dest in result_moves:
        safe_move(source, dest, "(test result)")

def reorganize_data_directories():
    """Reorganize data and runtime directories."""
    data_moves = [
        ("transcribe_mcp_data/jobs", "data/jobs"),
        ("transcribe_mcp_data/results", "data/results"),
        ("uploads", "data/uploads"),
        ("transcriptions", "data/transcriptions"),
        ("logs", "data/logs"),
        ("recordings", ".cache/recordings"),
    ]

    print("\n💾 Reorganizing Data Directories...")
    for source, dest in data_moves:
        safe_move(source, dest, "(data)")

    # Clean up empty transcribe_mcp_data
    try:
        if Path("transcribe_mcp_data").exists() and not any(Path("transcribe_mcp_data").iterdir()):
            Path("transcribe_mcp_data").rmdir()
            print("🗑️  Removed empty: transcribe_mcp_data/")
    except:
        pass

def reorganize_deployment():
    """Move deployment files to deploy/ directory."""
    deploy_moves = [
        ("Dockerfile", "deploy/docker/Dockerfile"),
        ("docker-compose.yml", "deploy/docker/docker-compose.yml"),
    ]

    print("\n🚀 Reorganizing Deployment Files...")
    for source, dest in deploy_moves:
        safe_move(source, dest, "(deployment)")

def create_config_files():
    """Create proper configuration files."""
    print("\n⚙️  Creating Configuration Files...")

    # Create default environment config
    default_config = """# Default TranscribeMCP Configuration
WHISPERX_MODEL_SIZE=large-v2
MAX_FILE_SIZE=5368709120
TRANSCRIBE_MCP_LOG_LEVEL=INFO
TRANSCRIBE_MCP_WORK_DIR=./data
HF_TOKEN=your_huggingface_token_here
"""

    config_file = Path("config/default.env")
    if not config_file.exists():
        config_file.write_text(default_config)
        print("✅ Created: config/default.env")

    # Create logging configuration
    logging_config = """version: 1
formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default
    stream: ext://sys.stdout
  file:
    class: logging.FileHandler
    level: DEBUG
    formatter: default
    filename: data/logs/transcribe_mcp.log
loggers:
  src:
    level: DEBUG
    handlers: [console, file]
    propagate: no
root:
  level: INFO
  handlers: [console]
"""

    logging_file = Path("config/logging.yaml")
    if not logging_file.exists():
        logging_file.write_text(logging_config)
        print("✅ Created: config/logging.yaml")

def update_gitignore():
    """Update .gitignore for new structure."""
    gitignore_additions = """
# Reorganized structure additions
/data/
/test_reports/
/.cache/
/test_data/audio/*.wav
/test_data/audio/*.mp3
"""

    gitignore_path = Path(".gitignore")
    if gitignore_path.exists():
        current_content = gitignore_path.read_text()
        if "# Reorganized structure additions" not in current_content:
            gitignore_path.write_text(current_content + gitignore_additions)
            print("✅ Updated: .gitignore")

def print_summary():
    """Print reorganization summary."""
    print("\n" + "="*60)
    print("🎉 FOLDER REORGANIZATION COMPLETE")
    print("="*60)

    print("\n📁 NEW STRUCTURE:")
    print("├── config/           # Application configuration")
    print("├── docs/             # All documentation")
    print("├── src/              # Source code (unchanged)")
    print("├── tests/            # Organized test suites")
    print("├── test_data/        # Test fixtures and audio")
    print("├── test_reports/     # Test evidence & results")
    print("├── scripts/          # Standalone utilities")
    print("├── data/             # Runtime data")
    print("├── deploy/           # Deployment configs")
    print("└── .cache/           # Generated/cache files")

    print("\n📊 TEST EVIDENCE LOCATION:")
    print("test_reports/")
    print("├── coverage/         # Code coverage reports")
    print("├── execution/        # Test execution results")
    print("├── validation/       # Validation evidence")
    print("└── metrics/          # Performance metrics")

    print("\n🎯 VIEW TEST RESULTS:")
    print("• Coverage Dashboard: open test_reports/coverage/html/index.html")
    print("• Test Evidence: test_reports/validation/TEST_EVIDENCE_SUMMARY.md")
    print("• Requirements Traceability: test_reports/validation/requirements_traceability.csv")

def main():
    """Main reorganization process."""
    print("🚀 TranscribeMCP Folder Reorganization Script")
    print("=" * 50)

    # Confirm before proceeding
    response = input("This will reorganize the entire folder structure. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Reorganization cancelled.")
        sys.exit(0)

    try:
        print("\n1️⃣  Creating new directory structure...")
        create_new_structure()

        print("\n2️⃣  Moving documentation...")
        reorganize_documentation()

        print("\n3️⃣  Reorganizing tests...")
        reorganize_tests()

        print("\n4️⃣  Moving test results...")
        reorganize_test_results()

        print("\n5️⃣  Reorganizing data directories...")
        reorganize_data_directories()

        print("\n6️⃣  Moving deployment files...")
        reorganize_deployment()

        print("\n7️⃣  Creating configuration files...")
        create_config_files()

        print("\n8️⃣  Updating .gitignore...")
        update_gitignore()

        print("\n9️⃣  Cleaning up redundant directories...")
        cleanup_redundant_directories()

        print_summary()

    except KeyboardInterrupt:
        print("\n⚠️  Reorganization interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Reorganization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()