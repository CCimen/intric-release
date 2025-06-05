<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from "svelte";
  import { createDialog } from "./ctx.js";
  import type { Writable } from "svelte/store";

  export let alert = false;
  export let portal: string | null | undefined = undefined;
  export let openController: Writable<boolean> | undefined = undefined;

  const {
    states: { open }
  } = createDialog(alert, portal, openController);

  export { open as isOpen };

  const dispatch = createEventDispatcher();
  let unsubscribe: (() => void) | undefined;

  onMount(() => {
    unsubscribe = open.subscribe((visible) => {
      if (visible) {
        dispatch("open");
      } else {
        dispatch("close");
      }
    });

    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  });

  onDestroy(() => {
    // Ensure cleanup happens even if component is destroyed before mount completes
    if (unsubscribe) {
      unsubscribe();
    }
  });
</script>

<slot />
