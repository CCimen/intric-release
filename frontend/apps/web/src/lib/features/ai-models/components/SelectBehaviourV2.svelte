<script lang="ts">
  import {
    behaviourList,
    getBehaviour,
    getKwargs,
    type ModelBehaviour,
    type ModelKwArgs
  } from "../ModelBehaviours";
  import { createSelect } from "@melt-ui/svelte";
  import { IconChevronDown } from "@intric/icons/chevron-down";
  import { IconCheck } from "@intric/icons/check";
  import { IconQuestionMark } from "@intric/icons/question-mark";
  import { Input, Tooltip } from "@intric/ui";
  import type { CompletionModel } from "@intric/intric-js";

  export let kwArgs: ModelKwArgs;
  export let isDisabled: boolean;
  export let selectedModel: CompletionModel | null = null;
  export let aria: AriaProps = { "aria-label": "Select model behaviour" };

  // Thinking mode logic
  $: showThinkingToggle = selectedModel?.reasoning ?? false;
  $: isThinkingInteractive = selectedModel?.name === "gemini-2.5-flash-preview-05-20" || selectedModel?.name === "gemini-2.5-flash";
  $: isThinkingAlwaysOn = selectedModel?.reasoning && !isThinkingInteractive;
  
  // For display purposes: get the effective thinking budget value
  $: effectiveThinkingBudget = (() => {
    if (!showThinkingToggle) return undefined;
    
    // If thinking_budget is already set, use that value
    if (kwArgs.thinking_budget !== undefined && kwArgs.thinking_budget !== null) {
      return kwArgs.thinking_budget;
    }
    
    // For always-on models (2.5 Pro), show as enabled for display only
    if (isThinkingAlwaysOn) {
      return 1024; // Display value only - NOT set in kwArgs
    }
    
    // For interactive models (2.5 Flash), show as disabled by default
    return 0; // Show as disabled - NOT set in kwArgs
  })();
  
  // DISABLE auto-initialization completely to prevent backend errors
  // thinking_budget is only set when user explicitly interacts

  // Convert thinking budget to boolean for RadioSwitch
  $: thinkingEnabled = effectiveThinkingBudget !== undefined && effectiveThinkingBudget > 0;
  
  function validateThinkingBudget(value: number): number {
    // Validate thinking_budget values are within acceptable ranges
    const validValues = [0, 512, 1024];
    if (validValues.includes(value)) {
      return value;
    }
    // Fallback to closest valid value
    if (value < 256) return 0;
    if (value < 768) return 512;
    return 1024;
  }

  function handleThinkingToggle(enabled: boolean) {
    if (isThinkingInteractive) {
      // For 2.5 Flash: user can enable/disable thinking
      const newValue = validateThinkingBudget(enabled ? 512 : 0);
      kwArgs.thinking_budget = newValue;
      console.log("Thinking toggle for 2.5 Flash:", enabled ? "enabled (512)" : "disabled (0)");
    } else if (isThinkingAlwaysOn) {
      // For 2.5 Pro: always enabled, cannot be changed
      const newValue = validateThinkingBudget(1024);
      kwArgs.thinking_budget = newValue;
      console.log("Thinking for 2.5 Pro - always enabled (1024)");
    }
  }

  function handleThinkingToggleSwitch({ current, next }: { current: boolean; next: boolean }) {
    if (current !== next) {
      handleThinkingToggle(next);
    }
  }

  function getThinkingTooltipText(): string {
    if (isThinkingInteractive) {
      return "Enable thinking mode to let the model reason through complex problems step by step. This can improve answer quality for complex questions but may increase response time.";
    } else if (isThinkingAlwaysOn) {
      return "This model has reasoning capabilities that are always enabled. The model will automatically think through complex problems before responding.";
    } else {
      return "Enable thinking mode to let the model reason through complex problems step by step before providing an answer.";
    }
  }

  const {
    elements: { trigger, menu, option },
    helpers: { isSelected },
    states: { selected }
  } = createSelect<ModelBehaviour>({
    defaultSelected: { value: getBehaviour(kwArgs) },
    positioning: {
      placement: "bottom",
      fitViewport: true,
      sameWidth: true
    },
    portal: null,
    onSelectedChange: ({ next }) => {
      const args = next?.value ? getKwargs(next.value) : getKwargs("default");
      // If the user selects "custom", we want to keep the current kwargs settings if they already are custom
      // However, if they are not, then we initialise with a default custom setting
      const customArgs =
        getBehaviour(kwArgs) === "custom" ? kwArgs : { temperature: 1, top_p: null, thinking_budget: kwArgs.thinking_budget };
      // Preserve thinking_budget when changing behaviors
      const newArgs = args ? { ...args, thinking_budget: kwArgs.thinking_budget } : customArgs;
      // keep in mind: setting the kwargs will trigger the `watchKwArgs` function
      kwArgs = newArgs;
      return next;
    }
  });

  // This function will only be called on direct user input of custom temperature
  // If the selected value is not a named value, it will set the Kwargs
  // This can't be a declarative statement with $: as it would fire in too many situations
  let customTemp: number = 1;
  function maybeSetKwArgsCustom() {
    const args = { 
      temperature: customTemp, 
      top_p: null,
      thinking_budget: kwArgs.thinking_budget // Preserve thinking_budget
    };
    if (getBehaviour(args) === "custom") {
      kwArgs = args;
    }
  }

  function watchChanges(currentKwArgs: ModelKwArgs) {
    if (isDisabled) {
      $selected = { value: "default" };
      return;
    }

    const behaviour = getBehaviour(currentKwArgs);

    if ($selected?.value !== behaviour) {
      $selected = { value: behaviour };
    }

    if (
      behaviour === "custom" &&
      currentKwArgs.temperature &&
      currentKwArgs.temperature !== customTemp
    ) {
      customTemp = currentKwArgs.temperature;
    }
  }

  $: watchChanges(kwArgs);
</script>

<button
  {...$trigger}
  {...aria}
  use:trigger
  disabled={isDisabled}
  class:hover:cursor-default={isDisabled}
  class:text-secondary={isDisabled}
  class="border-default hover:bg-hover-default flex h-16 items-center justify-between border-b px-4"
>
  <span class="capitalize">{$selected?.value ?? "No behaviour found"}</span>
  <IconChevronDown />
</button>

<div
  class="border-stronger bg-primary z-20 flex flex-col overflow-y-auto rounded-lg border shadow-xl"
  {...$menu}
  use:menu
>
  <div
    class="bg-frosted-glass-secondary border-default sticky top-0 border-b px-4 py-2 font-mono text-sm"
  >
    Select a model behaviour
  </div>
  {#each behaviourList as behavior (behavior)}
    <div
      class="border-default hover:bg-hover-stronger flex min-h-16 items-center justify-between border-b px-4 hover:cursor-pointer"
      {...$option({ value: behavior })}
      use:option
    >
      <span class="capitalize">
        {behavior}
      </span>
      <div class="check {$isSelected(behavior) ? 'block' : 'hidden'}">
        <IconCheck class="text-positive-default" />
      </div>
    </div>
  {/each}
</div>

{#if $selected?.value === "custom"}
  <div
    class="border-default hover:bg-hover-stronger flex h-[4.125rem] items-center justify-between gap-8 border-b px-4"
  >
    <div class="flex items-center gap-2">
      <p class="w-24" aria-label="Temperature setting" id="temperature_label">Temperature</p>
      <Tooltip
        text="Randomness: A value between 0 and 2 (Default: 1)\nHigher values will create more creative responses.\nLower values will be more deterministic."
      >
        <IconQuestionMark class="text-muted hover:text-primary" />
      </Tooltip>
    </div>
    <Input.Slider
      bind:value={customTemp}
      max={2}
      min={0}
      step={0.01}
      onInput={maybeSetKwArgsCustom}
    />
    <Input.Number
      onInput={maybeSetKwArgsCustom}
      bind:value={customTemp}
      step={0.01}
      max={2}
      min={0}
      hiddenLabel={true}
    ></Input.Number>
  </div>
{/if}

{#if showThinkingToggle}
  <div
    class="border-default hover:bg-hover-stronger flex h-[4.125rem] items-center justify-between gap-8 border-b px-4"
  >
    <div class="flex items-center gap-2">
      <p class="w-24" aria-label="Thinking setting" id="thinking_label">Thinking</p>
      <Tooltip
        text={getThinkingTooltipText()}
      >
        <IconQuestionMark class="text-muted hover:text-primary" />
      </Tooltip>
    </div>
    <div class="flex items-center gap-4">
      {#if isThinkingInteractive}
        <Input.RadioSwitch
          bind:value={thinkingEnabled}
          labelTrue="On"
          labelFalse="Off"
          disabled={false}
          sideEffect={handleThinkingToggleSwitch}
        />
      {:else if isThinkingAlwaysOn}
        <Input.RadioSwitch
          value={true}
          labelTrue="Always On"
          labelFalse="Off"
          disabled={true}
        />
      {/if}
    </div>
  </div>
{/if}

{#if isDisabled}
  <p
    class="label-warning border-label-default bg-label-dimmer text-label-stronger mt-2.5 rounded-md border px-2 py-1 text-sm"
  >
    <span class="font-bold">Warning:&nbsp;</span>Temperature settings not available for this model.
  </p>
{/if}

<style lang="postcss">
  @reference "@intric/ui/styles";
  div[data-highlighted] {
    @apply bg-hover-default;
  }

  /* div[data-selected] { } */

  div[data-disabled] {
    @apply opacity-30 hover:bg-transparent;
  }
</style>
