import { useEffect, useRef, useState } from "react";

export default function NewChatModal({ onConfirm, onCancel }) {
  const [prompt, setPrompt] = useState("");
  const textareaRef = useRef(null);

  useEffect(() => {
    textareaRef.current?.focus();
    const onKeyDown = (e) => {
      if (e.key === "Escape") onCancel();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onCancel]);

  const handleConfirm = () => onConfirm(prompt);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleConfirm();
    }
  };

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h3 className="modal-title">新建会话</h3>
        <p className="modal-subtitle">
          自定义系统提示词（可选，留空使用默认「八字大师」角色）
        </p>
        <textarea
          ref={textareaRef}
          className="modal-textarea"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="例如：你是一位资深旅游顾问，擅长日本关西地区的行程规划……"
          rows={6}
        />
        <div className="modal-actions">
          <button className="modal-btn modal-btn-cancel" onClick={onCancel}>
            取消
          </button>
          <button className="modal-btn modal-btn-primary" onClick={handleConfirm}>
            创建
          </button>
        </div>
      </div>
    </div>
  );
}
