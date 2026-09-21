"use client";

import { useState, useEffect } from "react";
import { Send, LogOut, Bot, User, ArrowLeft, FileText, MessageSquare, Loader2, X, AlertCircle, Calendar, Check } from "lucide-react";
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
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

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

  const showError = (message: string) => {
    setErrorMessage(message);
    setTimeout(() => setErrorMessage(null), 5000);
  };

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
    setErrorMessage(null);
    try {
      const res = await fetch(`${API_URL}/chats/${chatId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const formattedMessages = data.messages.map((m: any) => ({
          ...m,
          time: m.created_at 
            ? new Date(m.created_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) 
            : new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
        }));
        setMessages(formattedMessages);
      } else {
        throw new Error("Impossible de charger la discussion.");
      }
    } catch (error) {
      console.error("Erreur chargement discussion:", error);
      showError("Erreur lors du chargement de la discussion. Veuillez réessayer.");
    }
  };

  const handleSendMessage = async () => {
    if (!inputText.trim() || !token) return;

    const userMessage = inputText;
    const currentTime = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    setInputText("");
    
    setMessages(prev => [...prev, { role: "user", content: userMessage, time: currentTime }]);
    setIsLoading(true);
    setErrorMessage(null);

    try {
      let currentChatId = activeChat;
      
      if (!currentChatId) {
        const resCreate = await fetch(`${API_URL}/chats`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` }
        });
        if (!resCreate.ok) throw new Error("Erreur de création de discussion");
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
        const formattedMessages = dataMessage.messages.map((m: any) => ({
          ...m,
          time: m.created_at 
            ? new Date(m.created_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) 
            : new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
        }));
        setMessages(formattedMessages);
        fetchChatsList(token);
      } else {
        throw new Error("Erreur lors de la réponse de l'IA");
      }
    } catch (error) {
      console.error("Erreur d'envoi:", error);
      showError("Une erreur est survenue lors de la communication avec l'IA.");
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateReview = async () => {
    if (!reviewTopic.trim() || !activeChat || !token) return;
    setIsGenerating(true);
    setErrorMessage(null);

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
        setActiveChat(null);
        setActiveTab('reviews');
      } else {
        throw new Error("Erreur lors de la génération");
      }
    } catch (error) {
      console.error("Erreur génération revue:", error);
      showError("La génération de la revue a échoué.");
      setIsModalOpen(false);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopyReview = (review: any, index: number) => {
    const reviewDate = review.created_at ? new Date(review.created_at).toLocaleDateString('fr-FR') : new Date().toLocaleDateString('fr-FR');
    let textToCopy = `${review.title}\nDate : ${reviewDate}\n\nSynthèse générale :\n${review.general_summary}\n\n`;
    if (review.articles) {
      review.articles.forEach((art: any) => {
        textToCopy += `- ${art.title} : ${art.summary}\n`;
      });
    }
    navigator.clipboard.writeText(textToCopy);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  };

  return (
    <div className="flex h-screen bg-[#F3F4F6] text-gray-800 font-['Inter']">
      
      {/* SIDEBAR */}
      <aside className="w-64 bg-white flex flex-col border-r border-gray-200">
        <div className="p-6 text-[#803CDA] font-bold flex items-center gap-2 text-lg uppercase tracking-wider border-b border-gray-100">
          NewsFoundry <Bot size={20} />
        </div>
        <div className="flex-1 overflow-y-auto">
          {chatsList.map((chat) => {
            const displayDate = chat.updated_at || chat.created_at 
              ? new Date(chat.updated_at || chat.created_at).toLocaleDateString('fr-FR')
              : new Date().toLocaleDateString('fr-FR');
              
            return (
              <button 
                key={chat.id} 
                onClick={() => loadSpecificChat(chat.id)}
                className={`w-full text-left p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${activeChat === chat.id ? 'bg-gray-50 border-l-4 border-l-[#803CDA]' : ''}`}
              >
                <div className="text-[16px] font-normal text-[#2A2A31] truncate">{chat.preview || "Nouvelle discussion"}</div>
                <div className="text-[12px] font-normal text-[#717182] mt-1">{displayDate}</div>
              </button>
            );
          })}
        </div>
        {/* BOUTON DÉCONNEXION : Hauteur fixée à 105px pour s'aligner avec la barre de saisie */}
        <button 
          onClick={handleLogout} 
          className="flex items-center gap-2 px-6 h-[105px] shrink-0 w-full text-[14px] font-normal text-[#2A2A31] hover:text-gray-900 hover:bg-gray-50 transition-colors border-t border-gray-200"
        >
          <LogOut size={16} /> Se déconnecter
        </button>
      </aside>

      {/* ZONE PRINCIPALE */}
      <main className="flex-1 flex flex-col relative h-screen overflow-hidden">
        
        {/* ALERTE D'ERREUR VISUELLE */}
        {errorMessage && (
          <div className="absolute bottom-28 left-1/2 -translate-x-1/2 z-50 w-full max-w-2xl bg-red-50 border-l-4 border-red-500 text-red-700 p-4 rounded-md shadow-lg flex items-start gap-3 animate-fade-in">
            <AlertCircle size={20} className="shrink-0 mt-0.5" />
            <div className="flex-1 text-sm">{errorMessage}</div>
            <button onClick={() => setErrorMessage(null)} className="text-red-400 hover:text-red-600 transition-colors">
              <X size={18} />
            </button>
          </div>
        )}

        <header className="h-20 bg-white flex items-center px-8 border-b border-gray-200 justify-between shrink-0">
          {!activeChat ? (
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button 
                onClick={() => setActiveTab('chat')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-[14px] transition-colors ${activeTab === 'chat' ? 'bg-[#803CDA] text-white shadow-sm font-bold' : 'text-gray-500 hover:text-gray-700 font-normal'}`}
              >
                <MessageSquare size={16} /> Chat
              </button>
              <button 
                onClick={() => setActiveTab('reviews')}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-[14px] transition-colors ${activeTab === 'reviews' ? 'bg-[#803CDA] text-white shadow-sm font-bold' : 'text-gray-500 hover:text-gray-700 font-normal'}`}
              >
                <FileText size={16} /> Revue de presse
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-4">
              <button 
                onClick={() => {setActiveChat(null); setMessages([]); setActiveTab('chat');}} 
                className="text-[#000000] hover:text-gray-600 transition-colors mt-1"
              >
                <ArrowLeft size={20} strokeWidth={1.5} />
              </button>
              <div className="flex flex-col">
                <h2 className="text-[18px] font-normal text-[#000000] font-['IBM_Plex_Sans'] leading-tight">Nouvelle discussion</h2>
                <span className="text-[14px] font-normal text-[#9999AB] font-['Inter'] leading-tight mt-0.5">Conversation active</span>
              </div>
            </div>
          )}

          {activeChat && (
            <button 
              onClick={() => setIsModalOpen(true)}
              className="flex items-center justify-center gap-2 bg-[#803CDA] text-white rounded-md text-[16px] font-normal hover:bg-[#717182] transition-colors shadow-sm w-[290px] h-[61px] shrink-0"
            >
              <FileText size={16} /> Générer une revue de presse
            </button>
          )}
        </header>

        {/* ZONE DE DÉFILEMENT */}
        <div className="flex-1 overflow-y-auto p-8 flex flex-col items-center pb-28">
          {activeTab === 'chat' ? (
            !activeChat && messages.length === 0 ? (
              <div className="bg-white rounded-xl shadow-sm p-10 max-w-2xl w-full text-center mt-10">
                <Bot size={48} className="text-[#803CDA] mx-auto mb-6" />
                
                <h1 className="text-[32px] font-normal text-[#803CDA] mb-4 font-['IBM_Plex_Sans']">
                  Assistant Revue de Presse IA
                </h1>
                
                <p className="text-[16px] font-normal text-[#838392] mb-8 leading-relaxed max-w-md mx-auto">
                  Posez-moi des questions sur l'actualité récente ou demandez-moi de générer une revue de presse sur un sujet spécifique.
                </p>

                <div className="text-left p-6 max-w-lg mx-auto">
                  <div className="text-[14px] font-bold text-[#717182] mb-3">Exemples :</div>
                  <ul className="space-y-2 text-[14px] font-normal text-[#717182]">
                    <li>• "Quelles sont les dernières nouvelles en politique ?"</li>
                    <li>• "Génère une revue de presse sur la technologie"</li>
                    <li>• "Résume l'actualité économique de la semaine"</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="w-full max-w-4xl flex flex-col gap-6">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`flex items-start gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-gray-800 text-white' : 'bg-transparent text-gray-500'}`}>
                      {msg.role === 'user' ? <User size={16} /> : <Bot size={20} />}
                    </div>
                    <div className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} max-w-[80%]`}>
                      <div className={`p-4 rounded-xl text-sm relative ${msg.role === 'user' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-800'}`}>
                        <div className="prose prose-sm max-w-none mb-4">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                        {msg.time && (
                          <div className="text-[12px] font-normal text-gray-400 absolute bottom-1 left-4">
                            {msg.time}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 bg-transparent text-[#803CDA]">
                      <Loader2 size={20} className="animate-spin" />
                    </div>
                  </div>
                )}
              </div>
            )
          ) : (
            <div className="w-full max-w-4xl">
              <h2 className="text-2xl font-semibold text-gray-800 mb-2">Revues de Presse</h2>
              <p className="text-gray-500 text-sm mb-8">Consultez et gérez vos revues de presse générées par l'IA</p>
              
              {pressReviews.length === 0 ? (
                <div className="text-center p-10 bg-white rounded-xl shadow-sm text-gray-500">
                  Aucune revue de presse n'a encore été générée.
                </div>
              ) : (
                <div className="flex flex-col gap-6">
                  {pressReviews.map((review, idx) => {
                    const reviewDisplayDate = review.created_at ? new Date(review.created_at).toLocaleDateString('fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }) : new Date().toLocaleDateString('fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
                    return (
                      <div key={idx} className="bg-white rounded-xl shadow-sm p-8 relative">
                        <button 
                          onClick={() => handleCopyReview(review, idx)}
                          className="absolute top-8 right-8 bg-[#272930] text-white px-4 py-2 rounded text-sm hover:bg-gray-800 flex items-center gap-2 transition-all"
                        >
                          {copiedIndex === idx ? <><Check size={16} /> Copié !</> : "Copier"}
                        </button>
                        
                        <h3 className="text-[16px] font-normal text-[#0A0A0A] uppercase tracking-wide pr-32 font-['IBM_Plex_Sans']">
                          {review.title}
                        </h3>
                        
                        <div className="text-[14px] font-normal text-[#717182] flex items-center gap-2 mt-1 mb-6">
                          <Calendar size={14} /> {reviewDisplayDate}
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
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>

        {/* BARRE DE SAISIE FIXE : Hauteur fixée à 105px pour s'aligner avec le bouton déconnexion */}
        <div className="px-6 bg-white border-t border-gray-200 shrink-0 w-full z-20 h-[105px] flex flex-col justify-center">
          <div className="max-w-4xl mx-auto relative flex gap-2 w-full">
            <input 
              type="text" 
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder={activeTab === 'reviews' ? "La saisie est désactivée dans l'onglet Revue de presse..." : "Tapez votre message ici..."} 
              className={`w-full py-4 pl-4 pr-14 rounded-lg bg-white border border-gray-200 focus:outline-none focus:border-[#803CDA] shadow-sm transition-colors ${activeTab === 'reviews' ? 'opacity-50 cursor-not-allowed bg-gray-100' : ''}`}
              disabled={isLoading || activeTab === 'reviews'}
            />
            {/* BOUTON D'ENVOI : Parfaitement centré verticalement via top-1/2 et -translate-y-1/2 */}
            <button 
              onClick={handleSendMessage}
              disabled={isLoading || activeTab === 'reviews'}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-md text-white bg-[#803CDA] hover:bg-[#2a2a31] disabled:bg-gray-300 transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>

      {/* MODALE DE GÉNÉRATION */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl w-full max-w-md p-8 relative shadow-2xl">
            <button 
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-sm flex items-center gap-1"
            >
              Fermer
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
                  className="w-full px-4 py-3 rounded-lg bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#803CDA] text-sm"
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