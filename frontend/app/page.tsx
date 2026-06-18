"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { motion, AnimatePresence, useMotionValue, useTransform, useSpring } from "framer-motion";
import {
  LayoutDashboard,
  Users,
  Sliders,
  Play,
  Database,
  Search,
  PlusCircle,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  TrendingUp,
  Cpu,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  X,
  Layers,
  Upload,
  RefreshCw,
  ChevronDown
} from "lucide-react";

const VideoBackground = () => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    let frameId: number;

    const updateOpacity = () => {
      if (!video || video.paused) return;
      const duration = video.duration || 10;
      const currentTime = video.currentTime;

      let opacity = 1;
      if (currentTime < 0.5) {
        opacity = currentTime / 0.5;
      } else if (duration - currentTime < 0.5) {
        opacity = (duration - currentTime) / 0.5;
      }

      video.style.opacity = Math.max(0, Math.min(1, opacity)).toString();
      frameId = requestAnimationFrame(updateOpacity);
    };

    const handlePlay = () => {
      frameId = requestAnimationFrame(updateOpacity);
    };

    const handleEnded = () => {
      if (!video) return;
      video.style.opacity = "0";
      setTimeout(() => {
        video.currentTime = 0;
        video.play().catch(e => console.log("Play interrupted", e));
      }, 100);
    };

    // Try to play when video data is loaded
    const handleCanPlay = () => {
      video.play().catch(e => console.log("Autoplay blocked", e));
    };

    video.addEventListener("play", handlePlay);
    video.addEventListener("ended", handleEnded);
    video.addEventListener("canplay", handleCanPlay);

    // Also try to play immediately
    video.play().catch(() => {});

    return () => {
      cancelAnimationFrame(frameId);
      video.removeEventListener("play", handlePlay);
      video.removeEventListener("ended", handleEnded);
      video.removeEventListener("canplay", handleCanPlay);
    };
  }, []);

  return (
    <>
      <div className="absolute inset-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <video 
          ref={videoRef}
          src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_065045_c44942da-53c6-4804-b734-f9e07fc22e08.mp4"
          autoPlay 
          muted 
          playsInline
          className="absolute inset-0 w-full h-full object-cover"
          style={{ opacity: 0 }}
        />
      </div>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[984px] h-[527px] opacity-90 bg-gray-950 blur-[82px] pointer-events-none z-0" />
    </>
  );
};


// Types matching Backend Schemas
interface Job {
  job_id: string;
  title: string;
  seniority: string;
  location: string;
  must_have: string[];
  nice_to_have: string[];
  raw_text: string;
}

interface Candidate {
  id: string;
  raw_resume_text: string;
  skills_raw: string[];
  experience_years: number;
  education: string;
  location: string;
  github_url: string;
  activity_metadata: Record<string, unknown>;
}

interface FeatureVector {
  skill_overlap: number;
  kg_skill_distance: number;
  dense_similarity: number;
  bm25_score: number;
  trajectory_alignment: number;
  behavioral_score: number;
  seniority_match: number;
}

interface RankingResult {
  candidate_id: string;
  rank: number;
  final_score: number;
  tags: string[];
  narrative: string;
  matched_points: string[];
  missing_points: string[];
  features: FeatureVector;
}

// 1. Particle Canvas Background Component
const NeuralBackground = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const particles: Array<{
      x: number;
      y: number;
      vx: number;
      vy: number;
      radius: number;
    }> = [];

    const numParticles = 50;
    for (let i = 0; i < numParticles; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        radius: Math.random() * 2 + 1,
      });
    }

    let mouseX = 0;
    let mouseY = 0;
    let mouseActive = false;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
      mouseY = e.clientY - rect.top;
      mouseActive = true;
    };

    const handleMouseLeave = () => {
      mouseActive = false;
    };

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener("resize", handleResize);
    window.addEventListener("mousemove", handleMouseMove);
    canvas.addEventListener("mouseleave", handleMouseLeave);

    const draw = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = "rgba(6, 9, 19, 0.97)"; // Deep navy backdrop
      ctx.fillRect(0, 0, width, height);

      // Connect nodes
      ctx.lineWidth = 0.5;
      for (let i = 0; i < particles.length; i++) {
        const p1 = particles[i];

        p1.x += p1.vx;
        p1.y += p1.vy;

        if (p1.x < 0 || p1.x > width) p1.vx *= -1;
        if (p1.y < 0 || p1.y > height) p1.vy *= -1;

        if (mouseActive) {
          const dx = mouseX - p1.x;
          const dy = mouseY - p1.y;
          const dist = Math.hypot(dx, dy);
          if (dist < 180) {
            p1.x += (dx / dist) * 0.15;
            p1.y += (dy / dist) * 0.15;
          }
        }

        ctx.fillStyle = "rgba(129, 140, 248, 0.35)"; // Glowing indigo
        ctx.beginPath();
        ctx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2);
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
          if (dist < 120) {
            const alpha = (1 - dist / 120) * 0.15;
            ctx.strokeStyle = `rgba(139, 92, 246, ${alpha})`; // Purple lines
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      }

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
      canvas.removeEventListener("mouseleave", handleMouseLeave);
    };
  }, []);

  return <canvas ref={canvasRef} className="fixed inset-0 -z-10 pointer-events-none" />;
};

// 2. Rotating 3D Logo Component
const Rotating3DLogo = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let frameId: number;
    let angle = 0;
    const width = (canvas.width = 36);
    const height = (canvas.height = 36);

    const draw = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.save();
      ctx.translate(width / 2, height / 2);

      // Draw orbit rings
      ctx.strokeStyle = "rgba(99, 102, 241, 0.4)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.ellipse(0, 0, 15, 5, Math.PI / 4 + angle * 0.2, 0, Math.PI * 2);
      ctx.stroke();

      ctx.beginPath();
      ctx.ellipse(0, 0, 15, 5, -Math.PI / 4 - angle * 0.2, 0, Math.PI * 2);
      ctx.stroke();

      // Draw center rotating sphere
      const gradient = ctx.createRadialGradient(-2, -2, 1, 0, 0, 8);
      gradient.addColorStop(0, "#c084fc"); // Purple-400
      gradient.addColorStop(1, "#6366f1"); // Indigo-500
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(0, 0, 7.5, 0, Math.PI * 2);
      ctx.fill();

      // Floating electron nodes
      const x1 = 15 * Math.cos(angle);
      const y1 = 5 * Math.sin(angle);
      const cosA = Math.cos(Math.PI / 4 + angle * 0.2);
      const sinA = Math.sin(Math.PI / 4 + angle * 0.2);
      const rx1 = x1 * cosA - y1 * sinA;
      const ry1 = x1 * sinA + y1 * cosA;

      ctx.fillStyle = "#ffffff";
      ctx.shadowColor = "#a855f7";
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.arc(rx1, ry1, 2, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
      angle += 0.04;
      frameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(frameId);
    };
  }, []);

  return (
    <div className="w-9 h-9 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center shadow-[0_0_15px_rgba(99,102,241,0.2)]">
      <canvas ref={canvasRef} width="36" height="36" />
    </div>
  );
};

// 3. Custom SVG Radar Chart Component
interface RadarChartProps {
  features: FeatureVector;
}

const RadarChart: React.FC<RadarChartProps> = ({ features }) => {
  const width = 300;
  const height = 300;
  const cx = width / 2;
  const cy = height / 2;
  const radius = 90;

  const axes = [
    { name: "Skill Overlap", key: "skill_overlap" as keyof FeatureVector, fn: (v: number) => v },
    { name: "KG Closeness", key: "kg_skill_distance" as keyof FeatureVector, fn: (v: number) => Math.max(0, 1 - v) },
    { name: "Dense Similarity", key: "dense_similarity" as keyof FeatureVector, fn: (v: number) => v },
    { name: "Keyword (BM25)", key: "bm25_score" as keyof FeatureVector, fn: (v: number) => Math.min(1, v / 15) },
    { name: "Trajectory Align", key: "trajectory_alignment" as keyof FeatureVector, fn: (v: number) => v },
    { name: "Behavioral", key: "behavioral_score" as keyof FeatureVector, fn: (v: number) => v },
    { name: "Seniority Match", key: "seniority_match" as keyof FeatureVector, fn: (v: number) => v }
  ];

  // Draw concentric webs
  const gridCircles = [0.25, 0.5, 0.75, 1];
  const gridPolygons = gridCircles.map((scale) => {
    return axes.map((_, i) => {
      const angle = (i * 2 * Math.PI) / axes.length - Math.PI / 2;
      const x = cx + radius * scale * Math.cos(angle);
      const y = cy + radius * scale * Math.sin(angle);
      return `${x},${y}`;
    }).join(" ");
  });

  // Calculate points for the candidate's scores
  const candidatePoints = axes.map((axis, i) => {
    const rawValue = features[axis.key] ?? 0;
    const value = axis.fn(rawValue);
    const angle = (i * 2 * Math.PI) / axes.length - Math.PI / 2;
    const x = cx + radius * value * Math.cos(angle);
    const y = cy + radius * value * Math.sin(angle);
    return { x, y, name: axis.name, val: Math.round(value * 100) };
  });

  const candidatePolygon = candidatePoints.map((p) => `${p.x},${p.y}`).join(" ");

  return (
    <div className="flex flex-col items-center justify-center bg-white/5 border border-white/10 rounded-xl p-4">
      <h4 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-2">Feature Alignment Vector</h4>
      <svg width={width} height={height} className="overflow-visible">
        {/* Grids */}
        {gridPolygons.map((points, idx) => (
          <polygon
            key={idx}
            points={points}
            fill="none"
            stroke="rgba(148, 163, 184, 0.12)"
            strokeWidth="1"
            strokeDasharray={idx < 3 ? "3,3" : "none"}
          />
        ))}

        {/* Axes lines */}
        {axes.map((_, i) => {
          const angle = (i * 2 * Math.PI) / axes.length - Math.PI / 2;
          const x = cx + radius * Math.cos(angle);
          const y = cy + radius * Math.sin(angle);
          return (
            <line
              key={i}
              x1={cx}
              y1={cy}
              x2={x}
              y2={y}
              stroke="rgba(148, 163, 184, 0.15)"
              strokeWidth="1"
            />
          );
        })}

        {/* Candidate Polygon */}
        <polygon
          points={candidatePolygon}
          fill="rgba(99, 102, 241, 0.2)"
          stroke="rgba(129, 140, 248, 0.8)"
          strokeWidth="2"
          className="transition-all duration-500"
        />

        {/* Interactive Points */}
        {candidatePoints.map((p, i) => (
          <g key={i}>
            <circle
              cx={p.x}
              cy={p.y}
              r="4"
              fill="rgb(168, 85, 247)"
              stroke="white"
              strokeWidth="1"
            />
            {/* Axis Label */}
            {(() => {
              const angle = (i * 2 * Math.PI) / axes.length - Math.PI / 2;
              const lx = cx + (radius + 20) * Math.cos(angle);
              const ly = cy + (radius + 12) * Math.sin(angle);
              let textAnchor: "middle" | "start" | "end" = "middle";
              if (Math.cos(angle) > 0.1) textAnchor = "start";
              if (Math.cos(angle) < -0.1) textAnchor = "end";
              return (
                <text
                  x={lx}
                  y={ly}
                  fill="rgb(148, 163, 184)"
                  fontSize="8.5"
                  fontWeight="600"
                  textAnchor={textAnchor}
                  alignmentBaseline="middle"
                  className="font-sans"
                >
                  {p.name} ({p.val}%)
                </text>
              );
            })()}
          </g>
        ))}
      </svg>
    </div>
  );
};

// 4. Interactive 3D Confetti Particle Splash
const ConfettiGenerator = ({ active }: { active: boolean }) => {
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; vx: number; vy: number; color: string; size: number }>>([]);

  useEffect(() => {
    if (!active) {
      setParticles([]);
      return;
    }

    const newParticles = [];
    const colors = ["#6366f1", "#8b5cf6", "#ec4899", "#10b981", "#f59e0b", "#3b82f6"];
    for (let i = 0; i < 50; i++) {
      newParticles.push({
        id: i,
        x: window.innerWidth / 2 + (Math.random() - 0.5) * 150,
        y: window.innerHeight / 2 - 100,
        vx: (Math.random() - 0.5) * 12,
        vy: (Math.random() - 0.8) * 12 - 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        size: Math.random() * 5 + 4,
      });
    }
    setParticles(newParticles);

    let frameId: number;
    const update = () => {
      setParticles((prev) =>
        prev
          .map((p) => ({
            ...p,
            x: p.x + p.vx,
            y: p.y + p.vy,
            vy: p.vy + 0.35, // Gravity drift
            vx: p.vx * 0.98,
          }))
          .filter((p) => p.y < window.innerHeight && p.x > 0 && p.x < window.innerWidth)
      );
      frameId = requestAnimationFrame(update);
    };
    frameId = requestAnimationFrame(update);

    return () => cancelAnimationFrame(frameId);
  }, [active]);

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {particles.map((p) => (
        <div
          key={p.id}
          className="absolute rounded-full"
          style={{
            left: p.x,
            top: p.y,
            width: p.size,
            height: p.size,
            backgroundColor: p.color,
            boxShadow: `0 0 8px ${p.color}`,
          }}
        />
      ))}
    </div>
  );
};

// 5. Encapsulated Metric Card with 3D Tilt Hover Effects
interface MetricProps {
  title: string;
  value: string | number;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
  delay: number;
}

const AnimatedMetricCard: React.FC<MetricProps> = ({ title, value, subtitle, icon: Icon, delay }) => {
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const rotateX = useSpring(useTransform(y, [-50, 50], [8, -8]), { damping: 20, stiffness: 150 });
  const rotateY = useSpring(useTransform(x, [-50, 50], [-8, 8]), { damping: 20, stiffness: 150 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    x.set((e.clientX - rect.left - rect.width / 2) * 0.3);
    y.set((e.clientY - rect.top - rect.height / 2) * 0.3);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
      whileHover={{ scale: 1.02, rotateY: 5, rotateX: -5 }}
      className="p-5 rounded-2xl bg-white/5 border border-white/10 shadow-[0_0_20px_rgba(255,255,255,0.02)] backdrop-blur-xl flex items-center justify-between group overflow-hidden relative"
    >
      <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-indigo-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
      <div className="z-10">
        <h3 className="text-xl font-black text-white font-heading tracking-tight">{value}</h3>
        <span className="text-[10px] text-slate-400 block font-sans">{title}</span>
        <span className="text-[10px] text-slate-500 block font-sans">{subtitle}</span>
      </div>
      <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-indigo-400 group-hover:scale-110 group-hover:text-purple-400 transition-all duration-300">
        <Icon className="w-5 h-5" />
      </div>
    </motion.div>
  );
};

// 6. Holographic Candidate Card Component with Mouse Tracking 3D Tilt
interface CandidateCardProps {
  result: RankingResult;
  isSelected: boolean;
  onClick: () => void;
}

const HolographicCandidateCard: React.FC<CandidateCardProps> = ({ result, isSelected, onClick }) => {
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const rotateX = useSpring(useTransform(y, [-80, 80], [10, -10]), { damping: 20, stiffness: 150 });
  const rotateY = useSpring(useTransform(x, [-80, 80], [-10, 10]), { damping: 20, stiffness: 150 });

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    x.set((e.clientX - rect.left - rect.width / 2) * 0.3);
    y.set((e.clientY - rect.top - rect.height / 2) * 0.3);
  };

  const handleMouseLeave = () => {
    x.set(0);
    y.set(0);
  };

  const scorePct = Math.round(result.final_score * 100);

  return (
    <motion.div
      style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onClick={onClick}
      whileHover={{ scale: 1.02, boxShadow: "0 0 30px rgba(168, 85, 247, 0.25)" }}
      className={`p-4 rounded-xl border transition-all duration-300 cursor-pointer flex justify-between items-center relative overflow-hidden group ${
        isSelected
          ? "bg-gradient-to-br from-indigo-950/45 to-purple-950/35 border-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.2)]"
          : "bg-white/5 border-white/10 hover:border-indigo-500/50 hover:bg-white/10"
      }`}
    >
      <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-indigo-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
      
      <div className="flex items-center space-x-4 z-10">
        <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center font-mono font-bold text-sm text-indigo-400 border border-white/10 group-hover:border-indigo-500/50 transition-colors">
          #{result.rank}
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h4 className="text-sm font-bold text-slate-100 group-hover:text-white transition-colors">{result.candidate_id}</h4>
            {result.tags.slice(0, 2).map((t, i) => (
              <span key={i} className="text-[9px] font-semibold bg-indigo-950/40 border border-indigo-900/60 text-indigo-300 px-1.5 py-0.5 rounded">
                {t}
              </span>
            ))}
          </div>
          <div className="flex flex-wrap gap-1 mt-1">
            {result.matched_points.slice(0, 3).map((item, idx) => (
              <span key={idx} className="text-[8px] bg-white/5 text-slate-400 border border-white/10 px-1.5 py-0.5 rounded font-mono">
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-3 text-right z-10">
        <div>
          <div className="text-[9px] text-slate-500 uppercase font-bold tracking-wider leading-none">Blended</div>
          <div className="text-base font-black text-indigo-400 font-mono mt-0.5 group-hover:text-purple-400 transition-colors">{scorePct}%</div>
        </div>
        <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-indigo-400 transition-colors" />
      </div>
    </motion.div>
  );
};

// 7. Resume Highlight Pulse Renderer
const HighlightedResume = ({ text, mustHave, niceToHave }: { text: string, mustHave: string[], niceToHave: string[] }) => {
  if (!text) return <p className="text-slate-500 italic">No resume data available.</p>;
  const skills = [...mustHave, ...niceToHave];
  if (skills.length === 0) return <p className="text-slate-400 leading-relaxed font-mono whitespace-pre-wrap">{text}</p>;

  const pattern = new RegExp(`\\b(${skills.join("|")})\\b`, "gi");
  const parts = text.split(pattern);

  return (
    <p className="text-slate-400 leading-relaxed font-mono whitespace-pre-wrap text-[11px]">
      {parts.map((part, idx) => {
        const isMust = mustHave.some((s) => s.toLowerCase() === part.toLowerCase());
        const isNice = niceToHave.some((s) => s.toLowerCase() === part.toLowerCase());

        if (isMust) {
          return (
            <span key={idx} className="relative inline-block px-1 rounded bg-rose-950/40 border border-rose-900/60 text-rose-300 font-semibold animate-pulse">
              {part}
            </span>
          );
        }
        if (isNice) {
          return (
            <span key={idx} className="relative inline-block px-1 rounded bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 font-semibold animate-pulse">
              {part}
            </span>
          );
        }
        return part;
      })}
    </p>
  );
};

// 8. Auto-Drawing Timeline Journey
const CareerJourneyTimeline = ({ experienceYears, skills }: { experienceYears: number, skills: string[] }) => {
  return (
    <div className="space-y-4">
      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Professional Journey</h4>
      <div className="relative pl-6 border-l border-indigo-500/30 space-y-4">
        {/* Timeline top dot */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2 }}
          className="absolute -left-1.5 top-1.5 w-3 h-3 rounded-full bg-indigo-500 border border-slate-900 shadow-[0_0_8px_rgba(99,102,241,0.8)]"
        />
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-white">Advanced Technical Execution</span>
            <span className="text-[9px] bg-indigo-950/40 text-indigo-300 border border-indigo-900/60 px-1.5 py-0.2 rounded">Current</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
            Demonstrates specialized engineering competency in: {skills.slice(0, 3).join(", ")}.
          </p>
        </div>

        {/* Timeline bottom dot */}
        <div className="relative">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.4 }}
            className="absolute -left-[29.5px] top-1.5 w-3 h-3 rounded-full bg-purple-500 border border-slate-900"
          />
          <div>
            <div className="text-xs font-bold text-white">Industrial Experience base</div>
            <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
              Synthesizing {experienceYears || 3} years of industrial coding history and system development.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// --- HERO SECTION ---
const HeroSection = ({ onEnterApp }: { onEnterApp: () => void }) => {
  const [isLaunching, setIsLaunching] = useState(false);

  const handleLaunch = () => {
    setIsLaunching(true);
    setTimeout(() => {
      onEnterApp();
    }, 1200); // Wait 1.2s to show loading state before entering
  };

  return (
    <div className="relative min-h-screen flex flex-col overflow-visible bg-background font-sans">
      <VideoBackground />

      <div className="relative z-10 flex flex-col flex-1">


        <div className="flex-1 flex flex-col items-center justify-center text-center px-4">
          <h1 className="text-[90px] md:text-[180px] font-normal leading-[1.02] tracking-[-0.024em] font-heading whitespace-nowrap">
            <span className="text-foreground">Talent</span>
            <span className="bg-clip-text text-transparent" style={{ backgroundImage: "linear-gradient(to left, #6366f1, #a855f7, #fcd34d)" }}>Graph</span>
          </h1>
          <p className="text-hero-sub text-lg leading-8 max-w-md mt-[9px] opacity-80 font-sans">
            The most powerful AI ever deployed<br />in talent acquisition
          </p>
          <button 
            onClick={handleLaunch} 
            disabled={isLaunching}
            className="px-[29px] py-[24px] mt-[25px] rounded-full bg-white/10 hover:bg-white/20 transition border border-white/20 text-white font-medium text-lg flex items-center justify-center gap-3 w-64 shadow-[0_0_20px_rgba(99,102,241,0.2)] disabled:opacity-80 disabled:cursor-not-allowed"
          >
            {isLaunching ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                Initializing...
              </>
            ) : (
              "Click to Start"
            )}
          </button>
        </div>

        <div className="w-full max-w-6xl mx-auto pb-12 px-6 grid grid-cols-1 md:grid-cols-4 gap-6 text-left relative z-10 mt-auto">
          <div className="p-5 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition duration-300">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="text-white font-semibold mb-2">Knowledge Graph</h3>
            <p className="text-slate-400 text-sm leading-relaxed">Models skill ontologies, normalizes synonyms, and calculates distances.</p>
          </div>
          <div className="p-5 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition duration-300">
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center mb-4">
              <Search className="w-5 h-5" />
            </div>
            <h3 className="text-white font-semibold mb-2">Hybrid Retrieval</h3>
            <p className="text-slate-400 text-sm leading-relaxed">Merges dense embeddings and BM25 keywords via Reciprocal Rank Fusion.</p>
          </div>
          <div className="p-5 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition duration-300">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center mb-4">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="text-white font-semibold mb-2">Behavioral Signals</h3>
            <p className="text-slate-400 text-sm leading-relaxed">Analyzes candidate trajectory, learning velocity, and OSS contribution frequency.</p>
          </div>
          <div className="p-5 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition duration-300">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4">
              <Sparkles className="w-5 h-5" />
            </div>
            <h3 className="text-white font-semibold mb-2">Explainability Engine</h3>
            <p className="text-slate-400 text-sm leading-relaxed">Generates automated match justifications and professional recruiter narratives.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function App() {
  const [showPortal, setShowPortal] = useState(false);

  if (!showPortal) {
    return <HeroSection onEnterApp={() => setShowPortal(true)} />;
  }

  return <PortalApp />;
}

// --- MAIN PORTAL COMPONENT ---
function PortalApp() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "catalog" | "benchmarks">("dashboard");
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);
  const [healthInfo, setHealthInfo] = useState<Record<string, string> | null>(null);
  const [llmProvider, setLlmProvider] = useState<string>("ollama");

  // Data states
  const [jobs, setJobs] = useState<Job[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [activeJobId, setActiveJobId] = useState<string>("");
  const [alpha, setAlpha] = useState<number>(0.5);
  const [topN, setTopN] = useState<number>(10);

  // Ranking calculation states
  const [rankingResults, setRankingResults] = useState<RankingResult[]>([]);
  const [isRanking, setIsRanking] = useState<boolean>(false);
  const [seeding, setSeeding] = useState<boolean>(false);
  const [confetti, setConfetti] = useState<boolean>(false);

  // Catalog search/upload states
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [activeCandidate, setActiveCandidate] = useState<RankingResult | null>(null);
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);

  // New Job and Candidate form fields
  const [newJobTitle, setNewJobTitle] = useState("");
  const [newJobDesc, setNewJobDesc] = useState("");
  const [newJobMust, setNewJobMust] = useState("");
  const [newJobNice, setNewJobNice] = useState("");
  const [newJobSeniority, setNewJobSeniority] = useState("Senior");
  const [newJobLocation, setNewJobLocation] = useState("Remote");

  const [newCandId, setNewCandId] = useState("");
  const [newCandResume, setNewCandResume] = useState("");
  const [newCandSkills, setNewCandSkills] = useState("");
  const [newCandExp, setNewCandExp] = useState(3);
  const [newCandEdu, setNewCandEdu] = useState("");
  const [newCandLoc, setNewCandLoc] = useState("");
  const [newCandGit, setNewCandGit] = useState("");

  const API_BASE = "http://localhost:8000";

  // Check backend health & Load initial data
  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        setBackendHealthy(true);
        setHealthInfo(data);
      } else {
        setBackendHealthy(false);
      }
    } catch {
      setBackendHealthy(false);
    }
  };

  const fetchJobs = async () => {
    try {
      const res = await fetch(`${API_BASE}/jobs`);
      if (res.ok) {
        const data = await res.json();
        setJobs(data.jobs || []);
        if (data.jobs && data.jobs.length > 0 && !activeJobId) {
          setActiveJobId(data.jobs[0].job_id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch jobs", err);
    }
  };

  const fetchCandidates = async () => {
    try {
      const res = await fetch(`${API_BASE}/candidates`);
      if (res.ok) {
        const data = await res.json();
        setCandidates(data.candidates || []);
      }
    } catch (err) {
      console.error("Failed to fetch candidates", err);
    }
  };

  useEffect(() => {
    checkHealth();
    fetchJobs();
    fetchCandidates();
  }, []);

  const activeJob = useMemo(() => {
    return jobs.find((j) => j.job_id === activeJobId) || null;
  }, [jobs, activeJobId]);

  // Seeder for database
  const seedSampleData = async () => {
    setSeeding(true);
    try {
      const sampleJobs = [
        {
          id: "j1",
          title: "Senior Data Scientist",
          raw_description: "We are looking for a Senior Data Scientist to lead candidate recommendation analytics. The candidate must have solid experience in Python, Machine Learning, and Data Science, with exposure to Qdrant or FastAPI.",
          must_have_skills: ["Python", "Machine Learning", "Data Science"],
          nice_to_have_skills: ["Qdrant", "FastAPI"],
          seniority: "Senior",
          location: "Remote"
        },
        {
          id: "j2",
          title: "Machine Learning Engineer Lead",
          raw_description: "We need an ML Lead to design, train, and deploy large language models. Strong hands-on knowledge of PyTorch, Transformers, LLMs, and Qdrant is required. Experience with vector search indexing is a plus.",
          must_have_skills: ["Python", "PyTorch", "Transformers"],
          nice_to_have_skills: ["Qdrant", "LLMs", "Vector Databases"],
          seniority: "Lead",
          location: "San Francisco"
        },
        {
          id: "j3",
          title: "Senior React Frontend Developer",
          raw_description: "Looking for a Senior Frontend Developer to design and develop stunning Next.js interfaces. The ideal candidate has deep expertise in React, TypeScript, Next.js, and CSS styling.",
          must_have_skills: ["React", "TypeScript", "Next.js"],
          nice_to_have_skills: ["Tailwind CSS", "Framer Motion"],
          seniority: "Senior",
          location: "Remote"
        }
      ];

      for (const job of sampleJobs) {
        await fetch(`${API_BASE}/jobs`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(job)
        });
      }

      const sampleCandidates = [
        {
          id: "c1",
          raw_resume_text: "Experienced Python Developer with 6 years of experience building scalable backends using FastAPI, Qdrant, SQL, and Docker. Strong background in database design and indexing.",
          skills_raw: ["Python", "FastAPI", "Qdrant", "SQL", "Docker"],
          experience_years: 6.0,
          education: "B.S. in Computer Science",
          location: "Remote",
          github_url: "https://github.com/example-c1",
          activity_metadata: { pull_requests: 45, commits: 350, languages: { Python: 80, SQL: 20 } }
        },
        {
          id: "c2",
          raw_resume_text: "Machine Learning Specialist with 5 years of experience building deep learning models, PyTorch, Transformers, LLMs, NLP, and Qdrant. Worked on vector embeddings and index optimization.",
          skills_raw: ["Python", "PyTorch", "Transformers", "Qdrant", "LLMs", "NLP"],
          experience_years: 5.0,
          education: "M.S. in Artificial Intelligence",
          location: "San Francisco",
          github_url: "https://github.com/example-c2",
          activity_metadata: { pull_requests: 60, commits: 420, languages: { Python: 90, "C++": 10 } }
        },
        {
          id: "c3",
          raw_resume_text: "Talented Frontend Engineer with 4 years of experience specializing in React, TypeScript, Next.js, and Tailwind CSS. Passionate about UX design, component libraries, and animations.",
          skills_raw: ["React", "TypeScript", "Next.js", "Tailwind CSS", "Framer Motion"],
          experience_years: 4.0,
          education: "B.S. in Software Engineering",
          location: "Remote",
          github_url: "https://github.com/example-c3",
          activity_metadata: { pull_requests: 25, commits: 180, languages: { TypeScript: 70, CSS: 30 } }
        },
        {
          id: "c_ml_specialist",
          raw_resume_text: "Lead Machine Learning Scientist with 8 years of experience. Expert in PyTorch, transformers, LLMs, recommender systems, and deploying vector databases with Qdrant.",
          skills_raw: ["Python", "PyTorch", "Transformers", "LLMs", "Qdrant", "Recommender Systems"],
          experience_years: 8.0,
          education: "Ph.D. in Computer Science (ML focus)",
          location: "New York",
          github_url: "https://github.com/example-c-ml",
          activity_metadata: { pull_requests: 80, commits: 600, languages: { Python: 95, Rust: 5 } }
        }
      ];

      await fetch(`${API_BASE}/candidates/bulk-upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sampleCandidates)
      });

      // Reload databases
      await fetchJobs();
      await fetchCandidates();
      alert("Database seeded successfully with 3 sample jobs and 4 structured candidates!");
    } catch (err) {
      console.error("Seeding failed", err);
      alert("Seeding failed. Please check if backend is running on http://localhost:8000");
    } finally {
      setSeeding(false);
    }
  };

  // Run Ranking Pipeline
  const runRanking = async () => {
    if (!activeJobId) {
      alert("Please select or add a Job first.");
      return;
    }
    setIsRanking(true);
    setActiveCandidate(null);
    setConfetti(false);
    try {
      const res = await fetch(`${API_BASE}/rank/${activeJobId}?alpha=${alpha}&top_n=${topN}&provider=${llmProvider}`, {
        method: "POST"
      });
      if (res.ok) {
        const data = await res.json();
        setRankingResults(data.results || []);
        setConfetti(true);
        setTimeout(() => setConfetti(false), 3000);
      } else {
        const errData = await res.json();
        alert(`Error running ranking: ${errData.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error(err);
      alert("Ranking failed. Please check your backend logs.");
    } finally {
      setIsRanking(false);
    }
  };

  // Add Custom Job Form Handler
  const handleAddJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newJobTitle || !newJobDesc) {
      alert("Title and raw description are required.");
      return;
    }
    const payload = {
      id: "j_" + Date.now().toString().slice(-6),
      title: newJobTitle,
      raw_description: newJobDesc,
      must_have_skills: newJobMust.split(",").map((s) => s.trim()).filter(Boolean),
      nice_to_have_skills: newJobNice.split(",").map((s) => s.trim()).filter(Boolean),
      seniority: newJobSeniority,
      location: newJobLocation
    };

    try {
      const res = await fetch(`${API_BASE}/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setNewJobTitle("");
        setNewJobDesc("");
        setNewJobMust("");
        setNewJobNice("");
        await fetchJobs();
        setActiveJobId(payload.id);
        alert("Job added successfully!");
      }
    } catch (err) {
      alert("Failed to submit job.");
    }
  };

  // Add Custom Candidate Form Handler
  const handleAddCandidate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCandId || !newCandResume) {
      alert("ID and resume text are required.");
      return;
    }
    const payload = {
      id: newCandId,
      raw_resume_text: newCandResume,
      skills_raw: newCandSkills.split(",").map((s) => s.trim()).filter(Boolean),
      experience_years: newCandExp,
      education: newCandEdu || "N/A",
      location: newCandLoc || "Remote",
      github_url: newCandGit || "https://github.com/example",
      activity_metadata: { commits: 120, pull_requests: 15 }
    };

    try {
      const res = await fetch(`${API_BASE}/candidates/bulk-upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify([payload])
      });
      if (res.ok) {
        setNewCandId("");
        setNewCandResume("");
        setNewCandSkills("");
        setNewCandEdu("");
        setNewCandLoc("");
        setNewCandGit("");
        await fetchCandidates();
        setIsUploadOpen(false);
        alert("Candidate added successfully!");
      }
    } catch (err) {
      alert("Failed to add candidate.");
    }
  };

  // Filter Catalog candidates by search
  const filteredCandidates = useMemo(() => {
    if (!searchQuery) return candidates;
    const q = searchQuery.toLowerCase();
    return candidates.filter((c) => {
      const matchesId = c.id.toLowerCase().includes(q);
      const matchesLoc = c.location ? c.location.toLowerCase().includes(q) : false;
      const matchesSkills = c.skills_raw.some((s) => s.toLowerCase().includes(q));
      return matchesId || matchesLoc || matchesSkills;
    });
  }, [candidates, searchQuery]);

  return (
    <div className="min-h-screen text-foreground flex overflow-hidden font-sans relative bg-background">
      {/* Dynamic Confetti Celebration */}
      <ConfettiGenerator active={confetti} />

      {/* Video Background from Hero */}
      <VideoBackground />

      {/* --- SIDEBAR PANEL --- */}
      <aside className="w-80 bg-white/5 border-r border-white/10 flex flex-col justify-between shrink-0 backdrop-blur-xl z-20">
        <div>
          {/* Logo with 3D Orbit Canvas Logo */}
          <div className="p-6 border-b border-white/10 flex items-center space-x-3">
            <Rotating3DLogo />
            <div>
              <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-indigo-200 to-indigo-400 bg-clip-text text-transparent font-heading">
                TalentGraph
              </h1>
              <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
                Recruiter AI Portal
              </p>
            </div>
          </div>

          {/* Navigation Links with slide & pulse active states */}
          <nav className="p-4 space-y-1">
            <button
              onClick={() => setActiveTab("dashboard")}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 border-l-4 ${
                activeTab === "dashboard"
                  ? "bg-indigo-600/10 border-indigo-500 text-indigo-300 shadow-[0_0_15px_rgba(99,102,241,0.06)]"
                  : "border-transparent text-slate-400 hover:bg-slate-900/60 hover:text-slate-200"
              }`}
            >
              <LayoutDashboard className="w-4 h-4 text-indigo-400" />
              <span>Matching Dashboard</span>
            </button>

            <button
              onClick={() => setActiveTab("catalog")}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 border-l-4 ${
                activeTab === "catalog"
                  ? "bg-indigo-600/10 border-indigo-500 text-indigo-300 shadow-[0_0_15px_rgba(99,102,241,0.06)]"
                  : "border-transparent text-slate-400 hover:bg-slate-900/60 hover:text-slate-200"
              }`}
            >
              <Users className="w-4 h-4 text-purple-400" />
              <span>Candidates Catalog</span>
            </button>

            <button
              onClick={() => setActiveTab("benchmarks")}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 border-l-4 ${
                activeTab === "benchmarks"
                  ? "bg-indigo-600/10 border-indigo-500 text-indigo-300 shadow-[0_0_15px_rgba(99,102,241,0.06)]"
                  : "border-transparent text-slate-400 hover:bg-slate-900/60 hover:text-slate-200"
              }`}
            >
              <Layers className="w-4 h-4 text-pink-400" />
              <span>Benchmarking Harness</span>
            </button>
          </nav>
        </div>

        {/* Database Control Center (Bottom Section) */}
        <div className="p-4 border-t border-white/10 space-y-3">
          <div className="rounded-lg bg-white/5 p-3 border border-white/10">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-400">Total Catalog</span>
              <span className="text-slate-200 font-mono font-bold">{candidates.length}</span>
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">Active Job Roles</span>
              <span className="text-slate-200 font-mono font-bold">{jobs.length}</span>
            </div>
          </div>

          <button
            onClick={seedSampleData}
            disabled={seeding}
            className="w-full bg-white/5 hover:bg-white/10 text-indigo-300 hover:text-indigo-200 border border-white/10 hover:border-indigo-500/30 font-medium py-2 px-3 rounded-lg text-xs flex items-center justify-center space-x-2 transition-all duration-200 cursor-pointer"
          >
            {seeding ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Seeding Database...</span>
              </>
            ) : (
              <>
                <Database className="w-3.5 h-3.5 text-indigo-400" />
                <span>Seed Database Catalog</span>
              </>
            )}
          </button>
          <div className="text-[10px] text-center text-slate-500 font-medium">
            SQLite Registry Engine
          </div>
        </div>
      </aside>

      {/* --- MAIN WORKSPACE AREA --- */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto z-10 relative">
        
        {/* --- HEADER CONTROLS --- */}
        <header className="p-6 bg-white/5 border-b border-white/10 backdrop-blur-md flex items-center justify-between z-10">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-black tracking-tight text-white capitalize bg-gradient-to-r from-white via-indigo-200 to-purple-400 bg-clip-text text-transparent font-heading">
              {activeTab === "dashboard" && "TalentGraph Recruiter Portal"}
              {activeTab === "catalog" && "Candidates Catalog"}
              {activeTab === "benchmarks" && "Cross-Metric Benchmark Harness"}
            </h2>
            
            {/* Environment Status Pills */}
            <div className="flex items-center space-x-2">
              <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold border bg-white/5 border-white/10 text-slate-400 uppercase tracking-wider font-mono">
                Model: Gemma 4
              </span>
              <button 
                onClick={checkHealth}
                className={`flex items-center space-x-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold border tracking-wider uppercase font-mono transition-all ${
                  backendHealthy === true
                    ? "bg-emerald-950/40 text-emerald-400 border-emerald-800/60"
                    : backendHealthy === false
                    ? "bg-rose-950/40 text-rose-400 border-rose-800/60"
                    : "bg-slate-900 text-slate-500 border-slate-800"
                }`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${backendHealthy === true ? "bg-emerald-400" : backendHealthy === false ? "bg-rose-400" : "bg-slate-500"} animate-pulse`} />
                <span>API: {backendHealthy === true ? "Online" : backendHealthy === false ? "Offline" : "Checking..."}</span>
              </button>
            </div>
          </div>

          <div className="text-xs text-slate-400 bg-white/5 px-3 py-1.5 border border-white/10 rounded-lg font-mono">
            Host: <span className="text-indigo-400">localhost:8000</span>
          </div>
        </header>

        {/* --- CONTENT TABS CONTENT --- */}
        <div className="p-8 max-w-7xl w-full mx-auto space-y-8 flex-1">
          
          {/* Top Metric Cards showing 3D Interactive Tilts */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <AnimatedMetricCard
              title="Catalog Candidates"
              value={candidates.length}
              subtitle="Registered in sqlite database"
              icon={Users}
              delay={0.0}
            />
            <AnimatedMetricCard
              title="Active Job Roles"
              value={jobs.length}
              subtitle="Indexed matching criteria"
              icon={Layers}
              delay={0.1}
            />
            <AnimatedMetricCard
              title="AI Scoring Top Ranks"
              value={rankingResults.length > 0 ? rankingResults.length : "N/A"}
              subtitle="Shortlist count"
              icon={TrendingUp}
              delay={0.2}
            />
            <AnimatedMetricCard
              title="Explainability Runs"
              value={rankingResults.length > 0 ? "Ollama Ready" : "Standby"}
              subtitle="LLM Justification generation"
              icon={Sparkles}
              delay={0.3}
            />
          </div>
          
          {/* TABS 1: MATCHING DASHBOARD */}
          {activeTab === "dashboard" && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              
              {/* LEFT COLUMN: CRITERIA & CONFIG (COL 5) */}
              <div className="lg:col-span-5 space-y-6">
                
                {/* Section A: Selection Dropdown */}
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-5 shadow-lg space-y-4">
                  <div className="flex justify-between items-center">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                      Target Job Profile
                    </label>
                    <span className="text-[10px] text-indigo-400 font-semibold bg-indigo-950/40 border border-indigo-900/60 px-2 py-0.5 rounded-full">
                      SQLite Registry
                    </span>
                  </div>

                  <div className="flex gap-2">
                    <select
                      value={activeJobId}
                      onChange={(e) => {
                        setActiveJobId(e.target.value);
                        setRankingResults([]);
                        setActiveCandidate(null);
                      }}
                      className="flex-1 bg-white/5 border border-white/10 text-sm rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500/80 transition"
                    >
                      <option value="">-- Select active job role --</option>
                      {jobs.map((job) => (
                        <option key={job.job_id} value={job.job_id}>
                          {job.title} ({job.job_id})
                        </option>
                      ))}
                    </select>
                  </div>

                  {activeJob ? (
                    <motion.div 
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="bg-slate-950/60 border border-slate-850 rounded-lg p-4 space-y-3 overflow-hidden"
                    >
                      <div className="flex justify-between items-start">
                        <h3 className="text-sm font-bold text-white">{activeJob.title}</h3>
                        <span className="text-[10px] bg-slate-900 text-indigo-300 border border-slate-800 px-2 py-0.5 rounded font-mono">
                          {activeJob.seniority}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 leading-relaxed font-mono italic">
                        &quot;{activeJob.raw_text.slice(0, 160)}...&quot;
                      </div>
                      
                      <div className="space-y-1.5 pt-1">
                        <div className="text-[10px] uppercase font-bold text-slate-500">Must Have Skills:</div>
                        <div className="flex flex-wrap gap-1.5">
                          {activeJob.must_have.map((skill, idx) => (
                            <span key={idx} className="text-[10px] font-semibold bg-red-950/40 border border-red-900/40 text-red-300 px-2 py-0.5 rounded">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="space-y-1.5 pt-1">
                        <div className="text-[10px] uppercase font-bold text-slate-500">Nice To Have Skills:</div>
                        <div className="flex flex-wrap gap-1.5">
                          {activeJob.nice_to_have.map((skill, idx) => (
                            <span key={idx} className="text-[10px] font-semibold bg-emerald-950/40 border border-emerald-900/40 text-emerald-300 px-2 py-0.5 rounded">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  ) : (
                    <div className="text-xs text-slate-500 text-center py-4 bg-slate-950/30 rounded-lg border border-dashed border-slate-850">
                      No active job selected. Select or add a job profile.
                    </div>
                  )}
                </div>

                {/* Section B: Control Sliders */}
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-5 shadow-lg space-y-5">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                    <Sliders className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Scoring Configuration</span>
                  </h3>

                  {/* Alpha Blending Slider */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-300 font-medium">Alpha (Reranker Retrieval Bias)</span>
                      <span className="text-indigo-400 font-mono font-bold">{alpha}</span>
                    </div>
                    <input
                      type="range"
                      min="0.0"
                      max="1.0"
                      step="0.05"
                      value={alpha}
                      onChange={(e) => setAlpha(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                    />
                    <div className="flex justify-between text-[9px] text-slate-500 font-mono">
                      <span>Keyword (BM25)</span>
                      <span>Balanced</span>
                      <span>Semantic (Dense/CE)</span>
                    </div>
                  </div>

                  {/* Top N Slider */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-300 font-medium">Top N Candidates</span>
                      <span className="text-indigo-400 font-mono font-bold">{topN}</span>
                    </div>
                    <input
                      type="range"
                      min="3"
                      max="20"
                      step="1"
                      value={topN}
                      onChange={(e) => setTopN(parseInt(e.target.value))}
                      className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                    />
                  </div>

                  {/* LLM Provider Selection Dropdown */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <label className="text-slate-300 font-medium font-sans">Justification LLM Engine</label>
                      <span className="text-indigo-400 font-semibold font-mono">
                        {llmProvider === "ollama" && "Ollama"}
                        {llmProvider === "claude" && "Claude"}
                        {llmProvider === "groq" && "Groq"}
                        {llmProvider === "gemini" && "Gemini"}
                      </span>
                    </div>
                    <select
                      value={llmProvider}
                      onChange={(e) => setLlmProvider(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-850 text-xs rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-indigo-500 transition"
                    >
                      <option value="ollama">Ollama (Local Host)</option>
                      <option value="claude">Claude (Anthropic)</option>
                      <option value="groq">Groq API (Llama-3.1)</option>
                      <option value="gemini">Gemini API (Google)</option>
                    </select>
                    {/* Visual Credentials indicators */}
                    <div className="flex space-x-2 pt-1 text-[9px] font-mono">
                      {llmProvider === "claude" && (
                        <span className={`px-2 py-0.5 rounded border ${healthInfo?.has_anthropic === "True" ? "bg-emerald-950/40 text-emerald-400 border-emerald-900/40" : "bg-red-950/40 text-red-400 border-red-900/40 animate-pulse"}`}>
                          {healthInfo?.has_anthropic === "True" ? "Claude Key: Loaded" : "Claude Key: Missing in .env"}
                        </span>
                      )}
                      {llmProvider === "groq" && (
                        <span className={`px-2 py-0.5 rounded border ${healthInfo?.has_groq === "True" ? "bg-emerald-950/40 text-emerald-400 border-emerald-900/40" : "bg-red-950/40 text-red-400 border-red-900/40 animate-pulse"}`}>
                          {healthInfo?.has_groq === "True" ? "Groq Key: Loaded" : "Groq Key: Missing in .env"}
                        </span>
                      )}
                      {llmProvider === "gemini" && (
                        <span className={`px-2 py-0.5 rounded border ${healthInfo?.has_gemini === "True" ? "bg-emerald-950/40 text-emerald-400 border-emerald-900/40" : "bg-red-950/40 text-red-400 border-red-900/40 animate-pulse"}`}>
                          {healthInfo?.has_gemini === "True" ? "Gemini Key: Loaded" : "Gemini Key: Missing in .env"}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Run Pipeline Button */}
                  <button
                    onClick={runRanking}
                    disabled={isRanking || !activeJobId}
                    className="w-full bg-gradient-to-r from-indigo-650 to-purple-650 hover:from-indigo-550 hover:to-purple-550 disabled:from-slate-800 disabled:to-slate-800 text-white font-medium py-2.5 px-4 rounded-lg text-sm flex items-center justify-center space-x-2 cursor-pointer shadow-[0_4px_15px_rgba(99,102,241,0.2)] hover:shadow-[0_6px_20px_rgba(99,102,241,0.3)] transition-all duration-300"
                  >
                    {isRanking ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin text-white" />
                        <span>Running Inferences with Gemma4...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 text-indigo-200 fill-indigo-200" />
                        <span>Run AI Candidate Scoring</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Section C: Quick Add Job Form */}
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-5 shadow-lg space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                    <PlusCircle className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Create Custom Job Role</span>
                  </h3>
                  <form onSubmit={handleAddJob} className="space-y-3">
                    <div>
                      <input
                        type="text"
                        placeholder="Job Title (e.g. Senior Data Analyst)"
                        value={newJobTitle}
                        onChange={(e) => setNewJobTitle(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 text-xs rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <textarea
                        placeholder="Raw Job Description (must be > 20 characters)"
                        value={newJobDesc}
                        onChange={(e) => setNewJobDesc(e.target.value)}
                        rows={2}
                        className="w-full bg-white/5 border border-white/10 text-xs rounded px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-indigo-500 font-sans"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        placeholder="Must Haves (comma separated)"
                        value={newJobMust}
                        onChange={(e) => setNewJobMust(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 text-[10px] rounded px-2.5 py-1.5 text-slate-200 focus:outline-none"
                      />
                      <input
                        type="text"
                        placeholder="Nice To Haves (comma separated)"
                        value={newJobNice}
                        onChange={(e) => setNewJobNice(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 text-[10px] rounded px-2.5 py-1.5 text-slate-200 focus:outline-none"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <select
                        value={newJobSeniority}
                        onChange={(e) => setNewJobSeniority(e.target.value)}
                        className="bg-white/5 border border-white/10 text-[10px] rounded px-2.5 py-1.5 text-slate-300"
                      >
                        <option value="Junior">Junior</option>
                        <option value="Mid">Mid</option>
                        <option value="Senior">Senior</option>
                        <option value="Lead">Lead</option>
                      </select>
                      <input
                        type="text"
                        placeholder="Location"
                        value={newJobLocation}
                        onChange={(e) => setNewJobLocation(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 text-[10px] rounded px-2.5 py-1.5 text-slate-200"
                      />
                    </div>
                    <button
                      type="submit"
                      className="w-full bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 text-indigo-305 py-1.5 rounded text-xs font-semibold transition"
                    >
                      Save to Registry
                    </button>
                  </form>
                </div>
              </div>

              {/* RIGHT COLUMN: CANDIDATES GRID AND ANALYSIS (COL 7) */}
              <div className="lg:col-span-7 space-y-6">
                
                {/* Ranking Output List with staggered holographic cards */}
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6 shadow-lg space-y-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Ranking Results Shortlist ({rankingResults.length})
                  </h3>

                  {rankingResults.length > 0 ? (
                    <div className="space-y-3">
                      {rankingResults.map((result) => {
                        const isSelected = activeCandidate?.candidate_id === result.candidate_id;
                        return (
                          <HolographicCandidateCard
                            key={result.candidate_id}
                            result={result}
                            isSelected={isSelected}
                            onClick={() => {
                              // Find corresponding candidate resume text from candidates list
                              const matchCand = candidates.find(c => c.id === result.candidate_id);
                              setActiveCandidate({
                                ...result,
                                narrative: result.narrative, // keep backend narrative
                                // we can carry candidate details if needed
                              });
                            }}
                          />
                        );
                      })}
                    </div>
                  ) : (
                    <div className="py-12 border border-dashed border-slate-850 rounded-xl flex flex-col items-center justify-center text-slate-500 space-y-3">
                      <Layers className="w-10 h-10 text-slate-700" />
                      <div className="text-center">
                        <p className="text-sm font-semibold text-slate-400">No Ranking Data Loaded</p>
                        <p className="text-xs text-slate-500 mt-0.5">Select a job and click &quot;Run AI Candidate Scoring&quot; above.</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Candidate Deep-Dive Modal Drawer (exploding content effect) */}
                <AnimatePresence>
                  {activeCandidate && (
                    <motion.div 
                      initial={{ opacity: 0, scale: 0.9, y: 30 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.9, y: 30 }}
                      transition={{ type: "spring", damping: 20 }}
                      className="bg-gradient-to-br from-slate-900/90 to-indigo-950/50 backdrop-blur-2xl border border-indigo-500/30 rounded-2xl p-6 shadow-2xl space-y-6"
                    >
                      <div className="flex justify-between items-start border-b border-slate-800/80 pb-4">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-[10px] font-bold bg-indigo-500 text-white px-2 py-0.5 rounded font-mono shadow-[0_0_10px_rgba(99,102,241,0.5)]">
                              RANK #{activeCandidate.rank}
                            </span>
                            <h3 className="text-lg font-extrabold text-white">{activeCandidate.candidate_id}</h3>
                          </div>
                          <p className="text-xs text-slate-400 mt-0.5">Dual-Perspective Radar Alignment &amp; Resume Highlights</p>
                        </div>
                        <button
                          onClick={() => setActiveCandidate(null)}
                          className="p-1 rounded bg-white/5 border border-white/10 hover:border-slate-700 text-slate-400 hover:text-white"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      {/* Side-by-side: Radar Chart vs Resume Highlight Preview */}
                      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                        
                        {/* Radar align */}
                        <div className="lg:col-span-5 flex justify-center">
                          <RadarChart features={activeCandidate.features} />
                        </div>

                        {/* Resume Highlight pulses */}
                        <div className="lg:col-span-7 bg-slate-950/60 border border-slate-850 rounded-xl p-4 space-y-3 h-[320px] overflow-y-auto">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
                            <FileText className="w-3.5 h-3.5 text-indigo-400" />
                            <span>Matched Resume Highlights</span>
                          </h4>
                          <HighlightedResume
                            text={
                              candidates.find(c => c.id === activeCandidate.candidate_id)?.raw_resume_text ||
                              "Resume highlights indexed under sqlite records."
                            }
                            mustHave={activeJob?.must_have || []}
                            niceToHave={activeJob?.nice_to_have || []}
                          />
                        </div>
                      </div>

                      {/* Timeline journey */}
                      <div className="bg-slate-950/30 border border-slate-850 rounded-xl p-5">
                        <CareerJourneyTimeline
                          experienceYears={
                            candidates.find(c => c.id === activeCandidate.candidate_id)?.experience_years || 5
                          }
                          skills={
                            candidates.find(c => c.id === activeCandidate.candidate_id)?.skills_raw || []
                          }
                        />
                      </div>

                      {/* Explanations narrative */}
                      <div className="bg-slate-950/80 border border-slate-850 rounded-xl p-5 space-y-4">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-405 flex items-center space-x-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                          <span>AI Justification Explanation (Gemma 4)</span>
                        </h4>

                        <p className="text-xs text-indigo-200 leading-relaxed italic bg-indigo-950/10 border-l-2 border-indigo-500 p-3 rounded-r-lg font-sans">
                          &ldquo;{activeCandidate.narrative}&rdquo;
                        </p>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                          {/* Matched Points */}
                          <div className="space-y-2">
                            <div className="text-[10px] uppercase font-bold text-emerald-400 flex items-center space-x-1">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>Matched Profile Points</span>
                            </div>
                            <ul className="text-xs text-slate-400 space-y-1.5">
                              {activeCandidate.matched_points.map((p, idx) => (
                                <li key={idx} className="flex items-start space-x-1.5">
                                  <span className="text-emerald-500 font-bold mt-0.5">•</span>
                                  <span>{p}</span>
                                </li>
                              ))}
                              {activeCandidate.matched_points.length === 0 && (
                                <li className="text-slate-600 text-[11px] italic">No direct matches identified.</li>
                              )}
                            </ul>
                          </div>

                          {/* Missing Points */}
                          <div className="space-y-2">
                            <div className="text-[10px] uppercase font-bold text-amber-500 flex items-center space-x-1">
                              <AlertTriangle className="w-3 h-3" />
                              <span>Missing/Gaps Identified</span>
                            </div>
                            <ul className="text-xs text-slate-400 space-y-1.5">
                              {activeCandidate.missing_points.map((p, idx) => (
                                <li key={idx} className="flex items-start space-x-1.5">
                                  <span className="text-amber-500 font-bold mt-0.5">•</span>
                                  <span>{p}</span>
                                </li>
                              ))}
                              {activeCandidate.missing_points.length === 0 && (
                                <li className="text-slate-600 text-[11px] italic">No gaps identified.</li>
                              )}
                            </ul>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          )}

          {/* TABS 2: CANDIDATES CATALOG */}
          {activeTab === "catalog" && (
            <div className="space-y-6">
              
              {/* Header search bar and upload options */}
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-5 shadow-lg flex flex-col md:flex-row items-center justify-between gap-4">
                
                {/* Search Bar */}
                <div className="relative w-full md:w-96">
                  <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Filter catalog by ID, location, or skills (e.g. Python)..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 text-xs rounded-lg pl-9 pr-4 py-2.5 text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                {/* Buttons */}
                <button
                  onClick={() => setIsUploadOpen(!isUploadOpen)}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold py-2 px-4 rounded-lg flex items-center space-x-2 cursor-pointer transition"
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>Ingest New Candidate</span>
                </button>
              </div>

              {/* Upload Form Modal panel */}
              {isUploadOpen && (
                <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-6 space-y-4 max-w-2xl">
                  <div className="flex justify-between items-center border-b border-slate-850 pb-2">
                    <h3 className="text-sm font-bold text-white">Upload / Ingest Single Candidate</h3>
                    <button onClick={() => setIsUploadOpen(false)} className="text-slate-500 hover:text-white">
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  <form onSubmit={handleAddCandidate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-3">
                      <div>
                        <label className="text-[10px] font-bold uppercase text-slate-500 block mb-1">Candidate ID*</label>
                        <input
                          type="text"
                          placeholder="e.g. c_ml_specialist"
                          value={newCandId}
                          onChange={(e) => setNewCandId(e.target.value)}
                          className="w-full bg-white/5 border border-white/10 text-xs rounded px-2.5 py-1.5 text-slate-200"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] font-bold uppercase text-slate-500 block mb-1">Experience Years</label>
                        <input
                          type="number"
                          value={newCandExp}
                          onChange={(e) => setNewCandExp(parseFloat(e.target.value))}
                          className="w-full bg-white/5 border border-white/10 text-xs rounded px-2.5 py-1.5 text-slate-200"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] font-bold uppercase text-slate-500 block mb-1">Skills (Comma-separated)</label>
                        <input
                          type="text"
                          placeholder="Python, PyTorch, SQL"
                          value={newCandSkills}
                          onChange={(e) => setNewCandSkills(e.target.value)}
                          className="w-full bg-slate-955 border border-slate-850 text-xs rounded px-2.5 py-1.5 text-slate-200"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] font-bold uppercase text-slate-500 block mb-1">Location</label>
                        <input
                          type="text"
                          placeholder="e.g. Remote, San Francisco"
                          value={newCandLoc}
                          onChange={(e) => setNewCandLoc(e.target.value)}
                          className="w-full bg-slate-955 border border-slate-850 text-xs rounded px-2.5 py-1.5 text-slate-200"
                        />
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <label className="text-[10px] font-bold uppercase text-slate-500 block mb-1">Education</label>
                        <input
                          type="text"
                          placeholder="e.g. M.S. in Computer Science"
                          value={newCandEdu}
                          onChange={(e) => setNewCandEdu(e.target.value)}
                          className="w-full bg-slate-955 border border-slate-850 text-xs rounded px-2.5 py-1.5 text-slate-200"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] font-bold uppercase text-slate-500 block mb-1">GitHub URL</label>
                        <input
                          type="text"
                          placeholder="https://github.com/octocat"
                          value={newCandGit}
                          onChange={(e) => setNewCandGit(e.target.value)}
                          className="w-full bg-slate-955 border border-slate-850 text-xs rounded px-2.5 py-1.5 text-slate-200"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="text-[10px] font-bold uppercase text-slate-505 block mb-1">Raw Resume Text*</label>
                        <textarea
                          placeholder="Paste full raw resume details here..."
                          value={newCandResume}
                          onChange={(e) => setNewCandResume(e.target.value)}
                          rows={3}
                          className="w-full bg-slate-955 border border-slate-855 text-xs rounded px-2.5 py-1.5 text-slate-202 font-sans"
                        />
                      </div>
                    </div>

                    <div className="md:col-span-2 pt-2">
                      <button
                        type="submit"
                        className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold py-2 rounded-lg transition"
                      >
                        Ingest &amp; Index Candidate
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* Table list of all candidates */}
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden shadow-lg">
                <table className="w-full border-collapse text-left">
                  <thead>
                    <tr className="bg-slate-950/80 border-b border-slate-850 text-xs font-bold uppercase text-slate-400 tracking-wider">
                      <th className="p-4">Candidate ID</th>
                      <th className="p-4">Experience</th>
                      <th className="p-4">Location</th>
                      <th className="p-4">Extracted Skills</th>
                      <th className="p-4">GitHub Portfolio</th>
                    </tr>
                  </thead>
                  <tbody className="text-xs divide-y divide-slate-850">
                    {filteredCandidates.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-900/30 transition-all">
                        <td className="p-4 font-semibold text-indigo-400 font-mono">{c.id}</td>
                        <td className="p-4 text-slate-300 font-medium">
                          {c.experience_years ? `${c.experience_years.toFixed(1)} yrs` : "N/A"}
                        </td>
                        <td className="p-4 text-slate-400 font-medium">{c.location || "Remote"}</td>
                        <td className="p-4">
                          <div className="flex flex-wrap gap-1.5 max-w-lg">
                            {c.skills_raw.map((s, idx) => (
                              <span key={idx} className="text-[9px] bg-slate-950 text-indigo-300 border border-slate-850 px-2 py-0.5 rounded-full font-semibold">
                                {s}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="p-4">
                          {c.github_url ? (
                            <a
                              href={c.github_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-slate-400 hover:text-indigo-400 flex items-center space-x-1 font-mono transition"
                            >
                              <span>{c.github_url.replace("https://", "")}</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          ) : (
                            <span className="text-slate-600 font-mono">None</span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {filteredCandidates.length === 0 && (
                      <tr>
                        <td colSpan={5} className="text-center py-12 text-slate-500 font-medium">
                          No candidates found matching the search criteria.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TABS 3: BENCHMARK HARNESS */}
          {activeTab === "benchmarks" && (
            <div className="space-y-6">
              
              {/* Harness introduction */}
              <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl p-6 shadow-lg space-y-3">
                <div className="flex items-center space-x-2.5">
                  <Layers className="w-5 h-5 text-indigo-400" />
                  <h3 className="text-sm font-bold text-white">Candidate Trade-Off Matrix</h3>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Compare candidate features side-by-side. This dashboard visualizes individual quantitative scores 
                  (retrieved via the Hybrid Retrieval engine and Knowledge Graph distance index) across all ranked candidates.
                </p>
              </div>

              {/* Benchmark Table with animated progress bars */}
              {rankingResults.length > 0 ? (
                <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden shadow-lg">
                  <table className="w-full border-collapse text-left">
                    <thead>
                      <tr className="bg-slate-950/80 border-b border-slate-855 text-xs font-bold uppercase text-slate-400 tracking-wider">
                        <th className="p-4">Rank</th>
                        <th className="p-4">Candidate ID</th>
                        <th className="p-4">Blended Score</th>
                        <th className="p-4">Skill Overlap</th>
                        <th className="p-4">Semantic Match</th>
                        <th className="p-4">Keyword Match</th>
                        <th className="p-4">Behavioral Signal</th>
                      </tr>
                    </thead>
                    <tbody className="text-xs divide-y divide-slate-855 font-mono">
                      {rankingResults.map((result) => (
                        <tr key={result.candidate_id} className="hover:bg-slate-900/30 transition">
                          <td className="p-4 font-bold text-indigo-400">#{result.rank}</td>
                          <td className="p-4 font-sans text-slate-200 font-bold">{result.candidate_id}</td>
                          <td className="p-4 text-indigo-300 font-black">
                            {Math.round(result.final_score * 100)}%
                          </td>
                          <td className="p-4">
                            <div className="flex items-center space-x-2">
                              <span className="text-slate-300">{(result.features.skill_overlap ?? 0).toFixed(2)}</span>
                              <div className="w-16 h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-855">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${Math.min(100, (result.features.skill_overlap ?? 0) * 100)}%` }}
                                  transition={{ duration: 0.8, ease: "easeOut" }}
                                  className="h-full bg-indigo-500 rounded-full"
                                />
                              </div>
                            </div>
                          </td>
                          <td className="p-4">
                            <div className="flex items-center space-x-2">
                              <span className="text-slate-300">{(result.features.dense_similarity ?? 0).toFixed(2)}</span>
                              <div className="w-16 h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-855">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${Math.min(100, (result.features.dense_similarity ?? 0) * 100)}%` }}
                                  transition={{ duration: 0.8, ease: "easeOut" }}
                                  className="h-full bg-purple-500 rounded-full"
                                />
                              </div>
                            </div>
                          </td>
                          <td className="p-4">
                            <div className="flex items-center space-x-2">
                              <span className="text-slate-300">{(result.features.bm25_score ?? 0).toFixed(2)}</span>
                              <div className="w-16 h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-855">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${Math.min(100, ((result.features.bm25_score ?? 0) / 15) * 100)}%` }}
                                  transition={{ duration: 0.8, ease: "easeOut" }}
                                  className="h-full bg-pink-500 rounded-full"
                                />
                              </div>
                            </div>
                          </td>
                          <td className="p-4">
                            <div className="flex items-center space-x-2">
                              <span className="text-slate-300">{(result.features.behavioral_score ?? 0).toFixed(2)}</span>
                              <div className="w-16 h-1.5 bg-slate-950 rounded-full overflow-hidden border border-slate-855">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${Math.min(100, (result.features.behavioral_score ?? 0) * 100)}%` }}
                                  transition={{ duration: 0.8, ease: "easeOut" }}
                                  className="h-full bg-emerald-500 rounded-full"
                                />
                              </div>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-12 border border-dashed border-slate-850 rounded-xl flex flex-col items-center justify-center text-slate-500 space-y-3 bg-slate-900/30">
                  <Layers className="w-10 h-10 text-slate-700" />
                  <div className="text-center">
                    <p className="text-sm font-semibold text-slate-400">No Benchmark Data Available</p>
                    <p className="text-xs text-slate-505 mt-0.5">Please run candidates ranking under Matching Dashboard first.</p>
                  </div>
                </div>
              )}
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
