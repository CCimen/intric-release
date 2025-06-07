# Thinking Parameter Implementation Plan

## Project Overview
Re-enable the "thinking" parameter in assistant settings that was temporarily disabled during Gemini model implementation. The goal is to provide a complete implementation where users can enable/disable thinking mode based on model capabilities.

## Model Behavior Requirements
- **Gemini 2.5 Flash**: Interactive thinking (user can toggle on/off)
- **Gemini 2.0 Flash**: No thinking capability (hide thinking section)
- **Gemini 2.5 Pro**: Always-on reasoning (show as "Always On", disabled toggle)

## Implementation Strategy
**Selected Approach**: Hybrid Option 2 + 3 (Enhanced UX + Selective Robustness)

### Rationale
- **UX Critical**: Users need clear understanding of thinking mode per model
- **Validation Prevents Issues**: Prevent invalid thinking_budget values
- **Graceful Error Handling**: Handle backend rejections properly
- **Phased Implementation**: Reduce risk, add robustness incrementally

## Implementation Phases

### Phase 1: Core Implementation (High Priority)
Replace disabled section with functional RadioSwitch components and restore backend integration.

#### Tasks:
1. ✅ **Remove temporarily disabled section** (lines 201-217)
   - Removed hardcoded "Temporarily disabled" display
   - Cleared opacity styling and static text

2. ✅ **Add conditional thinking section display logic**
   - Implemented show/hide logic based on model type
   - Uses existing `showThinkingToggle`, `isThinkingInteractive`, `isThinkingAlwaysOn` reactive variables

3. ✅ **Implement RadioSwitch for interactive models** (2.5 Flash)
   - Added functional RadioSwitch component
   - Bound to `thinkingEnabled` state
   - Labels: "On"/"Off"

4. ✅ **Implement always-on indicator for reasoning models** (2.5 Pro)
   - Added disabled RadioSwitch showing "Always On" state
   - Clear indication this cannot be changed

5. ✅ **Uncomment and fix handleThinkingToggle function**
   - Restored commented-out logic (lines 51-65)
   - Proper thinking_budget value setting:
     - 2.5 Flash: 0 (disabled) or 512 (enabled)
     - 2.5 Pro: 1024 (always-on)

### Phase 2: Integration & UX (Medium Priority)

#### Tasks:
6. ✅ **Create handleThinkingToggleSwitch function**
   - Bridge between RadioSwitch sideEffect and existing logic
   - Handles { current, next } parameter structure from RadioSwitch

7. ✅ **Add model-specific tooltip text function**
   - Created `getThinkingTooltipText()` function
   - Dynamic tooltip text based on model type:
     - Interactive models: Explains toggle functionality and performance impact
     - Always-on models: Explains automatic reasoning behavior
     - Fallback: General thinking mode explanation

8. ✅ **Add basic validation for thinking_budget values**
   - Created `validateThinkingBudget()` function
   - Ensures values are within acceptable ranges (0, 512, 1024)
   - Fallback logic for invalid values to prevent backend errors

### Phase 3: Testing & Verification (Medium Priority)

#### Tasks:
9. ⏳ **Test state preservation across behavior changes**
   - Verify thinking_budget persists when switching model behaviors
   - Ensure no unintended resets

10. ⏳ **Test all three model scenarios**
    - **2.5 Flash**: Interactive toggle functionality
    - **2.5 Pro**: Always-on display behavior  
    - **2.0 Flash**: Hidden thinking section

## Technical Implementation Details

### Current State Management
```typescript
// Reactive variables for model detection
$: showThinkingToggle = selectedModel?.reasoning ?? false;
$: isThinkingInteractive = selectedModel?.name === "gemini-2.5-flash-preview-05-20" || selectedModel?.name === "gemini-2.5-flash";
$: isThinkingAlwaysOn = selectedModel?.reasoning && !isThinkingInteractive;

// Convert thinking budget to boolean for RadioSwitch
$: thinkingEnabled = effectiveThinkingBudget !== undefined && effectiveThinkingBudget > 0;
```

### Key Functions
```typescript
function handleThinkingToggle(enabled: boolean) {
  if (isThinkingInteractive) {
    kwArgs.thinking_budget = enabled ? 512 : 0;
  } else if (isThinkingAlwaysOn) {
    kwArgs.thinking_budget = 1024;
  }
}

function handleThinkingToggleSwitch({ current, next }: { current: boolean; next: boolean }) {
  if (current !== next) {
    handleThinkingToggle(next);
  }
}
```

### UI Components Used
- `Input.RadioSwitch`: For toggle functionality
- `Tooltip`: For explanatory text
- Conditional rendering based on model capabilities

## Backend Integration
- Uses existing `ModelKwargs.thinking_budget` parameter
- Values: `0` (disabled), `512` (Flash enabled), `1024` (Pro always-on)
- Preserved across behavior changes in `onSelectedChange` handler

## Testing Strategy
- **Manual Testing**: User to test in dev container during Phase 3
- **Scenarios to Test**:
  1. Switch between Gemini models and verify correct UI behavior
  2. Toggle thinking on/off for 2.5 Flash models
  3. Verify state persistence across model behavior changes
  4. Confirm backend receives correct thinking_budget values

## Progress Tracking
- ✅ Completed
- ⏳ In Progress / Pending
- ❌ Not Started

## New Technical Functions Added

### Model-Specific Tooltip Function
```typescript
function getThinkingTooltipText(): string {
  if (isThinkingInteractive) {
    return "Enable thinking mode to let the model reason through complex problems step by step. This can improve answer quality for complex questions but may increase response time.";
  } else if (isThinkingAlwaysOn) {
    return "This model has reasoning capabilities that are always enabled. The model will automatically think through complex problems before responding.";
  } else {
    return "Enable thinking mode to let the model reason through complex problems step by step before providing an answer.";
  }
}
```

### Validation Function
```typescript
function validateThinkingBudget(value: number): number {
  const validValues = [0, 512, 1024];
  if (validValues.includes(value)) {
    return value;
  }
  // Fallback to closest valid value
  if (value < 256) return 0;
  if (value < 768) return 512;
  return 1024;
}
```

**Current Status**: Phase 1 & 2 Complete, Ready for Phase 3 Testing