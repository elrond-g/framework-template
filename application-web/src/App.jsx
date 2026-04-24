import { useState, useEffect, useRef } from "react";
import ChatWindow from "./components/ChatWindow";
import NewChatModal from "./components/NewChatModal";
import {
  createConversation,
  listConversations,
  deleteConversation,
  updateConversation,
} from "./api/chat";
import "./App.css";

function App() {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [error, setError] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [showNewChatModal, setShowNewChatModal] = useState(false);
  const [pendingFirstMessage, setPendingFirstMessage] = useState(null);
  const editInputRef = useRef(null);

  const loadConversations = async () => {
    const res = await listConversations();
    if (res.code === 0) {
      setConversations(res.data || []);
    } else {
      setError(res.message);
    }
  };

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (editingId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingId]);

  const handleNew = () => {
    setShowNewChatModal(true);
  };

  const handleConfirmNew = async (payload) => {
    setShowNewChatModal(false);
    // preset：使用默认 system_prompt，创建后直接带着首条消息发起对话
    // custom：把自定义 system_prompt 持久化到会话
    const systemPrompt = payload.kind === "custom" ? payload.systemPrompt : "";
    const res = await createConversation("New Conversation", systemPrompt);
    if (res.code !== 0) {
      setError(res.message);
      return;
    }
    if (payload.kind === "preset") {
      setPendingFirstMessage({ text: payload.prompt, formData: payload.formData });
    }
    setActiveId(res.data.id);
    loadConversations();
  };

  const handleDelete = async (id) => {
    const res = await deleteConversation(id);
    if (res.code !== 0) {
      setError(res.message);
    }
    if (activeId === id) setActiveId(null);
    loadConversations();
  };

  const handleDoubleClick = (e, conv) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditingTitle(conv.title);
  };

  const handleRenameSubmit = async (id) => {
    const trimmed = editingTitle.trim();
    if (!trimmed) {
      setEditingId(null);
      return;
    }
    const res = await updateConversation(id, trimmed);
    if (res.code !== 0) {
      setError(res.message);
    }
    setEditingId(null);
    loadConversations();
  };

  const handleRenameKeyDown = (e, id) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleRenameSubmit(id);
    } else if (e.key === "Escape") {
      setEditingId(null);
    }
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <button className="new-chat-btn" onClick={handleNew}>
          + New Chat
        </button>
        <ul className="conversation-list">
          {conversations.map((c) => (
            <li
              key={c.id}
              className={c.id === activeId ? "active" : ""}
              onClick={() => setActiveId(c.id)}
            >
              {editingId === c.id ? (
                <input
                  ref={editInputRef}
                  className="conv-title-input"
                  value={editingTitle}
                  onChange={(e) => setEditingTitle(e.target.value)}
                  onBlur={() => handleRenameSubmit(c.id)}
                  onKeyDown={(e) => handleRenameKeyDown(e, c.id)}
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span
                  className="conv-title"
                  onDoubleClick={(e) => handleDoubleClick(e, c)}
                >
                  {c.title}
                </span>
              )}
              <button
                className="delete-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(c.id);
                }}
              >
                x
              </button>
            </li>
          ))}
        </ul>
      </aside>
      <main className="main">
        {error && (
          <div className="error-bar">
            <span>{error}</span>
            <button onClick={() => setError(null)}>x</button>
          </div>
        )}
        {activeId ? (
          <ChatWindow
            conversationId={activeId}
            onTitleUpdated={loadConversations}
            initialMessage={pendingFirstMessage}
            onInitialMessageConsumed={() => setPendingFirstMessage(null)}
          />
        ) : (
          <div className="empty-state">
            <h2>Welcome to Fleeting</h2>
            <p>Create a new conversation to get started.</p>
          </div>
        )}
      </main>
      {showNewChatModal && (
        <NewChatModal
          onConfirm={handleConfirmNew}
          onCancel={() => setShowNewChatModal(false)}
        />
      )}
    </div>
  );
}

export default App;
