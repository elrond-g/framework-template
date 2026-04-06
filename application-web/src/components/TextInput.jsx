import { useState, useRef } from "react";

function TextInput({ onSend, disabled }) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
    // 重置 textarea 高度
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleInput = (e) => {
    setText(e.target.value);
    // 自动调整高度
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 150) + "px";
  };

  return (
    <div className="text-input-wrapper">
      <div className="text-input-container">
        <textarea
          ref={textareaRef}
          className="text-input"
          placeholder="输入追问内容…（Enter 发送，Shift+Enter 换行）"
          value={text}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
        />
        <button
          className="text-send-btn"
          onClick={handleSubmit}
          disabled={disabled || !text.trim()}
        >
          发送
        </button>
      </div>
    </div>
  );
}

export default TextInput;
