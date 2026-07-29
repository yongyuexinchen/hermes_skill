#!/usr/bin/env python3
"""
DRBCV Reviewer Check — Hard-Rule Validation for Concept Cards

Runs BEFORE the LLM Reviewer. If any check fails, the card is sent back to
Card-Writer for repair. This script enforces the V0.5 "placeholder zero-tolerance"
policy.

Usage:
    python reviewer_check.py <concepts_dir> [--vault-type math|general] [--report <output_path>]

Exit codes:
    0 = all cards passed
    1 = one or more cards failed

Example:
    python reviewer_check.py D:/DRBCV-Knowledge/Calculus/Concepts --vault-type math
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------------------------
# Placeholder patterns — the core of the V0.5 fix
# ---------------------------------------------------------------------------
PLACEHOLDER_PATTERNS = [
    r"待补充",
    r"待爆破",
    r"TODO",
    r"\?\?\?",
    r"（待补充[^）]*）",       # 含括号的变体: （待补充具体例子）
    r"（待爆破[^）]*）",
    r"\(待补充[^)]*\)",        # 半角括号变体
    r"\(待爆破[^)]*\)",
]

# LLM thinking-process leakage patterns — sub-agents sometimes dump their
# internal reasoning into card content
LLM_LEAKAGE_PATTERNS = [
    r"(?m)^(?:Wait,|Actually,|Let me|Hmm,|OK let|I should|looking at|recheck|double-check)",
    r"tool_calls",
    r"invoke name",
    r"parameter name",
    r"<.*?thinking.*?>",
    r"end.*thinking",
    r"I'll (?:now|first|start)",
    r"Let's (?:look|check|read|start)",
    r"First,? I",
]

# Required frontmatter fields
REQUIRED_FRONTMATTER = ["name", "type", "status"]

# Math vault specific required sections
# Each section accepts multiple naming variants — vault cards may use different headers
MATH_REQUIRED_SECTIONS = {
    "derivation": [
        r"##\s*推导过程",
        r"##\s*详细解释.*推导",
        r"##\s*详细解释",       # Many cards embed derivation inside 详细解释
        r"##\s*是什么",          # Some cards put derivation under 是什么
    ],
    "examples": [
        r"##\s*经典例题",
        r"##\s*正例",
        r"##\s*例题",
    ],
    "analogy": [
        r"##\s*类比",
        r"##\s*物理映射",
    ],
    "relations": [
        r"##\s*关系",
        r"##\s*与其他.*关系",
    ],
}


def read_file(path):
    """Read file content with UTF-8 encoding."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return None


def extract_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm_text = parts[1]
    fm = {}
    for line in fm_text.strip().split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and val:
                fm[key] = val
    return fm


def check_placeholders(content):
    """Check for placeholder text in card content."""
    findings = []
    for pattern in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            findings.extend(matches)
    return findings


def check_llm_leakage(content):
    """Check for LLM thinking-process text leaked into card content."""
    findings = []
    for pattern in LLM_LEAKAGE_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            findings.extend(matches[:3])  # cap at 3 per pattern
    return findings


def check_frontmatter(content):
    """Check that required frontmatter fields exist and are non-empty.
    
    Supports two formats:
    - New format: name, type, status
    - Old format (concept-card): title (name is optional)
    """
    fm = extract_frontmatter(content)
    issues = []

    is_old_format = fm.get("type") == "concept-card"

    if is_old_format:
        # Old format: title is the key field
        if "title" not in fm or not fm["title"]:
            issues.append("old-format frontmatter missing: title")
        # status should exist in both formats
        if "status" not in fm or not fm["status"]:
            issues.append("missing frontmatter field: status")
    else:
        # New format: name, type, status required
        for field in REQUIRED_FRONTMATTER:
            if field not in fm or not fm[field]:
                issues.append(f"missing frontmatter field: {field}")
    return issues, fm


def check_wikilinks(content):
    """Check that card has at least one [[wikilink]]."""
    links = re.findall(r"\[\[([^\]]+)\]\]", content)
    # Filter out namespace tags
    links = [l for l in links if l not in ("Calculus",)]
    if not links:
        return ["no [[wikilink]] found in card"]
    return []


def check_math_sections(content):
    """Check for required sections in math/physics vault cards."""
    issues = []
    for section_name, patterns in MATH_REQUIRED_SECTIONS.items():
        found = any(re.search(p, content) for p in patterns)
        if not found:
            issues.append(f"math card missing section: {section_name}")
    return issues


def check_example_count(content):
    """Check that math cards have >= 2 examples in the examples section."""
    # Find the examples section
    examples_match = re.search(r"##\s*(?:经典例题|正例)(.*?)(?=\n##\s|\Z)", content, re.DOTALL)
    if not examples_match:
        return ["cannot find examples section to count"]
    examples_text = examples_match.group(1)
    # Count numbered examples (### 例题, **例, 例1, etc.)
    count = len(re.findall(r"(?:###\s*例|例\s*\d|题目\s*\d|^\s*\d+[\.、])", examples_text, re.MULTILINE))
    if count < 2:
        return [f"only {count} examples found (need >= 2)"]
    return []


def check_latex_balance(content):
    """Check that $ signs are balanced (even count)."""
    # Remove code blocks and frontmatter first
    body = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
    body = re.sub(r"^---.*?---", "", body, flags=re.DOTALL)
    dollar_count = body.count("$")
    if dollar_count % 2 != 0:
        return [f"odd number of $ signs ({dollar_count}) - possible unclosed LaTeX"]
    return []


def check_card(filepath, vault_type="math"):
    """
    Run all checks on a single card file.
    Returns dict with results.
    """
    content = read_file(filepath)
    if content is None:
        return {"file": filepath, "passed": False, "errors": ["cannot read file"], "warnings": []}

    errors = []
    warnings = []

    # 1. Placeholder scan (the big one)
    placeholders = check_placeholders(content)
    if placeholders:
        errors.append(f"PLACEHOLDERS FOUND ({len(placeholders)}): {placeholders[:5]}")

    # 2. LLM thinking-process leakage
    leakage = check_llm_leakage(content)
    if leakage:
        errors.append(f"LLM LEAKAGE ({len(leakage)}): {leakage[:3]}")

    # 3. Frontmatter completeness
    fm_issues, fm = check_frontmatter(content)
    errors.extend(fm_issues)

    # 4. Wikilink presence
    link_issues = check_wikilinks(content)
    errors.extend(link_issues)

    # 5. LaTeX balance
    latex_issues = check_latex_balance(content)
    warnings.extend(latex_issues)

    # 6. Math vault specific checks
    if vault_type == "math":
        section_issues = check_math_sections(content)
        errors.extend(section_issues)

        example_issues = check_example_count(content)
        errors.extend(example_issues)

    return {
        "file": os.path.basename(filepath),
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "frontmatter": fm,
    }


def run_review(concepts_dir, vault_type="math", report_path=None):
    """Run review on all .md files in concepts directory."""
    concepts_dir = Path(concepts_dir)
    if not concepts_dir.exists():
        print(f"ERROR: directory not found: {concepts_dir}")
        sys.exit(1)

    md_files = sorted(concepts_dir.glob("*.md"))
    if not md_files:
        print(f"ERROR: no .md files found in {concepts_dir}")
        sys.exit(1)

    results = []
    passed = 0
    failed = 0
    total_errors = 0

    for f in md_files:
        result = check_card(str(f), vault_type)
        results.append(result)
        if result["passed"]:
            passed += 1
        else:
            failed += 1
            total_errors += len(result["errors"])

    # Print summary
    print("=" * 60)
    print(f"DRBCV Reviewer Check Report")
    print(f"Directory: {concepts_dir}")
    print(f"Vault type: {vault_type}")
    print(f"Total cards: {len(md_files)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total errors: {total_errors}")
    print("=" * 60)

    if failed > 0:
        print("\nFAILED CARDS:")
        for r in results:
            if not r["passed"]:
                print(f"\n  [{r['file']}]")
                for e in r["errors"]:
                    print(f"    X {e}")

    # Warnings
    warning_count = sum(len(r["warnings"]) for r in results)
    if warning_count > 0:
        print(f"\nWARNINGS ({warning_count}):")
        for r in results:
            for w in r["warnings"]:
                print(f"  ! [{r['file']}] {w}")

    # Write report
    if report_path:
        report = {
            "directory": str(concepts_dir),
            "vault_type": vault_type,
            "total_cards": len(md_files),
            "passed": passed,
            "failed": failed,
            "total_errors": total_errors,
            "results": results,
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\nReport saved to: {report_path}")

    # Exit code
    if failed > 0:
        print(f"\nREVIEW FAILED — {failed} cards need repair.")
        sys.exit(1)
    else:
        print(f"\nREVIEW PASSED — all {passed} cards passed hard-rule checks.")
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DRBCV Reviewer Check — Hard-Rule Validation for Concept Cards"
    )
    parser.add_argument("concepts_dir", help="Path to Concepts/ directory")
    parser.add_argument(
        "--vault-type",
        default="math",
        choices=["math", "general"],
        help="Vault type: math (default) or general",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Path to save JSON report (optional)",
    )
    args = parser.parse_args()
    run_review(args.concepts_dir, args.vault_type, args.report)
