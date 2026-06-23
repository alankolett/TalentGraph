"use client";

import React, { useEffect, useRef, useState } from "react";
import NeuralBackground from "./NeuralBackground";
import Lenis from "@studio-freight/lenis";
import { gsap } from "gsap";
import { motion, AnimatePresence } from "framer-motion";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { 
  Terminal, 
  Sparkles, 
  ArrowRight, 
  Zap, 
  Check, 
  Copy, 
  Activity, 
  Database,
  Sun,
  Moon
} from "lucide-react";

// Register GSAP ScrollTrigger
if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}


// ==================== LIVE RANKING STACK COMPONENT ====================
const initialCandidates = [
  { id: 'cand-1', name: 'Elena Rostova', role: 'Senior Python Dev', score: 20, maxScore: 98, color: 'bg-indigo-500' },
  { id: 'cand-2', name: 'Marcus Vance', role: 'Lead Architect', score: 20, maxScore: 94, color: 'bg-violet-500' },
  { id: 'cand-3', name: 'Siddharth Nair', role: 'Backend Engineer', score: 20, maxScore: 89, color: 'bg-blue-500' },
  { id: 'cand-4', name: 'Structured Profile', role: 'Fullstack', score: 20, maxScore: 75, color: 'bg-emerald-500' }
];

const LiveRankingStack = () => {
  const [candidates, setCandidates] = useState(initialCandidates);

  useEffect(() => {
    let tick = 0;
    const interval = setInterval(() => {
      tick++;
      setCandidates(prev => {
        let updated = prev.map(c => {
          // Slowly increase score until maxScore
          if (c.score < c.maxScore) {
            return { ...c, score: Math.min(c.maxScore, c.score + Math.floor(Math.random() * 15) + 5) };
          }
          return c;
        });
        
        // Only sort if we have reached a certain tick to let bars fill first, then re-sort
        if (tick > 3) {
           updated = updated.sort((a, b) => b.score - a.score);
        }
        
        // Reset loop after a while
        if (tick > 15) {
          tick = 0;
          return initialCandidates;
        }
        
        return updated;
      });
    }, 600);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full max-w-md mx-auto space-y-3 relative perspective-1000">
      <div className="absolute -inset-4 bg-gradient-to-b from-indigo-500/5 to-transparent rounded-3xl blur-xl -z-10" />
      <AnimatePresence>
        {candidates.map((cand, i) => (
          <motion.div
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
            key={cand.id}
            className="flex items-center gap-4 p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm relative overflow-hidden"
          >
            {/* Background fill bar */}
            <motion.div 
              className={`absolute top-0 left-0 h-full opacity-10 dark:opacity-20 ${cand.color}`}
              initial={{ width: '20%' }}
              animate={{ width: `${cand.score}%` }}
              transition={{ ease: "easeOut", duration: 0.5 }}
            />
            
            <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-500 dark:text-slate-400 shrink-0 z-10">
              {cand.name.charAt(0)}
            </div>
            <div className="flex-1 z-10">
              <div className="text-sm font-bold text-slate-900 dark:text-white flex justify-between">
                <span>{cand.name}</span>
                <span className="font-mono text-indigo-600 dark:text-indigo-400">{cand.score}%</span>
              </div>
              <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                {cand.role}
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};


// ==================== FEATURE SCROLL RAIL COMPONENT ====================
const features = [
  {
    title: "Knowledge Graph",
    icon: <Database className="w-6 h-6 text-indigo-500" />,
    text: "Calculates synoymic skill node distances dynamically.",
    animation: (
      <div className="w-full h-24 bg-slate-100 dark:bg-slate-800/50 rounded-lg mt-4 flex items-center justify-center relative overflow-hidden">
        <motion.div
          className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-[10px] text-white font-bold absolute"
          animate={{ x: [-40, -10, -40] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          JS
        </motion.div>
        <motion.div
          className="w-8 h-8 rounded-full bg-violet-500 flex items-center justify-center text-[10px] text-white font-bold absolute"
          animate={{ x: [40, 10, 40] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          TS
        </motion.div>
        <motion.div
          className="absolute h-[2px] bg-indigo-300 dark:bg-indigo-700 z-[-1]"
          animate={{ width: [0, 40, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        />
      </div>
    )
  },
  {
    title: "Hybrid Retrieval",
    icon: <Activity className="w-6 h-6 text-emerald-500" />,
    text: "Merges BM25 lexical frequency with Qdrant vector scores.",
    animation: (
      <div className="w-full h-24 bg-slate-100 dark:bg-slate-800/50 rounded-lg mt-4 flex flex-col items-center justify-center gap-2 px-6">
        <div className="w-full flex justify-between gap-4">
          <motion.div className="h-2 bg-slate-300 dark:bg-slate-600 rounded-full flex-1" animate={{ scaleX: [0.3, 1, 0.3], originX: 0 }} transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }} />
          <motion.div className="h-2 bg-emerald-400 rounded-full flex-1" animate={{ scaleX: [1, 0.3, 1], originX: 1 }} transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }} />
        </div>
        <motion.div className="h-2 bg-gradient-to-r from-slate-400 to-emerald-500 rounded-full w-full" animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 2.5, repeat: Infinity, ease: "easeInOut" }} />
      </div>
    )
  },
  {
    title: "Behavioral Signals",
    icon: <Zap className="w-6 h-6 text-amber-500" />,
    text: "Telemetry indexing candidates OSS commits and velocities.",
    animation: (
      <div className="w-full h-24 bg-slate-100 dark:bg-slate-800/50 rounded-lg mt-4 flex items-end justify-center gap-1 p-4">
        {[0.2, 0.5, 0.3, 0.8, 0.4, 0.9, 0.6].map((h, i) => (
          <motion.div 
            key={i} 
            className="w-4 bg-amber-400 rounded-t-sm"
            initial={{ height: '10%' }}
            animate={{ height: `${h * 100}%` }}
            transition={{ duration: 1, repeat: Infinity, repeatType: "mirror", delay: i * 0.1 }}
          />
        ))}
      </div>
    )
  },
  {
    title: "Explainability Matrix",
    icon: <Sparkles className="w-6 h-6 text-purple-500" />,
    text: "Generates narratives detailing exactly why profiles align.",
    animation: (
      <div className="w-full h-24 bg-slate-100 dark:bg-slate-800/50 rounded-lg mt-4 flex flex-col items-start justify-center gap-2 p-4">
        <motion.div className="h-2 bg-purple-400 rounded-full w-3/4" animate={{ opacity: [0, 1] }} transition={{ duration: 0.5, repeat: Infinity, repeatType: "reverse", repeatDelay: 2 }} />
        <motion.div className="h-2 bg-slate-300 dark:bg-slate-600 rounded-full w-full" animate={{ opacity: [0, 1] }} transition={{ duration: 0.5, delay: 0.2, repeat: Infinity, repeatType: "reverse", repeatDelay: 2 }} />
        <motion.div className="h-2 bg-slate-300 dark:bg-slate-600 rounded-full w-5/6" animate={{ opacity: [0, 1] }} transition={{ duration: 0.5, delay: 0.4, repeat: Infinity, repeatType: "reverse", repeatDelay: 2 }} />
      </div>
    )
  }
];

const FeatureScrollRail = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);

  // Use layout effect for accurate GSAP calculations
  React.useLayoutEffect(() => {
    if (!containerRef.current || !trackRef.current) return;
    const track = trackRef.current;
    
    let ctx = gsap.context(() => {
      let mm = gsap.matchMedia();

      // Desktop + Motion preferred: Horizontal Pin
      mm.add("(min-width: 768px) and (prefers-reduced-motion: no-preference)", () => {
        const tl = gsap.timeline({
          scrollTrigger: {
            trigger: containerRef.current,
            start: "top 20%",
            end: () => `+=${track.scrollWidth - window.innerWidth}`,
            pin: true,
            scrub: 1,
            invalidateOnRefresh: true,
          }
        });

        tl.to(track, {
          x: () => -(track.scrollWidth - window.innerWidth + 100),
          ease: "none"
        });
      });

      // Mobile or Reduced Motion: Vertical Fade Stack
      mm.add("(max-width: 767px), (prefers-reduced-motion: reduce)", () => {
        // Reset track position if it was moved
        gsap.set(track, { clearProps: "all" });
        
        const cards = track.querySelectorAll('.bento-glass-card');
        cards.forEach(card => {
          gsap.fromTo(card, 
            { opacity: 0, y: 30 },
            { 
              opacity: 1, 
              y: 0, 
              scrollTrigger: {
                trigger: card,
                start: "top 80%",
              }
            }
          );
        });
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={containerRef} className="py-20 w-full">
      <div className="px-8 md:px-12 mb-10 text-center md:text-left">
        <h3 className="text-4xl md:text-5xl font-black tracking-tight text-slate-900 dark:text-white mb-4">
          Core Vector Subsystems
        </h3>
        <p className="text-slate-500 dark:text-slate-400 text-lg max-w-xl">
          Four low-latency ranking components running concurrently over sqlite and vector databases.
        </p>
      </div>

      <div ref={trackRef} className="flex flex-col md:flex-row md:flex-nowrap gap-8 px-8 md:px-12 w-full md:w-max">
        {features.map((card, i) => (
          <div 
            key={i} 
            className="w-full md:w-[450px] shrink-0 bento-glass-card p-8 flex flex-col justify-between hover:border-indigo-500/30 transition-all duration-300 bg-white/60 dark:bg-slate-900/60"
          >
            <div>
              <div className="w-12 h-12 rounded-2xl bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 flex items-center justify-center shadow-sm mb-6">
                {card.icon}
              </div>
              <h4 className="text-xl font-bold text-slate-900 dark:text-white font-heading mb-2">{card.title}</h4>
              <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed mb-6">{card.text}</p>
            </div>
            {card.animation}
          </div>
        ))}
      </div>
    </section>
  );
};


// ==================== SCROLL-TRIGGERED CODE REVEAL ====================
const CodeRevealBlock = () => {
  const codeLines = [
    { text: "import { rankCandidate, cosineDistance } from 'talentgraph/core';", tokens: [{ text: "import", class: "text-indigo-400" }, { text: " { rankCandidate, cosineDistance } ", class: "text-slate-300" }, { text: "from", class: "text-indigo-400" }, { text: " 'talentgraph/core';", class: "text-emerald-400" }] },
    { text: "function AnalyzeCandidateSignals(id) {", tokens: [{ text: "function", class: "text-indigo-400" }, { text: " AnalyzeCandidateSignals", class: "text-amber-300" }, { text: "(id) {", class: "text-slate-300" }] },
    { text: "  // Compute semantic vector weights", tokens: [{ text: "  // Compute semantic vector weights", class: "text-slate-500" }] },
    { text: "  const dist = cosineDistance(cand, job);", tokens: [{ text: "  const", class: "text-indigo-400" }, { text: " dist = ", class: "text-slate-300" }, { text: "cosineDistance", class: "text-amber-300" }, { text: "(cand, job);", class: "text-slate-300" }] },
    { text: "  return rankCandidate(id, dist, 0.5);", tokens: [{ text: "  return", class: "text-indigo-400" }, { text: " ", class: "text-slate-300" }, { text: "rankCandidate", class: "text-amber-300" }, { text: "(id, dist, ", class: "text-slate-300" }, { text: "0.5", class: "text-emerald-500" }, { text: ");", class: "text-slate-300" }] },
    { text: "}", tokens: [{ text: "}", class: "text-slate-300" }] }
  ];

  const containerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!containerRef.current) return;
    const lines = containerRef.current.querySelectorAll('.code-line');
    
    let ctx = gsap.context(() => {
      let mm = gsap.matchMedia();
      
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.set(lines, { opacity: 0, x: -10 });
        gsap.to(lines, {
          opacity: 1,
          x: 0,
          stagger: 0.1,
          ease: "power2.out",
          scrollTrigger: {
            trigger: containerRef.current,
            start: "top 70%",
            end: "top 30%",
            scrub: 1
          }
        });
      });
      
      mm.add("(prefers-reduced-motion: reduce)", () => {
        gsap.set(lines, { opacity: 1, x: 0 });
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <pre ref={containerRef} className="text-slate-400 select-none overflow-x-auto text-[10px] md:text-[11px] leading-loose">
      <code>
        {codeLines.map((line, i) => (
          <div key={i} className="code-line min-h-[1.5em]">
            {line.tokens.map((token, j) => (
              <span key={j} className={token.class}>{token.text}</span>
            ))}
          </div>
        ))}
      </code>
    </pre>
  );
};


// ==================== STAT COUNTERS ====================
const StatCounter = ({ endValue, label, suffix = "" }: { endValue: number, label: string, suffix?: string }) => {
  const nodeRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (!nodeRef.current) return;
    
    gsap.fromTo(nodeRef.current, 
      { innerText: 0 }, 
      { 
        innerText: endValue, 
        duration: 2, 
        ease: "power2.out",
        snap: { innerText: 1 },
        scrollTrigger: {
          trigger: nodeRef.current,
          start: "top 90%",
        },
        onUpdate: function() {
          if (nodeRef.current) {
            nodeRef.current.innerText = Math.ceil(Number(this.targets()[0].innerText)) + suffix;
          }
        }
      }
    );
  }, [endValue, suffix]);

  return (
    <div className="flex flex-col items-center justify-center p-6 border border-slate-200/50 dark:border-slate-800/50 rounded-2xl bg-white/40 dark:bg-slate-900/40 backdrop-blur-sm">
      <div ref={nodeRef} className="text-4xl md:text-5xl font-black text-indigo-600 dark:text-indigo-400 font-heading mb-2">0</div>
      <div className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">{label}</div>
    </div>
  );
};

const StatRow = () => (
  <section className="w-full max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 py-12 px-6">
    <StatCounter endValue={142} label="Active Job Roles" />
    <StatCounter endValue={85} suffix="k+" label="Catalog Candidates" />
    <StatCounter endValue={12} suffix="ms" label="Avg Query Latency" />
  </section>
);

interface RemixLandingPageProps {
  onEnterApp: () => void;
}

export default function RemixLandingPage({ onEnterApp }: RemixLandingPageProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const magneticRef = useRef<HTMLButtonElement>(null);
  const [copied, setCopied] = useState(false);
  const [email, setEmail] = useState("");
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const savedTheme = localStorage.getItem("theme") as "light" | "dark" | null;
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initialTheme = savedTheme || (systemPrefersDark ? "dark" : "light");
    setTheme(initialTheme);
    if (initialTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const codeString = `import { type Handle, on } from 'talentgraph/core';

function AnalyzeCandidateSignals(candidateId: string) {
  // Compute semantic vector alignment weights
  const semanticDist = cosineDistance(candidate, jobProfile);
  const commitsWeight = evaluateCommitVelocity(candidate.github);
  
  return rankCandidate({
    candidateId,
    semanticDist,
    commitsWeight,
    biasWeight: 0.5 // Slider Matrix Tuning
  });
}`;

  // ==================== LENIS + GSAP TICKER SETUP ====================
  useEffect(() => {
    if (typeof window === "undefined") return;

    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
      wheelMultiplier: 1.0,
      touchMultiplier: 2.0,
      infinite: false,
    });

    lenis.on("scroll", ScrollTrigger.update);

    const tickerUpdate = (time: number) => {
      lenis.raf(time * 1000);
    };
    gsap.ticker.add(tickerUpdate);
    gsap.ticker.lagSmoothing(0);

    return () => {
      lenis.destroy();
      gsap.ticker.remove(tickerUpdate);
    };
  }, []);

  // ==================== BENTO CARD ENTRY ANIMATIONS ====================
  useEffect(() => {
    const cards = document.querySelectorAll(".bento-glass-card");

    cards.forEach((card) => {
      // Set initial state
      gsap.set(card, {
        opacity: 0,
        scale: 0.92,
        rotateX: 12,
        y: 80,
        transformPerspective: 1200,
        transformOrigin: "center center",
      });

      // Animates on scroll
      gsap.to(card, {
        opacity: 1,
        scale: 1,
        rotateX: 0,
        y: 0,
        ease: "power2.out",
        scrollTrigger: {
          trigger: card,
          start: "top bottom-=40px",
          end: "top center+=120px",
          scrub: 0.6,
          invalidateOnRefresh: true,
        },
      });
    });
  }, []);

  // ==================== MAGNETIC BUTTON CTA physics ====================
  useEffect(() => {
    const btn = magneticRef.current;
    if (!btn) return;

    let mouseX = 0, mouseY = 0;
    let btnX = 0, btnY = 0;
    let reqId = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const boundBox = btn.getBoundingClientRect();
      const dx = e.clientX - (boundBox.left + boundBox.width / 2);
      const dy = e.clientY - (boundBox.top + boundBox.height / 2);

      // Check hover boundary radius (75px)
      if (Math.sqrt(dx * dx + dy * dy) < 75) {
        mouseX = dx * 0.4;
        mouseY = dy * 0.4;
      } else {
        mouseX = 0;
        mouseY = 0;
      }
    };

    const animateButton = () => {
      btnX += (mouseX - btnX) * 0.12;
      btnY += (mouseY - btnY) * 0.12;

      btn.style.transform = `translate3d(${btnX}px, ${btnY}px, 0)`;
      reqId = requestAnimationFrame(animateButton);
    };

    window.addEventListener("mousemove", handleMouseMove);
    reqId = requestAnimationFrame(animateButton);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      cancelAnimationFrame(reqId);
    };
  }, []);

  // ==================== NAV LINK BRACKETS MICRO-INTERACTION ====================
  const handleLinkEnter = (e: React.MouseEvent<HTMLElement>) => {
    const brackets = e.currentTarget.querySelectorAll(".bracket");
    gsap.to(brackets, { x: (i) => (i === 0 ? -3 : 3), duration: 0.2 });
  };

  const handleLinkLeave = (e: React.MouseEvent<HTMLElement>) => {
    const brackets = e.currentTarget.querySelectorAll(".bracket");
    gsap.to(brackets, { x: 0, duration: 0.2 });
  };

  // ==================== GLOBAL KEYBOARD SHORTCUTS ROUTER ====================
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (["INPUT", "TEXTAREA"].includes((event.target as HTMLElement).tagName)) return;

      const key = event.key.toUpperCase();
      if (key === "G") {
        window.open("https://github.com/alankolett/TalentGraph", "_blank");
      } else if (key === "D") {
        window.open("https://github.com/alankolett/TalentGraph#readme", "_blank");
      } else if (key === "B") {
        alert("Navigating to Blog... (Simulated)");
      } else if (key === "J") {
        alert("Navigating to Jam... (Simulated)");
      } else if (key === "S") {
        alert("Navigating to Store... (Simulated)");
      } else if (key === "P" || event.key === "Enter") {
        event.preventDefault();
        onEnterApp();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onEnterApp]);

  // ==================== TERMINAL COPY ACTION ====================
  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(codeString);
      setCopied(true);

      gsap.fromTo(
        "#icon-check",
        { scale: 0.4, rotate: -20 },
        { scale: 1, rotate: 0, ease: "back.out(2.5)", duration: 0.4 }
      );

      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Clipboard failure", err);
    }
  };

  // ==================== NEWSLETTER INPUT FOCUS GLOW ====================
  const handleFocus = () => {
    gsap.to(".charge-glow-element", { opacity: 1, duration: 0.4, ease: "power2.out" });
  };

  const handleBlur = () => {
    gsap.to(".charge-glow-element", { opacity: 0, duration: 0.3, ease: "power2.in" });
  };

  return (
    <div className="relative bg-transparent font-sans selection:bg-indigo-100 min-h-screen">
      {/* NEURAL BACKGROUND */}
      <NeuralBackground />

      {/* SECTION A: FIXED SHORTCUT NAVIGATION */}
      <nav className="fixed top-0 left-0 w-full h-20 flex items-center justify-between px-6 md:px-12 z-50 pointer-events-auto bg-white/40 border-b border-slate-200/30 backdrop-blur-md">
        <div className="flex items-center gap-2 font-black text-slate-900 text-lg tracking-tighter cursor-pointer">
          <div className="w-6 h-6 bg-gradient-to-tr from-indigo-600 to-violet-500 rounded-md flex items-center justify-center shadow-md shadow-indigo-500/10">
            <Sparkles className="w-3.5 h-3.5 text-white" />
          </div>
          <span>Talent<span className="text-indigo-600">Graph</span></span>
        </div>
        <div className="flex items-center gap-4 md:gap-6 font-mono text-[10px] md:text-xs text-slate-400">
          <a 
            href="https://github.com/alankolett/TalentGraph" 
            target="_blank"
            onMouseEnter={handleLinkEnter} 
            onMouseLeave={handleLinkLeave}
            className="nav-link text-slate-500 hover:text-slate-900 transition-colors"
          >
            <span className="bracket inline-block transition-transform duration-200 font-bold">[</span>G<span className="bracket inline-block transition-transform duration-200 font-bold">]</span> GITHUB
          </a>
          <a 
            href="https://github.com/alankolett/TalentGraph#readme" 
            target="_blank"
            onMouseEnter={handleLinkEnter} 
            onMouseLeave={handleLinkLeave}
            className="nav-link text-slate-500 hover:text-slate-900 transition-colors"
          >
            <span className="bracket inline-block transition-transform duration-200 font-bold">[</span>D<span className="bracket inline-block transition-transform duration-200 font-bold">]</span> DOCS
          </a>
          <button 
            onClick={toggleTheme}
            className="p-1.5 rounded-lg bg-white/40 border border-slate-200/30 hover:bg-white/60 dark:bg-slate-800/40 dark:border-slate-700/30 dark:hover:bg-slate-800/60 text-slate-500 dark:text-slate-400 transition cursor-pointer shadow-sm"
            aria-label="Toggle theme"
          >
            {theme === "light" ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
          </button>
          <button 
            onClick={onEnterApp}
            onMouseEnter={handleLinkEnter} 
            onMouseLeave={handleLinkLeave}
            className="nav-link text-indigo-600 hover:text-indigo-800 transition-colors font-bold"
          >
            <span className="bracket inline-block transition-transform duration-200 font-bold">[</span>P<span className="bracket inline-block transition-transform duration-200 font-bold">]</span> PORTAL
          </button>
        </div>
      </nav>

      {/* SCROLLABLE INTERACTIVE VIEW CONTENT */}
      <main className="relative z-20 pt-32 px-4 md:px-8 max-w-6xl mx-auto space-y-36 pb-36">
        
        {/* SECTION B: THE DESTINATION HERO CARD */}
        <section className="min-h-[85vh] flex flex-col lg:flex-row items-center justify-center gap-12 lg:gap-20 pt-10">
          <div className="flex-1 space-y-6 text-center lg:text-left z-10">
            <span className="text-[11px] font-bold tracking-[0.25em] text-slate-400 uppercase block font-mono">
              {"// Neural Recruiter Suite"}
            </span>
            <div className="hero-wordmark overflow-hidden">
              <h1 className="text-5xl md:text-7xl lg:text-8xl font-black text-slate-900 dark:text-white tracking-tighter leading-none font-heading flex flex-nowrap whitespace-nowrap justify-center lg:justify-start">
                {"TalentGraph".split('').map((char, index) => (
                  <motion.span 
                    key={index} 
                    initial={{ y: 100, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ ease: [0.16, 1, 0.3, 1], duration: 1, delay: index * 0.04 }}
                    className="inline-block"
                  >
                    {char}
                  </motion.span>
                ))}
              </h1>
            </div>
            <motion.p 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1, delay: 0.6 }}
              className="text-slate-500 dark:text-slate-400 text-base md:text-lg max-w-xl mx-auto lg:mx-0 leading-relaxed font-sans"
            >
              Synthesize resume semantic distances, commit velocities, and cross-functional skill ontologies directly on the GPU canvas.
            </motion.p>

            <motion.div 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.8 }}
              className="pt-4 flex justify-center lg:justify-start"
            >
              <button 
                ref={magneticRef}
                onClick={onEnterApp}
                className="magnetic-cta relative bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm px-8 py-4 rounded-xl shadow-luxe transition-all duration-300 active:scale-95 flex items-center gap-2 group cursor-pointer"
              >
                <span>Launch Recruiter Portal</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </motion.div>
          </div>
          
          <div className="flex-1 w-full z-10">
             <LiveRankingStack />
          </div>
        </section>

        <StatRow />

        {/* TALENTGRAPH FEATURE GRID */}
        <FeatureScrollRail />

        {/* SECTION C: INTERACTIVE LIVE-CODE FEATURE CARD */}
        <section>
          <div className="bento-glass-card p-6 md:p-8 grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
            <div className="flex flex-col justify-center space-y-4">
              <span className="text-xs font-mono text-indigo-600 tracking-widest uppercase block">{"// Declarative Scoring Code"}</span>
              <h3 className="text-2xl md:text-3xl font-black text-slate-900 font-heading">Interactive Scoring Pipeline</h3>
              <p className="text-slate-500 text-xs md:text-sm leading-relaxed">
                Tune rank operations dynamically using the sliding configuration weights. Read, verify, and copy candidate evaluations vectors directly to workspace environments.
              </p>
            </div>
            
            <div className="code-terminal bg-slate-900 rounded-2xl p-5 md:p-6 font-mono text-[11px] text-slate-300 relative border border-slate-800 shadow-inner flex flex-col justify-between min-h-[260px] overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-full blur-2xl" />
              <div className="flex items-center gap-2 mb-4 border-b border-slate-800 pb-3">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500/50"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500/50"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/50"></span>
                <span className="text-slate-500 ml-2 text-[10px]">scoring-pipeline.ts</span>
              </div>
              
              <CodeRevealBlock />

              <div className="flex justify-end pt-4">
                <button 
                  onClick={handleCopyCode}
                  className="flex items-center gap-1.5 bg-white/10 hover:bg-white/15 text-white px-3.5 py-2 rounded-lg transition-all border border-white/5 active:scale-95 text-[10px] font-sans font-semibold cursor-pointer"
                  aria-label="Copy code block"
                >
                  {copied ? (
                    <>
                      <Check id="icon-check" className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy to Clipboard</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* SECTION D: NEWSLETTER & ENTERPRISE SIGN-UP */}
        <section>
          <div className="bento-glass-card p-8 md:p-12 flex flex-col items-center text-center relative overflow-visible bg-white/50">
            {/* Soft Focus Glow Element */}
            <div className="charge-glow-element absolute inset-0 rounded-[24px] opacity-0 pointer-events-none transition-opacity duration-500" style={{ boxShadow: "0 0 50px 5px rgba(79, 70, 229, 0.08), inset 0 0 25px 2px rgba(79, 70, 229, 0.04)" }} />

            <span className="text-[10px] font-mono text-slate-400 tracking-widest uppercase mb-3 font-semibold">Subscribe to engineering updates</span>
            <h3 className="text-3xl md:text-4xl font-black text-slate-900 tracking-tight mb-4 font-heading">Stay in the Vector Loop</h3>
            <p className="text-slate-500 text-xs md:text-sm max-w-sm mb-8 leading-relaxed">
              Receive updates on skill ontology updates, custom reranker models, and pipeline performance benchmarks.
            </p>

            <form 
              onSubmit={(e) => {
                e.preventDefault();
                alert(`Successfully subscribed: ${email}`);
                setEmail("");
              }}
              className="w-full max-w-md relative flex items-center bg-white border border-slate-200 rounded-xl p-1 shadow-sm focus-within:border-indigo-500/50 transition-colors"
            >
              <input 
                type="email" 
                placeholder="Enter your email address" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onFocus={handleFocus}
                onBlur={handleBlur}
                className="newsletter-input w-full bg-transparent border-none outline-none text-slate-800 px-4 font-sans text-xs placeholder-slate-400" 
                required 
              />
              <button 
                type="submit" 
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-[10px] md:text-xs px-5 py-2.5 rounded-lg transition-colors whitespace-nowrap cursor-pointer shadow-sm"
              >
                Subscribe
              </button>
            </form>
          </div>
        </section>

        {/* PORTAL ENTRY LEADERBOARD CARD (Final CTA Section) */}
        <section>
          <div className="bento-glass-card p-6 md:p-8 space-y-6 relative overflow-hidden bg-white/60">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/50 pb-4">
              <div>
                <h4 className="text-base font-bold text-slate-900 font-heading">Live shortlists alignment</h4>
                <p className="text-[10px] text-slate-400 font-mono">STABLE PORTAL INTERFACE VERIFIED</p>
              </div>
              <div className="flex items-center gap-1 text-[10px] font-mono font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 px-2.5 py-0.5 rounded-full shrink-0">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                API ONLINE
              </div>
            </div>

            <div className="space-y-3 font-mono text-[11px]">
              {[
                { rank: "01", name: "Elena Rostova", score: "98.4%", role: "Match Confirmed", details: "FastAPI + Qdrant vectors match" },
                { rank: "02", name: "Marcus Vance", score: "94.1%", role: "High Potential", details: "Python expertise, Qdrant gap" },
                { rank: "03", name: "Siddharth Nair", score: "89.7%", role: "In Line", details: "Backend developer" }
              ].map((cand, i) => (
                <div key={i} className="p-3 bg-white/40 border border-slate-200/40 rounded-xl flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="text-slate-400 font-black">{cand.rank}</span>
                    <div>
                      <span className="font-bold text-slate-800">{cand.name}</span>
                      <span className="text-slate-400 text-[10px] block font-sans">{cand.details}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] bg-slate-100 px-1.5 py-0.5 border border-slate-200 text-slate-500 rounded font-sans">{cand.role}</span>
                    <span className="text-indigo-600 bg-indigo-50 border border-indigo-100 font-bold px-2 py-0.5 rounded">{cand.score}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-center pt-2">
              <button 
                onClick={onEnterApp}
                className="bg-slate-900 hover:bg-slate-800 active:scale-95 text-white font-bold text-xs py-3.5 px-8 rounded-xl shadow-md flex items-center gap-2 group transition-all cursor-pointer"
              >
                <span>ACTIVATE TALENT CORE</span>
                <Zap className="w-4 h-4 text-amber-400 fill-amber-400 group-hover:scale-110 transition-transform" />
              </button>
            </div>
          </div>
        </section>

      </main>

      {/* FIXED FOOTER SYSTEM TICKER MARQUEE */}
      <footer className="fixed bottom-0 left-0 right-0 p-2.5 bg-white/80 border-t border-slate-200/80 backdrop-blur-md z-50 overflow-hidden font-mono text-[10px] text-slate-400">
        <div className="flex items-center gap-4 max-w-6xl mx-auto">
          <span className="text-indigo-600 font-bold flex items-center gap-1 shrink-0">
            <Terminal className="w-3.5 h-3.5" /> SYSTEM_LOGS:
          </span>
          <div className="w-full overflow-hidden whitespace-nowrap relative">
            <div className="inline-block animate-marquee-scroll space-x-8 text-slate-500">
              <span>[SYSTEM]: Initializing light-mode Crystalline Graph workspace...</span>
              <span className="ml-8">[API]: Connected successfully to localhost:8000 (SQLite)...</span>
              <span className="ml-8">[STABLE]: Frame ticks synced at 60Hz...</span>
              <span className="ml-8">[VECTORS]: Candidate evaluation matrices computed accurately...</span>
              {/* Duplicate for loop */}
              <span className="ml-8">[SYSTEM]: Initializing light-mode Crystalline Graph workspace...</span>
              <span className="ml-8">[API]: Connected successfully to localhost:8000 (SQLite)...</span>
              <span className="ml-8">[STABLE]: Frame ticks synced at 60Hz...</span>
              <span className="ml-8">[VECTORS]: Candidate evaluation matrices computed accurately...</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
