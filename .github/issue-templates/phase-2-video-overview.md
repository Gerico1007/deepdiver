# Phase 2: Video Overview Implementation

**Labels**: `enhancement`, `studio-artifacts`, `phase-2`, `video-overview`
**Priority**: High
**Milestone**: NotebookLM Studio Artifacts
**Assignees**: @Gerico1007

## 📋 Description

Implement Video Overview generation with full customization support in DeepDiver. This builds on the successful Audio Overview implementation from PR #10 and applies the same patterns to video artifact generation.

## 🎯 Objectives

- Automate Video Overview generation via NotebookLM's Studio panel
- Support all customization options (format, visual style, language, steering prompt)
- Integrate with existing session tracking and metadata systems
- Provide CLI interface for video generation
- Ensure robust error handling and generation monitoring

## 🛠️ Technical Details

### Customization Options to Implement

1. **Format Selection**
   - Explainer (default): Comprehensive, structured video
   - Brief: 1-2 minute bite-sized overview

2. **Visual Styles** (Powered by Nano Banana)
   - Auto-select (let AI choose)
   - Classic (original default)
   - Whiteboard
   - Watercolor
   - Retro Print
   - Heritage
   - Paper-craft
   - Kawaii
   - Anime
   - Custom (text description input)

3. **Language Selection**
   - 80+ supported languages via dropdown

4. **Steering Prompt**
   - Freeform text input (5000 character limit)
   - Focus on specific sources, target audience, emphasize topics

### Key Implementation Patterns

- **UI Pattern**: Material Design dialog with CDK overlay
- **Edit Button**: `.create-artifact-button-container:has-text("Video Overview") button.edit-button`
- **Generation Monitoring**: Background polling every 5 seconds, 600s timeout
- **Completion Indicator**: "Load" button appearance
- **Metadata Tracking**: Duration, thumbnail URL, visual style, format

## ✅ Implementation Checklist

### Research & Planning
- [ ] Research Video Overview UI and DOM structure in NotebookLM
- [ ] Identify all CSS selectors for customization dialog elements
- [ ] Map all customization options (format, style, language, prompt)
- [ ] Document any differences from Audio Overview patterns
- [ ] Create technical specification document

### Core Implementation
- [ ] Implement `generate_video_overview()` method in `notebooklm_automator.py`
- [ ] Add format selection (radio button handling)
- [ ] Add visual style dropdown handling
- [ ] Add language selection dropdown handling
- [ ] Add steering prompt text area handling
- [ ] Implement generation monitoring with 600s timeout
- [ ] Add error handling for all customization steps

### Metadata & Session Integration
- [ ] Handle video-specific metadata (thumbnail, duration, visual style)
- [ ] Integrate with session tracking system
- [ ] Store complete customization parameters
- [ ] Add artifact URL and ID capture
- [ ] Implement video thumbnail retrieval

### CLI Integration
- [ ] Add `deepdiver studio video` command
- [ ] Add `--format` option (explainer|brief)
- [ ] Add `--style` option (all visual styles)
- [ ] Add `--language` option (80+ languages)
- [ ] Add `--prompt` option for steering prompt
- [ ] Add `--notebook-id` option for targeting specific notebooks
- [ ] Implement help documentation for video command

### Testing
- [ ] Test basic video generation (default settings)
- [ ] Test all visual styles (Classic, Anime, Whiteboard, etc.)
- [ ] Test Brief vs Explainer formats
- [ ] Test language selection (at least 5 different languages)
- [ ] Test custom steering prompts
- [ ] Test generation monitoring and timeout handling
- [ ] Test concurrent generation with other artifacts
- [ ] Test error scenarios (no sources, network errors, usage limits)
- [ ] Write unit tests for `generate_video_overview()`
- [ ] Write integration tests for end-to-end workflow

### Documentation
- [ ] Update README.md with video overview examples
- [ ] Add video generation examples to documentation
- [ ] Document all visual style options
- [ ] Create troubleshooting guide for common issues
- [ ] Update ROADMAP.md to reflect completion

### Quality Assurance
- [ ] Code review and refactoring
- [ ] Performance optimization
- [ ] Error message clarity and user feedback
- [ ] Cross-platform testing (if applicable)

## 📚 Resources

- [NotebookLM Support: Video Overviews](https://support.google.com/notebooklm/answer/16454555)
- [Google Blog: Nano Banana Visual Styles](https://blog.google/technology/google-labs/video-overviews-nano-banana/)
- [PR #10: Audio Overview Implementation](https://github.com/Gerico1007/deepdiver/pull/10)
- Implementation Guide: `docs/STUDIO_ARTIFACTS_IMPLEMENTATION.md`

## 🔗 Related Issues

- Depends on: Audio Overview implementation (PR #10)
- Blocks: Phase 3 (Mind Map), Phase 4 (Reports)

## 📝 Notes

- Visual styles require 18+ user age verification in NotebookLM
- Follow the same Material Design dialog patterns from Audio Overview
- Ensure concurrent generation support (users can generate multiple artifacts simultaneously)
- Video thumbnail URLs should be captured for session metadata

## 🎨 Assembly Context

**♠️🌿🎸🧵 G.MUSIC ASSEMBLY MODE**

- **♠️ Nyro**: Browser automation architecture, Material Design dialog patterns
- **🌿 Aureon**: Video content quality, visual style emotional resonance
- **🎸 JamAI**: Video workflow harmony, visual-audio integration
- **🧵 Synth**: Chrome MCP orchestration, terminal execution

---

**Success Criteria**: Video Overview generation works reliably with all customization options, integrates seamlessly with session tracking, and provides a great CLI user experience.
