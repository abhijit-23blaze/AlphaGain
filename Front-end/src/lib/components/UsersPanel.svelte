<script lang="ts">
  export let users: { user_id: string, username: string }[] = [];
  export let currentUserId: string;
</script>

<div class="users-panel">
  <div class="users-header">
    <h3>Active Users</h3>
    <span class="user-count">{users.length}</span>
  </div>
  
  <div class="users-list-container">
    {#if users.length === 0}
      <div class="empty-state">No users online</div>
    {:else}
      <ul class="users-list">
        {#each users as user}
          <li class="user-item {user.user_id === currentUserId ? 'current-user' : ''}">
            <div class="user-avatar">
              {user.username[0].toUpperCase()}
            </div>
            <div class="user-info">
              <span class="username">
                {user.username}
                {#if user.user_id === currentUserId}
                  <span class="user-tag">You</span>
                {/if}
                {#if user.user_id === 'ai'}
                  <span class="ai-tag">AI</span>
                {/if}
              </span>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>

<style>
  .users-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: var(--card-bg);
  }
  
  .users-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    border-bottom: 1px solid var(--border-color);
  }
  
  h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 500;
    color: var(--text-light);
  }
  
  .user-count {
    background-color: var(--primary-medium);
    color: var(--text-light);
    border-radius: 12px;
    padding: 0.15rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 500;
  }
  
  .users-list-container {
    flex: 1;
    overflow-y: auto;
  }
  
  .empty-state {
    padding: 1rem;
    text-align: center;
    color: var(--text-muted);
    font-size: 0.85rem;
  }
  
  .users-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .user-item {
    display: flex;
    align-items: center;
    padding: 0.75rem;
    border-bottom: 1px solid var(--border-color);
  }
  
  .user-item.current-user {
    background-color: rgba(148, 137, 121, 0.15);
  }
  
  .user-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: var(--primary-medium);
    color: var(--text-light);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 500;
    font-size: 0.8rem;
    margin-right: 0.75rem;
    flex-shrink: 0;
  }
  
  .current-user .user-avatar {
    background-color: #948979;
  }
  
  .user-info {
    flex: 1;
    min-width: 0;
  }
  
  .username {
    display: flex;
    align-items: center;
    font-size: 0.85rem;
    color: var(--text-light);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    gap: 0.5rem;
  }
  
  .user-tag {
    font-size: 0.65rem;
    padding: 0.1rem 0.3rem;
    background-color: var(--primary-light);
    border-radius: 4px;
    color: var(--text-light);
  }
  
  .ai-tag {
    font-size: 0.65rem;
    padding: 0.1rem 0.3rem;
    background-color: var(--primary-medium);
    border-radius: 4px;
    color: var(--text-light);
  }
</style> 