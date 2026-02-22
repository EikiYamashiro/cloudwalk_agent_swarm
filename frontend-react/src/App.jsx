import { useEffect, useMemo, useRef, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const SESSION_KEY = "cloudwalk_session";

function formatMoney(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "BRL"
  }).format(value);
}

function formatDate(value) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString("en-US");
}

function loadStoredSession() {
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveSession(session) {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

function clearSession() {
  window.localStorage.removeItem(SESSION_KEY);
}

export default function App() {
  const chatLogRef = useRef(null);
  const [session, setSession] = useState(() => loadStoredSession());
  const [usernameInput, setUsernameInput] = useState("");
  const [messageInput, setMessageInput] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi, I am your CloudWalk assistant. I can help with transfers and support questions."
    }
  ]);
  const [transfers, setTransfers] = useState([]);
  const [isSending, setIsSending] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const canSend = useMemo(
    () => messageInput.trim().length > 0 && !isSending && !!session,
    [messageInput, isSending, session]
  );

  const loadTransfers = async () => {
    if (!session?.user_id) {
      setTransfers([]);
      return;
    }

    const response = await fetch(
      `${API_URL}/customers/${encodeURIComponent(session.user_id)}/transfers?limit=20`
    );
    if (!response.ok) {
      setTransfers([]);
      return;
    }

    const data = await response.json();
    setTransfers(data.transfers || []);
  };

  useEffect(() => {
    if (!session?.user_id) {
      return;
    }
    loadTransfers();
  }, [session?.user_id]);

  useEffect(() => {
    const element = chatLogRef.current;
    if (!element) {
      return;
    }
    element.scrollTo({
      top: element.scrollHeight,
      behavior: "smooth"
    });
  }, [messages]);

  const handleLogin = async (event) => {
    event.preventDefault();
    const username = usernameInput.trim();
    if (!username) {
      return;
    }

    setIsLoggingIn(true);
    setErrorMessage("");

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username })
      });

      if (!response.ok) {
        setErrorMessage("Could not sign in right now. Please try again.");
        setIsLoggingIn(false);
        return;
      }

      const data = await response.json();
      const nextSession = { user_id: data.user_id, username: data.username };
      setSession(nextSession);
      saveSession(nextSession);
      setUsernameInput("");
      setMessages([
        {
          role: "assistant",
          content: `Welcome ${data.username}. How can I help you today?`
        }
      ]);
    } catch {
      setErrorMessage("Network error while signing in.");
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => {
    setSession(null);
    clearSession();
    setTransfers([]);
    setIsHistoryOpen(false);
    setErrorMessage("");
    setMessages([
      {
        role: "assistant",
        content:
          "Hi, I am your CloudWalk assistant. I can help with transfers and support questions."
      }
    ]);
  };

  const handleSendMessage = async (event) => {
    event.preventDefault();
    const content = messageInput.trim();
    if (!content || !session?.user_id) {
      return;
    }

    const nextMessages = [...messages, { role: "user", content }];
    setMessages(nextMessages);
    setMessageInput("");
    setIsSending(true);
    setErrorMessage("");

    try {
      const response = await fetch(`${API_URL}/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: content,
          user_id: session.user_id
        })
      });

      if (!response.ok) {
        setMessages([
          ...nextMessages,
          {
            role: "assistant",
            content: "I could not process that request right now. Please try again."
          }
        ]);
        setErrorMessage("API communication failed.");
        setIsSending(false);
        return;
      }

      const data = await response.json();
      setMessages([
        ...nextMessages,
        { role: "assistant", content: data.response || "No response at the moment." }
      ]);
      await loadTransfers();
    } catch {
      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: "I could not process that request right now. Please try again."
        }
      ]);
      setErrorMessage("Network error while calling the API.");
    } finally {
      setIsSending(false);
    }
  };

  if (!session) {
    return (
      <div className="auth-shell">
        <section className="auth-card">
          <p className="eyebrow">CloudWalk</p>
          <h1>Sign In</h1>
          <p className="muted">Enter your username to continue.</p>
          <form onSubmit={handleLogin} className="stack">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              value={usernameInput}
              onChange={(event) => setUsernameInput(event.target.value)}
              placeholder="Your name"
            />
            <button type="submit" disabled={isLoggingIn}>
              {isLoggingIn ? "Signing in..." : "Sign in"}
            </button>
          </form>
          {errorMessage && <p className="error-text">{errorMessage}</p>}
        </section>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">CloudWalk</p>
          <h1>Cloudwalk Assistant</h1>
          <p className="muted user-tag">
            Signed in as <strong>{session.username}</strong>
          </p>
        </div>
        <div className="topbar-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => setIsHistoryOpen(true)}
          >
            Transfer history
          </button>
          <button type="button" className="secondary-button" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </header>

      <main className="layout single-column">
        <section className="panel card chat-card">
          <h2>Chat</h2>
          <div className="chat-log" ref={chatLogRef}>
            {messages.map((message, index) => (
              <article key={index} className={`bubble ${message.role}`}>
                <span className="bubble-role">
                  {message.role === "assistant" ? "Assistant" : "You"}
                </span>
                <p>{message.content}</p>
              </article>
            ))}
            {isSending && (
              <article className="bubble assistant loading-bubble">
                <span className="bubble-role">Assistant</span>
                <div className="loading-row">
                  <span className="loading-dot" />
                  <span>Thinking...</span>
                </div>
              </article>
            )}
          </div>

          <form onSubmit={handleSendMessage} className="composer">
            <input
              value={messageInput}
              onChange={(event) => setMessageInput(event.target.value)}
              placeholder="Type your message"
            />
            <button type="submit" disabled={!canSend}>
              {isSending ? "Sending..." : "Send"}
            </button>
          </form>
          {errorMessage && <p className="error-text">{errorMessage}</p>}
        </section>
      </main>

      {isHistoryOpen && (
        <div className="modal-overlay" onClick={() => setIsHistoryOpen(false)}>
          <section className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h2>Transfer history</h2>
              <button
                type="button"
                className="icon-button"
                onClick={() => setIsHistoryOpen(false)}
              >
                Close
              </button>
            </div>

            {transfers.length === 0 && (
              <p className="muted">No transfer activity found for this account.</p>
            )}

            <ul className="transfer-list">
              {transfers.map((transfer, index) => (
                <li key={`${transfer.created_at}-${index}`}>
                  <div className="transfer-row">
                    <span
                      className={`direction-badge ${
                        transfer.direction === "received" ? "received" : "sent"
                      }`}
                    >
                      {transfer.direction}
                    </span>
                    <p className="transfer-destination">{transfer.counterparty}</p>
                  </div>
                  <p className="transfer-meta">
                    {formatMoney(transfer.amount)} | {transfer.status}
                  </p>
                  <p className="transfer-meta">{formatDate(transfer.created_at)}</p>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </div>
  );
}
