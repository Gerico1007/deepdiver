#!/bin/bash
# DeepDiver + Langfuse CLI Examples
# ♠️🌿🎸🧵 G.Music Assembly Team
#
# This script demonstrates CLI workflows with Langfuse integration

set -e  # Exit on error

echo "♠️🌿🎸🧵 DeepDiver CLI Examples with Langfuse Integration"
echo "=========================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# =============================================================================
# Example 1: Basic Session with Langfuse Tracing
# =============================================================================
echo -e "\n${BLUE}Example 1: Basic Session with Langfuse Tracing${NC}"
echo "------------------------------------------------"

# Set Langfuse credentials (in real usage, these would be set in environment)
# export LANGFUSE_PUBLIC_KEY="pk-lf-xxx"
# export LANGFUSE_SECRET_KEY="sk-lf-xxx"
# export LANGFUSE_HOST="https://cloud.langfuse.com"

echo -e "${GREEN}Step 1: Start session${NC}"
deepdiver session start --ai claude --issue 101

echo -e "\n${GREEN}Step 2: Create notebook with source${NC}"
deepdiver notebook create --source ./README.md

echo -e "\n${GREEN}Step 3: View session status${NC}"
deepdiver session status

# Future: View trace tree
# echo -e "\n${GREEN}Step 4: View Langfuse trace${NC}"
# deepdiver session view-trace

echo -e "\n${GREEN}Step 5: End session${NC}"
deepdiver session close


# =============================================================================
# Example 2: Multi-Notebook Research Session
# =============================================================================
echo -e "\n${BLUE}Example 2: Multi-Notebook Research Session${NC}"
echo "--------------------------------------------"

echo -e "${GREEN}Starting research session...${NC}"
deepdiver session start --ai claude --issue 202

echo -e "\n${GREEN}Creating topic-specific notebooks...${NC}"

# Notebook 1: Academic Papers
echo "Creating 'AI Research Papers' notebook..."
deepdiver notebook create --title "AI Research Papers"
NB1_ID=$(deepdiver session status | grep -oP 'Active Notebook: \K[a-f0-9-]+' | head -1)

echo "Adding paper sources..."
deepdiver notebook add-source "$NB1_ID" ./papers/transformer.pdf
deepdiver notebook add-source "$NB1_ID" ./papers/attention.pdf

# Notebook 2: Video Lectures
echo -e "\nCreating 'ML Lectures' notebook..."
deepdiver notebook create --title "ML Lectures"
NB2_ID=$(deepdiver session status | grep -oP 'Active Notebook: \K[a-f0-9-]+' | head -1)

echo "Adding YouTube lecture..."
deepdiver notebook add-source "$NB2_ID" "https://youtube.com/watch?v=example"

# Notebook 3: Documentation
echo -e "\nCreating 'Framework Docs' notebook..."
deepdiver notebook create --title "Framework Docs"
NB3_ID=$(deepdiver session status | grep -oP 'Active Notebook: \K[a-f0-9-]+' | head -1)

echo "Adding documentation URL..."
deepdiver notebook add-source "$NB3_ID" "https://pytorch.org/docs"

echo -e "\n${GREEN}Listing all notebooks...${NC}"
deepdiver notebook list

# Future: View comprehensive trace
# echo -e "\n${GREEN}Viewing comprehensive trace tree...${NC}"
# deepdiver session view-trace

echo -e "\n${GREEN}Ending research session...${NC}"
deepdiver session close


# =============================================================================
# Example 3: Assembly Team Prompt Usage
# =============================================================================
echo -e "\n${BLUE}Example 3: Assembly Team Prompt Usage${NC}"
echo "---------------------------------------"

# Initialize prompts if not already present
echo -e "${GREEN}Initializing Assembly Team prompts...${NC}"
# Future: deepdiver assembly init-prompts

# Get guidance from different personas
echo -e "\n${YELLOW}⚡ Jerry's Creative Direction:${NC}"
# Future: deepdiver assembly prompt-get jerry | head -20

echo -e "\n${YELLOW}♠️ Nyro's Structural Advice:${NC}"
# Future: deepdiver assembly prompt-get nyro | head -20

echo -e "\n${YELLOW}🌿 Aureon's Emotional Context:${NC}"
# Future: deepdiver assembly prompt-get aureon | head -20

echo -e "\n${YELLOW}🎸 JamAI's Musical Harmony:${NC}"
# Future: deepdiver assembly prompt-get jamai | head -20

echo -e "\n${YELLOW}🧵 Synth's Execution Clarity:${NC}"
# Future: deepdiver assembly prompt-get synth | head -20

# Start session with Assembly Team guidance
echo -e "\n${GREEN}Starting session with Assembly Team...${NC}"
deepdiver session start --ai claude --issue 303

# Add session notes with persona perspectives
echo -e "\n${GREEN}Adding Assembly Team notes...${NC}"
# Future: deepdiver session note "♠️ Nyro: The trace structure reveals recursive patterns"
# Future: deepdiver session note "🌿 Aureon: This notebook creates emotional resonance"
# Future: deepdiver session note "🎸 JamAI: The workflow has a 4/4 rhythm"

deepdiver session close


# =============================================================================
# Example 4: Collaborative Session Workflow
# =============================================================================
echo -e "\n${BLUE}Example 4: Collaborative Session (Simulation)${NC}"
echo "----------------------------------------------"

echo -e "${GREEN}Team Member A: Creating collaborative session...${NC}"
deepdiver session start --ai claude --issue 404
SESSION_ID=$(deepdiver session status | grep -oP 'Session ID: \K[a-f0-9-]+')

echo -e "\nSession ID for sharing: ${YELLOW}$SESSION_ID${NC}"

echo -e "\n${GREEN}Team Member A: Creating initial notebook...${NC}"
deepdiver notebook create --title "Collaborative Research"
COLLAB_NB=$(deepdiver session status | grep -oP 'Active Notebook: \K[a-f0-9-]+' | head -1)

deepdiver notebook add-source "$COLLAB_NB" ./requirements.md

echo -e "\n${GREEN}Team Member B: Adding more sources (simulated)...${NC}"
# In real collaboration, Team Member B would:
# deepdiver session load $SESSION_ID
deepdiver notebook add-source "$COLLAB_NB" ./architecture.md

echo -e "\n${GREEN}Team Member C: Reviewing session (simulated)...${NC}"
deepdiver session status

# Future: View collaborative trace
# echo -e "\n${GREEN}Viewing collaborative trace...${NC}"
# deepdiver session view-trace "$SESSION_ID"

deepdiver session close


# =============================================================================
# Example 5: Debugging with Traces
# =============================================================================
echo -e "\n${BLUE}Example 5: Debugging with Traces${NC}"
echo "----------------------------------"

echo -e "${GREEN}Starting debug session...${NC}"
deepdiver session start --ai claude --issue 505

echo -e "\n${GREEN}Attempting operation (may fail)...${NC}"
# This will fail if file doesn't exist, creating error trace
# deepdiver notebook create --source ./missing-file.pdf || true

echo -e "\n${GREEN}Attempting successful operation...${NC}"
deepdiver notebook create --source ./README.md

# Future: View trace with errors
# echo -e "\n${GREEN}Viewing trace with error context...${NC}"
# deepdiver session view-trace --show-errors

deepdiver session close


# =============================================================================
# Example 6: Session History Queries
# =============================================================================
echo -e "\n${BLUE}Example 6: Session History Queries (Future)${NC}"
echo "--------------------------------------------"

# These commands are planned for future implementation
echo -e "${YELLOW}Planned CLI commands:${NC}"

echo -e "\n# List all sessions with YouTube sources"
echo "$ deepdiver session query --source-type=youtube"

echo -e "\n# List sessions with >5 sources"
echo "$ deepdiver session query --min-sources=5"

echo -e "\n# Find sessions by issue number"
echo "$ deepdiver session query --issue=42"

echo -e "\n# View all traces for a session"
echo "$ deepdiver session list-traces"

echo -e "\n# Query traces with filters"
echo "$ deepdiver session query-traces --status=ended --min-notebooks=3"


# =============================================================================
# Example 7: Complete Research Workflow
# =============================================================================
echo -e "\n${BLUE}Example 7: Complete Research Workflow${NC}"
echo "---------------------------------------"

echo -e "${GREEN}Phase 1: Planning${NC}"
# Get Jerry's creative direction
# Future: deepdiver assembly prompt-get jerry | head -10

echo -e "\n${GREEN}Phase 2: Session Setup${NC}"
deepdiver session start --ai claude --issue 606

echo -e "\n${GREEN}Phase 3: Structured Notebook Creation${NC}"
# Following Nyro's structural guidance
deepdiver notebook create --title "Literature Review"
deepdiver notebook create --title "Methodology"
deepdiver notebook create --title "Analysis"

echo -e "\n${GREEN}Phase 4: Source Collection${NC}"
REVIEW_NB=$(deepdiver notebook list | grep -oP 'Literature Review.*?\K[a-f0-9-]+' | head -1 || echo "nb-fallback")
# deepdiver notebook add-source "$REVIEW_NB" ./paper1.pdf
# deepdiver notebook add-source "$REVIEW_NB" ./paper2.pdf
# deepdiver notebook add-source "$REVIEW_NB" "https://arxiv.org/abs/example"

echo -e "\n${GREEN}Phase 5: Review and Finalize${NC}"
deepdiver session status

# Future: Generate session summary
# deepdiver session summary

echo -e "\n${GREEN}Phase 6: Session Complete${NC}"
deepdiver session close


# =============================================================================
# Summary
# =============================================================================
echo -e "\n${BLUE}=========================================================="
echo "CLI Examples Complete!"
echo "==========================================================${NC}"

echo -e "\n${GREEN}What you've seen:${NC}"
echo "  ✅ Basic session with Langfuse tracing"
echo "  ✅ Multi-notebook research sessions"
echo "  ✅ Assembly Team prompt integration"
echo "  ✅ Collaborative workflows"
echo "  ✅ Debugging with traces"
echo "  ✅ Session history queries (planned)"
echo "  ✅ Complete research workflow"

echo -e "\n${YELLOW}Future CLI Commands (in development):${NC}"
echo "  • deepdiver session view-trace [trace_id]"
echo "  • deepdiver session query [filters]"
echo "  • deepdiver assembly prompt-get <persona>"
echo "  • deepdiver assembly prompt-sync <persona>"
echo "  • deepdiver session note <message>"

echo -e "\n♠️🌿🎸🧵 ${GREEN}Assembly Team: Ready for your next command!${NC}"
