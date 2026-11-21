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
    check_signed_in,
    describe_attach_timeout,
    find_keyring_prompt,
    adopt_user_data_dir,
    DEFAULT_USER_DATA_DIR,
    get_cdp_url,
    find_config_file
)
from .studio_artifacts import (
    ARTIFACT_TYPES,
    get_artifact_spec,
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
@click.argument('sources', nargs=-1, required=True)
@click.option('--name', '-n', help='Custom name for the source (one source only)')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def notebook_add_source(notebook_id: str, sources: tuple, name: Optional[str], config: str):
    """Add one or more sources to an existing notebook.

    Each SOURCE can be:
    - SimExp URL: https://app.simplenote.com/p/[NOTE_ID]
    - Web URL: https://example.com/article
    - YouTube URL: https://youtube.com/watch?v=... (public videos; the transcript is imported)
    - Local file: ./document.pdf

    All URLs go into the notebook in one insert; files are uploaded one by
    one. Exits 1 if any source could not be added.

    Examples:
        deepdiver notebook add-source abc-123 "https://youtube.com/watch?v=xyz"
        deepdiver notebook add-source abc-123 ./review-a.md ./review-b.md https://youtu.be/a https://youtu.be/b
    """
    if name and len(sources) > 1:
        console.print("❌ --name applies to a single source", style="red")
        sys.exit(2)
    urls = [s for s in sources if s.startswith(('http://', 'https://'))]
    files = [s for s in sources if not s.startswith(('http://', 'https://'))]
    console.print(f"📄 Adding {len(sources)} source(s) to notebook: {notebook_id}", style="blue")

    def source_record(source: str) -> dict:
        if source.startswith(('http://', 'https://')):
            return {'filename': name or source, 'path': source, 'type': 'url', 'size': 0}
        from pathlib import Path
        source_path = Path(source)
        return {
            'filename': name or source_path.name,
            'path': source,
            'type': source_path.suffix[1:] if source_path.suffix else 'unknown',
            'size': source_path.stat().st_size if source_path.exists() else 0,
        }

    async def run_add_source():
        from .notebooklm_automator import NotebookLMAutomator
        from .session_tracker import SessionTracker

        automator = NotebookLMAutomator(config)
        tracker = SessionTracker()
        tracker._load_current_session()
        failed = []

        try:
            if tracker.current_session and not tracker.get_notebook_by_id(notebook_id):
                console.print(f"⚠️  Notebook {notebook_id} not found in session", style="yellow")

            if not await automator.connect_to_browser():
                console.print("❌ Failed to connect to browser", style="red")
                console.print("💡 Make sure Chrome is running with: deepdiver init", style="yellow")
                return False

            batches = ([('\n'.join(urls), urls)] if urls else []) + [(f, [f]) for f in files]
            for payload, members in batches:
                console.print(f"📤 Adding: {', '.join(members)}", style="blue")
                if payload in files:
                    result_id = await automator.add_source(payload, notebook_id=notebook_id)
                else:
                    result_id = await automator.add_url_source(payload, notebook_id=notebook_id)
                not_imported = {e['title']: e['reason'] for e in automator.last_source_errors}
                automator.last_source_errors = []
                for member in members:
                    if member in not_imported:
                        console.print(f"❌ Not imported: {member} — {not_imported[member]}", style="red")
                if not result_id:
                    if not not_imported:
                        console.print(f"❌ Not added: {', '.join(members)}", style="red")
                    failed.extend(members)
                    continue
                failed.extend(m for m in members if m in not_imported)
                if tracker.current_session:
                    for member in members:
                        if member not in not_imported:
                            tracker.add_source_to_notebook(result_id, source_record(member))

            added = len(sources) - len(failed)
            console.print(f"✅ {added} of {len(sources)} source(s) added", style="green" if not failed else "yellow")
            if tracker.current_session:
                console.print(f"📚 Sources tracked for this notebook: "
                              f"{len(tracker.list_notebook_sources(notebook_id))}", style="cyan")
            console.print(f"🔗 Browser kept open for next command", style="dim")
            return not failed

        except Exception as e:
            console.print(f"❌ Failed to add source: {e}", style="red")
            return False

    if not asyncio.run(run_add_source()):
        sys.exit(1)


@notebook.command(name='remove-source')
@click.argument('notebook_id')
@click.argument('sources', nargs=-1, required=True)
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def notebook_remove_source(notebook_id: str, sources: tuple, cdp_url: str, config: str):
    """Remove sources from a notebook, by title or by the source id DeepDiver recorded.

    A source is named by its title as the Sources panel shows it (a file's name,
    a URL), or by the source_id the session tracker gave it when DeepDiver added
    it. A title that matches several sources is refused and nothing is removed.
    Exits 1 when any named source was not removed.

    Example (a revised source replaces its old copy):
        deepdiver notebook remove-source abc-123 spec-v1.md
        deepdiver notebook add-source abc-123 ./spec-v2.md
    """
    from .notebooklm_automator import NotebookLMAutomator
    from .session_tracker import SessionTracker

    async def run_remove():
        tracker = SessionTracker()
        tracker._load_current_session()
        automator = NotebookLMAutomator(config, cdp_url_override=cdp_url)
        if not await automator.connect_to_browser():
            console.print("❌ Failed to connect to browser", style="red")
            return False
        failed = []
        for ref in sources:
            tracked = tracker.find_source(notebook_id, ref) if tracker.current_session else None
            title = (tracked or {}).get('filename') or ref
            if tracked and tracked.get('type') == 'url':
                title = tracked.get('path') or title
            result = await automator.remove_source(title, notebook_id=notebook_id)
            if result['removed']:
                console.print(f"🗑️ Removed: {result['title']}", style="green")
                if tracker.current_session:
                    tracker.remove_source_from_notebook(notebook_id, (tracked or {}).get('source_id') or ref)
            else:
                console.print(f"❌ Not removed: {ref}: {result['reason']}", style="red")
                failed.append(ref)
        console.print(f"✅ {len(sources) - len(failed)} of {len(sources)} source(s) removed",
                      style="green" if not failed else "yellow")
        return not failed

    if not asyncio.run(run_remove()):
        sys.exit(1)


@notebook.command(name='ask')
@click.argument('notebook_id')
@click.argument('question')
@click.option('--output', '-o', help='Append the question and answer to this Markdown file')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def notebook_ask(notebook_id: str, question: str, output: Optional[str], cdp_url: str, config: str):
    """Ask a notebook's chat a question and print the answer as Markdown.

    The answer keeps the notebook's citations as [n]. With --output, the
    question and answer are appended to a Markdown file, so a set of
    questions put to a notebook becomes one record.

    Example:
        deepdiver notebook ask abc-123 "Which corrections did the person speak aloud?" -o asked.md
    """
    from .notebooklm_automator import NotebookLMAutomator

    async def run_ask():
        automator = NotebookLMAutomator(config, cdp_url_override=cdp_url)
        if not await automator.connect_to_browser():
            console.print("❌ Failed to connect to browser", style="red")
            return False
        result = await automator.ask_notebook(question, notebook_id=notebook_id)
        if not result:
            console.print("❌ No answer", style="red")
            return False
        console.print(result['answer'])
        if output:
            os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
            with open(output, 'a', encoding='utf-8') as f:
                f.write(f"## {question}\n\n_Asked {result['asked_at']} in notebook "
                        f"{notebook_id}_\n\n{result['answer']}\n\n")
            console.print(f"📝 Appended to {output}", style="dim")
        return True

    if not asyncio.run(run_ask()):
        sys.exit(1)


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
                    saved_path = await automator.download_audio(output_path, artifact=artifact_data)
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


def _seeded_focus(focus: Optional[str], review: bool, from_outline: Optional[str],
                  feedback_file: Optional[str]):
    """The prompt and review flag for a run, seeded when it starts from a kept outline.

    A seeded run stops at its own plan: that plan is the next version.
    """
    if feedback_file and not from_outline:
        console.print("❌ --feedback goes with --from-outline; on a paused card use studio proceed -i", style="red")
        sys.exit(2)
    if not from_outline:
        return focus, review
    from .outline import compose_seed

    feedback = Path(feedback_file).read_text(encoding='utf-8') if feedback_file else None
    return compose_seed(from_outline, focus, feedback), True


def _run_studio_generation(artifact_type: str, format: Optional[str], language: Optional[str],
                           length: Optional[str], focus: Optional[str],
                           notebook_id: Optional[str], cdp_url: Optional[str], config: str,
                           template: Optional[str] = None, review: bool = False):
    """Shared runner for non-audio Studio artifact generation commands.

    Exits 1 when nothing was generated, so agents running the binary can
    trust the exit status.
    """
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
                return False

            artifact_data = await automator.generate_studio_artifact(
                artifact_type,
                format=format,
                language=language,
                length=length,
                focus_prompt=focus,
                notebook_id=notebook_id,
                template=template,
                review=review,
            )

            if artifact_data and artifact_data.get('status') == 'awaiting_review':
                card = artifact_data.get('artifact_id', 'unknown')
                console.print("⏸️ Plan ready, nothing rendered yet", style="green")
                console.print(f"📋 Artifact ID: {card}", style="cyan")
                console.print(f"⏱️ Took {artifact_data.get('generation_time', 0)}s", style="cyan")
                console.print(f"   Save it:  deepdiver studio outline {card} -n <id> -o <dir>", style="dim")
                console.print(f"   Render:   deepdiver studio proceed {card} -n <id> -o <dir> [-i feedback.md]", style="dim")
                return True
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
                return True
            console.print("❌ Artifact generation failed or timed out", style="red")
            console.print("💡 Check 'deepdiver studio list' — the artifact may still exist", style="yellow")
            return False

        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
            return False

    if not asyncio.run(run_generation()):
        sys.exit(1)


@studio.command(name='slide-deck')
@click.option('--format', '-f',
              type=click.Choice(['presenter', 'detailed'], case_sensitive=False),
              help='presenter = spoken/explanatory deck; detailed = dense leave-behind')
@click.option('--language', '-l', default=None, help='Deck language')
@click.option('--length', type=click.Choice(['short', 'default', 'long'], case_sensitive=False),
              help='Deck length')
@click.option('--focus', help='Free-text deck brief (audience, tone, slide count, emphases)')
@click.option('--review', is_flag=True, default=False,
              help='Stop at the slide outline instead of rendering (see studio outline, studio proceed)')
@click.option('--from-outline', type=click.Path(exists=True, dir_okay=False),
              help='Seed the description from a kept outline; implies --review')
@click.option('--feedback', 'feedback_file', type=click.Path(exists=True, dir_okay=False),
              help='With --from-outline: a file of changes to make to that outline')
@click.option('--notebook-id', '-n', help='Notebook ID (uses current page if not provided)')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_slide_deck(format: Optional[str], language: Optional[str], length: Optional[str],
                      focus: Optional[str], review: bool, from_outline: Optional[str],
                      feedback_file: Optional[str], notebook_id: Optional[str],
                      cdp_url: str, config: str):
    """Generate a Slide Deck through the Studio tile.

    🖼️ Presenter Slides for a spoken/explanatory deck, Detailed Deck for a
    denser leave-behind. Tip: upload a short deck-brief source first so the
    deck knows its audience.

    Example:
        deepdiver studio slide-deck --format presenter \\
          --focus "Explain the bridge architecture for new operators" -n abc-123
        deepdiver studio slide-deck --review --focus "..." -n abc-123
    """
    console.print("🖼️ Generating Slide Deck...", style="blue")
    focus, review = _seeded_focus(focus, review, from_outline, feedback_file)
    _run_studio_generation('slide_deck', format, language, length, focus,
                           notebook_id, cdp_url, config, review=review)


@studio.command(name='generate')
@click.argument('artifact_type')
@click.option('--format', '-f', help='Family-specific format when supported')
@click.option('--language', '-l', default=None, help='Output language')
@click.option('--length', help='Length option when supported')
@click.option('--focus', help='Free-text prompt when supported')
@click.option('--template', '-t', help='Reports only: template name (see `studio report --help`)')
@click.option('--review', is_flag=True, default=False,
              help='Slide Deck and Video Overview: stop at the plan instead of rendering (see studio outline, studio proceed)')
@click.option('--from-outline', type=click.Path(exists=True, dir_okay=False),
              help='Seed the prompt from a kept outline; implies --review')
@click.option('--feedback', 'feedback_file', type=click.Path(exists=True, dir_okay=False),
              help='With --from-outline: a file of changes to make to that outline')
@click.option('--notebook-id', '-n', help='Notebook ID (uses current page if not provided)')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_generate(artifact_type: str, format: Optional[str], language: Optional[str],
                    length: Optional[str], focus: Optional[str], template: Optional[str],
                    review: bool, from_outline: Optional[str], feedback_file: Optional[str],
                    notebook_id: Optional[str], cdp_url: str, config: str):
    """Generate any Studio artifact family by name.

    ARTIFACT_TYPE is one of: audio_overview, slide_deck, video_overview,
    mind_map, reports, flashcards, quiz, infographic, data_table
    (display labels like "Slide Deck" also work).

    Examples:
        deepdiver studio generate mind_map -n abc-123
        deepdiver studio generate quiz --focus "Focus on chapter 3" -n abc-123
        deepdiver studio generate video_overview --language French -n abc-123
        deepdiver studio generate video_overview --review --focus "..." -n abc-123
    """
    if normalize_artifact_type(artifact_type) is None:
        console.print(f"❌ Unknown artifact type: {artifact_type}", style="red")
        console.print(f"💡 Known types: {', '.join(list_artifact_type_keys())}", style="yellow")
        return

    console.print(f"🎨 Generating Studio artifact: {artifact_type}", style="blue")
    focus, review = _seeded_focus(focus, review, from_outline, feedback_file)
    _run_studio_generation(artifact_type, format, language, length, focus,
                           notebook_id, cdp_url, config, template=template, review=review)


@studio.command(name='report')
@click.option('--format', '-f', type=click.Choice(['interactive', 'document'], case_sensitive=False),
              default='interactive', show_default=True,
              help='interactive = report with embedded studio content; document = text only')
@click.option('--template', '-t',
              help='Learning Overview (interactive); Create Your Own, Briefing Doc, Study Guide, '
                   'Blog Post, or a suggested template title (document)')
@click.option('--prompt', '-p', 'prompt', help='Describe the report you want (Customize Report)')
@click.option('--language', '-l', default=None, help='Report language')
@click.option('--notebook-id', '-n', help='Notebook ID (uses current page if not provided)')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_report(format: str, template: Optional[str], prompt: Optional[str],
                  language: Optional[str], notebook_id: Optional[str], cdp_url: str, config: str):
    """Generate a Report through the "Create report" dialog.

    Interactive reports embed the notebook's other studio items, which makes
    them a page to walk through on screen. The prompt can say which items to
    include ("include only the infographic and the audio overview") or which
    source to follow.

    Examples:
        deepdiver studio report --prompt "Walk through the screenwalk's handoff to Mia" -n abc-123
        deepdiver studio report --format document --template "Briefing Doc" -n abc-123
        deepdiver studio report --format document --prompt "A one-page spec of the pipeline" -n abc-123
    """
    console.print(f"📑 Generating {format} report...", style="blue")
    _run_studio_generation('reports', format, language, None, prompt,
                           notebook_id, cdp_url, config, template=template)


@studio.command(name='open')
@click.option('--title', '-t', help='Open the card with this title (or a title starting with it)')
@click.option('--family', '-f', help='Without --title: open the newest card of this family')
@click.option('--play', is_flag=True, help='Audio/Video Overview: start playback instead of opening the viewer')
@click.option('--notebook-id', '-n', help='Notebook ID (uses current page if not provided)')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_open(title: Optional[str], family: Optional[str], play: bool,
                notebook_id: Optional[str], cdp_url: str, config: str):
    """Open (or play) a Studio artifact on screen and leave it there.

    For a screenwalk: an Interactive report opens full-screen with its table
    of contents and embedded studio items; --play starts an Audio or Video
    Overview so it can be paused and talked over.

    Examples:
        deepdiver studio open --family reports -n abc-123
        deepdiver studio open --title "Screenwalk to Studio Media" -n abc-123
        deepdiver studio open --family video_overview --play -n abc-123
    """
    from .notebooklm_automator import NotebookLMAutomator
    from .studio_artifacts import ARTIFACT_CARD_SELECTOR

    if not title and not family:
        console.print("❌ Give --title or --family", style="red")
        sys.exit(2)

    async def run_open():
        automator = NotebookLMAutomator(config, cdp_url_override=cdp_url)
        if not await automator.connect_to_browser():
            console.print("❌ Failed to connect to browser", style="red")
            return False
        if notebook_id and not await automator.navigate_to_notebook(notebook_id=notebook_id):
            return False
        card = None
        if title:
            for candidate in await automator.page.query_selector_all(ARTIFACT_CARD_SELECTOR):
                title_el = await candidate.query_selector('.artifact-title')
                text = (await title_el.inner_text()).strip() if title_el else ''
                if text == title.strip() or text.startswith(title.strip()):
                    card = candidate
                    break
        else:
            spec = get_artifact_spec(family)
            if not spec:
                console.print(f"❌ Unknown family: {family}", style="red")
                return False
            card = await automator._find_artifact_card(spec['label'])
        if not card:
            console.print("❌ No matching artifact card", style="red")
            return False
        if not await automator.open_artifact_card(card, play=play):
            console.print("❌ The card could not be opened", style="red")
            return False
        console.print("✅ Opened" + (" and playing" if play else ""), style="green")
        return True

    if not asyncio.run(run_open()):
        sys.exit(1)


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
                spec = get_artifact_spec(family)
                marks = []
                if artifact.get('awaiting_review'):
                    marks.append(f"⏸️ waiting for review · {artifact.get('artifact_id')}")
                elif artifact.get('generating'):
                    marks.append('⏳ generating')
                else:
                    if artifact.get('playable'):
                        marks.append('▶️ playable')
                    if spec and spec.get('downloadable'):
                        marks.append('⬇️ downloadable')
                console.print(f"  • [{family}] {title} {' · '.join(marks) or '—'}", style="cyan")
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
@click.option('--keep', 'keep', is_flag=True, default=False,
              help='Also make what a git repository keeps: infographics as WebP, '
                   'video and audio re-encoded into keep/ with their transcripts, recorded as "kept" in the manifest')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_download(notebook_id: Optional[str], output: Optional[str], keep: bool,
                    cdp_url: str, config: str):
    """Download all downloadable artifacts + write manifest.json.

    ⬇️ The end-of-run export: every downloadable artifact lands in the
    output directory with a manifest.json (title, path, sha256, size, media
    probe) — ready to ship to other devices. A folder that already has a
    manifest.json gets only the cards it does not hold yet.

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
                return False

            output_dir = output
            if not output_dir:
                base = automator.config.get('STUDIO_SETTINGS', {}).get(
                    'artifact_download_dir', './output/artifacts')
                stamp = datetime.now().strftime('%Y%m%dT%H%M%S')
                output_dir = os.path.join(base, stamp)

            manifest = await automator.download_all_artifacts(output_dir, notebook_id=notebook_id)

            if manifest.get('error'):
                console.print(f"❌ {manifest['error']}", style="red")
                return False

            fresh = manifest.get('fresh', manifest['downloads'])
            console.print(f"✅ Downloaded {len(fresh)} new artifact(s)", style="green")
            if manifest.get('already'):
                console.print(f"📁 Already in this folder: {len(manifest['already'])}", style="dim")
            for entry in fresh:
                size_mb = entry['size'] / (1024 * 1024)
                console.print(f"  • {entry['title']} → {entry['path']} ({size_mb:.1f} MB)", style="cyan")
            if manifest['skipped']:
                console.print(f"⏭️ Not downloadable {len(manifest['skipped'])}:", style="yellow")
                for item in manifest['skipped']:
                    console.print(f"  • {item['title']}: {item['reason']}", style="dim")
            if manifest.get('failed'):
                console.print(f"❌ Failed {len(manifest['failed'])}:", style="red")
                for item in manifest['failed']:
                    console.print(f"  • {item['title']}: {item['reason']}", style="red")
            if manifest.get('manifest_path'):
                console.print(f"🗂️ Manifest: {manifest['manifest_path']}", style="bold blue")
            console.print("🔗 Browser kept open for next command", style="dim")
            if keep and manifest.get('manifest_path'):
                if not _print_kept(os.path.dirname(manifest['manifest_path'])):
                    return False
            return not manifest.get('failed')
        except Exception as e:
            console.print(f"❌ Error: {e}", style="red")
            return False

    if not asyncio.run(run_download()):
        sys.exit(1)


def _print_kept(folder: str, transcripts: bool = True) -> bool:
    """Run the keep step on a download folder and print what it kept."""
    from .keep import keep_folder
    console.print("📦 Keeping for git: WebP, keep/ re-encodes" + (", transcripts..." if transcripts else "..."),
                  style="blue")
    manifest = keep_folder(folder, transcripts=transcripts)
    ok = True
    for entry in manifest.get('downloads', []):
        if entry.get('kept'):
            kept = entry['kept']
            console.print(f"  • {entry['title']} → {kept['path']} ({kept['size'] / (1024 * 1024):.1f} MB)",
                          style="cyan")
            if kept.get('transcript'):
                console.print(f"      transcript → {kept['transcript']['path']}", style="dim")
            elif kept.get('transcript_error'):
                ok = False
                console.print(f"      no transcript: {kept['transcript_error']}", style="red")
        else:
            ok = False
            console.print(f"  • {entry['title']}: not kept, {entry.get('kept_error', 'unknown')}", style="red")
    return ok


@studio.command(name='iterate')
@click.argument('artifact')
@click.option('--instruction', '-i', 'instruction_file', required=True, type=click.Path(exists=True, dir_okay=False),
              help='File holding the new prompt for this version')
@click.option('--notebook-id', '-n', help='Notebook ID (uses current page if not provided)')
@click.option('--dry-run', is_flag=True, default=False,
              help="Fill the card's Iterate dialog, read it back and close it without generating")
@click.option('--review', is_flag=True, default=False,
              help='Stop the new version at its plan instead of rendering it')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_iterate(artifact: str, instruction_file: str, notebook_id: Optional[str], dry_run: bool,
                   review: bool, cdp_url: str, config: str):
    """Make a new version of an artifact from its own prompt, revised.

    ARTIFACT is the card's artifact id or exact title. Where the card's
    "View prompt and sources" dialog offers Iterate (Video Overviews do), its
    Customize dialog is filled with the instruction file and generated, so
    the new version keeps the card's format and sources. Otherwise the card's
    family is generated afresh with the instruction as its prompt.

    Example:
        deepdiver studio iterate "Session Continuity" -n abc-123 -i explainer-v3.md
        deepdiver studio iterate 919ca278-1dfd-43c8-a544-d0a834449d09 -n abc-123 -i v3.md --dry-run
    """
    from .notebooklm_automator import NotebookLMAutomator
    from .session_tracker import SessionTracker

    instruction = Path(instruction_file).read_text(encoding='utf-8').strip()
    if not instruction:
        console.print(f"❌ {instruction_file} is empty", style="red")
        sys.exit(1)

    async def run_iterate():
        tracker = SessionTracker()
        tracker.load_current_session()
        automator = NotebookLMAutomator(config, cdp_url_override=cdp_url, session_tracker=tracker)
        if not await automator.connect_to_browser():
            console.print("❌ Failed to connect to browser", style="red")
            return False
        result = await automator.iterate_studio_artifact(artifact, instruction, notebook_id=notebook_id,
                                                         dry_run=dry_run, review=review)
        if not result:
            return False
        origin = result['iterated_from']
        console.print(f"🔁 From: [{origin.get('family_label')}] {origin.get('title')} ({origin.get('artifact_id')})",
                      style="cyan")
        if result.get('dry_run'):
            if result['mode'] == 'iterate':
                console.print("✅ Iterate dialog filled and closed, nothing generated", style="green")
                console.print(f"   was: {result['previous_prompt'][:160]}", style="dim")
                console.print(f"   now: {result['filled'][:160]}", style="dim")
            else:
                console.print(f"ℹ️ {result['reason']} (dry run: nothing generated)", style="yellow")
            return True
        console.print(f"✅ New version ({result['mode']}): {result.get('title')} · {result.get('artifact_id')}",
                      style="green")
        return True

    if not asyncio.run(run_iterate()):
        sys.exit(1)


def _print_plan(plan: dict) -> None:
    console.print(f"[{plan.get('step') or 'Plan'}] {plan.get('title') or ''}", style="bold")
    for number, item in enumerate(plan.get('items') or [], 1):
        console.print(f"  {number}. {item}", markup=False)
    if not plan.get('items'):
        console.print(plan.get('text') or '', markup=False)


@studio.command(name='outline')
@click.argument('artifact', required=False)
@click.option('--output', '-o', required=True, help="Folder that keeps the plan, beside the notebook's media")
@click.option('--seeded-from', help='The kept plan this run was seeded from, so the wheel can link the two versions')
@click.option('--notebook-id', '-n', help='Notebook ID (uses current page if not provided)')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_outline(artifact: Optional[str], output: str, seeded_from: Optional[str], notebook_id: Optional[str],
                   cdp_url: str, config: str):
    """Save a paused card's outline or producer notes, and print them.

    ARTIFACT is the card's id, from `studio list` or the run that made it. It
    may be left out when one card is waiting. The card stays paused, so this
    can run any number of times; the same plan is not saved twice. Each new plan
    in a folder is the next version, outline-<NN>-<card>.md, listed in
    manifest.json where the episode room reads it.

    Example:
        deepdiver studio outline 26192ae5-88f2-4443-b870-8c0df3cc4e41 -n abc-123 -o <dir>
    """
    from .notebooklm_automator import NotebookLMAutomator

    async def run():
        automator = NotebookLMAutomator(config, cdp_url_override=cdp_url)
        if not await automator.connect_to_browser():
            console.print("❌ Failed to connect to browser", style="red")
            return False
        result = await automator.review_outline(artifact, output, notebook_id=notebook_id,
                                                seeded_from=os.path.basename(seeded_from) if seeded_from else None)
        if not result:
            return False
        _print_plan(result['plan'])
        console.print(f"✅ Saved {result['entry']['path']} (v{result['entry']['outline_version']}); "
                      f"card {result['card'].get('artifact_id')} is still waiting", style="green")
        return True

    if not asyncio.run(run()):
        sys.exit(1)


@studio.command(name='proceed')
@click.argument('artifact')
@click.option('--output', '-o', required=True, help="Folder that keeps the plan, beside the notebook's media")
@click.option('--instruction', '-i', 'feedback_file', type=click.Path(exists=True, dir_okay=False),
              help='File of feedback, applied to the render; Studio offers one round of it')
@click.option('--no-wait', is_flag=True, default=False, help='Return once the render has started')
@click.option('--notebook-id', '-n', help='Notebook ID (uses current page if not provided)')
@cdp_url_option
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def studio_proceed(artifact: str, output: str, feedback_file: Optional[str], no_wait: bool,
                   notebook_id: Optional[str], cdp_url: str, config: str):
    """Send a paused card on to render. This cannot be taken back.

    The plan and the feedback are saved first. Sending feedback renders at once
    with it applied, with no second plan to read, and Studio afterwards shows
    neither: "Prompt and sources" holds only the first prompt. To read another
    plan before rendering, start a new run with `studio generate --from-outline`.

    Example:
        deepdiver studio proceed 26192ae5-88f2-4443-b870-8c0df3cc4e41 -n abc-123 -o <dir> -i feedback.md
    """
    from .notebooklm_automator import NotebookLMAutomator

    feedback = None
    if feedback_file:
        feedback = Path(feedback_file).read_text(encoding='utf-8').strip()
        if not feedback:
            console.print(f"❌ {feedback_file} is empty", style="red")
            sys.exit(1)

    async def run():
        automator = NotebookLMAutomator(config, cdp_url_override=cdp_url)
        if not await automator.connect_to_browser():
            console.print("❌ Failed to connect to browser", style="red")
            return False
        result = await automator.proceed_review(artifact, output, notebook_id=notebook_id,
                                                feedback=feedback, wait=not no_wait)
        if not result:
            return False
        console.print(f"📝 Plan kept: {result['outline']['path']}", style="cyan")
        if result.get('feedback'):
            console.print(f"📝 Feedback kept: {result['feedback']['path']}", style="cyan")
        if result.get('artifact'):
            console.print(f"✅ Rendered: {result['artifact'].get('title')} · {result['artifact'].get('artifact_id')}",
                          style="green")
        else:
            console.print("⏳ Rendering; `studio list` shows it", style="green")
        return True

    if not asyncio.run(run()):
        sys.exit(1)


@studio.command(name='keep')
@click.argument('folder')
@click.option('--no-transcript', is_flag=True, default=False,
              help='Skip the transcripts of kept video and audio (they take a few minutes each)')
def studio_keep(folder: str, no_transcript: bool):
    """Make what a git repository keeps from a download folder.

    Infographics become WebP (quality 90, no metadata) and the PNG is removed;
    video and audio overviews are re-encoded into keep/, the download staying
    beside them, each with its transcript (keep/<name>.transcript.md); reports
    stay as they are. manifest.json records each as
    "kept". Run it on a folder `studio download` wrote. Needs ffmpeg.

    Example:
        deepdiver studio keep <episode>/captures/notebook-<id>
    """
    if not os.path.isfile(os.path.join(folder, 'manifest.json')):
        console.print(f"❌ No manifest.json in {folder}", style="red")
        sys.exit(1)
    if not _print_kept(folder, transcripts=not no_transcript):
        sys.exit(1)


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
@click.option('--user-data-dir', default=None,
              help='Chrome user data directory (default: DeepDiver\'s home, ~/.chrome-deepdiver)')
@click.option('--clone-profile', default=None,
              help='Seed the user data directory from this profile (e.g. "Profile 2") '
                   'when it does not exist yet; an existing one is reused, sign-in included')
@click.option('--fresh', is_flag=True, default=False,
              help='Clone into a new temporary folder instead (not signed in to Google)')
@click.option('--profile-root', default=None,
              help='Chrome config root for cloning (default: ~/.config/google-chrome)')
@click.option('--display', default=None,
              help='X display (default: $DISPLAY or :0 — needed from SSH/tmux)')
def chrome_launch(port: int, user_data_dir: Optional[str], clone_profile: Optional[str],
                  fresh: bool, profile_root: Optional[str], display: Optional[str]):
    """Launch Chrome with CDP enabled (SSH/tmux-safe).

    Uses DeepDiver's own Chrome home (~/.chrome-deepdiver), so a person signs in
    to Google once and every later launch reuses that sign-in. Passes
    DISPLAY/XAUTHORITY through so launching from SSH or tmux works, and binds
    the debug port to 127.0.0.1.

    Examples:
        deepdiver chrome launch
        deepdiver chrome launch --clone-profile "Profile 2"   # seeds the home once
        deepdiver chrome launch --clone-profile "Profile 2" --fresh
    """
    console.print(f"🚀 Launching Chrome with CDP on port {port}...", style="blue")
    home = os.path.expanduser(user_data_dir or DEFAULT_USER_DATA_DIR)
    if clone_profile and fresh:
        console.print(f"👤 Cloning profile into a temporary folder: {clone_profile}", style="cyan")
    elif os.path.isfile(os.path.join(home, 'Local State')):
        console.print(f"🏠 Reusing {home}", style="cyan")
    elif clone_profile:
        console.print(f"👤 Seeding {home} from profile: {clone_profile}", style="cyan")

    if not launch_chrome_cdp(port=port, user_data_dir=user_data_dir,
                             clone_from_profile=clone_profile,
                             profile_root=profile_root, display=display, fresh=fresh):
        console.print("❌ Chrome launch failed or CDP did not come up", style="red")
        console.print("💡 From SSH/tmux, X env is required: try --display :0", style="yellow")
        sys.exit(1)
    console.print(f"✅ Chrome launched — CDP live at http://127.0.0.1:{port}", style="green")
    signed_in = check_signed_in(f'http://127.0.0.1:{port}')
    if signed_in is None:
        console.print(f"❌ {describe_attach_timeout(f'http://127.0.0.1:{port}')}", style="red")
        sys.exit(3)
    if signed_in:
        console.print("✅ Signed in to Gemini Notebook", style="green")
    else:
        console.print("⚠️  Not signed in to Gemini Notebook: sign in once in this Chrome window. "
                      "The sign-in stays in this folder for later launches.", style="yellow")
        sys.exit(2)


@chrome.command(name='status')
@click.option('--port', default=9222, help='CDP port (default: 9222)')
def chrome_status(port: int):
    """Is Chrome up on the CDP port, and is it signed in to Gemini Notebook?

    Exit 0 signed in, 2 not signed in, 1 no Chrome on the port, 3 Chrome
    answers but DeepDiver cannot attach (a tab hangs).
    """
    cdp_url = f'http://127.0.0.1:{port}'
    if not check_chrome_cdp_running(cdp_url):
        console.print(f"❌ No Chrome answers on {cdp_url}", style="red")
        keyring = find_keyring_prompt()
        if keyring:
            console.print(f"   {keyring}", style="yellow")
        sys.exit(1)
    signed_in = check_signed_in(cdp_url)
    if signed_in:
        console.print(f"✅ Chrome on {cdp_url} is signed in to Gemini Notebook", style="green")
        return
    if signed_in is None:
        console.print(f"❌ {describe_attach_timeout(cdp_url)}", style="red")
        sys.exit(3)
    console.print(f"⚠️  Chrome on {cdp_url} is not signed in to Gemini Notebook", style="yellow")
    sys.exit(2)


@chrome.command(name='adopt')
@click.argument('source_dir')
@click.option('--user-data-dir', default=None,
              help='Destination (default: DeepDiver\'s home, ~/.chrome-deepdiver)')
def chrome_adopt(source_dir: str, user_data_dir: Optional[str]):
    """Move a Chrome folder that is already signed in into DeepDiver's home.

    For a sign-in made in a temporary clone: close that Chrome first, then
    adopt its folder so later launches reuse the sign-in. Refuses when Chrome
    still holds the folder or the destination exists.
    """
    dest = adopt_user_data_dir(source_dir, user_data_dir)
    if not dest:
        console.print("❌ Not adopted: the source must be a closed Chrome user-data-dir "
                      "and the destination must not exist", style="red")
        sys.exit(1)
    console.print(f"✅ {source_dir} is now {dest}", style="green")


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
