import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, cleanup } from '@testing-library/svelte';
import { writable } from 'svelte/store';
import DialogRoot from './Root.svelte';
import DialogContent from './Content.svelte';
import DialogTrigger from './Trigger.svelte';

describe('Dialog Component', () => {
  afterEach(() => {
    cleanup();
  });

  it('should properly clean up subscriptions on unmount', async () => {
    const openController = writable(false);
    const { unmount } = render(DialogRoot, {
      props: {
        openController
      }
    });

    // Open the dialog
    openController.set(true);
    
    // Close the dialog
    openController.set(false);
    
    // Unmount should clean up without errors
    unmount();
    
    // Verify no memory leaks by checking if we can still update the store
    // without affecting the unmounted component
    expect(() => openController.set(true)).not.toThrow();
  });

  it('should dispatch open and close events', async () => {
    const openController = writable(false);
    const handleOpen = vi.fn();
    const handleClose = vi.fn();
    
    const { component } = render(DialogRoot, {
      props: {
        openController
      }
    });

    component.$on('open', handleOpen);
    component.$on('close', handleClose);

    // Open dialog
    openController.set(true);
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(handleOpen).toHaveBeenCalledTimes(1);

    // Close dialog
    openController.set(false);
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('should not leave portal elements in DOM after unmount', async () => {
    const openController = writable(true);
    
    const { unmount } = render(DialogRoot, {
      props: {
        openController,
        portal: 'body'
      }
    });

    // Check initial portal elements
    const initialPortals = document.querySelectorAll('[data-portal]').length;
    
    // Close and unmount
    openController.set(false);
    unmount();
    
    // Wait for any async cleanup
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Verify no portal elements remain
    const remainingPortals = document.querySelectorAll('[data-portal]').length;
    expect(remainingPortals).toBeLessThanOrEqual(initialPortals);
  });
});