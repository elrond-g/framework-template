import { useState } from "react";

function MessageInput({ onSend, disabled }) {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="message-input-wrapper">
      <form className="message-input-form" onSubmit={handleSubmit}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Shift+Enter for new line)"
          disabled={disabled}
          rows={1}
        />
        <button type="submit" disabled={disabled || !text.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

export default MessageInput;
