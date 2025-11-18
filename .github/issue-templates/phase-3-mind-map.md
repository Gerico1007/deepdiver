# Phase 3: Mind Map Implementation

**Labels**: `enhancement`, `studio-artifacts`, `phase-3`, `mind-map`
**Priority**: Medium
**Milestone**: NotebookLM Studio Artifacts
**Assignees**: @Gerico1007

## 📋 Description

Implement Mind Map generation and interaction in DeepDiver. Unlike Audio/Video Overviews, Mind Maps are generated via chat chip interaction rather than customization dialogs, requiring a different automation approach.

## 🎯 Objectives

- Automate Mind Map generation via NotebookLM's chat interface
- Support source-specific mind map creation
- Enable node interaction (expand/collapse, querying)
- Integrate with session tracking system
- Provide CLI interface for mind map operations

## 🛠️ Technical Details

### Generation Method

Mind Maps use a **chat chip interaction pattern** instead of customization dialogs:

1. Click "Mind Map" chip in chat interface
2. Generation occurs automatically
3. Appears as new Note in Studio Panel

### Customization Strategy

Mind Maps don't have direct customization options. To "customize":
- Delete existing mind map via three-dot menu
- Ask specific chat query before generating
- Select specific sources before generation

### Interaction Features

- **Zoom/Scroll**: Pan and navigate the map
- **Expand/Collapse**: Click branches to show/hide sub-nodes
- **Query Nodes**: Click statement boxes to ask AI questions about that topic
- **Source-grounded**: All nodes linked to original sources

### Key Selectors

- **Mind Map Chip**: `.suggested-chip:has-text("Mind Map")`
- **Studio Artifact**: `.studio-artifact:has-text("Mind Map")`
- **Mind Map Nodes**: `.mind-map-node`
- **Node Statement Box**: `.mind-map-node .statement-box`

## ✅ Implementation Checklist

### Research & Planning
- [ ] Research Mind Map UI and DOM structure in NotebookLM
- [ ] Identify chat chip interaction patterns
- [ ] Map mind map node structure and selectors
- [ ] Document interaction methods (zoom, expand, query)
- [ ] Understand source selection impact on mind map generation

### Core Implementation
- [ ] Implement `generate_mind_map()` method in `notebooklm_automator.py`
- [ ] Add chat interface interaction for mind map trigger
- [ ] Add source selection functionality (`_select_sources()`)
- [ ] Add focus query support (send chat query before generation)
- [ ] Implement generation monitoring with 300s timeout
- [ ] Add error handling for chat interactions

### Node Interaction
- [ ] Implement `interact_with_mind_map_node()` method
- [ ] Add node click handling for AI queries
- [ ] Add expand/collapse functionality (if automatable)
- [ ] Add zoom/pan interaction (if needed)
- [ ] Implement node text extraction

### Export & Download
- [ ] Research mind map export capabilities
- [ ] Implement `export_mind_map()` method (PNG/PDF if available)
- [ ] Add screenshot capture as fallback
- [ ] Handle download completion

### Metadata & Session Integration
- [ ] Capture mind map metadata (node count, structure)
- [ ] Integrate with session tracking system
- [ ] Store focus query and source selections
- [ ] Add artifact URL and ID capture
- [ ] Track interaction history (queries made)

### CLI Integration
- [ ] Add `deepdiver studio mindmap` command
- [ ] Add `--query` option for focus query
- [ ] Add `--sources` option for source selection
- [ ] Add `--notebook-id` option
- [ ] Add `deepdiver studio mindmap-query` command for node interaction
- [ ] Add `deepdiver studio mindmap-export` command
- [ ] Implement help documentation

### Testing
- [ ] Test basic mind map generation (all sources)
- [ ] Test source-specific mind maps
- [ ] Test focus query before generation
- [ ] Test node interaction and querying
- [ ] Test concurrent generation with other artifacts
- [ ] Test error scenarios (no sources, chat errors)
- [ ] Test mind map export functionality
- [ ] Write unit tests for mind map methods
- [ ] Write integration tests for end-to-end workflow

### Documentation
- [ ] Update README.md with mind map examples
- [ ] Document chat chip interaction pattern
- [ ] Document node interaction capabilities
- [ ] Create guide for effective mind map queries
- [ ] Update ROADMAP.md to reflect completion

### Quality Assurance
- [ ] Code review and refactoring
- [ ] Performance optimization
- [ ] User feedback clarity
- [ ] Error handling robustness

## 📚 Resources

- [NotebookLM Support: Mind Maps](https://support.google.com/notebooklm/answer/16212283)
- [KDnuggets: How to Use Mind Maps in NotebookLM](https://www.kdnuggets.com/how-to-use-mind-maps-in-notebooklm)
- [YouTube: Mind Map Features](https://www.youtube.com/watch?v=ztq7G_eWUik)
- Implementation Guide: `docs/STUDIO_ARTIFACTS_IMPLEMENTATION.md`

## 🔗 Related Issues

- Depends on: Phase 2 (Video Overview)
- Related to: PR #10 (Audio Overview patterns)
- Blocks: None (can be developed in parallel with other phases)

## 📝 Notes

- Mind Maps use a **different UI pattern** than Audio/Video Overviews (chat chip vs edit button)
- No direct customization dialog - customization happens through source selection and focus queries
- Node interaction requires careful DOM navigation and event handling
- Export functionality may be limited - screenshot fallback may be necessary
- Mind maps are source-grounded, making them ideal for research and exploration tasks

## 🎨 Assembly Context

**♠️🌿🎸🧵 G.MUSIC ASSEMBLY MODE**

- **♠️ Nyro**: Chat interaction patterns, recursive mind map structure analysis
- **🌿 Aureon**: Visual knowledge representation, conceptual resonance
- **🎸 JamAI**: Information hierarchy harmony, structural flow
- **🧵 Synth**: Chat automation orchestration, node interaction synthesis

---

**Success Criteria**: Mind Map generation works via chat chip interaction, node querying functions properly, and the CLI provides intuitive access to all mind map features.
