#!/usr/bin/env python3
"""
GitHub Issues Creator for NotebookLM Studio Artifacts

This script helps create GitHub issues from the template files.
Since gh CLI may not be available, it provides formatted output
that can be easily copy-pasted into GitHub's web interface.

Usage:
    python create_issues.py                 # Show all issues
    python create_issues.py --phase 2       # Show specific phase
    python create_issues.py --export        # Export to JSON
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class IssueTemplate:
    """Represents a GitHub issue template"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = file_path.read_text()
        self.title = self._extract_title()
        self.labels = self._extract_labels()
        self.priority = self._extract_priority()
        self.phase = self._extract_phase()
        self.body = self._extract_body()

    def _extract_title(self) -> str:
        """Extract title from first # heading"""
        match = re.search(r'^#\s+(.+)$', self.content, re.MULTILINE)
        return match.group(1) if match else "Untitled"

    def _extract_labels(self) -> List[str]:
        """Extract labels from metadata section"""
        match = re.search(r'\*\*Labels\*\*:\s+(.+)$', self.content, re.MULTILINE)
        if match:
            labels_str = match.group(1)
            # Parse backtick-wrapped labels
            labels = re.findall(r'`([^`]+)`', labels_str)
            return labels
        return []

    def _extract_priority(self) -> str:
        """Extract priority from metadata section"""
        match = re.search(r'\*\*Priority\*\*:\s+(\w+)', self.content, re.MULTILINE)
        return match.group(1) if match else "Medium"

    def _extract_phase(self) -> Optional[int]:
        """Extract phase number from labels"""
        for label in self.labels:
            if label.startswith('phase-'):
                return int(label.split('-')[1])
        return None

    def _extract_body(self) -> str:
        """Extract issue body (everything after metadata)"""
        # Remove the title line
        lines = self.content.split('\n')

        # Find where metadata ends (after the first blank line following labels)
        start_idx = 0
        found_labels = False

        for i, line in enumerate(lines):
            if '**Labels**' in line:
                found_labels = True
            if found_labels and line.strip() == '' and i > 5:
                start_idx = i + 1
                break

        return '\n'.join(lines[start_idx:]).strip()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        return {
            'title': self.title,
            'labels': self.labels,
            'priority': self.priority,
            'phase': self.phase,
            'body': self.body,
            'file': str(self.file_path.name)
        }

    def to_markdown(self) -> str:
        """Format as markdown for display"""
        return f"""
{'=' * 80}
PHASE {self.phase}: {self.title}
{'=' * 80}

Title: {self.title}
Labels: {', '.join(self.labels)}
Priority: {self.priority}
File: {self.file_path.name}

{'─' * 80}
ISSUE BODY (Copy everything below this line):
{'─' * 80}

{self.body}

{'=' * 80}
"""

    def to_github_url(self, repo: str = "Gerico1007/deepdiver") -> str:
        """Generate GitHub issue creation URL with pre-filled data"""
        import urllib.parse

        title_encoded = urllib.parse.quote(self.title)
        labels_encoded = urllib.parse.quote(','.join(self.labels))
        body_encoded = urllib.parse.quote(self.body)

        # GitHub URL length limit workaround - just include title and labels
        url = f"https://github.com/{repo}/issues/new?"
        url += f"title={title_encoded}"
        url += f"&labels={labels_encoded}"

        return url


def load_templates(templates_dir: Path) -> List[IssueTemplate]:
    """Load all issue templates from directory"""
    templates = []

    for file_path in sorted(templates_dir.glob('phase-*.md')):
        try:
            template = IssueTemplate(file_path)
            templates.append(template)
        except Exception as e:
            print(f"Warning: Failed to parse {file_path.name}: {e}")

    return templates


def display_template(template: IssueTemplate, show_body: bool = True):
    """Display a single template"""
    if show_body:
        print(template.to_markdown())
    else:
        print(f"\nPhase {template.phase}: {template.title}")
        print(f"  Labels: {', '.join(template.labels)}")
        print(f"  Priority: {template.priority}")
        print(f"  File: {template.file_path.name}")
        print(f"  GitHub URL: {template.to_github_url()}")


def export_to_json(templates: List[IssueTemplate], output_file: Path):
    """Export templates to JSON"""
    data = {
        'repository': 'Gerico1007/deepdiver',
        'milestone': 'NotebookLM Studio Artifacts',
        'issues': [t.to_dict() for t in templates]
    }

    output_file.write_text(json.dumps(data, indent=2))
    print(f"\n✅ Exported {len(templates)} issue templates to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Create GitHub issues from NotebookLM Studio Artifacts templates'
    )
    parser.add_argument(
        '--phase',
        type=int,
        choices=[2, 3, 4, 5, 6],
        help='Show only specific phase'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all templates without full body'
    )
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export to JSON file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('issues_export.json'),
        help='Output file for JSON export (default: issues_export.json)'
    )

    args = parser.parse_args()

    # Load templates
    templates_dir = Path(__file__).parent
    templates = load_templates(templates_dir)

    if not templates:
        print("❌ No issue templates found!")
        return

    print(f"\n📋 Found {len(templates)} issue templates")

    # Filter by phase if specified
    if args.phase:
        templates = [t for t in templates if t.phase == args.phase]
        print(f"🔍 Filtered to Phase {args.phase}: {len(templates)} template(s)")

    # Export to JSON
    if args.export:
        export_to_json(templates, args.output)
        return

    # Display templates
    print("\n" + "=" * 80)
    print("NOTEBOOKLM STUDIO ARTIFACTS - GITHUB ISSUES")
    print("=" * 80)

    if args.list:
        print("\n📝 Issue Templates Summary:\n")
        for template in templates:
            display_template(template, show_body=False)

        print("\n" + "─" * 80)
        print("💡 To see full issue body: python create_issues.py --phase N")
        print("💡 To export to JSON: python create_issues.py --export")
        print("💡 To create issues in GitHub:")
        print("   1. Go to: https://github.com/Gerico1007/deepdiver/issues/new")
        print("   2. Run: python create_issues.py --phase N")
        print("   3. Copy the issue body section")
        print("   4. Paste into GitHub issue form")
        print("   5. Add labels and milestone manually")
    else:
        for template in templates:
            display_template(template, show_body=True)

        print("\n" + "=" * 80)
        print("📝 HOW TO CREATE THESE ISSUES IN GITHUB:")
        print("=" * 80)
        print("""
1. Copy the ISSUE BODY section from above (everything after the separator line)
2. Go to: https://github.com/Gerico1007/deepdiver/issues/new
3. Paste the title and body
4. Add the labels shown above
5. Set milestone to: "NotebookLM Studio Artifacts"
6. Assign to yourself
7. Click "Submit new issue"

Repeat for each phase!
        """)

    print("\n✅ Done!\n")


if __name__ == '__main__':
    main()
