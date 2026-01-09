#!/bin/bash
# =============================================================================
# Nora AI - Git Setup Script (Distro-Neutral)
# Initializes git repository for easy updates
# =============================================================================

set -e

echo "=============================================="
echo "  Git Repository Setup"
echo "=============================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "ERROR: Git is not installed."
    echo ""
    echo "Please install git for your distribution:"
    echo ""
    echo "  Debian/Ubuntu:  sudo apt install git"
    echo "  Fedora:         sudo dnf install git"
    echo "  Arch:           sudo pacman -S git"
    echo "  Gentoo:         sudo emerge dev-vcs/git"
    echo "  Alpine:         sudo apk add git"
    echo ""
    exit 1
fi

# Check if already a git repo
if [ -d ".git" ]; then
    echo "Git repository already initialized."
    echo ""
    REMOTE=$(git remote get-url origin 2>/dev/null || echo "none")
    echo "Remote: $REMOTE"
    echo ""
    echo "To update, run: ./update.sh"
    exit 0
fi

# Get repository URL
echo "Enter your Git repository URL:"
echo "(e.g., https://github.com/yourcompany/nora-ai.git)"
read REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "ERROR: Repository URL required"
    exit 1
fi

# Initialize and connect to remote
echo ""
echo "Setting up git repository..."
git init
git remote add origin "$REPO_URL"
git fetch origin

# Try to set up main branch
if git show-ref --verify --quiet refs/remotes/origin/main; then
    git checkout -b main
    git branch --set-upstream-to=origin/main main
    echo "Connected to 'main' branch"
elif git show-ref --verify --quiet refs/remotes/origin/master; then
    git checkout -b master
    git branch --set-upstream-to=origin/master master
    echo "Connected to 'master' branch"
else
    echo "Note: Remote has no main/master branch yet."
    echo "Run 'git push -u origin main' after your first commit."
fi

echo ""
echo "=============================================="
echo "  Git Setup Complete!"
echo "=============================================="
echo ""
echo "To update in the future, run: ./update.sh"
echo ""
