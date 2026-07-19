"""
Skills Manager Module
Part of DeepDiver - NotebookLM Podcast Automation System

DeepDiver ships agent-facing skills (SKILL.md folders) inside the package,
so any agent running the binary can discover them and install them into its
own skill directory — becoming capable of operating DeepDiver without
re-deriving the workflow from source.

    deepdiver skills list
    deepdiver skills show notebooklm-automation
    deepdiver skills install --agent claude
    deepdiver skills install notebooklm-automation --to ~/.hermes/skills/development

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional


# Where bundled skills live inside the installed package.
BUNDLED_SKILLS_DIR = Path(__file__).resolve().parent / 'skills'

# Well-known agent skill directories. 'project' variants resolve against the
# current working directory; the rest against the user's home.
AGENT_TARGETS: Dict[str, str] = {
    'claude': '~/.claude/skills',
    'claude-project': '.claude/skills',
    'hermes': '~/.hermes/skills/development',
    'codex': '~/.codex/skills',
}


def _parse_frontmatter(skill_md: Path) -> Dict[str, Any]:
    """Extract name/description from a SKILL.md YAML frontmatter block."""
    meta: Dict[str, Any] = {}
    try:
        text = skill_md.read_text(encoding='utf-8')
        if not text.startswith('---'):
            return meta
        end = text.find('\n---', 3)
        if end == -1:
            return meta
        import yaml
        parsed = yaml.safe_load(text[3:end]) or {}
        if isinstance(parsed, dict):
            meta = parsed
    except Exception:
        pass
    return meta


def list_bundled_skills() -> List[Dict[str, Any]]:
    """
    Discover the skills bundled inside the installed package.

    Returns:
        One dict per skill: name, description, path, files (relative).
    """
    skills: List[Dict[str, Any]] = []
    if not BUNDLED_SKILLS_DIR.is_dir():
        return skills

    for entry in sorted(BUNDLED_SKILLS_DIR.iterdir()):
        skill_md = entry / 'SKILL.md'
        if not entry.is_dir() or not skill_md.is_file():
            continue
        meta = _parse_frontmatter(skill_md)
        files = sorted(
            str(p.relative_to(entry))
            for p in entry.rglob('*') if p.is_file()
        )
        skills.append({
            'name': meta.get('name', entry.name),
            'dir_name': entry.name,
            'description': meta.get('description', ''),
            'path': str(entry),
            'files': files,
        })
    return skills


def get_bundled_skill(name: str) -> Optional[Dict[str, Any]]:
    """Find a bundled skill by its frontmatter name or directory name."""
    for skill in list_bundled_skills():
        if name in (skill['name'], skill['dir_name']):
            return skill
    return None


def resolve_install_target(agent: Optional[str] = None,
                           target_dir: Optional[str] = None) -> Optional[Path]:
    """
    Resolve where skills should be installed.

    Args:
        agent: A known agent preset (claude, claude-project, hermes, codex)
        target_dir: An explicit directory (wins over agent preset)

    Returns:
        Resolved Path, or None when neither input is usable.
    """
    if target_dir:
        return Path(os.path.expanduser(target_dir)).resolve()
    if agent:
        preset = AGENT_TARGETS.get(agent.strip().lower())
        if preset:
            return Path(os.path.expanduser(preset)).resolve()
    return None


def install_skill(name: str, target: Path, force: bool = False) -> Dict[str, Any]:
    """
    Copy one bundled skill folder into a target skills directory.

    Args:
        name: Bundled skill name (frontmatter or directory name)
        target: Skills directory to install into (created if missing)
        force: Overwrite an existing installed copy

    Returns:
        Result dict: name, installed (bool), destination, error/skipped info.
    """
    skill = get_bundled_skill(name)
    if not skill:
        return {'name': name, 'installed': False,
                'error': f'No bundled skill named {name!r}'}

    destination = target / skill['dir_name']
    if destination.exists():
        if not force:
            return {'name': skill['name'], 'installed': False,
                    'destination': str(destination),
                    'skipped': 'already installed (use --force to overwrite)'}
        shutil.rmtree(destination)

    try:
        target.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skill['path'], destination)
        return {'name': skill['name'], 'installed': True,
                'destination': str(destination), 'files': skill['files']}
    except Exception as e:
        return {'name': skill['name'], 'installed': False,
                'destination': str(destination), 'error': str(e)}


def install_all_skills(target: Path, force: bool = False) -> List[Dict[str, Any]]:
    """Install every bundled skill into the target directory."""
    return [
        install_skill(skill['name'], target, force=force)
        for skill in list_bundled_skills()
    ]
