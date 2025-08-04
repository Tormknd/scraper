// ScraperTerminal.tsx — interface console conversationnelle avec IA
"use client";

import React, { useState, useEffect, useRef } from "react";
import { Loader2, Bot, User, Globe, Download } from "lucide-react";

/**
 * Commandes :
 *   help                 affiche l'aide
 *   new                  crée une nouvelle session
 *   analyze <url>        analyse un site web
 *   chat <message>       envoie un message à l'IA
 *   scrape <requirements> extrait des données selon les exigences
 *   history              affiche l'historique de conversation
 *   clear                efface l'écran
 * ↑ / ↓                  navigue dans l'historique (10 entrées)
 */
export default function ScraperTerminal() {
  type Line =
    | { type: "prompt"; value: string }
    | { type: "system" | "info" | "error" | "json" | "ai" | "user"; value: string; session_id?: string }
    | { type: "analysis"; value: Record<string, unknown>; session_id: string }
    | { type: "extraction"; value: Record<string, unknown>; session_id: string };

  const helpText = [
    "🤖 Scraper-LLM - Interface Conversationnelle",
    "",
    "Commandes disponibles:",
    "  new                    Créer une nouvelle session IA",
    "  analyze <url>          Analyser un site web",
    "  chat <message>         Envoyer un message à l'IA",
    "  scrape <requirements> Extraire des données selon vos besoins",
    "  history                Afficher l'historique de conversation",
    "  clear                  Effacer l'écran",
    "  help                   Afficher cette aide",
    "",
    "Exemple d'utilisation:",
    "  1. new                 # Créer une session",
    "  2. analyze https://example.com",
    "  3. chat 'Je veux tous les produits avec prix'",
    "  4. scrape 'Extrais tous les produits avec titre, prix et image'",
    "",
    "💡 Astuce: Vous pouvez sélectionner et copier le texte du terminal !",
  ].join("\n");

  const [lines, setLines] = useState<Line[]>([
    { type: "system", value: helpText },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const termRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    termRef.current?.scrollTo({ top: termRef.current.scrollHeight });
  }, [lines, loading]);

  // Set initial input value after component mounts to prevent hydration mismatch
  useEffect(() => {
    if (!currentSessionId) {
      setInput("new");
    }
  }, [currentSessionId]);

  const push = (l: Line) => setLines((prev) => [...prev, l]);

  const runCommand = async (raw: string) => {
    const tokens = raw.trim().split(/\s+/);
    const cmd = tokens[0]?.toLowerCase();
    if (!cmd) return;

    if (cmd === "help") {
      push({ type: "system", value: helpText });
    } else if (cmd === "clear") {
      setLines([]);
    } else if (cmd === "new") {
      push({ type: "info", value: "Création d'une nouvelle session IA..." });
      setLoading(true);
      try {
        const res = await fetch("/api/session/new", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setCurrentSessionId(data.session_id);
        push({ 
          type: "info", 
          value: `✅ Session créée: ${data.session_id.slice(0, 8)}...`,
          session_id: data.session_id 
        });
        push({ 
          type: "ai", 
          value: "Bonjour ! Je suis votre assistant IA spécialisé dans l'analyse et l'extraction de données web. Je peux vous aider à analyser des sites web et extraire les informations dont vous avez besoin. Que souhaitez-vous faire ?",
          session_id: data.session_id 
        });
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Erreur lors de la création de la session";
        push({ type: "error", value: errorMessage });
      } finally {
        setLoading(false);
      }
    } else if (cmd === "analyze") {
      if (tokens.length < 2) {
        push({ type: "error", value: "usage: analyze <url>" });
        return;
      }
      if (!currentSessionId) {
        push({ type: "error", value: "Créez d'abord une session avec 'new'" });
        return;
      }
      const url = tokens[1];
      push({ type: "info", value: `🔍 Analyse de ${url}...` });
      setLoading(true);
      try {
        const res = await fetch("/api/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url, session_id: currentSessionId }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        
        if (data.success) {
          push({ 
            type: "analysis", 
            value: data.analysis, 
            session_id: currentSessionId 
          });
          push({ 
            type: "ai", 
            value: data.ai_response,
            session_id: currentSessionId 
          });
        } else {
          push({ type: "error", value: data.error || "Erreur lors de l'analyse" });
        }
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Erreur lors de l'analyse";
        push({ type: "error", value: errorMessage });
        
        // Get AI help for the error
        if (currentSessionId) {
          push({ type: "info", value: "🔧 Demande d'aide à l'IA pour résoudre l'erreur..." });
          try {
            const errorHelpResponse = await fetch("/api/error-help", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                error: errorMessage,
                context: `Analyse d'un site web avec l'URL: ${url}`,
                userCommand: `analyze ${url}`,
                sessionId: currentSessionId
              }),
            });
            
            if (errorHelpResponse.ok) {
              const helpData = await errorHelpResponse.json();
              push({ 
                type: "ai", 
                value: `🔧 **Aide pour résoudre l'erreur:**\n\n${helpData.response}`,
                session_id: currentSessionId 
              });
            }
          } catch (helpError) {
            // If error help fails, just continue
            console.error("Failed to get error help:", helpError);
          }
        }
      } finally {
        setLoading(false);
      }
    } else if (cmd === "chat") {
      if (tokens.length < 2) {
        push({ type: "error", value: "usage: chat <message>" });
        return;
      }
      if (!currentSessionId) {
        push({ type: "error", value: "Créez d'abord une session avec 'new'" });
        return;
      }
      const message = tokens.slice(1).join(" ");
      push({ type: "user", value: message, session_id: currentSessionId });
      setLoading(true);
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message, session_id: currentSessionId }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        push({ 
          type: "ai", 
          value: data.response,
          session_id: currentSessionId 
        });
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Erreur lors du chat";
        push({ type: "error", value: errorMessage });
        
        // Get AI help for the error
        if (currentSessionId) {
          push({ type: "info", value: "🔧 Demande d'aide à l'IA pour résoudre l'erreur..." });
          try {
            const errorHelpResponse = await fetch("/api/error-help", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                error: errorMessage,
                context: `Envoi d'un message à l'IA: "${message}"`,
                userCommand: `chat ${message}`,
                sessionId: currentSessionId
              }),
            });
            
            if (errorHelpResponse.ok) {
              const helpData = await errorHelpResponse.json();
              push({ 
                type: "ai", 
                value: `🔧 **Aide pour résoudre l'erreur:**\n\n${helpData.response}`,
                session_id: currentSessionId 
              });
            }
          } catch (helpError) {
            // If error help fails, just continue
            console.error("Failed to get error help:", helpError);
          }
        }
      } finally {
        setLoading(false);
      }
    } else if (cmd === "scrape") {
      if (tokens.length < 2) {
        push({ type: "error", value: "usage: scrape <requirements>" });
        return;
      }
      if (!currentSessionId) {
        push({ type: "error", value: "Créez d'abord une session avec 'new'" });
        return;
      }
      const requirements = tokens.slice(1).join(" ");
      push({ type: "info", value: `📊 Extraction selon: "${requirements}"` });
      setLoading(true);
      try {
        const res = await fetch("/api/extract", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ requirements, session_id: currentSessionId }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        
        if (data.success) {
          // Debug logging
          console.log("Extraction response:", data);
          
          // Show scraping info if available
          if (data.scraping_info) {
            push({ 
              type: "info", 
              value: `📊 Extraction terminée - ${data.scraping_info.pages_scraped} pages analysées: ${data.scraping_info.main_page}${data.scraping_info.additional_pages.length > 0 ? ' + ' + data.scraping_info.additional_pages.join(', ') : ''}` 
            });
          }
          
          // Add AI response first
          push({ 
            type: "ai", 
            value: data.ai_response,
            session_id: currentSessionId 
          });
          
          // Add extraction results inline with conversation
          if (data.data?.items && Array.isArray(data.data.items) && data.data.items.length > 0) {
            console.log("Extracted items:", data.data.items);
            push({ 
              type: "extraction", 
              value: data.data, 
              session_id: currentSessionId 
            });
          }
        } else {
          push({ type: "error", value: data.error || "Erreur lors de l'extraction" });
        }
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Erreur lors de l'extraction";
        push({ type: "error", value: errorMessage });
        
        // Get AI help for the error
        if (currentSessionId) {
          push({ type: "info", value: "🔧 Demande d'aide à l'IA pour résoudre l'erreur..." });
          try {
            const errorHelpResponse = await fetch("/api/error-help", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                error: errorMessage,
                              context: `Extraction de données avec les exigences: "${requirements}"`,
              userCommand: `scrape ${requirements}`,
                sessionId: currentSessionId
              }),
            });
            
            if (errorHelpResponse.ok) {
              const helpData = await errorHelpResponse.json();
              push({ 
                type: "ai", 
                value: `🔧 **Aide pour résoudre l'erreur:**\n\n${helpData.response}`,
                session_id: currentSessionId 
              });
            }
          } catch (helpError) {
            // If error help fails, just continue
            console.error("Failed to get error help:", helpError);
          }
        }
      } finally {
        setLoading(false);
      }
    } else if (cmd === "history") {
      if (!currentSessionId) {
        push({ type: "error", value: "Créez d'abord une session avec 'new'" });
        return;
      }
      push({ type: "info", value: "📜 Récupération de l'historique..." });
      setLoading(true);
      try {
        const res = await fetch(`/api/history/${currentSessionId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        
        const historyText = data.history
          .filter((msg: Record<string, unknown>) => msg.role !== "system")
          .map((msg: Record<string, unknown>) => `${msg.role === "user" ? "👤 Vous" : "🤖 IA"}: ${msg.content}`)
          .join("\n\n");
        
        push({ 
          type: "json", 
          value: historyText || "Aucun historique disponible" 
        });
      } catch (e: unknown) {
        const errorMessage = e instanceof Error ? e.message : "Erreur lors de la récupération de l'historique";
        push({ type: "error", value: errorMessage });
      } finally {
        setLoading(false);
      }
    } else {
      push({ type: "error", value: `Commande inconnue: ${cmd}. Tapez 'help' pour l'aide.` });
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cmd = input.trim();
    if (!cmd) return;
    push({ type: "prompt", value: cmd });
    setHistory((h) => [...h.slice(-9), cmd]);
    setInput("");
    runCommand(cmd);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowUp" && history.length) {
      e.preventDefault();
      const next = history.length - 1;
      setInput(history[next]);
    } else if (e.key === "ArrowDown" && history.length) {
      e.preventDefault();
      setInput("");
    }
  };

  const renderLine = (l: Line, i: number) => {
    const base = "whitespace-pre-wrap break-words select-text";
    
    if (l.type === "prompt")
      return (
        <p key={i} className={`${base} text-zinc-50`}>
          <span className="text-green-500">scraper&nbsp;$</span> {l.value}
        </p>
      );
    
    if (l.type === "system")
      return (
        <p key={i} className={`${base} text-zinc-300`}>
          {l.value}
        </p>
      );
    
    if (l.type === "info")
      return (
        <p key={i} className={`${base} text-blue-400 flex items-center gap-2`}>
          <Globe className="w-4 h-4" />
          {l.value}
        </p>
      );
    
    if (l.type === "error")
      return (
        <p key={i} className={`${base} text-red-400`}>
          ❌ {l.value}
        </p>
      );
    
    if (l.type === "user")
      return (
        <p key={i} className={`${base} text-cyan-400 flex items-center gap-2`}>
          <User className="w-4 h-4" />
          {l.value}
        </p>
      );
    
    if (l.type === "ai")
      return (
        <p key={i} className={`${base} text-yellow-300 flex items-center gap-2`}>
          <Bot className="w-4 h-4" />
          {l.value}
        </p>
      );
    
    if (l.type === "analysis") {
      const analysis = l.value as Record<string, unknown>;
      return (
        <div key={i} className="mb-4 p-4 bg-zinc-900/50 rounded-lg">
          <h3 className="text-zinc-300 mb-2 font-semibold flex items-center gap-2">
            <Globe className="w-4 h-4" />
            📊 Analyse du Site Web
          </h3>
          <div className="text-sm text-zinc-400 space-y-1">
            <p><strong>Type:</strong> {String(analysis.website_type || 'N/A')}</p>
            <p><strong>Description:</strong> {String(analysis.description || 'N/A')}</p>
            <p><strong>Données disponibles:</strong> {Array.isArray(analysis.available_data) ? analysis.available_data.join(", ") : 'N/A'}</p>
            <p><strong>Suggestions:</strong> {Array.isArray(analysis.suggested_extractions) ? analysis.suggested_extractions.join(", ") : 'N/A'}</p>
          </div>
        </div>
      );
    }
    
    if (l.type === "extraction") {
      const data = l.value as Record<string, unknown>;
      const summary = data.extraction_summary as Record<string, unknown> | undefined;
      const items = data.items as Record<string, unknown>[] | undefined;
      
      return (
        <div key={i} className="mb-4 p-4 bg-zinc-900/50 rounded-lg">
          <h3 className="text-zinc-300 mb-2 font-semibold flex items-center gap-2">
            <Download className="w-4 h-4" />
            📊 Données Extraites
          </h3>
          <div className="text-sm text-zinc-400 mb-4">
            <p><strong>Total:</strong> {String(summary?.total_items || 0)} éléments</p>
            <p><strong>Types:</strong> {Array.isArray(summary?.data_types_extracted) ? summary.data_types_extracted.join(", ") : "N/A"}</p>
            <p><strong>Images:</strong> {String(summary?.images_downloaded || 0)} téléchargées</p>
          </div>
          
          {/* Display extracted items inline */}
          {items && items.length > 0 && (
            <div className="mt-4">
              <h4 className="text-zinc-300 mb-3 font-medium flex items-center gap-2">
                📸 Éléments Extraits ({items.length})
              </h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                {items.map((item, idx) => {
                  const imgLocal = item.img_local as string | undefined;
                  const img = item.img as string | undefined;
                  const title = item.title as string | undefined;
                  const price = item.price as string | undefined;
                  const description = item.description as string | undefined;
                  
                  // Debug logging
                  console.log(`Item ${idx}:`, { imgLocal, img, title });
                  
                  // Determine image source
                  let imageSrc = "";
                  let isWebp = false;
                  
                  if (imgLocal) {
                    // Backend now returns full URLs like "https://scraper-mq45.onrender.com/images/filename.jpg"
                    imageSrc = imgLocal;
                    isWebp = imgLocal.endsWith(".webp");
                    console.log(`🔗 Using backend image URL: ${imageSrc}`);
                  } else if (img) {
                    // Fallback to original image URL
                    imageSrc = img;
                    isWebp = img.endsWith(".webp");
                    console.log(`🔗 Using original image URL: ${imageSrc}`);
                  } else {
                    console.log(`⚠️ No image URL found for item ${idx}`);
                  }

                  return (
                    <figure key={idx} className="text-center">
                      <picture>
                        {isWebp && (
                          <source
                            srcSet={imageSrc}
                            type="image/webp"
                          />
                        )}
                        <img
                          src={imageSrc}
                          alt={title || "Image"}
                          className="w-full h-24 object-cover rounded border border-zinc-700"
                          onError={(e) => {
                            console.log(`❌ Image failed to load: ${imageSrc}`);
                            console.log(`❌ Error details:`, e);
                            e.currentTarget.src =
                              "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiBmaWxsPSIjMzM0MTU1Ii8+Cjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIEltYWdlPC90ZXh0Pgo8L3N2Zz4K";
                          }}
                          onLoad={() => {
                            console.log(`✅ Image loaded successfully: ${imageSrc}`);
                          }}
                          onLoadStart={() => {
                            console.log(`🔄 Starting to load image: ${imageSrc}`);
                          }}
                        />
                      </picture>

                      <figcaption
                        className="mt-1 text-xs text-zinc-400 truncate"
                        title={title}
                      >
                        {title}
                      </figcaption>
                      {price && (
                        <div className="text-xs text-green-400 font-mono">
                          {price}
                        </div>
                      )}
                      {description && (
                        <div className="text-xs text-zinc-500 truncate" title={description}>
                          {description}
                        </div>
                      )}
                    </figure>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      );
    }
    
    return (
      <pre key={i} className="text-zinc-400 text-sm mb-2">
        {l.value}
      </pre>
    );
  };

  return (
    <div className="min-h-screen bg-black text-zinc-50 flex flex-col items-center py-10 px-4" suppressHydrationWarning>
      <style jsx>{`
        .select-text::selection {
          background-color: #3b82f6;
          color: white;
        }
        .select-text::-moz-selection {
          background-color: #3b82f6;
          color: white;
        }
      `}</style>
      <div
        ref={termRef}
        className="w-full max-w-4xl h-[70vh] overflow-y-auto font-mono text-base leading-relaxed select-text"
      >
        {lines.map(renderLine)}
        {loading && (
          <p className="flex items-center gap-2 text-zinc-400">
            <Loader2 className="animate-spin w-4 h-4" /> Traitement en cours...
          </p>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        className="w-full max-w-4xl mt-4 flex items-center font-mono"
      >
        <span className="text-green-500 mr-2">scraper&nbsp;$</span>
        <input
          autoFocus
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 bg-transparent outline-none border-none text-zinc-50 placeholder:text-zinc-500"
          placeholder={currentSessionId ? "chat 'Que puis-je extraire ?'" : "new"}
          suppressHydrationWarning
        />
      </form>
      
      {currentSessionId && (
        <div className="w-full max-w-4xl mt-2 text-xs text-zinc-500">
          Session: {currentSessionId.slice(0, 8)}...
        </div>
      )}
    </div>
  );
}
