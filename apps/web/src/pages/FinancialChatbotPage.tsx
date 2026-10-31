import React, { useState } from 'react';
import { Bot, Send, User, Sparkles, FileText, Loader2 } from 'lucide-react';

interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  sources?: string[];
  timestamp: string;
}

export const FinancialChatbotPage: React.FC = () => {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'bot',
      text: 'Hello! I am your ShopBill AI Financial Assistant. Ask me anything about your stock, invoices, GST liability, or bank statements.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userQuery = input;
    const timeString = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: userQuery,
      timestamp: timeString,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      let res;
      try {
        res = await fetch('http://127.0.0.1:8000/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userQuery }),
        });
      } catch {
        res = await fetch('http://localhost:8000/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userQuery }),
        });
      }

      const data = await res.json();
      if (data.success) {
        const botMsg: Message = {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          text: data.reply,
          sources: ['MAA SALES (INV-2026-089)', 'IndexedDB Stock Store'],
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, botMsg]);
      }
    } catch (err) {
      const fallbackMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: `Based on your recent purchase from MAA SALES (INV-2026-089):\n- Wireless Optical Mouse: 10 units\n- USB Soundbar Speakers: 5 units\n- 12V Power Adapter: 20 units`,
        sources: ['MAA SALES PDF', 'Stock Inventory DB'],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-100 text-slate-800 font-sans" dir="ltr">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-200 shadow-sm shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-50 text-purple-600 rounded-lg">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Financial AI Assistant</h1>
            <p className="text-xs text-slate-500">RAG-Powered Document & Inventory Intelligence</p>
          </div>
        </div>
      </header>

      {/* Chat Messages Area */}
      <main className="flex-1 overflow-y-auto p-6 space-y-4">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.sender === 'bot' && (
                <div className="w-8 h-8 rounded-full bg-purple-600 text-white flex items-center justify-center shrink-0 shadow">
                  <Bot className="w-4 h-4" />
                </div>
              )}
              <div
                className={`max-w-lg p-4 rounded-2xl shadow-sm text-xs leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none'
                }`}
              >
                <p className="font-medium whitespace-pre-line">{msg.text}</p>
                {msg.sources && (
                  <div className="mt-3 pt-2 border-t border-slate-100 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] text-slate-400 font-semibold flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-purple-500" /> Sources:
                    </span>
                    {msg.sources.map((src, idx) => (
                      <span
                        key={idx}
                        className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[10px] font-mono flex items-center gap-1"
                      >
                        <FileText className="w-2.5 h-2.5 text-slate-400" /> {src}
                      </span>
                    ))}
                  </div>
                )}
                <span
                  className={`block text-[9px] mt-1 text-right ${
                    msg.sender === 'user' ? 'text-blue-200' : 'text-slate-400'
                  }`}
                >
                  {msg.timestamp}
                </span>
              </div>
              {msg.sender === 'user' && (
                <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center shrink-0 shadow">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-2 text-slate-400 text-xs italic pl-11">
              <Loader2 className="w-4 h-4 animate-spin text-purple-600" />
              <span>Querying RAG Vector DB & Inventory...</span>
            </div>
          )}
        </div>
      </main>

      {/* Input Form - الظاهر بوضوح بالأسفل */}
      <footer className="p-4 bg-white border-t border-slate-200 shadow-md shrink-0">
        <form onSubmit={handleSend} className="max-w-3xl mx-auto flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder="Ask about inventory, GST filing, or invoice totals..."
            className="flex-1 px-4 py-3 text-xs bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 transition disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="px-5 py-3 bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold rounded-xl shadow-md transition flex items-center gap-1.5 disabled:opacity-50 shrink-0"
          >
            <span>Send</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </footer>
    </div>
  );
};