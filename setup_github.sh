#!/bin/bash
# GitHub Repository Setup Script for DeepDiver
# Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵

echo "♠️🌿🎸🧵 DeepDiver GitHub Setup"
echo "================================"
echo ""

# Check if we're in the right directory
if [ ! -f "deepdiver/deepdive.py" ]; then
    echo "❌ Error: Please run this script from the deepdiver project root directory"
    exit 1
fi

echo "✅ Found DeepDiver project files"
echo ""

# Check current git status
echo "📊 Current Git Status:"
git status --short
echo ""

# Check current branch
current_branch=$(git branch --show-current)
echo "🌿 Current branch: $current_branch"
echo ""

# Prompt for GitHub repository URL
echo "🔗 Please provide your GitHub repository URL:"
echo "   Example: https://github.com/YOUR_USERNAME/deepdiver.git"
echo "   Or: git@github.com:YOUR_USERNAME/deepdiver.git"
echo ""
read -p "GitHub Repository URL: " github_url

if [ -z "$github_url" ]; then
    echo "❌ Error: No repository URL provided"
    exit 1
fi

echo ""
echo "🔧 Setting up GitHub connection..."

# Add remote origin
echo "📡 Adding remote origin..."
git remote add origin "$github_url"

# Verify remote was added
echo "✅ Remote added successfully"
echo ""

# Show current remotes
echo "📡 Current remotes:"
git remote -v
echo ""

# Push main branch first
echo "🚀 Pushing main branch to GitHub..."
git checkout main
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ Main branch pushed successfully"
else
    echo "❌ Failed to push main branch"
    echo "💡 You may need to authenticate with GitHub"
    echo "   Try: git push -u origin main"
    exit 1
fi

# Push feature branch
echo ""
echo "🚀 Pushing feature branch to GitHub..."
git checkout "$current_branch"
git push -u origin "$current_branch"

if [ $? -eq 0 ]; then
    echo "✅ Feature branch pushed successfully"
else
    echo "❌ Failed to push feature branch"
    echo "💡 You may need to authenticate with GitHub"
    echo "   Try: git push -u origin $current_branch"
fi

echo ""
echo "🎉 GitHub setup completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Go to your GitHub repository: $github_url"
echo "   2. Verify all files are uploaded correctly"
echo "   3. Create a Pull Request for the feature branch"
echo "   4. Set up GitHub Actions for CI/CD (optional)"
echo ""
echo "♠️🌿🎸🧵 Assembly Team: Repository connected successfully!"


