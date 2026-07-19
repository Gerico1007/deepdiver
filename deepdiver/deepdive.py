"""
DeepDiver CLI Module
Main command-line interface for NotebookLM Podcast Automation System

This module provides the command-line interface for DeepDiver,
enabling users to create podcasts from documents through terminal commands.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import asyncio
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ._version import __version__
from .notebooklm_automator import (
    NotebookLMAutomator,
    find_chrome_executable,
    check_chrome_cdp_running,
    get_cdp_version_info,
    launch_chrome_cdp,
    get_cdp_url,
    find_config_file
)
from .studio_artifacts import (
    ARTIFACT_TYPES,
    list_artifact_type_keys,
    normalize_artifact_type,
)


# Initialize Rich console for beautiful output
console = Console()


def cdp_url_option(f):
    """Shared --cdp-url override flag for browser-connecting commands."""
    return click.option(
        '--cdp-url', default=None,
        help='Override CDP URL (e.g. http://127.0.0.1:9222); beats env/config'
    )(f)


def print_assembly_header():
    """Print the Assembly team header."""
    header_text = Text("♠️🌿🎸🧵 DeepDiver - NotebookLM Podcast Automation", style="bold blue")
    subtitle = Text("Terminal-to-Web Audio Creation Bridge", style="italic green")
    
    console.print(Panel.fit(
        f"{header_text}\n{subtitle}",
        border_style="blue",
        padding=(1, 2)
    ))


@click.group()
@click.version_option(version=__version__, prog_name="DeepDiver")
def cli():
    """
    🎙️ DeepDiver - NotebookLM Podcast Automation System
    
    Create podcasts from documents using NotebookLM's Audio Overview feature
    through terminal commands and browser automation.
    
    Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
    """
    print_assembly_header()


@cli.command()
@click.option('--config', '-c', default=None,
              help='Path to configuration file (default: ~/.config/deepdiver/config.yaml)')
def init(config: str):
    """
    Initialize DeepDiver configuration and setup.

    This command:
    - Creates configuration file if needed
    - Validates configuration file
    - Checks Chrome CDP status
    - Offers to launch Chrome automatically
    - Provides setup instructions for NotebookLM
    """
    console.print("♠️🌿🎸🧵 DeepDiver Initialization", style="bold blue")
    console.print()

    try:
        # Determine config file location
        if config is None:
            # Default to user config directory
            config_dir = os.path.expanduser("~/.config/deepdiver")
            config = os.path.join(config_dir, "config.yaml")
            console.print(f"📂 Using default config location: {config}", style="cyan")

        # Check if config file exists, create if not
        if not os.path.exists(config):
            console.print(f"📝 Configuration file not found: {config}", style="yellow")
            console.print("🔧 Creating new configuration file...", style="cyan")

            # Create directory if it doesn't exist
            config_dir = os.path.dirname(config)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
                console.print(f"📁 Created directory: {config_dir}", style="green")

            # Look for template in package directory
            module_dir = os.path.dirname(os.path.abspath(__file__))
            template_paths = [
                os.path.join(module_dir, "deepdiver.yaml"),
                os.path.join(os.path.dirname(module_dir), "deepdiver", "deepdiver.yaml"),
            ]

            template_config = None
            for template_path in template_paths:
                if os.path.exists(template_path):
                    template_config = template_path
                    break

            if template_config:
                # Copy template to config location
                shutil.copy(template_config, config)
                console.print(f"✅ Created configuration file from template", style="green")
                console.print(f"   Location: {config}", style="dim")
            else:
                # Create basic default config
                default_config = """# DeepDiver Configuration
# NotebookLM Podcast Automation System

BASE_PATH: ./output

# Browser automation settings
BROWSER_SETTINGS:
  headless: false
  cdp_url: http://localhost:9222
  user_data_dir: /tmp/chrome-deepdiver
  timeout: 60

# Session tracking configuration
SESSION_TRACKING:
  enabled: true
  metadata_format: yaml
  session_dir: ./sessions

# NotebookLM specific settings
NOTEBOOKLM_SETTINGS:
  base_url: https://notebooklm.google.com
  upload_timeout: 120
  generation_timeout: 300
"""
                with open(config, 'w') as f:
                    f.write(default_config)
                console.print(f"✅ Created basic configuration file", style="green")
                console.print(f"   Location: {config}", style="dim")

            console.print()
        else:
            console.print(f"✅ Configuration file found: {config}", style="green")
            console.print()

        # Test configuration loading
        automator = NotebookLMAutomator(config)
        console.print("✅ Configuration loaded successfully", style="green")

        # Get CDP URL from configuration
        cdp_url = get_cdp_url(config_path=config)
        console.print(f"🔗 CDP URL: {cdp_url}", style="cyan")

        # ═══════════════════════════════════════════════════════════════
        # CHROME CDP SETUP - Auto-launch capability
        # ♠️🌿🎸🧵 G.Music Assembly - Following simexp patterns
        # ═══════════════════════════════════════════════════════════════

        console.print()
        console.print("🚀 Chrome CDP Setup", style="bold blue")
        console.print("   DeepDiver needs Chrome running with remote debugging.", style="dim")
        console.print()

        # Check if Chrome CDP is already running
        if check_chrome_cdp_running(cdp_url):
            console.print("✅ Chrome CDP is already running!", style="green")
            console.print(f"   Connected at: {cdp_url}", style="dim")
        else:
            console.print("⚠️  Chrome CDP is not running", style="yellow")

            # Offer to launch Chrome automatically
            chrome_cmd = find_chrome_executable()

            if chrome_cmd:
                console.print(f"   🔍 Found Chrome: {chrome_cmd}", style="cyan")
                console.print()

                # Ask user if they want to auto-launch
                launch = click.confirm("   Launch Chrome automatically with CDP?", default=True)

                if launch:
                    console.print("   🚀 Launching Chrome...", style="blue")

                    if launch_chrome_cdp():
                        console.print("   ✅ Chrome launched successfully with CDP on port 9222", style="green")
                        console.print(f"   🔗 Accessible at: http://localhost:9222", style="dim")
                    else:
                        console.print("   ⚠️  Could not launch Chrome automatically", style="yellow")
                        console.print()
                        console.print("   Run manually:", style="yellow")
                        console.print(f"   {chrome_cmd} --remote-debugging-port=9222 --user-data-dir=~/.chrome-deepdiver &", style="cyan")
                else:
                    console.print()
                    console.print("   Run this command to start Chrome with CDP:", style="yellow")
                    console.print(f"   {chrome_cmd} --remote-debugging-port=9222 --user-data-dir=~/.chrome-deepdiver &", style="cyan")
            else:
                console.print("   ⚠️  Could not find Chrome/Chromium on your system", style="yellow")
                console.print()
                console.print("   Install Chrome and run:", style="yellow")
                console.print("   google-chrome --remote-debugging-port=9222 --user-data-dir=~/.chrome-deepdiver &", style="cyan")

        # ═══════════════════════════════════════════════════════════════
        # NOTEBOOKLM SETUP INSTRUCTIONS
        # ═══════════════════════════════════════════════════════════════

        console.print()
        console.print("📝 NotebookLM Setup Instructions", style="bold blue")
        console.print("   1. A Chrome window has opened (or is already open)", style="dim")
        console.print("   2. Go to: https://notebooklm.google.com", style="dim")
        console.print("   3. Login with your Google account", style="dim")
        console.print("   4. Keep this Chrome window open while using DeepDiver", style="dim")
        console.print()

        console.print("💡 Ready to test? Run: deepdiver test", style="bold green")
        console.print()
        console.print("🎉 DeepDiver initialization complete!", style="bold green")

    except Exception as e:
        console.print(f"❌ Initialization failed: {e}", style="red")
        import traceback
        console.print(traceback.format_exc(), style="dim")


@cli.command()
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def test(config: str):
    """Test NotebookLM connection and automation setup."""
    console.print("🧪 Testing NotebookLM Connection...", style="blue")
    
    async def run_test():
        automator = NotebookLMAutomator(config)
        
        try:
            # Test browser connection
            console.print("🔗 Testing browser connection...", style="blue")
            if await automator.connect_to_browser():
                console.print("✅ Browser connection successful", style="green")
                
                # Test navigation
                console.print("🌐 Testing NotebookLM navigation...", style="blue")
                if await automator.navigate_to_notebooklm():
                    console.print("✅ NotebookLM navigation successful", style="green")
                    
                    # Test authentication
                    console.print("🔐 Checking authentication...", style="blue")
                    auth_status = await automator.check_authentication()
                    if auth_status:
                        console.print("✅ User appears to be authenticated", style="green")
                    else:
                        console.print("⚠️ User may need to sign in to Google account", style="yellow")
                    
                    console.print("🎉 All tests passed! DeepDiver is ready to use.", style="green")
                    console.print("🔗 Browser kept open for next command", style="dim")
                else:
                    console.print("❌ NotebookLM navigation failed", style="red")
            else:
                console.print("❌ Browser connection failed", style="red")
                console.print("Make sure Chrome is running with CDP enabled", style="yellow")

        except Exception as e:
            console.print(f"❌ Test failed: {e}", style="red")
        # Browser stays open - no close() call

    asyncio.run(run_test())


@cli.command()
@click.argument('source', type=click.Path(exists=True))
@click.option('--title', '-t', default='Generated Podcast',
              help='Title for the generated podcast')
@click.option('--output', '-o', default='./output',
              help='Output directory for generated audio')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def podcast(source: str, title: str, output: str, config: str):
    """Create a podcast from a document using NotebookLM."""
    console.print(f"🎙️ Creating podcast: {title}", style="blue")
    console.print(f"📄 Source: {source}", style="blue")
    console.print(f"📁 Output: {output}", style="blue")
    
    async def create_podcast():
        automator = NotebookLMAutomator(config)
        
        try:
            # Connect to browser
            if not await automator.connect_to_browser():
                console.print("❌ Failed to connect to browser", style="red")
                return
            
            # Navigate to NotebookLM
            if not await automator.navigate_to_notebooklm():
                console.print("❌ Failed to navigate to NotebookLM", style="red")
                return
            
            # Check authentication
            if not await automator.check_authentication():
                console.print("⚠️ Please sign in to your Google account in the browser", style="yellow")
                console.print("Then run the command again", style="yellow")
                return
            
            # Upload document
            console.print("📤 Uploading document...", style="blue")
            notebook_id = await automator.upload_document(source)
            if not notebook_id:
                console.print("❌ Failed to upload document", style="red")
                return

            # Generate Audio Overview
            console.print("🎵 Generating Audio Overview...", style="blue")
            if not await automator.generate_audio_overview(notebook_id=notebook_id):
                console.print("❌ Failed to generate Audio Overview", style="red")
                return
            
            # Download audio
            output_path = os.path.join(output, f"{title}.mp3")
            os.makedirs(output, exist_ok=True)
            
            console.print("⬇️ Downloading audio...", style="blue")
            saved_path = await automator.download_audio(output_path)
            if saved_path:
                console.print(f"✅ Podcast created successfully: {saved_path}", style="green")
            else:
                console.print("❌ Failed to download audio", style="red")
        
        except Exception as e:
            console.print(f"❌ Podcast creation failed: {e}", style="red")
        
        finally:
            await automator.close()
    
    asyncio.run(create_podcast())


@cli.group()
def session():
    """Session management commands."""
    pass


@session.command()
@click.option('--ai', default='claude', help='AI assistant name')
@click.option('--issue', type=int, help='Issue number')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def start(ai: str, issue: Optional[int], config: str):
    """Start a new DeepDiver session."""
    from .session_tracker import SessionTracker

    console.print("🔮 Starting new DeepDiver session...", style="blue")
    console.print(f"🤖 AI Assistant: {ai}", style="blue")
    if issue:
        console.print(f"🎯 Issue: #{issue}", style="blue")

    tracker = SessionTracker()
    if tracker.load_current_session():
        console.print("⚠️ An active session already exists:", style="yellow")
        console.print(f"   {tracker.current_session['session_id'][:16]}...", style="dim")
        console.print("💡 Close it first or continue using it", style="yellow")
        return

    result = tracker.start_session(ai_assistant=ai, issue_number=issue)
    if result.get('success'):
        console.print(f"✅ Session started: {result['session_id'][:16]}...", style="green")
        console.print(f"💾 Session file: {result['session_path']}", style="dim")
    else:
        console.print(f"❌ Failed to start session: {result.get('error')}", style="red")


@session.command()
@click.argument('message')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def write(message: str, config: str):
    """Write a note into the current session."""
    from .session_tracker import SessionTracker

    console.print(f"✍️ Writing to session: {message}", style="blue")

    tracker = SessionTracker()
    if not tracker.load_current_session():
        console.print("❌ No active session", style="red")
        console.print("💡 Start one with: deepdiver session start", style="yellow")
        return

    if tracker.write_to_session(message):
        console.print("✅ Message written to session", style="green")
    else:
        console.print("❌ Failed to write to session", style="red")


@session.command()
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def status(config: str):
    """Show current session status."""
    from .session_tracker import SessionTracker

    tracker = SessionTracker()
    tracker._load_current_session()

    if not tracker.current_session:
        console.print("❌ No active session", style="red")
        console.print("💡 Run 'deepdiver notebook create' to start a session", style="yellow")
        return

    session_status = tracker.get_session_status()

    console.print("📊 Session Status", style="bold blue")
    console.print()
    console.print(f"🔮 Session ID: {session_status['session_id'][:16]}...", style="cyan")
    console.print(f"🤖 AI Assistant: {session_status['ai_assistant']}", style="cyan")
    console.print(f"📓 Notebooks: {session_status['notebooks_count']}", style="cyan")
    if session_status['active_notebook_id']:
        console.print(f"🟢 Active Notebook: {session_status['active_notebook_id']}", style="green")
    console.print(f"📝 Notes: {session_status['notes_count']}", style="dim")
    console.print(f"📅 Created: {session_status['created_at']}", style="dim")


@session.command(name='close')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def close_session(config: str):
    """Close browser and cleanup session resources."""
    console.print("🔒 Closing browser session...", style="blue")

    async def run_close():
        from .notebooklm_automator import NotebookLMAutomator

        automator = NotebookLMAutomator(config)

        try:
            # Connect to browser (if it's still running)
            if await automator.connect_to_browser():
                console.print("✅ Connected to browser", style="green")
                # Close the browser
                await automator.close()
                console.print("✅ Browser closed successfully", style="green")
            else:
                console.print("⚠️  Browser not running", style="yellow")
        except Exception as e:
            console.print(f"⚠️  Error closing browser: {e}", style="yellow")
            console.print("Browser may have already been closed", style="dim")

    asyncio.run(run_close())
    console.print("💡 Session data preserved in ./sessions/", style="cyan")
    console.print("💡 Run 'deepdiver notebook create' to start a new session", style="cyan")


@cli.command()
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def status(cdp_url: str, config: str):
    """Show DeepDiver system status with a real CDP probe."""
    console.print("📊 DeepDiver System Status", style="blue")

    try:
        # Check configuration
        automator = NotebookLMAutomator(config, cdp_url_override=cdp_url)
        console.print("✅ Configuration loaded", style="green")

        # Probe the actual CDP endpoint — a healthy config means nothing
        # if Chrome isn't answering on the debug port.
        console.print(f"🔍 Probing CDP endpoint: {automator.cdp_url}", style="blue")
        version_info = get_cdp_version_info(automator.cdp_url)
        if version_info:
            console.print(f"✅ Chrome CDP live: {version_info.get('Browser', 'unknown')}", style="green")
            console.print("🎯 System Status: Ready for automation", style="green")
        else:
            console.print("❌ Chrome CDP is NOT answering", style="red")
            console.print("💡 Launch it with: deepdiver chrome launch", style="yellow")
            console.print("🎯 System Status: NOT ready — browser required", style="red")

    except Exception as e:
        console.print(f"❌ System status check failed: {e}", style="red")


@cli.command(name='get-html')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def get_html(config: str):
    """Get the HTML content of the NotebookLM page."""
    console.print("📄 Getting HTML content of NotebookLM page...", style="blue")
    
    async def run_get_html():
        from .notebooklm_automator import NotebookLMAutomator
        automator = NotebookLMAutomator(config)
        
        try:
            if await automator.connect_to_browser():
                if await automator.navigate_to_notebooklm():
                    content = await automator.get_page_content()
                    if content:
                        console.print(Text(content))
        except Exception as e:
            console.print(f"❌ Failed to get HTML: {e}", style="red")
        # Removed finally block to keep browser open
            
    asyncio.run(run_get_html())


@cli.group()
def notebook():
    """Notebook management commands."""
    pass


@notebook.command(name='create')
@click.option('--source', '-s', help='Add a source to the notebook (URL or file path)')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def notebook_create(source: str, config: str):
    """Create a new notebook in NotebookLM with optional initial source.

    The source can be:
    - SimExp session URL: https://app.simplenote.com/p/[NOTE_ID]
    - Web article URL: https://example.com/article
    - YouTube URL: https://youtube.com/watch?v=...
    - Local file path: ./document.pdf

    Examples:
        deepdiver notebook create --source "https://app.simplenote.com/p/abc123"
        deepdiver notebook create --source "https://example.com/research"
        deepdiver notebook create --source "./notes.pdf"
        deepdiver notebook create  # Create empty notebook
    """
    if source:
        console.print(f"📓 Creating notebook with source: {source}", style="blue")
    else:
        console.print("📓 Creating a new NotebookLM notebook...", style="blue")

    async def run_create_notebook():
        from .notebooklm_automator import NotebookLMAutomator
        from .session_tracker import SessionTracker

        automator = NotebookLMAutomator(config)
        tracker = SessionTracker()

        try:
            # Load or start session
            tracker._load_current_session()
            if not tracker.current_session:
                result = tracker.start_session(ai_assistant='claude')
                console.print(f"🔮 New session started: {result['session_id'][:8]}...", style="cyan")

            if await automator.connect_to_browser():
                if await automator.navigate_to_notebooklm():
                    notebook_data = await automator.create_notebook()

                    if notebook_data:
                        console.print("✅ Notebook created successfully!", style="green")
                        console.print(f"📋 Notebook ID: {notebook_data['id']}", style="cyan")
                        console.print(f"🔗 Notebook URL:", style="cyan")
                        console.print(f"   {notebook_data['url']}", style="bold blue")

                        # Add to session
                        tracker.add_notebook(notebook_data)
                        console.print(f"💾 Notebook saved to session", style="green")

                        # Add source if provided
                        if source:
                            console.print(f"\n🔗 Adding source to notebook...", style="blue")
                            result = await automator.add_source(source, notebook_id=notebook_data['id'])
                            if result:
                                console.print(f"✅ Source added successfully!", style="green")
                                # Update session tracker with source info
                                tracker.add_source_to_notebook(notebook_data['id'], {
                                    'source': source,
                                    'type': 'url' if source.startswith(('http://', 'https://')) else 'file'
                                })
                            else:
                                console.print(f"❌ Failed to add source", style="red")
                                console.print(f"💡 Tip: You can add sources later with 'deepdiver notebook add-source'", style="yellow")

                        console.print(f"\n🔗 Browser kept open for next command", style="dim")
                    else:
                        console.print("❌ Failed to create notebook", style="red")
        except Exception as e:
            console.print(f"❌ Failed to create notebook: {e}", style="red")
        # Browser stays open - no close() call

    asyncio.run(run_create_notebook())


@notebook.command(name='url')
@click.option('--notebook-id', '-n', help='Notebook ID (uses active notebook if not specified)')
@click.option('--format', '-f', type=click.Choice(['url', 'markdown', 'json']), default='url',
              help='Output format')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def notebook_url(notebook_id: Optional[str], format: str, config: str):
    """Get notebook URL in various formats."""
    from .session_tracker import SessionTracker

    tracker = SessionTracker()
    tracker._load_current_session()

    if not tracker.current_session:
        console.print("❌ No active session found", style="red")
        console.print("💡 Create a notebook first with: deepdiver notebook create", style="yellow")
        return

    # Get notebook
    if notebook_id:
        notebook = tracker.get_notebook_by_id(notebook_id)
    else:
        notebook = tracker.get_active_notebook()

    if not notebook:
        if notebook_id:
            console.print(f"❌ Notebook not found: {notebook_id}", style="red")
        else:
            console.print("❌ No active notebook found", style="red")
        console.print("💡 Available notebooks:", style="yellow")
        notebooks = tracker.list_notebooks()
        for nb in notebooks:
            console.print(f"   • {nb['id']}: {nb['url']}", style="cyan")
        return

    # Format output
    if format == 'url':
        console.print(f"🔗 Notebook URL:", style="bold green")
        console.print(f"{notebook['url']}", style="bold blue")

    elif format == 'markdown':
        console.print("📝 Markdown format:", style="bold green")
        title = notebook.get('title', 'NotebookLM Notebook')
        console.print(f"[{title}]({notebook['url']})", style="cyan")

    elif format == 'json':
        import json
        console.print("📊 JSON format:", style="bold green")
        output = {
            'id': notebook['id'],
            'url': notebook['url'],
            'title': notebook.get('title', 'Untitled Notebook'),
            'created_at': notebook.get('created_at'),
            'sources': notebook.get('sources', [])
        }
        console.print(json.dumps(output, indent=2), style="cyan")


@notebook.command(name='share')
@click.argument('email')
@click.option('--notebook-id', '-n', help='Notebook ID to share (uses active notebook if not specified)')
@click.option('--role', '-r', type=click.Choice(['editor', 'viewer']), default='editor',
              help='Role to grant (editor or viewer)')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def notebook_share(email: str, notebook_id: Optional[str], role: str, config: str):
    """Share notebook with a collaborator by email."""
    console.print(f"👥 Sharing notebook with: {email}", style="blue")
    console.print(f"📝 Role: {role}", style="cyan")

    async def run_share_notebook():
        from .notebooklm_automator import NotebookLMAutomator
        from .session_tracker import SessionTracker

        automator = NotebookLMAutomator(config)
        tracker = SessionTracker()
        tracker._load_current_session()

        try:
            # Get notebook to share
            if notebook_id:
                notebook = tracker.get_notebook_by_id(notebook_id)
            else:
                notebook = tracker.get_active_notebook()

            if not notebook:
                console.print("❌ No notebook found to share", style="red")
                return

            console.print(f"📓 Sharing notebook: {notebook['id']}", style="cyan")

            # Connect and navigate to notebook
            if await automator.connect_to_browser():
                if await automator.navigate_to_notebook(notebook_id=notebook['id']):
                    # Share the notebook
                    if await automator.share_notebook(email=email, role=role):
                        console.print(f"✅ Notebook shared successfully with {email}!", style="green")
                        console.print(f"📧 {email} will receive an invitation email", style="cyan")

                        # Track collaboration in session
                        if tracker.current_session:
                            collaborators = notebook.get('collaborators', [])
                            collaborators.append({'email': email, 'role': role, 'added_at': datetime.now().isoformat()})
                            tracker.update_notebook(notebook['id'], {'collaborators': collaborators})
                    else:
                        console.print(f"❌ Failed to share notebook", style="red")
                        console.print("💡 Make sure the notebook is open and you have permission to share", style="yellow")
                else:
                    console.print("❌ Failed to navigate to notebook", style="red")
        except Exception as e:
            console.print(f"❌ Failed to share notebook: {e}", style="red")
        # Browser stays open - no close() call

    asyncio.run(run_share_notebook())


@notebook.command(name='list')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def notebook_list(config: str):
    """List all notebooks in the current session."""
    from .session_tracker import SessionTracker

    tracker = SessionTracker()
    tracker._load_current_session()

    if not tracker.current_session:
        console.print("❌ No active session found", style="red")
        return

    notebooks = tracker.list_notebooks()

    if not notebooks:
        console.print("📭 No notebooks in this session", style="yellow")
        console.print("💡 Create one with: deepdiver notebook create", style="cyan")
        return

    console.print(f"📚 Notebooks in session ({len(notebooks)} total):", style="bold green")
    active_id = tracker.current_session.get('active_notebook_id')

    for nb in notebooks:
        active_marker = "🟢" if nb['id'] == active_id else "⚪"
        title = nb.get('title', 'Untitled')
        sources_count = len(nb.get('sources', []))
        console.print(f"\n{active_marker} {title}", style="bold cyan")
        console.print(f"   ID: {nb['id']}", style="dim")
        console.print(f"   URL: {nb['url']}", style="blue")
        console.print(f"   Sources: {sources_count}", style="dim")
        console.print(f"   Created: {nb.get('created_at', 'Unknown')}", style="dim")


@notebook.command(name='open')
@click.argument('notebook_id')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def notebook_open(notebook_id: str, config: str):
    """Navigate to an existing notebook."""
    console.print(f"🔄 Opening notebook: {notebook_id}", style="blue")

    async def run_open_notebook():
        from .notebooklm_automator import NotebookLMAutomator
        from .session_tracker import SessionTracker

        automator = NotebookLMAutomator(config)
        tracker = SessionTracker()
        tracker._load_current_session()

        try:
            if await automator.connect_to_browser():
                if await automator.navigate_to_notebook(notebook_id=notebook_id):
                    console.print("✅ Successfully navigated to notebook", style="green")

                    # Set as active in session
                    if tracker.current_session:
                        tracker.set_active_notebook(notebook_id)
                        console.print("💾 Set as active notebook in session", style="cyan")
                    console.print("🔗 Browser kept open for next command", style="dim")
                else:
                    console.print("❌ Failed to navigate to notebook", style="red")
        except Exception as e:
            console.print(f"❌ Failed to open notebook: {e}", style="red")
        # Browser stays open - no close() call

    asyncio.run(run_open_notebook())


@notebook.command(name='add-source')
@click.argument('notebook_id')
@click.argument('source')
@click.option('--name', '-n', help='Custom name for the source')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def notebook_add_source(notebook_id: str, source: str, name: Optional[str], config: str):
    """Add a source to an existing notebook.

    SOURCE can be:
    - SimExp URL: https://app.simplenote.com/p/[NOTE_ID]
    - Web URL: https://example.com/article
    - YouTube URL: https://youtube.com/watch?v=...
    - Local file: ./document.pdf

    Examples:
        deepdiver notebook add-source abc-123 "https://app.simplenote.com/p/xyz"
        deepdiver notebook add-source abc-123 "https://youtube.com/watch?v=xyz"
        deepdiver notebook add-source abc-123 ./research.pdf
    """
    console.print(f"📄 Adding source to notebook: {notebook_id}", style="blue")

    # Detect source type for better messaging
    if source.startswith(('http://', 'https://')):
        console.print(f"🔗 Source URL: {source}", style="cyan")
    else:
        console.print(f"📎 Source file: {source}", style="cyan")

    if name:
        console.print(f"🏷️  Custom name: {name}", style="cyan")

    async def run_add_source():
        from .notebooklm_automator import NotebookLMAutomator
        from .session_tracker import SessionTracker

        automator = NotebookLMAutomator(config)
        tracker = SessionTracker()
        tracker._load_current_session()

        try:
            # Verify notebook exists in session
            notebook = None
            if tracker.current_session:
                notebook = tracker.get_notebook_by_id(notebook_id)
                if not notebook:
                    console.print(f"⚠️  Notebook {notebook_id} not found in session", style="yellow")
                    console.print("💡 The notebook will still be added to if it exists in NotebookLM", style="dim")

            # Connect to browser
            if not await automator.connect_to_browser():
                console.print("❌ Failed to connect to browser", style="red")
                console.print("💡 Make sure Chrome is running with: deepdiver init", style="yellow")
                return

            # Add source to the specified notebook (handles both URLs and files)
            console.print(f"📤 Adding source to notebook...", style="blue")
            result_notebook_id = await automator.add_source(source, notebook_id=notebook_id)

            if result_notebook_id:
                console.print("✅ Source added successfully!", style="green")
                console.print(f"📋 Notebook ID: {result_notebook_id}", style="cyan")

                # Track source in session
                if tracker.current_session:
                    # Determine source type and create metadata
                    if source.startswith(('http://', 'https://')):
                        # URL source
                        source_data = {
                            'filename': name or source,
                            'path': source,
                            'type': 'url',
                            'size': 0  # Unknown for URLs
                        }
                    else:
                        # File source
                        from pathlib import Path
                        source_path = Path(source)
                        source_data = {
                            'filename': name or source_path.name,
                            'path': source,
                            'type': source_path.suffix[1:] if source_path.suffix else 'unknown',
                            'size': source_path.stat().st_size if source_path.exists() else 0
                        }

                    # Add source to notebook in session
                    if tracker.add_source_to_notebook(result_notebook_id, source_data):
                        console.print(f"💾 Source tracked in session", style="green")

                        # Display updated source count
                        sources = tracker.list_notebook_sources(result_notebook_id)
                        console.print(f"📚 Total sources in notebook: {len(sources)}", style="cyan")
                    else:
                        console.print("⚠️  Could not track source in session", style="yellow")

                console.print(f"🔗 Browser kept open for next command", style="dim")
            else:
                console.print("❌ Failed to add source to notebook", style="red")
                console.print("💡 Make sure the notebook ID is correct and you have permission to edit", style="yellow")

        except Exception as e:
            console.print(f"❌ Failed to add source: {e}", style="red")
            import traceback
            console.print(traceback.format_exc(), style="dim")
        # Browser stays open - no close() call

    asyncio.run(run_add_source())


@notebook.command(name='resume')
@click.argument('notebook_id')
@click.option('--source', '-s', 'sources', multiple=True,
              help='Local file that should be in the notebook (repeatable)')
@click.option('--source-dir', type=click.Path(exists=True, file_okay=False),
              help='Upload every file in this directory that is not yet in the notebook')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def notebook_resume(notebook_id: str, sources: tuple, source_dir: Optional[str],
                    cdp_url: str, config: str):
    """Resume an existing notebook: upload only its missing sources.

    Prefer resume over recreate. The session tracker's source list is
    diffed against the given files; already-uploaded names are skipped so
    a partially-completed run continues instead of starting over.

    Examples:
        deepdiver notebook resume abc-123 -s notes.md -s summary.pdf
        deepdiver notebook resume abc-123 --source-dir ./packet/sources
    """
    from .notebooklm_automator import NotebookLMAutomator
    from .session_tracker import SessionTracker

    source_paths = list(sources)
    if source_dir:
        source_paths.extend(sorted(
            str(p) for p in Path(source_dir).iterdir() if p.is_file()
        ))

    if not source_paths:
        console.print("❌ No sources given — use --source or --source-dir", style="red")
        return

    console.print(f"♻️ Resuming notebook: {notebook_id}", style="blue")
    console.print(f"📄 Candidate sources: {len(source_paths)}", style="cyan")

    async def run_resume():
        tracker = SessionTracker()
        tracker.load_current_session()
        automator = NotebookLMAutomator(config, cdp_url_override=cdp_url,
                                        session_tracker=tracker)

        try:
            if not await automator.connect_to_browser():
                console.print("❌ Failed to connect to browser", style="red")
                return

            summary = await automator.resume_notebook(notebook_id, source_paths)

            if summary.get('error'):
                console.print(f"❌ {summary['error']}", style="red")
                return

            console.print(f"✅ Resume complete", style="green")
            console.print(f"   Already present: {len(summary['skipped'])}", style="dim")
            console.print(f"   Uploaded now:    {len(summary['uploaded'])}", style="cyan")
            for name in summary['uploaded']:
                console.print(f"     • {name}", style="cyan")
            if summary['failed']:
                console.print(f"   Failed:          {len(summary['failed'])}", style="red")
                for item in summary['failed']:
                    console.print(f"     • {item['filename']}: {item['error']}", style="red")
            console.print("🔗 Browser kept open for next command", style="dim")
        except Exception as e:
            console.print(f"❌ Resume failed: {e}", style="red")

    asyncio.run(run_resume())


# ═══════════════════════════════════════════════════════════════
# STUDIO COMMANDS
# 🌸 Miette: Commands for giving DeepDiver a voice
# ═══════════════════════════════════════════════════════════════

@cli.group()
def studio():
    """Studio artifact generation commands.

    🎙️ audio       — Audio Overview with full customization (+ --download)
    🖼️ slide-deck  — Presenter/Detailed slide decks
    🎨 generate    — any Studio family (video_overview, mind_map, reports,
                     flashcards, quiz, infographic, data_table, ...)
    📋 list        — artifact cards currently visible in the Studio panel
    ⬇️ download    — download all downloadable artifacts + manifest.json
    """
    pass


@studio.command(name='audio')
@click.option('--format', '-f',
              type=click.Choice(['deep_dive', 'brief', 'critique', 'debate'], case_sensitive=False),
              help='Podcast format (default: deep_dive)')
@click.option('--language', '-l', default='English',
              help='Podcast language (default: English)')
@click.option('--length',
              type=click.Choice(['short', 'default', 'long'], case_sensitive=False),
              help='Podcast length (default: default)')
@click.option('--focus', help='Focus prompt for AI hosts (max 5000 chars)')
@click.option('--notebook-id', '-n', help='Notebook ID (uses current session if not provided)')
@click.option('--download/--no-download', default=False,
              help='Download the generated audio when complete')
@click.option('--output', '-o', default=None,
              help='Output path for downloaded audio (default: STUDIO_SETTINGS artifact dir)')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_audio(format: Optional[str], language: str, length: Optional[str],
                 focus: Optional[str], notebook_id: Optional[str],
                 download: bool, output: Optional[str], cdp_url: str, config: str):
    """Generate Audio Overview with advanced customization.

    🌸 Miette: "This is the ceremony of giving voice to content."

    Formats:
      - deep_dive: Lively, in-depth conversation (default)
      - brief: Concise, bite-sized summary
      - critique: Expert review and analysis
      - debate: Multiple thoughtful perspectives

    Lengths:
      - short: Quick overview (~2-3 minutes)
      - default: Balanced coverage (~5-8 minutes)
      - long: Comprehensive deep dive (~10-15 minutes)

    Examples:
      # Basic generation with defaults
      deepdiver studio audio --notebook-id abc-123

      # Deep dive format, long length
      deepdiver studio audio --format deep_dive --length long

      # Brief summary, short length
      deepdiver studio audio --format brief --length short

      # Critique with custom focus
      deepdiver studio audio --format critique \\
        --focus "Analyze the research methodology and findings"

      # Multilingual
      deepdiver studio audio --language Spanish

      # Full customization
      deepdiver studio audio \\
        --format debate \\
        --language French \\
        --length long \\
        --focus "Present multiple perspectives on the ethical implications" \\
        --notebook-id abc-123
    """
    console.print("🎙️ Generating Audio Overview...", style="blue")

    if format:
        console.print(f"   Format: {format}", style="cyan")
    if language != 'English':
        console.print(f"   Language: {language}", style="cyan")
    if length:
        console.print(f"   Length: {length}", style="cyan")
    if focus:
        preview = focus[:60] + '...' if len(focus) > 60 else focus
        console.print(f"   Focus: {preview}", style="cyan")
    if notebook_id:
        console.print(f"   Notebook: {notebook_id}", style="cyan")

    async def run_audio_generation():
        from .notebooklm_automator import NotebookLMAutomator
        from .session_tracker import SessionTracker

        tracker = SessionTracker()
        tracker.load_current_session()
        automator = NotebookLMAutomator(config, cdp_url_override=cdp_url,
                                        session_tracker=tracker)

        try:
            # Connect to browser
            if not await automator.connect_to_browser():
                console.print("❌ Failed to connect to browser", style="red")
                console.print("💡 Make sure Chrome is running with: deepdiver init", style="yellow")
                return

            # Generate Audio Overview
            console.print("🚀 Starting Audio Overview generation...", style="blue")

            artifact_data = await automator.generate_audio_overview(
                format=format,
                language=language,
                length=length,
                focus_prompt=focus,
                notebook_id=notebook_id
            )

            if artifact_data:
                console.print("✅ Audio Overview generated successfully!", style="green")
                console.print(f"📋 Artifact ID: {artifact_data.get('artifact_id', 'unknown')}", style="cyan")
                console.print(f"🎙️ Format: {artifact_data.get('format', 'unknown')}", style="cyan")
                console.print(f"🌍 Language: {artifact_data.get('language', 'unknown')}", style="cyan")
                console.print(f"📏 Length: {artifact_data.get('length', 'unknown')}", style="cyan")
                console.print(f"⏱️ Generation time: {artifact_data.get('generation_time', 0)}s", style="cyan")
                if artifact_data.get('recovered_after_timeout'):
                    console.print("♻️ Recovered after monitor timeout (artifact card was present)", style="yellow")

                if download:
                    output_path = output
                    if not output_path:
                        artifact_dir = automator.config.get('STUDIO_SETTINGS', {}).get(
                            'artifact_download_dir', './output/artifacts')
                        stamp = datetime.now().strftime('%Y%m%dT%H%M%S')
                        output_path = os.path.join(artifact_dir, f'audio-overview-{stamp}.mp3')

                    console.print(f"⬇️ Downloading audio to: {output_path}", style="blue")
                    saved_path = await automator.download_audio(output_path)
                    if saved_path:
                        size = os.path.getsize(saved_path)
                        console.print(f"✅ Downloaded ({size} bytes): {saved_path}", style="green")
                        if tracker.current_session and notebook_id:
                            tracker.record_artifact_download(notebook_id,
                                                             artifact_data.get('artifact_id'), {
                                'title': artifact_data.get('title'),
                                'path': saved_path,
                                'size': size,
                                'sha256': automator._sha256_file(saved_path),
                                'downloaded_at': datetime.now().isoformat(),
                            })
                    else:
                        console.print("❌ Download failed — artifact remains in NotebookLM", style="red")

                console.print(f"🔗 Browser kept open - artifact ready to load", style="dim")
            else:
                console.print("❌ Failed to generate Audio Overview", style="red")
                console.print("💡 Check logs for details", style="yellow")

        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
            import traceback
            console.print(traceback.format_exc(), style="dim")

    asyncio.run(run_audio_generation())


def _run_studio_generation(artifact_type: str, format: Optional[str], language: Optional[str],
                           length: Optional[str], focus: Optional[str],
                           notebook_id: Optional[str], cdp_url: Optional[str], config: str):
    """Shared runner for non-audio Studio artifact generation commands."""
    from .notebooklm_automator import NotebookLMAutomator
    from .session_tracker import SessionTracker

    async def run_generation():
        tracker = SessionTracker()
        tracker.load_current_session()
        automator = NotebookLMAutomator(config, cdp_url_override=cdp_url,
                                        session_tracker=tracker)

        try:
            if not await automator.connect_to_browser():
                console.print("❌ Failed to connect to browser", style="red")
                console.print("💡 Make sure Chrome is running with: deepdiver init", style="yellow")
                return

            artifact_data = await automator.generate_studio_artifact(
                artifact_type,
                format=format,
                language=language,
                length=length,
                focus_prompt=focus,
                notebook_id=notebook_id,
            )

            if artifact_data:
                console.print(f"✅ Artifact generated successfully!", style="green")
                console.print(f"📋 Artifact ID: {artifact_data.get('artifact_id', 'unknown')}", style="cyan")
                if artifact_data.get('title'):
                    console.print(f"🏷️ Title: {artifact_data['title']}", style="cyan")
                console.print(f"⏱️ Generation time: {artifact_data.get('generation_time', 0)}s", style="cyan")
                if artifact_data.get('recovered_after_timeout'):
                    console.print("♻️ Recovered after monitor timeout (artifact card was present)", style="yellow")
                console.print("💡 A ready artifact can still have a disabled 'Copy link' — that is a", style="dim")
                console.print("   notebook-sharing gate, not a generation failure.", style="dim")
                console.print("🔗 Browser kept open for next command", style="dim")
            else:
                console.print("❌ Artifact generation failed or timed out", style="red")
                console.print("💡 Check 'deepdiver studio list' — the artifact may still exist", style="yellow")

        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")

    asyncio.run(run_generation())


@studio.command(name='slide-deck')
@click.option('--format', '-f',
              type=click.Choice(['presenter', 'detailed'], case_sensitive=False),
              help='presenter = spoken/explanatory deck; detailed = dense leave-behind')
@click.option('--language', '-l', default=None, help='Deck language')
@click.option('--length', type=click.Choice(['short', 'default', 'long'], case_sensitive=False),
              help='Deck length')
@click.option('--focus', help='Free-text deck brief (audience, tone, slide count, emphases)')
@click.option('--notebook-id', '-n', help='Notebook ID (uses current page if not provided)')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_slide_deck(format: Optional[str], language: Optional[str], length: Optional[str],
                      focus: Optional[str], notebook_id: Optional[str],
                      cdp_url: str, config: str):
    """Generate a Slide Deck through the Studio tile.

    🖼️ Presenter Slides for a spoken/explanatory deck, Detailed Deck for a
    denser leave-behind. Tip: upload a short deck-brief source first so the
    deck knows its audience.

    Example:
        deepdiver studio slide-deck --format presenter \\
          --focus "Explain the bridge architecture for new operators" -n abc-123
    """
    console.print("🖼️ Generating Slide Deck...", style="blue")
    _run_studio_generation('slide_deck', format, language, length, focus,
                           notebook_id, cdp_url, config)


@studio.command(name='generate')
@click.argument('artifact_type')
@click.option('--format', '-f', help='Family-specific format when supported')
@click.option('--language', '-l', default=None, help='Output language')
@click.option('--length', help='Length option when supported')
@click.option('--focus', help='Free-text prompt when supported')
@click.option('--notebook-id', '-n', help='Notebook ID (uses current page if not provided)')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_generate(artifact_type: str, format: Optional[str], language: Optional[str],
                    length: Optional[str], focus: Optional[str], notebook_id: Optional[str],
                    cdp_url: str, config: str):
    """Generate any Studio artifact family by name.

    ARTIFACT_TYPE is one of: audio_overview, slide_deck, video_overview,
    mind_map, reports, flashcards, quiz, infographic, data_table
    (display labels like "Slide Deck" also work).

    Examples:
        deepdiver studio generate mind_map -n abc-123
        deepdiver studio generate quiz --focus "Focus on chapter 3" -n abc-123
        deepdiver studio generate video_overview --language French -n abc-123
    """
    if normalize_artifact_type(artifact_type) is None:
        console.print(f"❌ Unknown artifact type: {artifact_type}", style="red")
        console.print(f"💡 Known types: {', '.join(list_artifact_type_keys())}", style="yellow")
        return

    console.print(f"🎨 Generating Studio artifact: {artifact_type}", style="blue")
    _run_studio_generation(artifact_type, format, language, length, focus,
                           notebook_id, cdp_url, config)


@studio.command(name='list')
@click.option('--notebook-id', '-n', help='Notebook ID (uses current page if not provided)')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_list(notebook_id: Optional[str], cdp_url: str, config: str):
    """List artifact cards currently visible in the Studio panel."""
    from .notebooklm_automator import NotebookLMAutomator

    console.print("📋 Listing Studio artifacts...", style="blue")

    async def run_list():
        automator = NotebookLMAutomator(config, cdp_url_override=cdp_url)

        try:
            if not await automator.connect_to_browser():
                console.print("❌ Failed to connect to browser", style="red")
                return

            if notebook_id:
                if not await automator.navigate_to_notebook(notebook_id=notebook_id):
                    console.print("❌ Failed to navigate to notebook", style="red")
                    return
                await automator.dismiss_rebrand_modal()

            artifacts = await automator.list_studio_artifacts()
            if not artifacts:
                console.print("📭 No artifact cards visible in the Studio panel", style="yellow")
                return

            console.print(f"📦 {len(artifacts)} artifact(s):", style="bold green")
            for artifact in artifacts:
                family = artifact.get('family_label') or 'Unknown family'
                title = artifact.get('title') or 'Untitled'
                playable = '▶️ downloadable' if artifact.get('playable') else '—'
                console.print(f"  • [{family}] {title} {playable}", style="cyan")
                if artifact.get('details'):
                    console.print(f"      {artifact['details']}", style="dim")
            console.print("🔗 Browser kept open for next command", style="dim")
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")

    asyncio.run(run_list())


@studio.command(name='download')
@click.option('--notebook-id', '-n', help='Notebook ID (uses current page if not provided)')
@click.option('--output', '-o', default=None,
              help='Output directory (default: STUDIO_SETTINGS.artifact_download_dir)')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_download(notebook_id: Optional[str], output: Optional[str],
                    cdp_url: str, config: str):
    """Download all downloadable artifacts + write manifest.json.

    ⬇️ The end-of-run export: every downloadable artifact lands in the
    output directory with a manifest.json (title, path, sha256, size, media
    probe) — ready to ship to other devices.

    Example:
        deepdiver studio download -n abc-123 -o ./output/artifacts/run-42
    """
    from .notebooklm_automator import NotebookLMAutomator
    from .session_tracker import SessionTracker

    console.print("⬇️ Downloading Studio artifacts...", style="blue")

    async def run_download():
        tracker = SessionTracker()
        tracker.load_current_session()
        automator = NotebookLMAutomator(config, cdp_url_override=cdp_url,
                                        session_tracker=tracker)

        try:
            if not await automator.connect_to_browser():
                console.print("❌ Failed to connect to browser", style="red")
                return

            output_dir = output
            if not output_dir:
                base = automator.config.get('STUDIO_SETTINGS', {}).get(
                    'artifact_download_dir', './output/artifacts')
                stamp = datetime.now().strftime('%Y%m%dT%H%M%S')
                output_dir = os.path.join(base, stamp)

            manifest = await automator.download_all_artifacts(output_dir, notebook_id=notebook_id)

            if manifest.get('error'):
                console.print(f"❌ {manifest['error']}", style="red")
                return

            console.print(f"✅ Downloaded {len(manifest['downloads'])} artifact(s)", style="green")
            for entry in manifest['downloads']:
                size_mb = entry['size'] / (1024 * 1024)
                console.print(f"  • {entry['title']} → {entry['path']} ({size_mb:.1f} MB)", style="cyan")
            if manifest['skipped']:
                console.print(f"⏭️ Skipped {len(manifest['skipped'])}:", style="yellow")
                for item in manifest['skipped']:
                    console.print(f"  • {item['title']}: {item['reason']}", style="dim")
            if manifest.get('manifest_path'):
                console.print(f"🗂️ Manifest: {manifest['manifest_path']}", style="bold blue")
            console.print("🔗 Browser kept open for next command", style="dim")
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")

    asyncio.run(run_download())


# ═══════════════════════════════════════════════════════════════
# CHROME COMMANDS
# 🧵 Synth: Browser lifecycle with profile-clone support
# ═══════════════════════════════════════════════════════════════

@cli.group()
def chrome():
    """Chrome browser lifecycle commands."""
    pass


@chrome.command(name='launch')
@click.option('--port', default=9222, help='CDP port (default: 9222)')
@click.option('--user-data-dir', default=None, help='Chrome user data directory')
@click.option('--clone-profile', default=None,
              help='Clone this authenticated profile (e.g. "Profile 3") into a '
                   'disposable user-data-dir so the live profile is never touched')
@click.option('--profile-root', default=None,
              help='Chrome config root for cloning (default: ~/.config/google-chrome)')
@click.option('--display', default=None,
              help='X display (default: $DISPLAY or :0 — needed from SSH/tmux)')
def chrome_launch(port: int, user_data_dir: Optional[str], clone_profile: Optional[str],
                  profile_root: Optional[str], display: Optional[str]):
    """Launch Chrome with CDP enabled (SSH/tmux-safe).

    Passes DISPLAY/XAUTHORITY through so launching from a non-interactive
    SSH or tmux context works, binds the debug port to 127.0.0.1, and can
    clone an authenticated profile instead of touching the live one.

    Examples:
        deepdiver chrome launch
        deepdiver chrome launch --clone-profile "Profile 3"
        deepdiver chrome launch --port 9223 --display :0
    """
    console.print(f"🚀 Launching Chrome with CDP on port {port}...", style="blue")
    if clone_profile:
        console.print(f"👤 Cloning profile: {clone_profile}", style="cyan")

    if launch_chrome_cdp(port=port, user_data_dir=user_data_dir,
                         clone_from_profile=clone_profile,
                         profile_root=profile_root, display=display):
        console.print(f"✅ Chrome launched — CDP live at http://127.0.0.1:{port}", style="green")
        console.print("💡 Log in to NotebookLM in the Chrome window, then: deepdiver test", style="yellow")
    else:
        console.print("❌ Chrome launch failed or CDP did not come up", style="red")
        console.print("💡 From SSH/tmux, X env is required: try --display :0", style="yellow")


# ═══════════════════════════════════════════════════════════════
# SKILLS COMMANDS
# ♠️ Nyro: The package carries its own operating knowledge
# ═══════════════════════════════════════════════════════════════

@cli.group()
def skills():
    """Agent skills bundled with DeepDiver.

    DeepDiver ships SKILL.md operating manuals inside the package so agents
    can discover them and install them into their own skill directories.
    """
    pass


@skills.command(name='list')
def skills_list():
    """List skills bundled inside this DeepDiver installation."""
    from .skills_manager import list_bundled_skills, AGENT_TARGETS

    bundled = list_bundled_skills()
    if not bundled:
        console.print("📭 No skills bundled in this installation", style="yellow")
        return

    console.print(f"📚 Bundled skills ({len(bundled)}):", style="bold green")
    for skill in bundled:
        console.print(f"\n  🎓 {skill['name']}", style="bold cyan")
        if skill['description']:
            console.print(f"     {skill['description']}", style="dim")
        console.print(f"     Files: {', '.join(skill['files'])}", style="dim")

    console.print("\n💡 Install into your agent:", style="yellow")
    for agent, path in AGENT_TARGETS.items():
        console.print(f"   deepdiver skills install --agent {agent}   →  {path}", style="cyan")
    console.print("   deepdiver skills install --to <dir>", style="cyan")


@skills.command(name='show')
@click.argument('name')
def skills_show(name: str):
    """Print a bundled skill's SKILL.md content."""
    from .skills_manager import get_bundled_skill

    skill = get_bundled_skill(name)
    if not skill:
        console.print(f"❌ No bundled skill named: {name}", style="red")
        console.print("💡 See available skills with: deepdiver skills list", style="yellow")
        return

    skill_md = Path(skill['path']) / 'SKILL.md'
    console.print(skill_md.read_text(encoding='utf-8'))


@skills.command(name='install')
@click.argument('name', required=False)
@click.option('--agent', type=click.Choice(['claude', 'claude-project', 'hermes', 'codex']),
              help='Install into a known agent skill directory')
@click.option('--to', 'target_dir', default=None,
              help='Install into an explicit skills directory')
@click.option('--force', is_flag=True, default=False,
              help='Overwrite an already-installed copy')
def skills_install(name: Optional[str], agent: Optional[str],
                   target_dir: Optional[str], force: bool):
    """Install bundled skill(s) into an agent's skill directory.

    With NAME, installs that one skill; without it, installs all bundled
    skills. Target comes from --agent (claude, claude-project, hermes,
    codex) or an explicit --to directory.

    Examples:
        deepdiver skills install --agent claude
        deepdiver skills install notebooklm-automation --to ~/.hermes/skills/development
    """
    from .skills_manager import (
        install_skill, install_all_skills, resolve_install_target,
    )

    target = resolve_install_target(agent=agent, target_dir=target_dir)
    if target is None:
        console.print("❌ No install target — use --agent or --to", style="red")
        return

    console.print(f"📦 Installing into: {target}", style="blue")

    if name:
        results = [install_skill(name, target, force=force)]
    else:
        results = install_all_skills(target, force=force)

    for result in results:
        if result.get('installed'):
            console.print(f"✅ {result['name']} → {result['destination']}", style="green")
        elif result.get('skipped'):
            console.print(f"⏭️ {result['name']}: {result['skipped']}", style="yellow")
        else:
            console.print(f"❌ {result['name']}: {result.get('error')}", style="red")


def main():
    """Main entry point for DeepDiver CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n👋 DeepDiver session interrupted", style="yellow")
    except Exception as e:
        console.print(f"❌ DeepDiver error: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    main()
