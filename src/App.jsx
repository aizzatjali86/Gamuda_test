import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2 } from 'lucide-react';

const App = () => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'System online. How can I help?' }
  ]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim() || loading) return;

    const userMsg = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query }),
      });

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Error connecting to gateway." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white text-slate-800 font-sans">
      {/* Message List */}
      <div className="flex-1 overflow-y-auto px-4 py-8 md:px-0">
        <div className="max-w-2xl mx-auto space-y-8">
          {messages.map((msg, idx) => (
            <div key={idx} className="flex flex-col">
              <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">
                {msg.role === 'user' ? 'You' : 'Gamuda AI'}
              </span>
              <div className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <Loader2 size={18} className="animate-spin text-slate-300" />
          )}
          <div ref={scrollRef} />
        </div>
      </div>

      {/* Simplified Input */}
      <div className="border-t border-slate-100 p-4 md:p-8">
        <form onSubmit={handleSend} className="max-w-2xl mx-auto relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type your query..."
            className="w-full bg-slate-50 border-none rounded-lg px-4 py-3 text-sm focus:ring-2 focus:ring-slate-200 outline-none transition-all"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-slate-400 hover:text-slate-600 disabled:opacity-30"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default App;