<script lang="ts">
  import { onMount, afterUpdate } from 'svelte';
  import { marked } from 'marked';
  import hljs from 'highlight.js';
  import type { Message } from '../types';
  
  export let message: Message;
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
  
  // Process message content as markdown
  $: {
    try {
      // Mark string as string type to avoid type issues
      renderedContent = marked.parse(message.content) as string;
    } catch (e) {
      console.error('Error parsing markdown:', e);
      renderedContent = message.content;
    }
  }
  
  // After content updates, apply syntax highlighting to any code blocks
  afterUpdate(() => {
    if (contentElement) {
      // Find all unhighlighted code blocks and apply highlighting
      const codeBlocks = contentElement.querySelectorAll('pre code:not(.hljs)');
      codeBlocks.forEach((block) => {
        hljs.highlightElement(block as HTMLElement);
      });
    }
  });
</script>

<div class="message {message.role}">
  <div class="avatar">
    {#if message.role === 'assistant'}
      <div class="assistant-avatar">AI</div>
    {:else}
      <div class="user-avatar">You</div>
    {/if}
  </div>
  <div class="content">
    {#if message.role === 'assistant'}
      <div class="markdown-content" bind:this={contentElement} contenteditable="false" bind:innerHTML={renderedContent}></div>
    {:else}
      <p>{message.content}</p>
    {/if}
  </div>
</div>

<style>
  .message {
    display: flex;
    gap: 1rem;
    padding: 0.5rem;
    border-radius: 8px;
    max-width: 100%;
  }
  
  .message.user {
    background-color: #f0f0f0;
    align-self: flex-end;
  }
  
  .message.assistant {
    background-color: #f9f9f9;
    align-self: flex-start;
  }
  
  .avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    flex-shrink: 0;
  }
  
  .assistant-avatar, .user-avatar {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
  }
  
  .assistant-avatar {
    background-color: #0066cc;
    color: white;
  }
  
  .user-avatar {
    background-color: #333;
    color: white;
  }
  
  .content {
    flex: 1;
  }
  
  p {
    margin: 0;
    white-space: pre-wrap;
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
    background-color: #f2f2f2;
    padding: 0.75em;
    border-radius: 4px;
    overflow-x: auto;
    margin: 0.75em 0;
  }
  
  .markdown-content :global(code) {
    font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: 0.9em;
    background-color: #f2f2f2;
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
    border-left: 4px solid #ddd;
    color: #555;
  }
  
  .markdown-content :global(a) {
    color: #0066cc;
    text-decoration: none;
  }
  
  .markdown-content :global(a:hover) {
    text-decoration: underline;
  }
  
  .markdown-content :global(table) {
    border-collapse: collapse;
    margin: 1em 0;
    width: 100%;
  }
  
  .markdown-content :global(th),
  .markdown-content :global(td) {
    border: 1px solid #ddd;
    padding: 0.5em;
    text-align: left;
  }
  
  .markdown-content :global(th) {
    background-color: #f2f2f2;
    font-weight: 600;
  }
</style> 