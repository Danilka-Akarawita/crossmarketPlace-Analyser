"use client";

import type { CSSProperties } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";

type ChatRole = "user" | "assistant" | "system" | "error";

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: number;
};

const DEFAULT_USER_ID = "guest-user";

function safeRandomId() {
  if (typeof globalThis.crypto !== "undefined" && globalThis.crypto.randomUUID) {
    return globalThis.crypto.randomUUID();
  }

  return Math.random().toString(36).slice(2, 10);
}

function formatAssistantResponse(payload: unknown): string {
  if (payload == null) {
    return "(empty response)";
  }

  if (typeof payload === "string") {
    return payload;
  }

  if (typeof payload === "object") {
    try {
      return JSON.stringify(payload, null, 2);
    } catch (error) {
      console.error("Failed to stringify assistant payload", error);
    }
  }

  return String(payload);
}

export function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [userId, setUserId] = useState(DEFAULT_USER_ID);
  const [sessionId, setSessionId] = useState<string>("");
  const [isSending, setIsSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const backendUrl = useMemo(() => {
    return process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
  }, []);

  useEffect(() => {
    setSessionId(safeRandomId());
  }, []);

  const resetConversation = useCallback(() => {
    setMessages([]);
    setErrorMessage(null);
    setSessionId(safeRandomId());
  }, []);

  const appendMessage = useCallback((role: ChatRole, content: string) => {
    setMessages((previous) => [
      ...previous,
      {
        id: safeRandomId(),
        role,
        content,
        timestamp: Date.now(),
      },
    ]);
  }, []);

  const handleSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      setErrorMessage(null);

      const trimmed = inputValue.trim();
      if (!trimmed) {
        return;
      }

      appendMessage("user", trimmed);
      setInputValue("");
      setIsSending(true);

      const payload = {
        query: trimmed,
        user_id: userId.trim() || DEFAULT_USER_ID,
        session_id: sessionId || safeRandomId(),
      };

      try {
        const response = await fetch(`${backendUrl}/chat`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            `Backend returned ${response.status}: ${errorText || response.statusText}`,
          );
        }

        const data = (await response.json()) as Record<string, unknown>;
        const assistantAnswer = formatAssistantResponse(data.answer);

        appendMessage("assistant", assistantAnswer);
      } catch (error) {
        console.error("Chat request failed", error);
        const message =
          error instanceof Error ? error.message : "Unknown error occurred";
        appendMessage("error", message);
        setErrorMessage(message);
      } finally {
        setIsSending(false);
      }
    },
    [appendMessage, backendUrl, inputValue, sessionId, userId],
  );

  return (
    <div style={styles.wrapper}>
      <header style={styles.header}>
        <div>
          <h2 style={styles.title}>Laptop Intelligence</h2>
          <p style={styles.subtitle}>
            Ask anything about specs, pricing, or availability and we’ll answer using your
            marketplace data.
          </p>
        </div>
        <button type="button" style={styles.resetButton} onClick={resetConversation}>
          Reset chat
        </button>
      </header>

      <section style={styles.chatSurface}>
        {messages.length === 0 ? (
          <div style={styles.placeholder}>
            <p style={styles.placeholderHeading}>Start the conversation</p>
            <p style={styles.placeholderBody}>
              Try questions like “Find 16GB RAM laptops under $1,200” or “Compare ThinkPad
              X1 Carbon with Dell XPS 13.”
            </p>
          </div>
        ) : (
          messages.map((message) => {
            const isUser = message.role === "user";
            const isAssistant = message.role === "assistant";
            const bubbleStyle = isUser
              ? styles.userBubble
              : isAssistant
              ? styles.assistantBubble
              : styles.errorBubble;
            const name = isUser ? "You" : isAssistant ? "Laptop Intelligence" : "System";
            const avatarText = isUser ? "Y" : isAssistant ? "AI" : "!";

            return (
              <div key={message.id} style={styles.messageBlock}>
                <div style={styles.avatarColumn}>
                  <div
                    style={{
                      ...styles.avatar,
                      background: isUser ? "#1f2937" : isAssistant ? "#2563eb" : "#b91c1c",
                    }}
                  >
                    {avatarText}
                  </div>
                </div>
                <article style={{ ...styles.messageShell, ...bubbleStyle }}>
                  <div style={styles.messageHeaderRow}>
                    <span style={styles.messageAuthor}>{name}</span>
                    <time style={styles.timestamp}>
                      {new Intl.DateTimeFormat("en", {
                        hour: "numeric",
                        minute: "2-digit",
                      }).format(message.timestamp)}
                    </time>
                  </div>
                  <div style={styles.messageContentArea}>
                    <div style={styles.messageText}>{message.content}</div>
                  </div>
                </article>
              </div>
            );
          })
        )}
      </section>

      <form style={styles.composer} onSubmit={handleSubmit}>
        <div style={styles.identityRow}>
          <label style={styles.identityLabel}>
            User ID
            <input
              style={styles.identityInput}
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
            />
          </label>
          <span style={styles.sessionTag}>Session: {sessionId}</span>
        </div>
        <div style={styles.composerRow}>
          <textarea
            style={styles.textArea}
            placeholder="Message Laptop Intelligence"
            rows={2}
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
            disabled={isSending}
          />
          <button
            type="submit"
            style={{
              ...styles.sendButton,
              opacity: isSending || !inputValue.trim() ? 0.5 : 1,
              pointerEvents: isSending || !inputValue.trim() ? "none" : "auto",
            }}
          >
            {isSending ? "Sending…" : "Send"}
          </button>
        </div>
        <div style={styles.metaRow}>
          <small>
            Calling <code>{backendUrl}/chat</code>
          </small>
          {errorMessage ? <small style={styles.errorText}>Last error: {errorMessage}</small> : null}
        </div>
      </form>
    </div>
  );
}

const styles: Record<string, CSSProperties> = {
  wrapper: {
    display: "flex",
    flexDirection: "column",
    gap: "18px",
    maxWidth: "820px",
    margin: "0 auto",
    padding: "24px 28px 32px",
    background: "rgba(255,255,255,0.92)",
    borderRadius: "24px",
    border: "1px solid rgba(226,232,240,0.8)",
    boxShadow: "0 40px 80px -60px rgba(15,23,42,0.55)",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "18px",
    flexWrap: "wrap",
  },
  title: {
    margin: 0,
    fontSize: "1.8rem",
    fontWeight: 600,
  },
  subtitle: {
    margin: "6px 0 0",
    color: "#475569",
    maxWidth: "40rem",
    lineHeight: 1.6,
  },
  resetButton: {
    padding: "10px 16px",
    borderRadius: "999px",
    border: "1px solid rgba(148,163,184,0.5)",
    background: "rgba(244,244,245,0.8)",
    cursor: "pointer",
    fontWeight: 600,
    color: "#0f172a",
  },
  chatSurface: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    minHeight: "420px",
    maxHeight: "60vh",
    overflowY: "auto",
    padding: "8px 12px",
    background: "linear-gradient(180deg, rgba(241,245,249,0.6), rgba(248,250,252,0.6))",
    borderRadius: "18px",
  },
  placeholder: {
    margin: "auto",
    textAlign: "center",
    maxWidth: "24rem",
    color: "#64748b",
    lineHeight: 1.6,
  },
  placeholderHeading: {
    marginBottom: "6px",
    fontWeight: 600,
  },
  placeholderBody: {
    margin: 0,
  },
  messageBlock: {
    display: "flex",
    gap: "12px",
    width: "100%",
    maxWidth: "720px",
    margin: "0 auto 12px",
  },
  avatarColumn: {
    display: "flex",
    alignItems: "flex-start",
  },
  avatar: {
    width: "36px",
    height: "36px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#f8fafc",
    fontWeight: 600,
    fontSize: "0.9rem",
    boxShadow: "0 8px 18px -12px rgba(15,23,42,0.45)",
  },
  messageShell: {
    flexGrow: 1,
    maxWidth: "100%",
    padding: "16px 18px",
    borderRadius: "18px",
    lineHeight: 1.65,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    boxShadow: "0 20px 38px -30px rgba(15,23,42,0.45)",
  },
  assistantBubble: {
    background: "#f8fafc",
    color: "#0f172a",
    border: "1px solid rgba(203,213,225,0.6)",
  },
  userBubble: {
    background: "#0f172a",
    color: "#f8fafc",
    border: "1px solid rgba(15,23,42,0.5)",
  },
  errorBubble: {
    background: "#fee2e2",
    color: "#991b1b",
    border: "1px solid #fecaca",
  },
  messageHeaderRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "6px",
  },
  messageAuthor: {
    fontWeight: 600,
    fontSize: "0.9rem",
  },
  messageContentArea: {
    fontSize: "0.97rem",
  },
  messageText: {
    margin: 0,
    fontFamily: "inherit",
    fontSize: "0.97rem",
    whiteSpace: "pre-wrap",
    overflowWrap: "anywhere",
    wordBreak: "break-word",
    hyphens: "auto",
  },
  timestamp: {
    display: "block",
    marginTop: "8px",
    fontSize: "0.75rem",
    opacity: 0.7,
  },
  composer: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    borderTop: "1px solid rgba(226,232,240,0.8)",
    paddingTop: "12px",
  },
  identityRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "12px",
    flexWrap: "wrap",
  },
  identityLabel: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: "0.85rem",
    color: "#475569",
  },
  identityInput: {
    padding: "8px 12px",
    borderRadius: "10px",
    border: "1px solid rgba(148,163,184,0.5)",
    fontSize: "0.95rem",
  },
  sessionTag: {
    fontSize: "0.8rem",
    color: "#94a3b8",
  },
  composerRow: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  textArea: {
    flexGrow: 1,
    resize: "none",
    borderRadius: "16px",
    border: "1px solid rgba(148,163,184,0.45)",
    padding: "16px",
    fontSize: "1rem",
    fontFamily: "inherit",
    minHeight: "72px",
    background: "rgba(255,255,255,0.95)",
  },
  sendButton: {
    padding: "12px 22px",
    borderRadius: "999px",
    border: "none",
    fontWeight: 600,
    background: "linear-gradient(130deg, #2563eb, #1d4ed8)",
    color: "#fff",
    cursor: "pointer",
    boxShadow: "0 20px 30px -22px rgba(37,99,235,0.8)",
  },
  metaRow: {
    display: "flex",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: "12px",
    color: "#94a3b8",
    fontSize: "0.85rem",
  },
  errorText: {
    color: "#b91c1c",
  },
};

export default ChatWindow;
