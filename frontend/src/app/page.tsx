"use client";

import { useState, useEffect } from "react";
import { Send, LogOut, Bot, User, ArrowLeft, FileText, MessageSquare, Loader2, X } from "lucide-react";
import ReactMarkdown from "react-markdown";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://newsfoundry-production-35c3.up.railway.app";

export default function ChatApplication() {
  const [token, setToken] = useState<string | null>(null);
  const [activeChat, setActiveChat] = useState<number | null>(null);
  const [inputText, setInputText] = useState("");
  const [chatsList, setChatsList] = useState<any[]>([]);
  const [messages, setMessages] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const [activeTab, setActiveTab] = useState<'chat' | 'reviews'>('chat');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [reviewTopic, setReviewTopic] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [pressReviews, setPressReviews] = useState<any[]>([]);

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) {
      window.location.href = "/login";
      return;
    }
    setToken(storedToken);
    fetchChatsList(storedToken);
    fetchAllReviews(storedToken);
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

  const fetchAllReviews = async (authToken: string) => {
    try {
      const res = await fetch(`${API_URL}/press-reviews`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setPressReviews(data);
      }
    } catch (error) {
      console.error("Erreur chargement revues:", error);
    }
  };

  const loadSpecificChat = async (chatId: number) => {
    setActiveChat(chatId);
    setActiveTab('chat');
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

  const handleSendMessage = async () => {
    if (!inputText.trim() || !token) return;

    const userMessage = inputText;
    setInputText("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      let currentChatId = activeChat;
      
      if (!currentChatId) {
        const resCreate = await fetch(`${API_URL}/chats`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` }
        });
        const dataCreate = await resCreate.json();
        currentChatId = dataCreate.chat_id;
        setActiveChat(currentChatId);
      }

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
        fetchChatsList(token);
      }
    } catch (error) {
      console.error("Erreur d'envoi:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateReview = async () => {
    if (!reviewTopic.trim() || !activeChat || !token) return;
    setIsGenerating(true);

    try {
      const res = await fetch(`${API_URL}/chats/${activeChat}/press-reviews`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ topic: reviewTopic })
      });

      if (res.ok) {
        await fetchAllReviews(token);
        setIsModalOpen(false);
        setReviewTopic("");
        setActiveChat(null); // Retour à l'accueil pour voir les onglets
        setActiveTab('reviews');
      }
    } catch (error) {
      console.error("Erreur génération revue:", error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  };

  return (
    <div className="flex h-screen bg-[#F3F4F6] text-gray-800 font-sans">
      {/* SIDEBAR */}
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
              <div className="text-xs text-gray-400 mt-1">Discussion du {new Date().toLocaleDateString('fr-FR')}</div>
            </button>
          ))}
        </div>
        <button onClick={handleLogout} className="p-4 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 border-t border-gray-200">
          <LogOut size={16} /> Se déconnecter
        </button>
      </aside>

      {/* ZONE PRINCIPALE */}
      <main className="flex-1 flex flex-col relative">
        <header className="h-20 bg-white flex items-center px-8 border-b border-gray-200 justify-between">
          {!activeChat ? (
            // ACCUEIL : Affichage des onglets
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button 
                onClick={() => setActiveTab('chat')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'chat' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
              >
                <MessageSquare size={16} /> Chat
              </button>
              <button 
                onClick={() => setActiveTab('reviews')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'reviews' ? 'bg-[#7C3AED] text-white shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
              >
                <FileText size={16} /> Revue de presse
              </button>
            </div>
          ) : (
            // DISCUSSION ACTIVE : Bouton retour et titre
            <div className="flex items-center gap-4">
              <button 
                onClick={() => {setActiveChat(null); setMessages([]); setActiveTab('chat');}} 
                className="text-gray-400 hover:text-gray-600 mr-2 flex items-center gap-2 text-sm font-medium"
              >
                <ArrowLeft size={18} /> Retour
              </button>
              <h2 className="font-semibold text-gray-800">Nouvelle discussion</h2>
            </div>
          )}

          {/* BOUTON GÉNÉRER (Uniquement dans une discussion) */}
          {activeChat && (
            <button 
              onClick={() => setIsModalOpen(true)}
              className="flex items-center gap-2 bg-[#7C3AED] text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-[#6D28D9] transition-colors shadow-sm"
            >
              <FileText size={16} /> Générer une revue de presse
            </button>
          )}
        </header>

        {/* AFFICHAGE CONDITIONNEL : CHAT OU REVUES */}
        <div className="flex-1 overflow-y-auto p-8 flex flex-col items-center bg-[#F3F4F6]">
          {activeTab === 'chat' ? (
            // --- VUE CHAT ---
            !activeChat && messages.length === 0 ? (
              <div className="bg-white rounded-xl shadow-sm p-10 max-w-2xl w-full text-center mt-10">
                <Bot size={48} className="text-[#7C3AED] mx-auto mb-6" />
                <h1 className="text-2xl font-semibold text-[#7C3AED] mb-4">Assistant Revue de Presse IA</h1>
                <p className="text-gray-500 text-sm mb-8 leading-relaxed max-w-md mx-auto">
                  Ouvrez ou créez une discussion, posez des questions sur l'actualité, puis générez une revue de presse.
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
            )
          ) : (
            // --- VUE REVUES DE PRESSE ---
            <div className="w-full max-w-4xl">
              <h2 className="text-2xl font-semibold text-gray-800 mb-2">Revues de Presse</h2>
              <p className="text-gray-500 text-sm mb-8">Consultez et gérez vos revues de presse générées par l'IA</p>
              
              {pressReviews.length === 0 ? (
                <div className="text-center p-10 bg-white rounded-xl shadow-sm text-gray-500">
                  Aucune revue de presse n'a encore été générée.
                </div>
              ) : (
                <div className="flex flex-col gap-6">
                  {pressReviews.map((review, idx) => (
                    <div key={idx} className="bg-white rounded-xl shadow-sm p-8 relative">
                      <button className="absolute top-8 right-8 bg-[#272930] text-white px-4 py-2 rounded text-sm hover:bg-gray-800 flex items-center gap-2">
                        Copier
                      </button>
                      <h3 className="text-lg font-bold text-gray-900 uppercase tracking-wide mb-1">{review.title}</h3>
                      <div className="text-xs text-gray-400 flex items-center gap-2 mb-6">
                        <FileText size={14} /> ID Discussion : {review.chat_id}
                      </div>
                      
                      <div className="text-sm text-gray-700 leading-relaxed mb-6 font-medium">
                        **Synthèse générale :** <br/>
                        {review.general_summary}
                      </div>

                      <div className="space-y-4">
                        {review.articles && review.articles.map((article: any, i: number) => (
                          <div key={i} className="text-sm">
                            <span className="font-semibold text-gray-900">• {article.title} : </span>
                            <span className="text-gray-600">{article.summary}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* BARRE DE SAISIE */}
        {activeTab === 'chat' && (
          <div className="p-6 bg-transparent absolute bottom-0 w-full">
            <div className="max-w-4xl mx-auto relative flex gap-2">
              <input 
                type="text" 
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Tapez votre message ici..." 
                className="w-full py-4 pl-4 pr-14 rounded-lg bg-white border border-gray-200 focus:outline-none focus:border-[#7C3AED] shadow-sm transition-colors"
                disabled={isLoading}
              />
              <button 
                onClick={handleSendMessage}
                disabled={isLoading}
                className="absolute right-2 top-2 p-2 rounded-md text-white bg-[#7C3AED] hover:bg-[#6D28D9] disabled:bg-gray-300 transition-colors"
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        )}
      </main>

      {/* MODALE DE GÉNÉRATION */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl w-full max-w-md p-8 relative shadow-2xl">
            <button 
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-sm flex items-center gap-1"
            >
              Fermer <X size={16} />
            </button>
            
            <div className="text-center mb-8">
              <h3 className="text-xl font-bold text-gray-900">Générer une revue de presse</h3>
              <p className="text-sm text-gray-500 mt-1">Donner un titre à votre revue de presse</p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Titre de la revue de presse</label>
                <input 
                  type="text"
                  value={reviewTopic}
                  onChange={(e) => setReviewTopic(e.target.value)}
                  placeholder="Ex: Actualités Politiques - Semaine 39"
                  className="w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7C3AED] text-sm"
                />
              </div>

              <button 
                onClick={handleGenerateReview}
                disabled={isGenerating || !reviewTopic.trim()}
                className="w-full bg-[#272930] hover:bg-[#1e2025] text-white py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
              >
                {isGenerating ? (
                  <><Loader2 size={18} className="animate-spin" /> Génération en cours...</>
                ) : (
                  "Générer"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}