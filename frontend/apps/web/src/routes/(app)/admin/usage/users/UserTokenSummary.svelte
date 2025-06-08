<!--
    Copyright (c) 2024 Sundsvalls Kommun

    Licensed under the MIT License.
-->

<script lang="ts">
  import { Settings } from "$lib/components/layout";
  import type { TokenUsageSummary } from "@intric/intric-js";
  import UserOverviewBar from "./UserOverviewBar.svelte";
  import UserTokenTable from "./UserTokenTable.svelte";
  import { CalendarDate } from "@internationalized/date";
  import { getIntric } from "$lib/core/Intric";
  import { Input } from "@intric/ui";
  import { goto } from "$app/navigation";

  type Props = {
    tokenStats: TokenUsageSummary;
  };

  const { tokenStats }: Props = $props();
  let userStats = $state(null);
  let isLoading = $state(false);

  const intric = getIntric();

  const now = new Date();
  const today = new CalendarDate(now.getFullYear(), now.getMonth() + 1, now.getUTCDate());
  let dateRange = $state({
    start: today.subtract({ days: 30 }),
    end: today
  });

  async function updateUserStats(timeframe: { start: CalendarDate; end: CalendarDate }) {
    isLoading = true;
    try {
      userStats = await intric.usage.tokens.getUsersSummary({
        startDate: timeframe.start.toString(),
        // We add one day so the end day includes the whole day. otherwise this would be interpreted as 00:00
        endDate: timeframe.end.add({ days: 1 }).toString()
      });
    } catch (error) {
      console.error('Failed to load user token usage:', error);
    } finally {
      isLoading = false;
    }
  }

  $effect(() => {
    if (dateRange.start && dateRange.end) {
      updateUserStats(dateRange);
    }
  });

  function onUserClick(user: any) {
    goto(`/admin/usage/users/${user.user_id}`);
  }
</script>

<Settings.Page>
  <Settings.Group title="Overview">
    {#if userStats}
      <UserOverviewBar {userStats}></UserOverviewBar>
    {/if}
  </Settings.Group>
  <Settings.Group title="Details">
    <Settings.Row
      title="Usage by user"
      description="See token usage broken down by individual users within your organization."
      fullWidth
    >
      <div slot="toolbar">
        <Input.DateRange bind:value={dateRange}></Input.DateRange>
      </div>
      
      {#if isLoading}
        <div class="flex justify-center p-8">
          <div class="text-gray-500">Loading user token usage...</div>
        </div>
      {:else if userStats}
        <UserTokenTable users={userStats.users} {onUserClick}></UserTokenTable>
      {:else}
        <div class="flex justify-center p-8">
          <div class="text-gray-500">No user token usage data available for this period.</div>
        </div>
      {/if}
    </Settings.Row>
  </Settings.Group>
</Settings.Page>