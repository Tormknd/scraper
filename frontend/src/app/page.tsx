// ScraperTerminal.tsx — interface console façon vzlabs.ai
"use client";

import React, { useState, useEffect, useRef } from "react";
import { Loader2 } from "lucide-react";

/**
 * Commandes :
 *   help                 affiche l’aide
 *   scrap <url>          lance le scraping (POST /api/scrape)
 *   clear                efface l’écran
 * ↑ / ↓                  navigue dans l’historique (10 entrées)
 */
export default function ScraperTerminal() {
  type Line =
    | { type: "prompt"; value: string }
    | { type: "system" | "info" | "error" | "json"; value: string };

  const helpText = [
    "Available commands:",
    "help      Show this help",
    "scrap     Scrap <url>",
    "clear     Clear terminal",
  ].join("\n");

  const [lines, setLines] = useState<Line[]>([
    { type: "system", value: helpText },
  ]);
  const [input, setInput] = useState("help");
  const [loading, setLoading] = useState(false);
  const [gallery, setGallery] = useState<any[]>([]);
  const [history, setHistory] = useState<string[]>([]);
  const [histIdx, setHistIdx] = useState<number | null>(null);
  const termRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    termRef.current?.scrollTo({ top: termRef.current.scrollHeight });
  }, [lines, loading]);

  const push = (l: Line) => setLines((prev) => [...prev, l]);

  const runCommand = async (raw: string) => {
    const tokens = raw.trim().split(/\s+/);
    const cmd = tokens[0]?.toLowerCase();
    if (!cmd) return;

    if (cmd === "help") {
      push({ type: "system", value: helpText });
    } else if (cmd === "clear") {
      setLines([]);
      setGallery([]);
    } else if (cmd === "scrap") {
      if (tokens.length < 2) {
        push({ type: "error", value: "usage: scrap <url>" });
        return;
      }
      const url = tokens[1];
      push({ type: "info", value: `Scraping ${url} …` });
      setLoading(true);
      try {
        const res = await fetch("/api/scrape", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        push({ type: "json", value: JSON.stringify(data, null, 2) });

        if (data.items && Array.isArray(data.items)) {
          setGallery(data.items);
        }
      } catch (e: any) {
        push({ type: "error", value: e.message || "Unknown error" });
      } finally {
        setLoading(false);
      }
    } else {
      push({ type: "error", value: `command not found: ${cmd}` });
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cmd = input.trim();
    if (!cmd) return;
    push({ type: "prompt", value: cmd });
    setHistory((h) => [...h.slice(-9), cmd]);
    setHistIdx(null);
    setInput("");
    runCommand(cmd);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowUp" && history.length) {
      e.preventDefault();
      setHistIdx((idx) => {
        const next = idx === null ? history.length - 1 : Math.max(0, idx - 1);
        setInput(history[next]);
        return next;
      });
    } else if (e.key === "ArrowDown" && history.length) {
      e.preventDefault();
      setHistIdx((idx) => {
        if (idx === null) return null;
        if (idx >= history.length - 1) {
          setInput("");
          return null;
        }
        const next = idx + 1;
        setInput(history[next]);
        return next;
      });
    }
  };

  const renderLine = (l: Line, i: number) => {
    const base = "whitespace-pre-wrap break-words";
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
        <p key={i} className={`${base} text-blue-400`}>
          {l.value}
        </p>
      );
    if (l.type === "error")
      return (
        <p key={i} className={`${base} text-red-400`}>
          {l.value}
        </p>
      );
    return (
      <pre key={i} className="text-zinc-400 text-sm mb-2">
        {l.value}
      </pre>
    );
  };

  return (
    <div className="min-h-screen bg-black text-zinc-50 flex flex-col items-center py-10 px-4 select-none">
      <div
        ref={termRef}
        className="w-full max-w-4xl h-[70vh] overflow-y-auto font-mono text-base leading-relaxed"
      >
        {lines.map(renderLine)}
        {loading && (
          <p className="flex items-center gap-2 text-zinc-400">
            <Loader2 className="animate-spin w-4 h-4" /> processing…
          </p>
        )}

        {gallery.length > 0 && (
          <div className="mt-6 p-4 bg-zinc-900/50 rounded-lg">
            <h3 className="text-zinc-300 mb-4 font-semibold">
              📸 Scraped Images ({gallery.length})
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {gallery.map((item, idx) => {
                const isWebp = item.img_local.endsWith(".webp");
                const fallback = isWebp ? item.img : "";

                return (
                  <figure key={idx} className="text-center">
                    <picture>
                      {isWebp && (
                        <source
                          srcSet={`http://localhost:8000${item.img_local}`}
                          type="image/webp"
                        />
                      )}
                      <img
                        src={
                          isWebp
                            ? fallback || `http://localhost:8000${item.img_local}`
                            : `http://localhost:8000${item.img_local}`
                        }
                        alt={item.title}
                        className="w-full h-24 object-cover rounded border border-zinc-700"
                        onError={(e) => {
                          e.currentTarget.src =
                            "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiBmaWxsPSIjMzM0MTU1Ii8+Cjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPk5vIEltYWdlPC90ZXh0Pgo8L3N2Zz4K";
                        }}
                      />
                    </picture>
                    <figcaption
                      className="mt-1 text-xs text-zinc-400 truncate"
                      title={item.title}
                    >
                      {item.title}
                    </figcaption>
                    {item.price && (
                      <div className="text-xs text-green-400 font-mono">
                        {item.price}
                      </div>
                    )}
                  </figure>
                );
              })}
            </div>
          </div>
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
          placeholder="help"
        />
      </form>
    </div>
  );
}
