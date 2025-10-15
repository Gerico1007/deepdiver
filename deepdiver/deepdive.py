"""
DeepDiver CLI Module
Main command-line interface for NotebookLM Podcast Automation System

This module provides the command-line interface for DeepDiver,
enabling users to create podcasts from documents through terminal commands.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .notebooklm_automator import (
    NotebookLMAutomator,
    find_chrome_executable,
    check_chrome_cdp_running,
    launch_chrome_cdp,
    get_cdp_url
)


# Initialize Rich console for beautiful output
console = Console()


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
@click.version_option(version="0.1.0", prog_name="DeepDiver")
def cli():
    """
    🎙️ DeepDiver - NotebookLM Podcast Automation System
    
    Create podcasts from documents using NotebookLM's Audio Overview feature
    through terminal commands and browser automation.
    
    Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
    """
    print_assembly_header()


@cli.command()
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def init(config: str):
    """
    Initialize DeepDiver configuration and setup.

    This command:
    - Validates configuration file
    - Checks Chrome CDP status
    - Offers to launch Chrome automatically
    - Provides setup instructions for NotebookLM
    """
    console.print("♠️🌿🎸🧵 DeepDiver Initialization", style="bold blue")
    console.print()

    try:
        # Check if config file exists
        if not os.path.exists(config):
            console.print(f"❌ Configuration file not found: {config}", style="red")
            console.print("Please ensure deepdiver.yaml exists in the project directory.", style="yellow")
            return

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
                else:
                    console.print("❌ NotebookLM navigation failed", style="red")
            else:
                console.print("❌ Browser connection failed", style="red")
                console.print("Make sure Chrome is running with CDP enabled", style="yellow")
        
        except Exception as e:
            console.print(f"❌ Test failed: {e}", style="red")
        
        finally:
            await automator.close()
    
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
            if not await automator.upload_document(source):
                console.print("❌ Failed to upload document", style="red")
                return
            
            # Generate Audio Overview
            console.print("🎵 Generating Audio Overview...", style="blue")
            if not await automator.generate_audio_overview(title):
                console.print("❌ Failed to generate Audio Overview", style="red")
                return
            
            # Download audio
            output_path = os.path.join(output, f"{title}.mp3")
            os.makedirs(output, exist_ok=True)
            
            console.print("⬇️ Downloading audio...", style="blue")
            if await automator.download_audio(output_path):
                console.print(f"✅ Podcast created successfully: {output_path}", style="green")
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
    console.print("🔮 Starting new DeepDiver session...", style="blue")
    console.print(f"🤖 AI Assistant: {ai}", style="blue")
    if issue:
        console.print(f"🎯 Issue: #{issue}", style="blue")
    
    # TODO: Implement session management
    console.print("⚠️ Session management not yet implemented", style="yellow")
    console.print("This feature will be available in a future release", style="yellow")


@session.command()
@click.argument('message')
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def write(message: str, config: str):
    """Write to the current session."""
    console.print(f"✍️ Writing to session: {message}", style="blue")
    
    # TODO: Implement session writing
    console.print("⚠️ Session writing not yet implemented", style="yellow")
    console.print("This feature will be available in a future release", style="yellow")


@session.command()
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def status(config: str):
    """Show current session status."""
    console.print("📊 Session Status", style="blue")
    
    # TODO: Implement session status
    console.print("⚠️ Session status not yet implemented", style="yellow")
    console.print("This feature will be available in a future release", style="yellow")


@cli.command()
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def status(config: str):
    """Show DeepDiver system status."""
    console.print("📊 DeepDiver System Status", style="blue")
    
    try:
        # Check configuration
        automator = NotebookLMAutomator(config)
        console.print("✅ Configuration loaded", style="green")
        
        # Check Chrome browser
        console.print("🔍 Checking Chrome browser...", style="blue")
        console.print("Make sure Chrome is running with CDP enabled", style="yellow")
        
        console.print("🎯 System Status: Ready for automation", style="green")
        
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
@click.option('--config', '-c', default='deepdiver/deepdiver.yaml',
              help='Path to configuration file')
def notebook_create(config: str):
    """Create a new notebook in NotebookLM."""
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
                    else:
                        console.print("❌ Failed to create notebook", style="red")
        except Exception as e:
            console.print(f"❌ Failed to create notebook: {e}", style="red")
        finally:
            await automator.close()

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
        finally:
            await automator.close()

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
                else:
                    console.print("❌ Failed to navigate to notebook", style="red")
        except Exception as e:
            console.print(f"❌ Failed to open notebook: {e}", style="red")
        finally:
            await automator.close()

    asyncio.run(run_open_notebook())

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
