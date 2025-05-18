<script lang="ts">
  export let users: { user_id: string, username: string }[] = [];
  export let currentUserId: string;
</script>

<div class="users-panel">
  <div class="panel-header">
    <h3>Active Users</h3>
    <span class="user-count">{users.length}</span>
  </div>
  
  <div class="users-list">
    {#if users.length === 0}
      <div class="empty-state">No users online</div>
    {:else}
      <ul>
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
    background-color: #f9f9f9;
    border-left: 1px solid #eee;
    display: flex;
    flex-direction: column;
    width: 240px;
    flex-shrink: 0;
  }
  
  .panel-header {
    padding: 1rem;
    border-bottom: 1px solid #eee;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  h3 {
    font-size: 1rem;
    margin: 0;
    font-weight: 600;
    color: #333;
  }
  
  .user-count {
    background-color: #0066cc;
    color: white;
    border-radius: 12px;
    padding: 0.15rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
  }
  
  .users-list {
    flex: 1;
    overflow-y: auto;
  }
  
  .empty-state {
    padding: 1rem;
    text-align: center;
    color: #999;
    font-size: 0.9rem;
  }
  
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .user-item {
    display: flex;
    align-items: center;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #eee;
  }
  
  .user-item.current-user {
    background-color: rgba(0, 102, 204, 0.05);
  }
  
  .user-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: #0066cc;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.8rem;
    margin-right: 0.75rem;
    flex-shrink: 0;
  }
  
  .user-info {
    flex: 1;
    min-width: 0;
  }
  
  .username {
    display: flex;
    align-items: center;
    font-size: 0.9rem;
    color: #333;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    gap: 0.5rem;
  }
  
  .user-tag {
    font-size: 0.7rem;
    padding: 0.1rem 0.3rem;
    background-color: #eee;
    border-radius: 4px;
    color: #666;
  }
  
  .ai-tag {
    font-size: 0.7rem;
    padding: 0.1rem 0.3rem;
    background-color: #0066cc;
    border-radius: 4px;
    color: white;
  }
</style> 