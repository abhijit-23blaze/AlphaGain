<script lang="ts">
  import { onMount, afterUpdate } from 'svelte';
  import { marked } from 'marked';
  import hljs from 'highlight.js';
  
  export let message: {
    type: string;
    user_id: string;
    username: string;
    content: string;
    timestamp?: string;
  };
  export let currentUserId: string;
  export let isAiMessage: boolean = false;
  
  let renderedContent: string = '';
  let contentElement: HTMLElement;
  
  // Configure marked options with syntax highlighting
  // Use type assertion to handle the highlight property not in MarkedOptions type
  marked.setOptions({
    gfm: true, // GitHub Flavored Markdown
    breaks: true, // Adds <br> on a single line break
    highlight: function(code: string, lang: string): string {
      // Apply syntax highlighting with highlight.js
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(code, { language: lang }).value;
        } catch (e) {
          console.error('Error highlighting code:', e);
        }
      }
      return hljs.highlightAuto(code).value;
    }
  } as any); // Use type assertion since MarkedOptions type doesn't include highlight
  
  // Process message content as markdown if it's an AI message
  $: {
    try {
      if (isAiMessage) {
        // Mark string as string type to avoid type issues
        renderedContent = marked.parse(message.content) as string;
      } else {
        // For regular user messages, just escape HTML and add line breaks
        renderedContent = message.content
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/\n/g, '<br>');
      }
    } catch (e) {
      console.error('Error parsing content:', e);
      renderedContent = message.content;
    }
  }
  
  // After content updates, apply syntax highlighting to any code blocks
  afterUpdate(() => {
    if (contentElement && isAiMessage) {
      // Find all unhighlighted code blocks and apply highlighting
      const codeBlocks = contentElement.querySelectorAll('pre code:not(.hljs)');
      codeBlocks.forEach((block) => {
        hljs.highlightElement(block as HTMLElement);
      });
    }
  });
  
  // Format timestamp if provided
  $: formattedTime = message.timestamp 
    ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';
  
  // Determine if the message is from the current user
  $: isCurrentUser = message.user_id === currentUserId;
  
  // Determine avatar text (first letter of username)
  $: avatarText = message.username ? message.username[0].toUpperCase() : '?';
</script>

<div class="message {isCurrentUser ? 'current-user' : ''} {message.user_id === 'ai' ? 'ai-message' : ''}">
  <div class="avatar" class:ai-avatar={message.user_id === 'ai'} class:current-user-avatar={isCurrentUser}>
    {avatarText}
  </div>
  
  <div class="message-content">
    <div class="message-header">
      <span class="username">
        {message.username}
        {#if isCurrentUser}
          <span class="user-tag">You</span>
        {/if}
      </span>
      {#if formattedTime}
        <span class="timestamp">{formattedTime}</span>
      {/if}
    </div>
    
    <div class="content">
      {#if isAiMessage}
        <div class="markdown-content" bind:this={contentElement} contenteditable="false" bind:innerHTML={renderedContent}></div>
      {:else}
        <div class="user-content" contenteditable="false" bind:innerHTML={renderedContent}></div>
      {/if}
    </div>
  </div>
</div>

<style>
  .message {
    display: flex;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    max-width: 100%;
    animation: fadeIn 0.3s ease;
  }
  
  .message.current-user {
    background-color: rgba(148, 137, 121, 0.1);
  }
  
  .message.ai-message {
    background-color: rgba(148, 137, 121, 0.15);
  }
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  .avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: var(--primary-darkest);
    color: var(--text-light);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 500;
    font-size: 0.8rem;
    flex-shrink: 0;
  }
  
  .ai-avatar {
    background-color: var(--primary-medium);
  }
  
  .current-user-avatar {
    background-color: var(--primary-medium);
  }
  
  .message-content {
    flex: 1;
    min-width: 0;
  }
  
  .message-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.25rem;
  }
  
  .username {
    font-weight: 500;
    font-size: 0.9rem;
    color: var(--text-light);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .user-tag {
    font-size: 0.7rem;
    padding: 0.1rem 0.3rem;
    background-color: var(--primary-medium);
    border-radius: 4px;
    color: var(--text-light);
    font-weight: 400;
  }
  
  .timestamp {
    font-size: 0.75rem;
    color: var(--text-muted);
  }
  
  .content {
    word-break: break-word;
    color: var(--text-light);
  }
  
  .user-content {
    white-space: pre-wrap;
    line-height: 1.4;
  }
  
  /* Markdown styling */
  .markdown-content {
    line-height: 1.5;
  }
  
  .markdown-content :global(h1),
  .markdown-content :global(h2),
  .markdown-content :global(h3),
  .markdown-content :global(h4),
  .markdown-content :global(h5),
  .markdown-content :global(h6) {
    margin-top: 1em;
    margin-bottom: 0.5em;
    font-weight: 600;
    color: var(--text-light);
  }
  
  .markdown-content :global(h1) {
    font-size: 1.5em;
  }
  
  .markdown-content :global(h2) {
    font-size: 1.3em;
  }
  
  .markdown-content :global(h3) {
    font-size: 1.2em;
  }
  
  .markdown-content :global(p) {
    margin: 0.5em 0;
  }
  
  .markdown-content :global(ul),
  .markdown-content :global(ol) {
    margin: 0.5em 0;
    padding-left: 1.5em;
  }
  
  .markdown-content :global(li) {
    margin: 0.25em 0;
  }
  
  .markdown-content :global(pre) {
    background-color: var(--primary-darkest);
    padding: 0.75em;
    border-radius: 4px;
    overflow-x: auto;
    margin: 0.75em 0;
    border: 1px solid var(--border-color);
  }
  
  .markdown-content :global(code) {
    font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: 0.9em;
    background-color: var(--primary-darkest);
    padding: 0.2em 0.4em;
    border-radius: 3px;
  }
  
  .markdown-content :global(pre code) {
    padding: 0;
    background-color: transparent;
    border-radius: 0;
    font-size: 0.85em;
    overflow-wrap: normal;
    white-space: pre;
  }
  
  .markdown-content :global(blockquote) {
    margin: 0.5em 0;
    padding-left: 1em;
    border-left: 4px solid var(--primary-medium);
    color: var(--text-muted);
  }
  
  .markdown-content :global(a) {
    color: var(--primary-light);
    text-decoration: none;
  }
  
  .markdown-content :global(a:hover) {
    text-decoration: underline;
    color: var(--primary-light);
  }
  
  .markdown-content :global(table) {
    border-collapse: collapse;
    margin: 1em 0;
    width: 100%;
  }
  
  .markdown-content :global(th),
  .markdown-content :global(td) {
    border: 1px solid var(--border-color);
    padding: 0.5em;
    text-align: left;
  }
  
  .markdown-content :global(th) {
    background-color: var(--primary-darkest);
    font-weight: 600;
  }
</style> 