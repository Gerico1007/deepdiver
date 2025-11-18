# Phase 5: Flashcards Implementation

**Labels**: `enhancement`, `studio-artifacts`, `phase-5`, `flashcards`, `study-tools`
**Priority**: High
**Milestone**: NotebookLM Studio Artifacts
**Assignees**: @Gerico1007

## 📋 Description

Implement Flashcard generation and interaction in DeepDiver. Flashcards are interactive study tools with customizable quantity, difficulty, and focus areas. This implementation includes card generation, flipping mechanics, explanation features, and optional export capabilities.

## 🎯 Objectives

- Automate Flashcard generation via NotebookLM's Studio panel
- Support full customization (number, difficulty, focus prompt)
- Enable card interaction (flip, explain, navigate)
- Integrate with session tracking system
- Provide comprehensive CLI interface for flashcard operations
- Support export functionality (if available)

## 🛠️ Technical Details

### Customization Options

1. **Number of Cards**
   - **Fewer**: ~15-20 cards
   - **Standard** (default): ~28-35 cards
   - **More**: ~50-60 cards
   - UI: Button toggle group (3 options)

2. **Difficulty Level**
   - **Easy**: Basic concepts and definitions
   - **Medium** (default): Balanced complexity
   - **Hard**: Advanced concepts and applications
   - UI: Button toggle group (3 options)

3. **Custom Focus Prompt**
   - Freeform text input
   - Examples:
     - "Focus on chapter one"
     - "Key terms only"
     - "Include definitions and examples"
     - "Make front of cards shorter for memorization"

4. **Source Selection**
   - Can specify chapters or specific sources

### Interaction Features

- **Flip Cards**: Click to reveal answer
- **Explain Button**: Get detailed explanation for any card
- **Navigate**: Scroll through cards (e.g., "1 of 28")
- **Expand View**: Full-screen card display option

### Key Selectors

- **Flashcards Tile**: `.create-artifact-button-container:has-text("Flashcards")`
- **Toggle Options**: `button.toggle-option`
- **Difficulty Options**: `button.difficulty-option`
- **Focus Prompt**: `textarea[placeholder="What should the AI focus on?"]`
- **Flashcard Container**: `.flashcard-container`
- **Card Face**: `.flashcard-container .card-face`
- **Explain Button**: `button:has-text("Explain")`
- **Navigation**: `button.next-card`, `button.prev-card`

## ✅ Implementation Checklist

### Research & Planning
- [ ] Research Flashcards UI and DOM structure in NotebookLM
- [ ] Identify all customization controls (toggle groups, text areas)
- [ ] Map card interaction mechanics (flip, explain, navigate)
- [ ] Document card navigation patterns
- [ ] Understand export capabilities (Anki, Quizlet integration)

### Core Implementation - Generation
- [ ] Implement `generate_flashcards()` method in `notebooklm_automator.py`
- [ ] Add number selection (button toggle group handling)
- [ ] Add difficulty selection (button toggle group handling)
- [ ] Add custom prompt text area handling
- [ ] Add source selection functionality
- [ ] Implement generation monitoring with 300s timeout
- [ ] Add error handling for customization steps

### Card Interaction
- [ ] Implement `interact_with_flashcard()` method
- [ ] Add card flip functionality
- [ ] Add explain feature integration
- [ ] Add card navigation (next, previous)
- [ ] Implement card number tracking (current position)
- [ ] Add expand/full-screen view handling

### Export & Download
- [ ] Research flashcard export options
- [ ] Implement `export_flashcards()` method
- [ ] Add Anki export (if available)
- [ ] Add Quizlet export (if available)
- [ ] Add generic export fallback (CSV/JSON)
- [ ] Handle download completion

### Metadata & Session Integration
- [ ] Capture flashcard metadata (count, difficulty, number setting)
- [ ] Store custom prompt and source selections
- [ ] Track card interaction history (flips, explains)
- [ ] Add artifact URL and ID capture
- [ ] Integrate with session tracking system
- [ ] Store card content for offline access (optional)

### CLI Integration
- [ ] Add `deepdiver studio flashcards` command
- [ ] Add `--number` option (fewer|standard|more)
- [ ] Add `--difficulty` option (easy|medium|hard)
- [ ] Add `--prompt` option for custom focus
- [ ] Add `--sources` option for source selection
- [ ] Add `--notebook-id` option
- [ ] Add `deepdiver studio flashcard-flip` command for interaction
- [ ] Add `deepdiver studio flashcard-explain` command
- [ ] Add `deepdiver studio flashcards-export` command
- [ ] Implement help documentation with examples

### Testing
- [ ] Test basic flashcard generation (default settings)
- [ ] Test all number options (fewer, standard, more)
- [ ] Test all difficulty levels (easy, medium, hard)
- [ ] Test all number/difficulty combinations
- [ ] Test custom focus prompts
- [ ] Test source-specific flashcard generation
- [ ] Test card flipping mechanics
- [ ] Test explain functionality
- [ ] Test card navigation
- [ ] Test concurrent generation with other artifacts
- [ ] Test export functionality (all available formats)
- [ ] Test error scenarios (no sources, invalid options)
- [ ] Write unit tests for flashcard methods
- [ ] Write integration tests for end-to-end workflow

### Documentation
- [ ] Update README.md with flashcard examples
- [ ] Document all customization options
- [ ] Create guide for effective flashcard prompts
- [ ] Document interaction features
- [ ] Add study workflow examples
- [ ] Document export formats and procedures
- [ ] Update ROADMAP.md to reflect completion

### Quality Assurance
- [ ] Code review and refactoring
- [ ] Performance optimization
- [ ] User interaction responsiveness
- [ ] Error handling robustness
- [ ] Export format validation

## 📚 Resources

- [NotebookLM Support: Flashcards & Quizzes](https://support.google.com/notebooklm/answer/16206563)
- [CNET: NotebookLM Flashcards and Quizzes](https://www.cnet.com/tech/services-and-software/notebooklm-can-now-make-flashcards-and-quizzes-to-help-you-study/)
- [YouTube: Flashcard Features Demo](https://www.youtube.com/watch?v=mM6TrgMY0G8)
- [AI Maker: Customization Guide](https://aimaker.substack.com/p/learn-ai-agents-notebooklm-customization-guide)
- Implementation Guide: `docs/STUDIO_ARTIFACTS_IMPLEMENTATION.md`

## 🔗 Related Issues

- Depends on: Phase 2 (Video Overview)
- Related to: Phase 6 (Quizzes) - similar UI patterns
- Related to: PR #10 (Audio Overview patterns)

## 📝 Notes

- Flashcards use **button toggle groups** (similar to quizzes) rather than radio buttons
- Explain feature provides AI-powered explanations for any card answer
- Card counts are approximate - actual count may vary slightly
- Export to Anki/Quizlet may not be directly available - fallback formats needed
- Full-screen/expand view improves readability for complex cards
- Custom prompts can significantly improve card quality and focus

## 💡 Use Case Examples

### Basic Study Session
```bash
# Generate standard flashcards for all sources
deepdiver studio flashcards
```

### Chapter-Focused Study
```bash
# Generate many flashcards focused on chapter 3
deepdiver studio flashcards \
  --number more \
  --difficulty medium \
  --prompt "Focus on Chapter 3: Neural Networks"
```

### Quick Review
```bash
# Generate fewer easy cards for quick review
deepdiver studio flashcards \
  --number fewer \
  --difficulty easy \
  --prompt "Key terms and definitions only"
```

### Advanced Concepts
```bash
# Generate many hard cards for deep learning
deepdiver studio flashcards \
  --number more \
  --difficulty hard \
  --prompt "Include application scenarios and edge cases"
```

### Card Interaction
```bash
# Flip a specific card
deepdiver studio flashcard-flip --card-number 15

# Get explanation for a card
deepdiver studio flashcard-explain --card-number 8
```

### Export for External Tools
```bash
# Export flashcards to Anki
deepdiver studio flashcards-export --format anki

# Export as CSV for custom import
deepdiver studio flashcards-export --format csv
```

## 🎨 Assembly Context

**♠️🌿🎸🧵 G.MUSIC ASSEMBLY MODE**

- **♠️ Nyro**: Flashcard structure patterns, spaced repetition architecture
- **🌿 Aureon**: Learning resonance, memory retention focus
- **🎸 JamAI**: Q&A rhythm harmony, knowledge flow structure
- **🧵 Synth**: Card interaction orchestration, navigation synthesis

---

**Success Criteria**: Flashcard generation works with all customization options, card interaction is smooth and reliable, explain feature provides valuable insights, and export functionality enables integration with external study tools.
