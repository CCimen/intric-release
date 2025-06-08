<!--
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
-->

<script lang="ts">
  import type { UserTokenUsage } from "@intric/intric-js";
  import { createRender } from "svelte-headless-table";
  import { Button, Table } from "@intric/ui";
  import { formatNumber } from "$lib/core/formatting/formatNumber";
  import UsageBadge from "./UsageBadge.svelte";

  interface Props {
    users: UserTokenUsage[];
    onUserClick: (user: UserTokenUsage) => void;
  }

  const { users, onUserClick }: Props = $props();

  // Sort users by total tokens (highest first) following the pattern
  let sortedUsers = $derived(users.toSorted((a, b) => b.total_tokens - a.total_tokens));
  
  let showAllItems = $state(false);
  let visibleItems = $derived(showAllItems ? sortedUsers : sortedUsers.slice(0, 15));

  const table = Table.createWithResource([]);

  const viewModel = table.createViewModel([
    table.columnPrimary({
      header: "User",
      value: (item) => item.username,
      cell: (item) => {
        return createRender(Table.ButtonCell, {
          label: item.value.username,
          onclick: () => {
            onUserClick(item.value);
          }
        });
      },
      plugins: {
        sort: {
          getSortValue(item) {
            return item.username.toLowerCase();
          }
        }
      }
    }),

    table.column({
      header: "Usage Level",
      accessor: (item) => item.total_requests,
      id: "usage_level",
      cell: (item) => {
        return createRender(UsageBadge, {
          requests: item.value
        });
      },
      plugins: {
        sort: {
          getSortValue(item) {
            return item;
          }
        }
      }
    }),

    table.column({
      header: "Input tokens",
      accessor: "total_input_tokens",
      id: "input_tokens",
      cell: (item) => formatNumber(item.value),
      plugins: {
        sort: {
          getSortValue(item) {
            return item;
          }
        }
      }
    }),

    table.column({
      header: "Output tokens",
      accessor: "total_output_tokens",
      id: "output_tokens", 
      cell: (item) => formatNumber(item.value),
      plugins: {
        sort: {
          getSortValue(item) {
            return item;
          }
        }
      }
    }),

    table.column({
      header: "Total tokens",
      accessor: "total_tokens",
      id: "total_tokens",
      cell: (item) => formatNumber(item.value),
      plugins: {
        sort: {
          getSortValue(item) {
            return item;
          }
        }
      }
    }),

    table.column({
      header: "Requests",
      accessor: "total_requests",
      id: "requests",
      cell: (item) => formatNumber(item.value),
      plugins: {
        sort: {
          getSortValue(item) {
            return item;
          }
        }
      }
    })
  ]);

  // Update table when visibleItems changes - following exact TokenOverviewTable pattern
  $effect(() => {
    table.update(visibleItems);
  });
</script>

<!-- Table following exact TokenOverviewTable pattern -->
<Table.Root {viewModel} resourceName="user" displayAs="list"></Table.Root>

<!-- Show more/less button exactly like TokenOverviewTable -->
{#if users.length > 15}
  <Button
    variant="outlined"
    class="h-12"
    onclick={() => {
      showAllItems = !showAllItems;
    }}
  >
    {showAllItems ? "Show only 15 users" : `Show all ${users.length} users`}
  </Button>
{/if}

<!-- Empty state -->
{#if users.length === 0}
  <div class="text-center py-12">
    <div class="mx-auto w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
      <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
      </svg>
    </div>
    <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No User Activity</h3>
    <p class="text-gray-500 dark:text-gray-400">No users have token usage in the selected time period.</p>
  </div>
{/if}