#!/bin/bash
# Create all NotebookLM Studio Artifacts GitHub issues
# Requires: gh CLI (https://cli.github.com/)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

REPO="Gerico1007/deepdiver"
MILESTONE="NotebookLM Studio Artifacts"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  NotebookLM Studio Artifacts - GitHub Issues Creator${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ Error: gh CLI is not installed${NC}"
    echo ""
    echo "Please install gh CLI from: https://cli.github.com/"
    echo ""
    echo -e "${YELLOW}Alternative: Use the Python script instead:${NC}"
    echo "  python .github/issue-templates/create_issues.py --list"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Error: Not authenticated with GitHub${NC}"
    echo ""
    echo "Please run: gh auth login"
    exit 1
fi

echo -e "${GREEN}✅ gh CLI is installed and authenticated${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to create issue from template
create_issue() {
    local phase=$1
    local template_file=$2
    local title=$3
    local labels=$4

    echo -e "${YELLOW}Creating Phase ${phase} issue...${NC}"

    # Extract body (skip metadata section)
    body=$(awk '
        BEGIN { in_body=0 }
        /^## 📋 Description/ { in_body=1 }
        in_body { print }
    ' "$template_file")

    # Create issue
    issue_url=$(gh issue create \
        --repo "$REPO" \
        --title "$title" \
        --body "$body" \
        --label "$labels" \
        --milestone "$MILESTONE" \
        --assignee "@me")

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Created: $issue_url${NC}"
        echo ""
    else
        echo -e "${RED}❌ Failed to create Phase ${phase} issue${NC}"
        echo ""
    fi
}

# Create issues for each phase
echo -e "${BLUE}Creating issues...${NC}"
echo ""

create_issue 2 \
    "$SCRIPT_DIR/phase-2-video-overview.md" \
    "Phase 2: Video Overview Implementation" \
    "enhancement,studio-artifacts,phase-2,video-overview"

create_issue 3 \
    "$SCRIPT_DIR/phase-3-mind-map.md" \
    "Phase 3: Mind Map Implementation" \
    "enhancement,studio-artifacts,phase-3,mind-map"

create_issue 4 \
    "$SCRIPT_DIR/phase-4-reports.md" \
    "Phase 4: Study Guides & Reports Implementation" \
    "enhancement,studio-artifacts,phase-4,reports,study-guides"

create_issue 5 \
    "$SCRIPT_DIR/phase-5-flashcards.md" \
    "Phase 5: Flashcards Implementation" \
    "enhancement,studio-artifacts,phase-5,flashcards,study-tools"

create_issue 6 \
    "$SCRIPT_DIR/phase-6-quizzes.md" \
    "Phase 6: Quizzes Implementation" \
    "enhancement,studio-artifacts,phase-6,quizzes,study-tools"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ All issues created successfully!${NC}"
echo ""
echo "View all issues: https://github.com/$REPO/issues"
echo "View milestone: https://github.com/$REPO/milestone/$(echo "$MILESTONE" | sed 's/ /%20/g')"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
