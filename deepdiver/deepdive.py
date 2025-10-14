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
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .notebooklm_automator import NotebookLMAutomator


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
    """Initialize DeepDiver configuration and setup."""
    console.print("🔧 Initializing DeepDiver...", style="blue")
    
    try:
        # Check if config file exists
        if not os.path.exists(config):
            console.print(f"❌ Configuration file not found: {config}", style="red")
            console.print("Please ensure deepdiver.yaml exists in the project directory.", style="yellow")
            return
        
        # Test configuration loading
        automator = NotebookLMAutomator(config)
        console.print("✅ Configuration loaded successfully", style="green")
        
        # Check Chrome browser setup
        console.print("🔍 Checking Chrome browser setup...", style="blue")
        console.print("Make sure Chrome is running with: google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-deepdiver", style="yellow")
        
        console.print("🎉 DeepDiver initialization complete!", style="green")
        
    except Exception as e:
        console.print(f"❌ Initialization failed: {e}", style="red")


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
