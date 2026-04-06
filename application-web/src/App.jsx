import { useState, useEffect } from "react";
import ChatWindow from "./components/ChatWindow";
import {
  createConversation,
  listConversations,
  deleteConversation,
} from "./api/chat";
import "./App.css";

function App() {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [error, setError] = useState(null);

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

  const handleNew = async () => {
    const res = await createConversation();
    if (res.code === 0) {
      setActiveId(res.data.id);
      loadConversations();
    } else {
      setError(res.message);
    }
  };

  const handleDelete = async (id) => {
    const res = await deleteConversation(id);
    if (res.code !== 0) {
      setError(res.message);
    }
    if (activeId === id) setActiveId(null);
    loadConversations();
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
              <span className="conv-title">{c.title}</span>
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
          <ChatWindow conversationId={activeId} onTitleUpdated={loadConversations} />
        ) : (
          <div className="empty-state">
            <h2>Welcome to Chatbot</h2>
            <p>Create a new conversation to get started.</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
