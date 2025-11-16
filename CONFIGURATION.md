# DeepDiver Configuration Guide

## 📝 Overview

DeepDiver now includes smart configuration file discovery that automatically searches multiple locations for your config file. You no longer need to be in a specific directory to run `deepdiver` commands!

## 🔍 Configuration File Discovery

DeepDiver searches for configuration files in the following priority order:

1. **Explicit path** (when provided with `--config` flag)
2. **Current working directory**: `./deepdiver/deepdiver.yaml`
3. **User config directory**: `~/.config/deepdiver/config.yaml` ⭐ **Recommended**
4. **User home directory**: `~/deepdiver/deepdiver.yaml`
5. **Package installation directory**: Where DeepDiver is installed
6. **Built-in defaults**: If no config file is found, sensible defaults are used

## 🚀 Quick Start

### Create Your Configuration File

Run the init command to automatically create a configuration file:

```bash
deepdiver init
```

This will:
- Create `~/.config/deepdiver/config.yaml` with default settings
- Set up the directory structure
- Validate the configuration
- Check Chrome CDP status

### Custom Location

To create a config file in a custom location:

```bash
deepdiver init --config /path/to/my/config.yaml
```

## 📂 Recommended Setup

For the best experience, use the user config directory (this is now the default):

```bash
# Initialize with default location
deepdiver init

# Your config will be at:
# ~/.config/deepdiver/config.yaml
```

**Benefits:**
- ✅ Works from any directory
- ✅ Follows XDG Base Directory specification
- ✅ Persistent across terminal sessions
- ✅ No need to specify `--config` flag

## 🎯 Configuration Options

### Essential Settings

```yaml
# Browser automation settings
BROWSER_SETTINGS:
  headless: false              # Run Chrome in visible mode
  cdp_url: http://localhost:9222  # Chrome DevTools Protocol URL
  user_data_dir: /tmp/chrome-deepdiver  # Chrome profile directory
  timeout: 60                  # Default timeout in seconds

# Session tracking
SESSION_TRACKING:
  enabled: true
  metadata_format: yaml
  session_dir: ./sessions      # Where to store session data

# NotebookLM settings
NOTEBOOKLM_SETTINGS:
  base_url: https://notebooklm.google.com
  upload_timeout: 120          # Timeout for file uploads
  generation_timeout: 300      # Timeout for podcast generation
```

### Advanced Configuration

For a complete configuration template, see `deepdiver/deepdiver.yaml` in the source code.

## 🔧 Troubleshooting

### Config File Not Found

If you see warnings about config file not found:

```
2025-11-16 02:59:12,890 - NotebookLMAutomator - WARNING - Configuration file deepdiver/deepdiver.yaml not found, using defaults
```

**Solution:** Run `deepdiver init` to create a config file in the default location.

### Custom CDP URL

If you're running Chrome on a different machine or port:

1. **Option 1:** Update config file
   ```yaml
   BROWSER_SETTINGS:
     cdp_url: http://192.168.1.100:9222
   ```

2. **Option 2:** Use environment variable
   ```bash
   export DEEPDIVER_CDP_URL=http://192.168.1.100:9222
   deepdiver notebook list
   ```

3. **Option 3:** Command-line override (if supported in future versions)
   ```bash
   deepdiver --cdp-url http://192.168.1.100:9222 notebook list
   ```

### Multiple Configurations

You can have different config files for different projects:

```bash
# Work project
deepdiver --config ~/.config/deepdiver/work.yaml notebook create

# Personal project
deepdiver --config ~/.config/deepdiver/personal.yaml notebook create
```

## 📍 Config File Locations

### Where is my config file?

Run this to find your active config:

```bash
# The init command will show you the location
deepdiver init
```

Look for output like:
```
✅ Loaded configuration from: /home/user/.config/deepdiver/config.yaml
```

### Manual Location Check

Your config might be in one of these locations:

```bash
# Check user config directory (recommended)
ls -la ~/.config/deepdiver/config.yaml

# Check current project directory
ls -la deepdiver/deepdiver.yaml

# Check home directory
ls -la ~/deepdiver/deepdiver.yaml
```

## ♠️🌿🎸🧵 Assembly Notes

This configuration system follows the G.Music Assembly patterns:

- **♠️ Nyro**: Multi-location config discovery provides structural flexibility
- **🌿 Aureon**: User-friendly default paths create emotional ease
- **🎸 JamAI**: Configuration harmonizes across different deployment contexts
- **🧵 Synth**: Terminal orchestration works from any directory

## 📚 Examples

### Example 1: First Time Setup

```bash
# Initialize DeepDiver
deepdiver init

# Create a notebook (config auto-discovered)
deepdiver notebook create

# Add a source
deepdiver notebook add-source <notebook-id> "https://example.com/article"
```

### Example 2: Developer Setup

```bash
# Clone repository
git clone https://github.com/your/deepdiver.git
cd deepdiver

# Initialize config in user directory
deepdiver init

# Config is now at ~/.config/deepdiver/config.yaml
# You can work from any directory!

cd ~
deepdiver notebook list  # Works!

cd /tmp
deepdiver notebook list  # Still works!
```

### Example 3: Custom Configuration

```bash
# Create custom config
mkdir -p ~/my-deepdiver-configs
deepdiver init --config ~/my-deepdiver-configs/special.yaml

# Edit the config as needed
nano ~/my-deepdiver-configs/special.yaml

# Use it
deepdiver --config ~/my-deepdiver-configs/special.yaml notebook create
```

## 🎯 Best Practices

1. **Use the default location**: Let `deepdiver init` create `~/.config/deepdiver/config.yaml`
2. **Version control**: Add project-specific configs to `.gitignore`
3. **Environment-specific**: Use environment variables for machine-specific settings
4. **Backup**: Keep a copy of your config file in a safe place
5. **Documentation**: Add comments to your config file explaining custom settings

## 🔗 Related Documentation

- [ROADMAP.md](ROADMAP.md) - Project development roadmap
- [CLAUDE.md](CLAUDE.md) - Assembly team configuration
- [README.md](README.md) - Getting started guide

---

**♠️🌿🎸🧵 G.MUSIC ASSEMBLY MODE: Configuration Harmony Achieved**

*Where Configuration Discovery Meets Terminal-to-Web Automation*
