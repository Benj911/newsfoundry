"use client";

import { useState } from "react";
import { Send, LogOut, Bot, User, ArrowLeft, FileText, MessageSquare } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function ChatApplication() {
  const [activeChat, setActiveChat] = useState<number | null>(null);
  const [inputText, setInputText] = useState("");
  
  // Données factices pour tester l'interface avant de brancher l'API
  const [messages, setMessages] = useState([
    { role: "user", content: "Peux-tu me donner les dernières actualités politiques ?", time: "10:31" },
    { role: "assistant", content: "Voici un résumé des dernières nouvelles politiques :\n\n* Le gouvernement a annoncé de nouvelles mesures économiques\n* Débat sur la réforme des retraites au Parlement\n* Visite diplomatique prévue la semaine prochaine\n\nSouhaitez-vous que je génère une revue de presse détaillée sur l'un de ces sujets ?", time: "10:31" },
    { role: "user", content: "Je suis particulièrement curieux des applications dans le domaine de la santé et de l'éducation.", time: "10:31" }
  ]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    window.location.href = "/login";
  };

  return (
    <div className="flex h-screen bg-[#F3F4F6] text-gray-800 font-sans">
      
      {/* SIDEBAR GAUCHE */}
      <aside className="w-64 bg-white flex flex-col border-r border-gray-200">
        <div className="p-6 text-[#7C3AED] font-bold flex items-center gap-2 text-lg uppercase tracking-wider border-b border-gray-100">
          NewsFoundry <Bot size={20} />
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <button 
              key={i} 
              onClick={() => setActiveChat(i)}
              className={`w-full text-left p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${activeChat === i ? 'bg-gray-50 border-l-4 border-l-[#7C3AED]' : ''}`}
            >
              <div className="text-sm font-medium text-gray-700">Discussion du</div>
              <div className="text-xs text-gray-400 mt-1">10/12/2026</div>
            </button>
          ))}
        </div>

        <button onClick={handleLogout} className="p-4 flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 border-t border-gray-200">
          <LogOut size={16} /> Se déconnecter
        </button>
      </aside>

      {/* CONTENU PRINCIPAL */}
      <main className="flex-1 flex flex-col relative">
        
        {/* HEADER DYNAMIQUE */}
        <header className="h-20 bg-white flex items-center px-8 border-b border-gray-200 justify-between">
          {!activeChat ? (
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button className="flex items-center gap-2 bg-[#7C3AED] text-white px-4 py-2 rounded-md text-sm font-medium">
                <MessageSquare size={16} /> Chat
              </button>
              <button className="flex items-center gap-2 text-gray-500 hover:text-gray-700 px-4 py-2 rounded-md text-sm font-medium">
                <FileText size={16} /> Revue de presse
              </button>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-4">
                <button onClick={() => setActiveChat(null)} className="text-gray-400 hover:text-gray-600">
                  <ArrowLeft size={20} />
                </button>
                <div>
                  <h2 className="font-semibold text-gray-800">Nouvelle discussion</h2>
                  <p className="text-xs text-gray-500">Conversation active</p>
                </div>
              </div>
              <button className="bg-[#7C3AED] text-white px-4 py-2 rounded-md flex items-center gap-2 text-sm font-medium hover:bg-[#6D28D9] transition-colors">
                <FileText size={16} /> Générer une revue de presse
              </button>
            </>
          )}
        </header>

        {/* ZONE DE CHAT OU ACCUEIL */}
        <div className="flex-1 overflow-y-auto p-8 flex flex-col items-center">
          {!activeChat ? (
            <div className="bg-white rounded-xl shadow-sm p-10 max-w-2xl w-full text-center mt-10">
              <Bot size={48} className="text-[#7C3AED] mx-auto mb-6" />
              <h1 className="text-2xl font-semibold text-[#7C3AED] mb-4">Assistant Revue de Presse IA</h1>
              <p className="text-gray-500 text-sm mb-8 leading-relaxed max-w-md mx-auto">
                Posez-moi des questions sur l'actualité récente ou demandez-moi de générer une revue de presse sur un sujet spécifique.
              </p>
              
              <div className="text-sm text-gray-600">
                <p className="font-medium mb-3">Exemples :</p>
                <ul className="space-y-2">
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
                    <div className={`p-4 rounded-xl text-sm ${msg.role === 'user' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-800'}`}>
                      <div className="prose prose-sm max-w-none">
                        <ReactMarkdown>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    </div>
                    <span className="text-xs text-gray-400 mt-2">{msg.time}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ZONE DE SAISIE */}
        <div className="p-6 bg-transparent">
          <div className="max-w-4xl mx-auto relative">
            <input 
              type="text" 
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Tapez votre message ici..." 
              className={`w-full py-4 pl-4 pr-14 rounded-lg focus:outline-none transition-colors ${!activeChat ? 'bg-white border-transparent' : 'bg-white border border-[#7C3AED]'}`}
            />
            <button 
              className={`absolute right-2 top-2 p-2 rounded-md text-white transition-colors ${!activeChat ? 'bg-gray-300' : 'bg-[#7C3AED] hover:bg-[#6D28D9]'}`}
            >
              <Send size={18} />
            </button>
          </div>
        </div>

      </main>
    </div>
  );
}