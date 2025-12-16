#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate SonarQube-style reports for code analysis.

This script generates three types of reports:
1. Code Complexity Report (using Radon)
2. Code Smells Report (using Pylint)
3. Bugs Report (using Pylint errors)
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def run_command(cmd: list[str], capture_output: bool = True) -> tuple[str, int]:
    """Run a command and return output and return code."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            check=False,
            encoding='utf-8',
            errors='replace'
        )
        output = result.stdout if capture_output else ""
        return output, result.returncode
    except (FileNotFoundError, OSError) as e:
        print(f"Error running command {' '.join(cmd)}: {e}", file=sys.stderr)
        return "", 1


def generate_complexity_report(output_path: Path) -> None:
    """Generate code complexity report using Radon."""
    print("[*] Generating Code Complexity Report...")
    
    source_dir = Path(__file__).parent.parent / "src" / "nemesis"
    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}", file=sys.stderr)
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Run radon cc (cyclomatic complexity)
    cmd = ["radon", "cc", str(source_dir), "--min", "C"]
    output, returncode = run_command(cmd)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=== Code Complexity Report ===\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("This report contains code complexity metrics.\n")
        f.write("Functions/methods with grades C, D, E, F need refactoring.\n\n")
        
        if output:
            f.write(output)
        else:
            f.write("No complexity issues found (all functions have grade A or B).\n")
        
        f.write("\n-------------------------------------------------------------------\n")
        
        # Get average complexity
        cmd_avg = ["radon", "cc", str(source_dir), "--average"]
        avg_output, _ = run_command(cmd_avg)
        if avg_output:
            f.write(f"\nAverage Complexity:\n{avg_output}\n")
    
    print(f"[OK] Complexity report saved to: {output_path}")


def generate_smells_report(output_path: Path) -> None:
    """Generate code smells report using Pylint."""
    print("[*] Generating Code Smells Report...")
    
    source_dir = Path(__file__).parent.parent / "src" / "nemesis"
    if not source_dir.exists():
        print(f"[ERROR] Source directory not found: {source_dir}", file=sys.stderr)
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Run pylint for code smells (warnings and conventions, exclude errors)
    # Using --disable=E to exclude errors (bugs), keeping only W (warnings) and C (conventions)
    # Also disable C0301 (line-too-long) and W0706 (try-except-raise) as they're handled separately
    cmd = [
        "pylint",
        str(source_dir),
        "--output-format=text",
        "--disable=E,C0301,W0706",  # Exclude errors, line-too-long, and try-except-raise
        "--msg-template={path}:{line}:{column}: {msg_id}: {msg} ({symbol})"
    ]
    output, returncode = run_command(cmd)
    
    with open(output_path, "w", encoding="utf-8") as f:
        if output:
            f.write(output)
        else:
            f.write("No code smells found.\n")
        
        f.write("\n------------------------------------------------------------------\n")
        
        # Run pylint again to get rating
        cmd_rating = [
            "pylint",
            str(source_dir),
            "--output-format=text",
            "--disable=E,C0301,W0706",
            "--disable=F"
        ]
        rating_output, _ = run_command(cmd_rating)
        
        # Extract rating from output
        rating_line = None
        for line in rating_output.split('\n'):
            if 'Your code has been rated at' in line:
                rating_line = line
                break
        
        if rating_line:
            f.write(f"\n{rating_line}\n")
    
    print(f"[OK] Code Smells report saved to: {output_path}")


def generate_bugs_report(output_path: Path) -> None:
    """Generate bugs report using Pylint errors."""
    print("[*] Generating Bugs Report...")
    
    source_dir = Path(__file__).parent.parent / "src" / "nemesis"
    if not source_dir.exists():
        print(f"[ERROR] Source directory not found: {source_dir}", file=sys.stderr)
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Run pylint for bugs (errors only, E and F categories)
    cmd = [
        "pylint",
        str(source_dir),
        "--output-format=text",
        "--disable=W,C,R,I",  # Only show errors (E) and fatal (F)
        "--enable=E,F",
        "--msg-template={path}:{line}:{column}: {msg_id}: {msg} ({symbol})"
    ]
    output, returncode = run_command(cmd)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=== Bugs Report ===\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("This report contains logical errors and bugs that may cause incorrect program behavior.\n\n")
        
        if output:
            # Filter only E and F messages
            bug_lines = []
            for line in output.split('\n'):
                if ': E' in line or ': F' in line:
                    bug_lines.append(line)
            
            if bug_lines:
                f.write('\n'.join(bug_lines))
            else:
                f.write("No bugs found.\n")
        else:
            f.write("No bugs found.\n")
        
        f.write("\n\n-------------------------------------------------------------------\n")
        
        # Get rating
        cmd_rating = [
            "pylint",
            str(source_dir),
            "--output-format=text",
            "--disable=W,C,R,I"
        ]
        rating_output, _ = run_command(cmd_rating)
        
        rating_line = None
        for line in rating_output.split('\n'):
            if 'Your code has been rated at' in line:
                rating_line = line
                break
        
        if rating_line:
            f.write(f"\n{rating_line}\n")
    
    print(f"[OK] Bugs report saved to: {output_path}")


def main():
    """Main function to generate all reports."""
    project_root = Path(__file__).parent.parent
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Delete old reports
    print("[*] Cleaning up old reports...")
    for pattern in ["*_Code_Complexity_*.txt", "*_Code_Smells_*.txt", "*_Bugs_*.txt"]:
        for old_report in project_root.glob(pattern):
            try:
                old_report.unlink()
                print(f"   Deleted: {old_report.name}")
            except OSError as e:
                print(f"   Warning: Could not delete {old_report.name}: {e}")
    
    # Generate new reports
    print("\n[*] Generating new reports...\n")
    
    complexity_report = project_root / f"01_Code_Complexity_{timestamp}.txt"
    smells_report = project_root / f"02_Code_Smells_{timestamp}.txt"
    bugs_report = project_root / f"03_Bugs_{timestamp}.txt"
    
    generate_complexity_report(complexity_report)
    print()
    generate_smells_report(smells_report)
    print()
    generate_bugs_report(bugs_report)
    
    print("\n[OK] All reports generated successfully!")
    print(f"\nReports location:")
    print(f"  - Complexity: {complexity_report.name}")
    print(f"  - Code Smells: {smells_report.name}")
    print(f"  - Bugs: {bugs_report.name}")


if __name__ == "__main__":
    main()

