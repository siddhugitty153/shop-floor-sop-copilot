import React, { useState, useEffect, useRef } from "react";
import {
  ShieldAlert,
  Mic,
  MicOff,
  Search,
  Settings,
  FileText,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Cpu,
  Clock,
  Layers,
  Sparkles,
  ExternalLink
} from "lucide-react";

export default function App() {
  // Dynamic LAN API discovery: default to the hostname of the browser
  const [apiBaseUrl, setApiBaseUrl] = useState(() => {
    const hostname = window.location.hostname || "localhost";
    return `http://${hostname}:8000`;
  });

  const [health, setHealth] = useState({ online: false, chunks: 0, llm: "connecting..." });
  const [documents, setDocuments] = useState([]);
  const [category, setCategory] = useState("All");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [expandedSources, setExpandedSources] = useState({});
  const [isListening, setIsListening] = useState(false);
  const [speechError, setSpeechError] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [tempUrl, setTempUrl] = useState(apiBaseUrl);

  const recognitionRef = useRef(null);

  // Poll Health
  const checkHealth = async (url = apiBaseUrl) => {
    try {
      const res = await fetch(`${url}/health`, { method: "GET", credentials: "omit" });
      if (res.ok) {
        const data = await res.json();
        setHealth({
          online: true,
          chunks: data.indexed_chunks,
          llm: data.configured_llm
        });
      } else {
        setHealth({ online: false, chunks: 0, llm: "offline" });
      }
    } catch (e) {
      setHealth({ online: false, chunks: 0, llm: "offline" });
    }
  };

  // Fetch Documents
  const fetchDocs = async (url = apiBaseUrl) => {
    try {
      const res = await fetch(`${url}/documents`);
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (e) {
      console.warn("Could not fetch documents", e);
    }
  };

  useEffect(() => {
    checkHealth(apiBaseUrl);
    fetchDocs(apiBaseUrl);
    const interval = setInterval(() => checkHealth(apiBaseUrl), 8000);
    return () => clearInterval(interval);
  }, [apiBaseUrl]);

  // Setup Web Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-US";

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setQuestion(transcript);
        setIsListening(false);
        setSpeechError("");
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
        if (event.error === "not-allowed") {
          setSpeechError("Microphone access denied.");
        } else {
          setSpeechError(`Voice input error: ${event.error}`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      setSpeechError("Voice input is not supported in this browser. Please type your query.");
      return;
    }
    setSpeechError("");
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (err) {
        console.error("Speech start error", err);
        setIsListening(false);
      }
    }
  };

  const handleAsk = async (queryText = question, cat = category) => {
    const q = queryText.trim();
    if (!q) return;

    setLoading(true);
    setResponse(null);
    setExpandedSources({});

    try {
      const res = await fetch(`${apiBaseUrl}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, category_filter: cat })
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data = await res.json();
      setResponse(data);
    } catch (err) {
      setResponse({
        question: q,
        answer: `Connection Error: Unable to reach backend at ${apiBaseUrl}. Ensure FastAPI is running on host 0.0.0.0:8000.`,
        is_answerable: false,
        safety_warning: null,
        sources: [],
        llm_used: "client-error",
        latency_ms: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleSource = (idx) => {
    setExpandedSources((prev) => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const PRELOADED_QUESTIONS = [
    {
      label: "💧 Coolant Concentration",
      category: "Maintenance",
      text: "What is the recommended coolant concentration for the TX-200 CNC turning centre?"
    },
    {
      label: "🚨 Alarm AL-104 Action",
      category: "Maintenance",
      text: "The machine is showing alarm AL-104. What does it mean and what should the operator do?"
    },
    {
      label: "🔒 Lockout Removal Authority",
      category: "Safety",
      text: "Who is allowed to remove a lockout lock from a machine?"
    },
    {
      label: "📏 BH-220 OD Tolerance",
      category: "Quality",
      text: "What is the outer diameter tolerance for the BH-220 bearing housing?"
    },
    {
      label: "⏱️ Spindle Runout Frequency",
      category: "Maintenance",
      text: "How often should spindle runout be checked, and who does it?"
    },
    {
      label: "⚠️ Mandatory LOTO & PPE",
      category: "Safety",
      text: "What are the mandatory Lockout/Tagout (LOTO) and PPE requirements before performing maintenance?"
    },
    {
      label: "🔧 Preventive Maintenance",
      category: "Maintenance",
      text: "What is the standard preventive maintenance and lubrication schedule for the shop-floor equipment?"
    },
    {
      label: "🔍 Out-of-Tolerance Defect",
      category: "Quality",
      text: "What are the quality inspection criteria and actions required when an out-of-tolerance defect is detected?"
    },
    {
      label: "🚫 Out-of-Scope (Flight Policy)",
      category: "All",
      isRefusalTest: true,
      text: "What is the corporate reimbursement policy for international business class flights and hotel stays?"
    }
  ];

  return (
    <div className="min-h-screen bg-[#090D16] text-slate-100 flex flex-col font-sans pb-16">
      {/* TOP INDUSTRIAL HEADER */}
      <header className="sticky top-0 z-30 bg-[#111827]/95 backdrop-blur border-b border-[#1F2937] px-4 py-3 shadow-md">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 font-black text-xl shadow-inner">
              ⚙️
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold tracking-wider text-amber-400 text-sm md:text-base">
                  PLANT OPS
                </span>
                <span className="text-slate-500 text-xs">//</span>
                <span className="font-bold text-slate-200 text-xs md:text-sm">
                  SOP COPILOT
                </span>
              </div>
              <div className="text-[10px] uppercase tracking-widest text-slate-400 font-mono">
                BiztelAI Grounded Assistant
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* LAN Live Status Pill */}
            <div
              className={`flex items-center space-x-1.5 px-2.5 py-1.5 rounded-full text-xs font-mono border ${
                health.online
                  ? "bg-emerald-950/60 border-emerald-500/40 text-emerald-300"
                  : "bg-red-950/60 border-red-500/40 text-red-300 animate-pulse"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  health.online ? "bg-emerald-400 animate-pulse" : "bg-red-500"
                }`}
              />
              <span className="hidden sm:inline">
                {health.online ? `LAN ONLINE • ${health.chunks} CHUNKS` : "OFFLINE"}
              </span>
              <span className="sm:hidden">{health.online ? `${health.chunks} Chunks` : "Offline"}</span>
            </div>

            {/* Settings Button */}
            <button
              onClick={() => {
                setTempUrl(apiBaseUrl);
                setShowSettings(true);
              }}
              className="min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
              title="Settings & Loaded Documents"
              aria-label="Settings"
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* MAIN CONTAINER */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-3 sm:px-4 pt-4 space-y-4">
        {/* CATEGORY FILTER BAR (Large Touch Targets >= 48px) */}
        <section aria-label="Category Selection">
          <div className="grid grid-cols-4 gap-2">
            {["All", "Safety", "Maintenance", "Quality"].map((cat) => {
              const active = category === cat;
              return (
                <button
                  key={cat}
                  onClick={() => setCategory(cat)}
                  className={`min-h-[48px] rounded-xl font-bold text-xs sm:text-sm tracking-wide transition-all uppercase flex items-center justify-center shadow-sm select-none active:scale-95 ${
                    active
                      ? "bg-amber-500 text-slate-950 font-black shadow-amber-500/20 shadow-lg ring-2 ring-amber-400"
                      : "bg-[#111827] text-slate-300 hover:bg-slate-800 border border-[#1F2937]"
                  }`}
                >
                  {cat === "Safety" && "⚠️ "}
                  {cat === "Maintenance" && "🔧 "}
                  {cat === "Quality" && "🔍 "}
                  {cat}
                </button>
              );
            })}
          </div>
        </section>

        {/* SHOP-FLOOR SEARCH BAR & VOICE INPUT */}
        <section className="bg-[#111827] p-2.5 sm:p-3 rounded-2xl border border-[#1F2937] shadow-xl space-y-2">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleAsk();
            }}
            className="flex items-center space-x-2"
          >
            <div className="relative flex-1">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask SOP procedure, specs, or safety rules..."
                className="w-full min-h-[52px] bg-[#090D16] border border-[#1F2937] rounded-xl px-4 pl-11 text-sm sm:text-base text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500 transition"
              />
              <Search className="w-5 h-5 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            {/* Voice Input Button */}
            <button
              type="button"
              onClick={toggleListening}
              className={`min-h-[52px] min-w-[52px] rounded-xl flex items-center justify-center border transition active:scale-95 ${
                isListening
                  ? "bg-red-600 text-white border-red-500 animate-bounce shadow-lg shadow-red-500/30"
                  : "bg-slate-800 hover:bg-slate-700 text-amber-400 border-slate-700"
              }`}
              title="Voice Input (Hands-free)"
              aria-label="Hands-free Voice Input"
            >
              {isListening ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
            </button>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="min-h-[52px] px-5 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-40 disabled:hover:bg-amber-500 text-slate-950 font-black text-sm tracking-wide uppercase flex items-center justify-center transition active:scale-95 shadow-md shadow-amber-500/20"
            >
              {loading ? (
                <RefreshCw className="w-5 h-5 animate-spin text-slate-950" />
              ) : (
                "Search"
              )}
            </button>
          </form>

          {isListening && (
            <div className="text-xs text-amber-400 font-mono animate-pulse flex items-center space-x-2 pt-1 pl-1">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
              <span>Listening to shop-floor voice input... Speak now</span>
            </div>
          )}

          {speechError && (
            <div className="text-xs text-red-400 font-mono flex items-center space-x-1 pt-1 pl-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>{speechError}</span>
            </div>
          )}
        </section>

        {/* GLOVE-FRIENDLY QUICK QUESTION CHIPS */}
        <section className="space-y-1.5">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1 font-mono uppercase tracking-wider">
            <span>⚡ Supervisor Quick-Tap Chips</span>
            <span className="text-[10px] text-slate-500">Tap to test</span>
          </div>

          <div className="flex flex-wrap gap-2">
            {PRELOADED_QUESTIONS.map((q, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuestion(q.text);
                  setCategory(q.category);
                  handleAsk(q.text, q.category);
                }}
                className={`min-h-[48px] px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition active:scale-95 text-left border flex items-center space-x-2 shadow-sm ${
                  q.isRefusalTest
                    ? "bg-red-950/40 hover:bg-red-900/50 border-red-500/50 text-red-300 ring-1 ring-red-500/30"
                    : "bg-[#111827] hover:bg-slate-800 border-[#1F2937] text-slate-200"
                }`}
              >
                <span>{q.label}</span>
              </button>
            ))}
          </div>
        </section>

        {/* LOADING INDICATOR */}
        {loading && (
          <div className="bg-[#111827] border border-[#1F2937] rounded-2xl p-8 flex flex-col items-center justify-center space-y-3 shadow-xl">
            <div className="relative">
              <div className="w-12 h-12 rounded-full border-4 border-amber-500/20 border-t-amber-500 animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-amber-400" />
              </div>
            </div>
            <div className="text-sm font-bold text-slate-200 tracking-wide">
              RETRIEVING GROUNDED SOP EVIDENCE...
            </div>
            <div className="text-xs text-slate-400 font-mono">
              Cosine similarity filter & safety scanner active
            </div>
          </div>
        )}

        {/* RESPONSE DISPLAY */}
        {response && !loading && (
          <section className="space-y-3">
            {/* Refusal / Out-of-Scope Card */}
            {!response.is_answerable ? (
              <div className="bg-[#181116] border-2 border-amber-500/60 rounded-2xl p-5 shadow-2xl space-y-3">
                <div className="flex items-center space-x-3 text-amber-400 font-black text-sm sm:text-base uppercase tracking-wider">
                  <XCircle className="w-6 h-6 text-amber-400 flex-shrink-0" />
                  <span>Out of Scope — Not Found in Plant SOPs</span>
                </div>
                <div className="bg-amber-950/30 border border-amber-500/30 rounded-xl p-4 text-slate-200 text-sm leading-relaxed">
                  {response.answer}
                </div>
                <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] font-mono text-slate-400">
                  <span className="bg-slate-800 px-2 py-1 rounded border border-slate-700">
                    Engine: {response.llm_used}
                  </span>
                  <span className="bg-slate-800 px-2 py-1 rounded border border-slate-700">
                    Latency: {response.latency_ms}ms
                  </span>
                  <span className="text-amber-400/80">Strict zero-hallucination guardrail active</span>
                </div>
              </div>
            ) : (
              /* Verified Answer Card */
              <div className="bg-[#111827] border border-[#1F2937] rounded-2xl p-4 sm:p-6 shadow-2xl space-y-4">
                {/* AUTOMATED SAFETY / LOTO HAZARD BANNER */}
                {response.safety_warning && (
                  <div className="bg-gradient-to-r from-red-950/80 via-red-900/60 to-amber-950/80 border-2 border-red-500 rounded-xl p-4 flex items-start space-x-3 shadow-lg shadow-red-950/50">
                    <ShieldAlert className="w-7 h-7 text-red-400 flex-shrink-0 animate-pulse mt-0.5" />
                    <div>
                      <div className="text-xs font-black text-red-300 uppercase tracking-widest">
                        CRITICAL SAFETY / LOTO REMINDER
                      </div>
                      <div className="text-sm sm:text-base font-bold text-white mt-0.5 leading-snug">
                        {response.safety_warning}
                      </div>
                    </div>
                  </div>
                )}

                {/* Copilot Answer Content */}
                <div>
                  <div className="flex items-center justify-between pb-2 border-b border-[#1F2937] mb-3">
                    <div className="flex items-center space-x-2 text-xs font-mono uppercase text-emerald-400 font-bold">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Grounded Plant Answer</span>
                    </div>
                    <div className="flex items-center space-x-2 text-[11px] font-mono text-slate-400">
                      <span className="flex items-center space-x-1">
                        <Cpu className="w-3 h-3 text-slate-400" />
                        <span>{response.llm_used}</span>
                      </span>
                      <span>•</span>
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span>{response.latency_ms}ms</span>
                      </span>
                    </div>
                  </div>

                  <div className="text-sm sm:text-base text-slate-100 leading-relaxed whitespace-pre-line space-y-2">
                    {response.answer}
                  </div>
                </div>

                {/* EXPANDABLE RAW PDF EVIDENCE SNIPPETS */}
                {response.sources && response.sources.length > 0 && (
                  <div className="pt-2 border-t border-[#1F2937] space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase tracking-wider">
                      <span className="flex items-center space-x-1.5">
                        <Layers className="w-3.5 h-3.5 text-amber-400" />
                        <span>Cited SOP Documents ({response.sources.length})</span>
                      </span>
                      <span className="text-[10px] text-slate-500">Tap to inspect raw text</span>
                    </div>

                    <div className="space-y-2">
                      {response.sources.map((src, idx) => {
                        const isExpanded = !!expandedSources[idx];
                        const matchPct = Math.round(src.score * 100);
                        return (
                          <div
                            key={idx}
                            className="border border-[#1F2937] rounded-xl overflow-hidden bg-[#090D16]"
                          >
                            <button
                              type="button"
                              onClick={() => toggleSource(idx)}
                              className="w-full min-h-[48px] px-3.5 py-2.5 flex items-center justify-between text-left hover:bg-slate-800/60 transition active:scale-[0.99]"
                            >
                              <div className="flex items-center space-x-2 truncate">
                                <FileText className="w-4 h-4 text-amber-400 flex-shrink-0" />
                                <span className="text-xs sm:text-sm font-bold text-slate-200 truncate">
                                  {src.source_file}
                                </span>
                                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300 font-mono">
                                  p. {src.page_number}
                                </span>
                                <span className="text-xs px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 font-mono">
                                  {matchPct}% match
                                </span>
                              </div>
                              <div className="flex items-center space-x-1 text-slate-400 ml-2">
                                <span className="text-[10px] uppercase font-mono hidden sm:inline">
                                  {isExpanded ? "Collapse" : "Snippet"}
                                </span>
                                {isExpanded ? (
                                  <ChevronUp className="w-4 h-4 text-amber-400" />
                                ) : (
                                  <ChevronDown className="w-4 h-4" />
                                )}
                              </div>
                            </button>

                            {isExpanded && (
                              <div className="px-4 py-3 bg-[#0D1322] border-t border-[#1F2937] text-xs font-mono text-slate-300 leading-relaxed">
                                <div className="text-[10px] text-amber-400 uppercase tracking-widest pb-1">
                                  Exact Page Excerpt:
                                </div>
                                <blockquote className="border-l-2 border-amber-500 pl-3 italic text-slate-200">
                                  "{src.snippet}"
                                </blockquote>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </section>
        )}
      </main>

      {/* SETTINGS & DOCUMENTS MODAL */}
      {showSettings && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#111827] border border-[#1F2937] rounded-2xl max-w-lg w-full p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-2 border-b border-[#1F2937]">
              <div className="flex items-center space-x-2 text-amber-400 font-black tracking-wide">
                <Settings className="w-5 h-5" />
                <span>SETTINGS & LOADED SOPs</span>
              </div>
              <button
                onClick={() => setShowSettings(false)}
                className="text-slate-400 hover:text-white p-1"
                aria-label="Close Settings"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-mono uppercase text-slate-300 mb-1">
                  FastAPI Backend URL
                </label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={tempUrl}
                    onChange={(e) => setTempUrl(e.target.value)}
                    placeholder="http://192.168.1.x:8000"
                    className="flex-1 bg-[#090D16] border border-[#1F2937] rounded-xl px-3 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-amber-500"
                  />
                  <button
                    onClick={() => {
                      setApiBaseUrl(tempUrl);
                      checkHealth(tempUrl);
                      fetchDocs(tempUrl);
                      setShowSettings(false);
                    }}
                    className="px-4 py-2 bg-amber-500 text-slate-950 font-bold rounded-xl text-xs uppercase"
                  >
                    Save
                  </button>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Default: Dynamically inherits current hostname (e.g., your laptop's Wi-Fi IP).
                </p>
              </div>

              <div className="pt-2 border-t border-[#1F2937]">
                <div className="text-xs font-mono uppercase text-slate-300 mb-2 flex items-center justify-between">
                  <span>Indexed Plant Documents</span>
                  <span className="text-amber-400 font-bold">{documents.length} Files</span>
                </div>

                {documents.length === 0 ? (
                  <div className="text-xs text-slate-400 bg-[#090D16] p-3 rounded-xl border border-[#1F2937]">
                    No documents indexed yet. Drop the 4 PDFs into <code className="text-amber-300">data/pdfs/</code> and run <code className="text-amber-300">python -m app.ingest</code>.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {documents.map((doc, i) => (
                      <div
                        key={i}
                        className="p-2.5 rounded-lg bg-[#090D16] border border-[#1F2937] text-xs flex items-center justify-between"
                      >
                        <div>
                          <div className="font-bold text-slate-200">{doc.source_file}</div>
                          <div className="text-slate-400 text-[10px] font-mono">
                            Category: {doc.category} • Max Page: {doc.max_page}
                          </div>
                        </div>
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-amber-400 font-mono text-[11px]">
                          {doc.chunks} chunks
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="pt-3 border-t border-[#1F2937] flex justify-end">
              <button
                onClick={() => setShowSettings(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold uppercase"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

