import { useState, useRef, useEffect } from "react";

const API = "http://localhost:8000";

export default function Assistant() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hello! I'm your EEE department assistant. How can i help you?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage() {
    const question = input.trim();
    if (!question || loading) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Something went wrong");
      setMessages((prev) => [...prev, { role: "assistant", text: data.answer }]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: `Error: ${e.message}`, isError: true },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="chat-page w-3/4">

      <main className="chat-main">

        <div className="messages-area">
          {messages.map((msg, i) => (
            <Message key={i} msg={msg} />
          ))}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        <div className="input-area">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              className="chat-input"
              placeholder="Ask an engineering question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              rows={1}
            />
            <button
              className="send-btn"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              aria-label="Send"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>
      </main>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        .chat-page {
          display: flex;
          height: 100vh;
          background: #f7f6f3;
          font-family: 'DM Sans', sans-serif;
        }

        /* ── Main ── */
        .chat-main {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        /* ── Messages ── */
        .messages-area {
          flex: 1;
          overflow-y: auto;
          padding: 32px;
          display: flex;
          flex-direction: column;
          gap: 24px;
          scroll-behavior: smooth;
        }

        .messages-area::-webkit-scrollbar { width: 4px; }
        .messages-area::-webkit-scrollbar-track { background: transparent; }
        .messages-area::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }

        .message {
          display: flex;
          gap: 14px;
          max-width: 780px;
          animation: msgIn 0.3s ease;
        }

        @keyframes msgIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .message.user {
          align-self: flex-end;
          flex-direction: row-reverse;
        }

        .msg-avatar {
          width: 34px;
          height: 34px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 0.75rem;
          font-weight: 600;
          flex-shrink: 0;
          margin-top: 2px;
        }

        .message.assistant .msg-avatar {
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          color: white;
          font-family: 'Instrument Serif', serif;
        }

        .message.user .msg-avatar {
          background: #e8e6e0;
          color: #666;
        }

        .msg-bubble {
          padding: 14px 18px;
          border-radius: 14px;
          font-size: 0.9rem;
          line-height: 1.7;
          max-width: calc(100% - 50px);
        }

        .message.assistant .msg-bubble {
          background: white;
          color: #2a2a38;
          border: 1px solid #eae8e2;
          border-bottom-left-radius: 4px;
          box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        }

        .message.assistant .msg-bubble.error {
          background: #fff5f5;
          border-color: #ffd0d0;
          color: #c0392b;
        }

        .message.user .msg-bubble {
          background: #1a1a24;
          color: #e8e8f0;
          border-bottom-right-radius: 4px;
        }

        /* ── Typing indicator ── */
        .typing {
          display: flex;
          gap: 14px;
          align-items: center;
        }

        .typing-avatar {
          width: 34px;
          height: 34px;
          border-radius: 50%;
          background: linear-gradient(135deg, #6366f1, #8b5cf6);
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'Instrument Serif', serif;
          font-size: 0.75rem;
          color: white;
          flex-shrink: 0;
        }

        .typing-dots {
          display: flex;
          gap: 5px;
          padding: 14px 18px;
          background: white;
          border: 1px solid #eae8e2;
          border-radius: 14px;
          border-bottom-left-radius: 4px;
        }

        .typing-dots span {
          width: 7px;
          height: 7px;
          background: #c5c3bb;
          border-radius: 50%;
          animation: bounce 1.2s infinite;
        }

        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes bounce {
          0%, 60%, 100% { transform: translateY(0); }
          30% { transform: translateY(-6px); }
        }

        /* ── Input ── */
        .input-area {
          padding: 20px 32px 24px;
          background: #faf9f7;
          border-top: 1px solid #e8e6e0;
        }

        .input-wrapper {
          display: flex;
          gap: 10px;
          background: white;
          border: 1.5px solid #e0ddd6;
          border-radius: 12px;
          padding: 10px 10px 10px 16px;
          align-items: flex-end;
          transition: border-color 0.2s, box-shadow 0.2s;
        }

        .input-wrapper:focus-within {
          border-color: #a5b4fc;
          box-shadow: 0 0 0 3px rgba(99,102,241,0.08);
        }

        .chat-input {
          flex: 1;
          border: none;
          outline: none;
          resize: none;
          background: transparent;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.9rem;
          color: #2a2a38;
          line-height: 1.5;
          max-height: 140px;
          overflow-y: auto;
        }

        .chat-input::placeholder { color: #bbb; }

        .send-btn {
          width: 38px;
          height: 38px;
          border-radius: 8px;
          background: #1a1a24;
          border: none;
          color: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          transition: background 0.15s, transform 0.1s;
        }

        .send-btn:hover:not(:disabled) {
          background: #6366f1;
        }

        .send-btn:active:not(:disabled) { transform: scale(0.93); }

        .send-btn:disabled {
          opacity: 0.35;
          cursor: not-allowed;
        }

      `}</style>
    </div>
  );
}

function Message({ msg }) {
  return (
    <div className={`message ${msg.role}`}>
      <div className="msg-avatar">{msg.role === "assistant" ? "A" : "U"}</div>
      <div className={`msg-bubble ${msg.isError ? "error" : ""}`}>{msg.text}</div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="typing">
      <div className="typing-avatar">A</div>
      <div className="typing-dots">
        <span /><span /><span />
      </div>
    </div>
  );
}