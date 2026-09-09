"use client";

import { useState, useEffect } from "react";
import { Send, LogOut, Bot, User, ArrowLeft, FileText, MessageSquare, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://newsfoundry-production-35c3.up.railway.app";

export default function ChatApplication() {
  const [token, setToken] = useState<string | null>(null);
  const [activeChat, setActiveChat] = useState<number | null>(null);
  const [inputText, setInputText] = useState("");
  const [chatsList, setChatsList] = useState<any[]>([]);
  const [messages, setMessages] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // 1. Vérification du token et chargement de l'historique
  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      window.location.href = "/login";
      return;
    }
    setToken(storedToken);
    fetchChatsList(storedToken);
  }, []);

  const fetchChatsList = async (authToken: string) => {
    try {
      const res = await fetch(`${API_URL}/chats`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setChatsList(data);
      }
    } catch (error) {
      console.error("Erreur chargement historique:", error);
    }
  };

  const loadSpecificChat = async (chatId: number) => {
    setActiveChat(chatId);
    try {
      const res = await fetch(`${API_URL}/chats/${chatId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages);
      }
    } catch (error) {
      console.error("Erreur chargement discussion:", error);
    }
  };

  // 2. Envoi d'un message
  const handleSendMessage = async () => {
    if (!inputText.trim() || !token) return;

    const userMessage = inputText;
    setInputText("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      let currentChatId = activeChat;
      
      // Créer un nouveau chat si aucun n'est actif
      if (!currentChatId) {
        const resCreate = await fetch(`${API_URL}/chats`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` }
        });
        const dataCreate = await resCreate.json();
        currentChatId = dataCreate.chat_id;
        setActiveChat(currentChatId);
      }

      // Envoyer le message à Mistral
      const resMessage = await fetch(`${API_URL}/chats/${currentChatId}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ content: userMessage })
      });

      if (resMessage.ok) {
        const dataMessage = await resMessage.json();
        setMessages(dataMessage.messages);
        fetchChatsList(token); // Mettre à jour la sidebar
      }
    } catch (error) {
      console.error("Erreur d'envoi:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  };

  return (
    <div className="flex h-screen bg-[#F3F4F6] text-gray-800 font-sans">
      <aside className="w-64 bg-white flex flex-col border-r border-gray-200">
        <div className="p-6 text-[#7C3AED] font-bold flex items-center gap-2 text-lg uppercase tracking-wider border-b border-gray-100">
          NewsFoundry <Bot size={20} />
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {chatsList.map((chat) => (
            <button 
              key={chat.id} 
              onClick={() => loadSpecificChat(chat.id)}
              className={`w-full text-left p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${activeChat === chat.id ? 'bg-gray-50 border-l-4 border-l-[#7C3AED]' : ''}`}
            >
              <div className="text-sm font-medium text-gray-700 truncate">{chat.preview || "Nouvelle discussion"}</div>
              <div className="text-xs text-gray-400 mt-1">Chat #{chat.id}</div>
            </button>
          ))}
        </div>

        <button onClick={handleLogout} className="p-4 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 border-t border-gray-200">
          <LogOut size={16} /> Se déconnecter
        </button>
      </aside>

      <main className="flex-1 flex flex-col relative">
        <header className="h-20 bg-white flex items-center px-8 border-b border-gray-200 justify-between">
          {!activeChat ? (
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button className="flex items-center gap-2 bg-[#7C3AED] text-white px-4 py-2 rounded-md text-sm font-medium">
                <MessageSquare size={16} /> Chat
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-4">
              <button onClick={() => {setActiveChat(null); setMessages([]);}} className="text-gray-400 hover:text-gray-600">
                <ArrowLeft size={20} />
              </button>
              <div>
                <h2 className="font-semibold text-gray-800">Discussion active</h2>
              </div>
            </div>
          )}
        </header>

        <div className="flex-1 overflow-y-auto p-8 flex flex-col items-center">
          {!activeChat && messages.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm p-10 max-w-2xl w-full text-center mt-10">
              <Bot size={48} className="text-[#7C3AED] mx-auto mb-6" />
              <h1 className="text-2xl font-semibold text-[#7C3AED] mb-4">Assistant Revue de Presse IA</h1>
              <p className="text-gray-500 text-sm mb-8 leading-relaxed max-w-md mx-auto">
                Posez-moi des questions sur l'actualité récente ou demandez-moi de générer une revue de presse.
              </p>
            </div>
          ) : (
            <div className="w-full max-w-4xl flex flex-col gap-6 pb-20">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex items-start gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-gray-800 text-white' : 'bg-transparent text-gray-500'}`}>
                    {msg.role === 'user' ? <User size={16} /> : <Bot size={20} />}
                  </div>
                  <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} max-w-[80%]`}>
                    <div className={`p-4 rounded-xl text-sm ${msg.role === 'user' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-800'}`}>
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex items-start gap-4">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-transparent text-[#7C3AED]">
                    <Loader2 size={20} className="animate-spin" />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="p-6 bg-transparent absolute bottom-0 w-full">
          <div className="max-w-4xl mx-auto relative flex gap-2">
            <input 
              type="text" 
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Tapez votre message ici..." 
              className="w-full py-4 pl-4 pr-14 rounded-lg bg-white border border-[#7C3AED] focus:outline-none shadow-sm"
              disabled={isLoading}
            />
            <button 
              onClick={handleSendMessage}
              disabled={isLoading}
              className="absolute right-2 top-2 p-2 rounded-md text-white bg-[#7C3AED] hover:bg-[#6D28D9] disabled:bg-gray-300"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}