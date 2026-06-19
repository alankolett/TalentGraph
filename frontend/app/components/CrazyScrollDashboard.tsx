"use client";

import React, { useRef } from "react";
import {
  motion,
  useScroll,
  useTransform,
  useSpring,
} from "framer-motion";
import {
  Cpu,
  Terminal,
  Shield,
  Layers,
  Zap,
  CheckCircle,
  FileText,
} from "lucide-react";

interface CrazyScrollDashboardProps {
  onEnterApp: () => void;
}

export default function CrazyScrollDashboard({ onEnterApp }: CrazyScrollDashboardProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // 1. Capture global scroll progress across the entire cinematic journey
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  // Smooth out the scroll raw values to ensure fluid 120fps physics
  const smoothProgress = useSpring(scrollYProgress, {
    damping: 25,
    stiffness: 120,
    mass: 0.2,
  });

  // PILLAR 1: HERO TRANSFORMATIONS (Scroll-Linked)
  const heroScale = useTransform(smoothProgress, [0, 0.2], [1, 0.4]);
  const heroOpacity = useTransform(smoothProgress, [0, 0.15], [1, 0]);
  const heroBlur = useTransform(
    smoothProgress,
    [0, 0.12],
    ["blur(0px)", "blur(20px)"]
  );
  const watermarkScale = useTransform(smoothProgress, [0, 0.4], [1, 2.5]);
  const watermarkOpacity = useTransform(
    smoothProgress,
    [0, 0.2, 0.5],
    [0.05, 0.15, 0.02]
  );

  // PILLAR 2: THE 3D TUNNEL RESUME INGESTION (Sticky Storytelling)
  const resume1X = useTransform(smoothProgress, [0.15, 0.35], [-600, 0]);
  const resume1Rot = useTransform(smoothProgress, [0.15, 0.35], [-45, 0]);
  const resume1Z = useTransform(smoothProgress, [0.3, 0.45], [0, 400]);
  const resume1Opacity = useTransform(
    smoothProgress,
    [0.15, 0.2, 0.4, 0.45],
    [0, 1, 1, 0]
  );

  const resume2X = useTransform(smoothProgress, [0.25, 0.45], [600, 0]);
  const resume2Rot = useTransform(smoothProgress, [0.25, 0.45], [45, 0]);
  const resume2Z = useTransform(smoothProgress, [0.4, 0.55], [0, 400]);
  const resume2Opacity = useTransform(
    smoothProgress,
    [0.25, 0.3, 0.5, 0.55],
    [0, 1, 1, 0]
  );

  // PILLAR 3: FEATURE MATRIX FOLD-OUT
  const matrixRotateX = useTransform(smoothProgress, [0.5, 0.7], [60, 0]);
  const matrixScale = useTransform(smoothProgress, [0.5, 0.7], [0.8, 1]);
  const matrixOpacity = useTransform(smoothProgress, [0.45, 0.6], [0, 1]);

  // PILLAR 4: HOLOGRAPHIC LEADERBOARD REVEAL
  const boardY = useTransform(smoothProgress, [0.7, 0.9], [200, 0]);
  const boardOpacity = useTransform(smoothProgress, [0.7, 0.85], [0, 1]);

  return (
    <div
      ref={containerRef}
      className="relative bg-[#030307] text-white font-sans selection:bg-purple-500/30"
    >
      {/* PERSISTENT CINEMATIC BACKGROUND */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        {/* Dynamic Dark-mode Wormhole Mesh */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(26,15,56,0.3)_0%,transparent_70%)] animate-pulse-slow" />
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-purple-500/20 to-transparent" />

        {/* Animated grid lines for depth */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: `linear-gradient(rgba(139,92,246,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(139,92,246,0.3) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }} />

        {/* Massive Dynamic Watermark Title */}
        <motion.h1
          style={{ scale: watermarkScale, opacity: watermarkOpacity }}
          className="absolute inset-0 flex items-center justify-center font-black text-[14vw] text-purple-500 tracking-tighter select-none will-change-transform"
        >
          TALENTGRAPH
        </motion.h1>
      </div>

      {/* ==================== SECTION 1: THE HERO LANDING (Height: 100vh) ==================== */}
      <section className="relative h-screen flex flex-col items-center justify-center z-10 px-4 text-center sticky top-0 overflow-hidden">
        <motion.div
          style={{
            scale: heroScale,
            opacity: heroOpacity,
            filter: heroBlur,
          }}
          className="will-change-transform space-y-6 max-w-4xl"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/30 backdrop-blur-md text-xs font-bold tracking-widest text-purple-300 uppercase animate-bounce">
            <Zap className="w-3 h-3 text-amber-400 fill-amber-400" /> Run India
            Hackathon Edition
          </div>
          <h1 className="text-7xl md:text-9xl font-black tracking-tight">
            <span className="bg-clip-text text-transparent bg-gradient-to-b from-white via-neutral-200 to-neutral-500">
              Talent
            </span>
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-400">
              Graph
            </span>
          </h1>
          <p className="text-neutral-400 text-lg md:text-2xl max-w-2xl mx-auto font-light leading-relaxed">
            The most powerful neural ranker deployed to contextualize
            multi-modal talent telemetry.
          </p>
          <div className="pt-6 flex flex-col items-center gap-2">
            <div className="w-12 h-20 border-2 border-neutral-700 rounded-full p-2 flex justify-center">
              <motion.div
                animate={{ y: [0, 24, 0] }}
                transition={{
                  repeat: Infinity,
                  duration: 1.5,
                  ease: "easeInOut",
                }}
                className="w-2 h-4 bg-purple-500 rounded-full"
              />
            </div>
            <span className="text-xs text-neutral-500 uppercase tracking-widest font-mono">
              Scroll to Ingest
            </span>
          </div>
        </motion.div>
      </section>

      {/* ==================== SECTION 2: 3D RESUME INGESTION TUNNEL (Height: 150vh) ==================== */}
      <section className="relative h-[150vh] z-10">
        <div className="sticky top-0 h-screen w-full flex flex-col items-center justify-center overflow-hidden perspective-1200">
          <div className="absolute top-24 font-mono text-xs text-purple-400 tracking-wider flex items-center gap-2 px-4 py-2 border border-purple-500/20 bg-purple-950/20 rounded-lg backdrop-blur-sm">
            <Terminal className="w-4 h-4 animate-pulse" /> ENGINE: PARSING
            VECTORS REAL-TIME...
          </div>

          <div
            className="relative w-full max-w-2xl h-[450px] flex items-center justify-center"
            style={{ transformStyle: "preserve-3d" }}
          >
            {/* INCOMING RESUME LAYER 1 */}
            <motion.div
              style={{
                x: resume1X,
                rotateY: resume1Rot,
                z: resume1Z,
                opacity: resume1Opacity,
                transformStyle: "preserve-3d",
              }}
              className="absolute w-[320px] h-[420px] bg-neutral-900/80 border-2 border-purple-500/40 rounded-2xl shadow-[0_0_50px_rgba(168,85,247,0.2)] p-6 backdrop-blur-xl flex flex-col justify-between"
            >
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b border-neutral-800 pb-3">
                  <FileText className="text-purple-400 w-8 h-8" />
                  <span className="font-mono text-[10px] text-green-400 bg-green-950/50 px-2 py-0.5 rounded border border-green-500/30">
                    VALID_METADATA
                  </span>
                </div>
                <div className="space-y-2 font-mono">
                  <div className="text-xs text-neutral-400">#RESUME-88219</div>
                  <div className="text-base font-bold text-white tracking-wide">
                    Aravind Sharma
                  </div>
                  <div className="text-xs text-purple-300">
                    Distributed Architect
                  </div>
                </div>
                <div className="space-y-1.5 pt-2">
                  <div className="h-1.5 w-full bg-neutral-800 rounded-full overflow-hidden">
                    <div className="h-full w-[92%] bg-purple-500" />
                  </div>
                  <div className="flex justify-between text-[10px] font-mono text-neutral-400">
                    <span>TensorFlow/Go</span>
                    <span>92%</span>
                  </div>
                </div>
              </div>
              <div className="bg-purple-950/30 border border-purple-500/20 rounded-lg p-2.5 font-mono text-[11px] text-purple-300">
                [Ontology Mapping]: Linked &apos;Golang&apos; directly to target system
                scale variables.
              </div>
            </motion.div>

            {/* INCOMING RESUME LAYER 2 */}
            <motion.div
              style={{
                x: resume2X,
                rotateY: resume2Rot,
                z: resume2Z,
                opacity: resume2Opacity,
                transformStyle: "preserve-3d",
              }}
              className="absolute w-[320px] h-[420px] bg-neutral-900/80 border-2 border-cyan-500/40 rounded-2xl shadow-[0_0_50px_rgba(6,182,212,0.2)] p-6 backdrop-blur-xl flex flex-col justify-between"
            >
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b border-neutral-800 pb-3">
                  <FileText className="text-cyan-400 w-8 h-8" />
                  <span className="font-mono text-[10px] text-amber-400 bg-amber-950/50 px-2 py-0.5 rounded border border-amber-500/30">
                    PARSING_SKILLS
                  </span>
                </div>
                <div className="space-y-2 font-mono">
                  <div className="text-xs text-neutral-400">#RESUME-77102</div>
                  <div className="text-base font-bold text-white tracking-wide">
                    Priya Patel
                  </div>
                  <div className="text-xs text-cyan-300">
                    LLM Infrastructure Engineer
                  </div>
                </div>
                <div className="space-y-1.5 pt-2">
                  <div className="h-1.5 w-full bg-neutral-800 rounded-full overflow-hidden">
                    <div className="h-full w-[97%] bg-cyan-500" />
                  </div>
                  <div className="flex justify-between text-[10px] font-mono text-neutral-400">
                    <span>PyTorch/CUDA</span>
                    <span>97%</span>
                  </div>
                </div>
              </div>
              <div className="bg-cyan-950/30 border border-cyan-500/20 rounded-lg p-2.5 font-mono text-[11px] text-cyan-300">
                [Semantic Distance]: Verified 0.04 cosine variance to core ML
                model pipeline.
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ==================== SECTION 3: FEATURE MATRIX FOLD-OUT ==================== */}
      <section className="relative min-h-screen z-10 max-w-7xl mx-auto px-6 py-24 flex flex-col justify-center">
        <motion.div
          style={{
            rotateX: matrixRotateX,
            scale: matrixScale,
            opacity: matrixOpacity,
            transformStyle: "preserve-3d",
          }}
          className="will-change-transform perspective-1000 space-y-12"
        >
          <div className="space-y-4">
            <h2 className="text-4xl md:text-5xl font-black tracking-tight">
              Algorithmic Stack Subsystems
            </h2>
            <p className="text-neutral-400 text-base max-w-xl">
              Four processing paradigms running concurrently on ingestion
              sequences.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              {
                title: "Knowledge Graph",
                icon: <Layers className="w-6 h-6" />,
                col: "from-purple-500/20",
                text: "Maps cross-functional engineering ontologies smoothly.",
              },
              {
                title: "Hybrid Retrieval",
                icon: <Cpu className="w-6 h-6" />,
                col: "from-cyan-500/20",
                text: "Blends fast lexical keywords alongside dense vectors.",
              },
              {
                title: "Behavioral Signals",
                icon: <Zap className="w-6 h-6" />,
                col: "from-amber-500/20",
                text: "Extracts commit velocities, contribution density & cadence.",
              },
              {
                title: "Explainability",
                icon: <Shield className="w-6 h-6" />,
                col: "from-emerald-500/20",
                text: "Generates clear, transparent reasons for match scoring.",
              },
            ].map((card, i) => (
              <div
                key={i}
                className="group relative p-6 rounded-2xl bg-gradient-to-b from-neutral-900 to-neutral-950 border border-neutral-800 hover:border-neutral-700 transition-all duration-300 shadow-2xl flex flex-col justify-between h-64 overflow-hidden"
              >
                <div
                  className={`absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b ${card.col} to-transparent opacity-30 group-hover:opacity-60 transition-opacity`}
                />
                <div className="relative z-10 text-neutral-300 group-hover:text-white transition-colors">
                  {card.icon}
                </div>
                <div className="relative z-10 space-y-2">
                  <h3 className="text-lg font-bold text-white tracking-wide">
                    {card.title}
                  </h3>
                  <p className="text-xs text-neutral-400 leading-relaxed">
                    {card.text}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* ==================== SECTION 4: HOLOGRAPHIC LEADERBOARD REVEAL ==================== */}
      <section className="relative min-h-screen z-10 max-w-4xl mx-auto px-6 py-24 flex flex-col justify-center">
        <motion.div
          style={{ y: boardY, opacity: boardOpacity }}
          className="bg-neutral-900/60 border border-neutral-800 rounded-3xl p-8 backdrop-blur-2xl shadow-[0_0_80px_rgba(0,0,0,0.8)] space-y-8 relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-purple-500 via-cyan-500 to-emerald-500" />

          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-black uppercase tracking-wider text-white">
                Live Leaderboard Array
              </h2>
              <p className="text-xs text-neutral-500 font-mono">
                INDEX_SEQUENCE: RUN_INDIA_HACKATHON_OUTPUT
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs font-mono px-3 py-1 bg-green-500/10 border border-green-500/30 text-green-400 rounded-full animate-pulse">
              <CheckCircle className="w-3.5 h-3.5" /> STACK ACTIVE
            </div>
          </div>

          <div className="space-y-3 font-mono">
            {[
              {
                rank: "01",
                name: "Priya Patel",
                match: "97.82%",
                role: "LLM Systems Specialist",
                tags: ["PyTorch", "CUDA", "Trident"],
              },
              {
                rank: "02",
                name: "Aravind Sharma",
                match: "92.45%",
                role: "Distributed Architecture Architect",
                tags: ["Go", "Kafka", "gRPC"],
              },
              {
                rank: "03",
                name: "Kabir Mehta",
                match: "89.12%",
                role: "MLOps Platform Architect",
                tags: ["Docker", "AWS", "Ray"],
              },
            ].map((candidate, i) => (
              <div
                key={i}
                className="p-4 rounded-xl border border-neutral-800/80 bg-neutral-950/40 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:border-purple-500/40 hover:bg-purple-950/10 transition-all duration-300"
              >
                <div className="flex items-center gap-4">
                  <span className="text-lg font-black text-neutral-600">
                    {candidate.rank}
                  </span>
                  <div>
                    <div className="text-sm font-bold text-white">
                      {candidate.name}
                    </div>
                    <div className="text-xs text-neutral-400">
                      {candidate.role}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 self-end md:self-auto">
                  <div className="flex gap-1">
                    {candidate.tags.map((t, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] px-2 py-0.5 rounded bg-neutral-900 border border-neutral-800 text-neutral-400"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                  <div className="px-3 py-1 text-sm rounded bg-purple-500/20 text-purple-300 font-black border border-purple-500/30 shadow-[0_0_15px_rgba(147,51,234,0.2)]">
                    {candidate.match}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* CTA to enter the app */}
          <div className="flex justify-center pt-4">
            <button
              onClick={onEnterApp}
              className="group relative px-10 py-4 text-lg font-bold bg-purple-700/30 border border-purple-500 rounded-full shadow-[0_0_20px_rgba(168,85,247,0.5)] transition-all duration-300 hover:shadow-[0_0_35px_rgba(168,85,247,0.8)] hover:bg-purple-700/50 cursor-pointer"
            >
              <span className="relative z-10 flex items-center gap-2">
                ACTIVATE TALENT CORE
                <Zap className="w-5 h-5 text-amber-400 fill-amber-400 group-hover:animate-pulse" />
              </span>
            </button>
          </div>
        </motion.div>
      </section>

      {/* Spacer to allow final scroll breathing room */}
      <div className="h-[20vh]" />

      {/* ==================== GLOBAL SYSTEM TICKER MARQUEE ==================== */}
      <footer className="fixed bottom-0 left-0 right-0 p-2.5 bg-neutral-950/80 border-t border-neutral-900 backdrop-blur-md z-50 overflow-hidden">
        <div className="font-mono text-xs text-neutral-400 flex items-center gap-4 max-w-7xl mx-auto">
          <span className="text-purple-400 font-bold flex items-center gap-1 shrink-0">
            <Terminal className="w-3.5 h-3.5" /> CONSOLE_LOG:
          </span>
          <div className="w-full overflow-hidden whitespace-nowrap relative">
            <div className="inline-block animate-marquee-scroll space-x-8 text-neutral-500">
              <span>
                [SYSTEM]: Synthesizing Indian Engineering Repository Data...
              </span>
              <span className="ml-8">
                [VECTOR]: Matrix transformations finalized over 14,000
                schemas...
              </span>
              <span className="ml-8">
                [SUCCESS]: Models compiled perfectly for evaluation
                presentation...
              </span>
              <span className="ml-8">
                [STABLE]: Frame loops locked safely at 120Hz...
              </span>
              {/* Duplicate for seamless loop */}
              <span className="ml-8">
                [SYSTEM]: Synthesizing Indian Engineering Repository Data...
              </span>
              <span className="ml-8">
                [VECTOR]: Matrix transformations finalized over 14,000
                schemas...
              </span>
              <span className="ml-8">
                [SUCCESS]: Models compiled perfectly for evaluation
                presentation...
              </span>
              <span className="ml-8">
                [STABLE]: Frame loops locked safely at 120Hz...
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
