function MessageBubble({ role, content, showRetry, onRetry }) {
  return (
    <div className={`message-bubble ${role}`}>
      <div className="message-content">{content}</div>
      {showRetry && (role === "assistant" || role === "error") && (
        <button className="retry-btn" onClick={onRetry}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10"></polyline>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
          </svg>
          <span>重试</span>
        </button>
      )}
    </div>
  );
}

export default MessageBubble;
