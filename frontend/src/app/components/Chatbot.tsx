import { useState } from "react";
import { MessageCircle, X, Send, Sparkles, Loader } from "lucide-react";

interface Message {
  id: string;
  text: string;
  sender: "user" | "bot";
  timestamp: Date;
}

const initialMessages: Message[] = [
  {
    id: "1",
    text: "Hi! I'm your F1 AI assistant. I can help you understand the prediction model, explain how factors work, or answer F1 questions. How can I help you today?",
    sender: "bot",
    timestamp: new Date(),
  },
];

const BACKEND_URL = "http://127.0.0.1:3001";

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: input }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        text: data.answer || "Sorry, I couldn't generate a response.",
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botResponse]);
    } catch (error) {
      console.error("Error calling chatbot API:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Sorry, I couldn't connect to the chatbot service. Make sure the backend is running on port 3001. Error: ${error instanceof Error ? error.message : "Unknown error"}`,
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="group fixed bottom-6 right-6 z-50 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-r from-[#e10600] to-[#c00500] text-white shadow-2xl shadow-[#e10600]/40 transition-all hover:scale-110"
        >
          <MessageCircle className="h-7 w-7 transition-transform group-hover:scale-110" />
          <span className="absolute -top-1 -right-1 flex h-5 w-5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#00ff88] opacity-75"></span>
            <span className="relative inline-flex h-5 w-5 items-center justify-center rounded-full bg-[#00ff88]">
              <Sparkles className="h-3 w-3 text-black" />
            </span>
          </span>
        </button>
      )}

      {isOpen && (
        <div className="fixed bottom-6 right-6 z-50 flex h-[600px] w-[400px] flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-2xl">
          <div className="flex items-center justify-between border-b border-border bg-gradient-to-r from-[#e10600] to-[#c00500] p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-white">F1 AI Assistant</h3>
                <div className="flex items-center gap-1 text-xs text-white/80">
                  <div className="h-2 w-2 rounded-full bg-[#00ff88]"></div>
                  <span>Online</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="rounded-lg p-2 text-white transition-colors hover:bg-white/20"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto bg-background p-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.sender === "user"
                      ? "bg-gradient-to-r from-[#e10600] to-[#c00500] text-white"
                      : "border border-border bg-secondary/50 text-foreground"
                  }`}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-line">{message.text}</p>
                  <div className="mt-1 text-xs opacity-60">
                    {message.timestamp.toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-border bg-card p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSend()}
                placeholder="Ask about F1 or predictions..."
                disabled={isLoading}
                className="flex-1 rounded-lg border border-border bg-secondary/30 px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-[#e10600] focus:outline-none focus:ring-2 focus:ring-[#e10600]/20 disabled:opacity-50"
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-r from-[#e10600] to-[#c00500] text-white transition-all hover:shadow-lg hover:shadow-[#e10600]/30 disabled:opacity-50"
              >
                {isLoading ? <Loader className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
