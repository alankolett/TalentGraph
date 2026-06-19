"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { motion, AnimatePresence, useMotionValue, useTransform, useSpring } from "framer-motion";
import RemixLandingPage from "./components/RemixLandingPage";
import {
  LayoutDashboard,
  Users,
  SlidersHorizontal,
  Briefcase,
  Activity,
  Database,
  Search,
  PlusCircle,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  TrendingUp,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  X,
  Layers,
  RefreshCw,
  ChevronDown
} from "lucide-react";




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
      ctx.fillStyle = "#F8FAFC"; // Clean light crystalline background
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

        ctx.fillStyle = "rgba(79, 70, 229, 0.25)"; // Glowing indigo
        ctx.beginPath();
        ctx.arc(p1.x, p1.y, p1.radius, 0, Math.PI * 2);
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const dist = Math.hypot(p1.x - p2.x, p1.y - p2.y);
          if (dist < 120) {
            const alpha = (1 - dist / 120) * 0.1;
            ctx.strokeStyle = `rgba(79, 70, 229, ${alpha})`; // Soft indigo lines
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
    <div className="flex flex-col items-center justify-center bg-white/60 border border-slate-200/60 rounded-xl p-4 shadow-sm">
      <h4 className="text-xs font-bold text-indigo-600 uppercase tracking-wider mb-2 font-sans">Feature Alignment Vector</h4>
      <svg width={width} height={height} className="overflow-visible">
        {/* Grids */}
        {gridPolygons.map((points, idx) => (
          <polygon
            key={idx}
            points={points}
            fill="none"
            stroke="rgba(15, 23, 42, 0.08)"
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
              stroke="rgba(15, 23, 42, 0.1)"
              strokeWidth="1"
            />
          );
        })}

        {/* Candidate Polygon */}
        <polygon
          points={candidatePolygon}
          fill="rgba(79, 70, 229, 0.12)"
          stroke="rgba(79, 70, 229, 0.8)"
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
              fill="#10B981" // Emerald nodes
              stroke="white"
              strokeWidth="1.5"
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
                  fill="#64748B"
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
      whileHover={{ scale: 1.02, backgroundColor: "rgba(255, 255, 255, 0.95)" }}
      className={`p-4 rounded-xl border transition-all duration-300 cursor-pointer flex justify-between items-center relative overflow-hidden group ${
        isSelected
          ? "bg-gradient-to-br from-indigo-50/70 to-violet-50/50 border-indigo-500/80 shadow-[0_10px_25px_-5px_rgba(79,70,229,0.08)]"
          : "bg-white/40 border-slate-200/60 hover:border-indigo-500/50 hover:bg-white"
      }`}
    >
      <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-indigo-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
      
      <div className="flex items-center space-x-4 z-10">
        <div className="w-10 h-10 rounded-full bg-slate-50 flex items-center justify-center font-mono font-bold text-sm text-indigo-600 border border-slate-100 group-hover:border-indigo-500/30 transition-colors shadow-sm">
          #{result.rank}
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h4 className="text-sm font-bold text-slate-850 group-hover:text-slate-950 transition-colors">{result.candidate_id}</h4>
            {result.tags.slice(0, 2).map((t, i) => (
              <span key={i} className="text-[9px] font-semibold bg-indigo-50 border border-indigo-100/50 text-indigo-600 px-1.5 py-0.5 rounded">
                {t}
              </span>
            ))}
          </div>
          <div className="flex flex-wrap gap-1 mt-1">
            {result.matched_points.slice(0, 3).map((item, idx) => (
              <span key={idx} className="text-[8px] bg-slate-50 text-slate-500 border border-slate-100 px-1.5 py-0.5 rounded font-mono">
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-3 text-right z-10">
        <div>
          <div className="text-[9px] text-slate-400 uppercase font-bold tracking-wider leading-none font-sans">Blended</div>
          <div className="text-base font-black text-indigo-600 font-mono mt-0.5 group-hover:text-indigo-700 transition-colors">{scorePct}%</div>
        </div>
        <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 transition-colors" />
      </div>
    </motion.div>
  );
};

// 7. Resume Highlight Pulse Renderer
const HighlightedResume = ({ text, mustHave, niceToHave }: { text: string, mustHave: string[], niceToHave: string[] }) => {
  if (!text) return <p className="text-slate-400 italic">No resume data available.</p>;
  const skills = [...mustHave, ...niceToHave];
  if (skills.length === 0) return <p className="text-slate-600 leading-relaxed font-mono whitespace-pre-wrap">{text}</p>;

  const pattern = new RegExp(`\\b(${skills.join("|")})\\b`, "gi");
  const parts = text.split(pattern);

  return (
    <p className="text-slate-650 leading-relaxed font-mono whitespace-pre-wrap text-[11px]">
      {parts.map((part, idx) => {
        const isMust = mustHave.some((s) => s.toLowerCase() === part.toLowerCase());
        const isNice = niceToHave.some((s) => s.toLowerCase() === part.toLowerCase());

        if (isMust) {
          return (
            <span key={idx} className="relative inline-block px-1 rounded bg-red-50 border border-red-200/50 text-red-500 font-semibold">
              {part}
            </span>
          );
        }
        if (isNice) {
          return (
            <span key={idx} className="relative inline-block px-1 rounded bg-emerald-50 border border-emerald-200/50 text-emerald-600 font-semibold">
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
      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Professional Journey</h4>
      <div className="relative pl-6 border-l border-indigo-500/30 space-y-4">
        {/* Timeline top dot */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2 }}
          className="absolute -left-1.5 top-1.5 w-3 h-3 rounded-full bg-indigo-650 border border-white shadow-sm"
        />
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-slate-800">Advanced Technical Execution</span>
            <span className="text-[9px] bg-indigo-50 text-indigo-600 border border-indigo-100 px-1.5 py-0.2 rounded font-semibold font-sans">Current</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
            Demonstrates specialized engineering competency in: {skills.slice(0, 3).join(", ")}.
          </p>
        </div>

        {/* Timeline bottom dot */}
        <div className="relative">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.4 }}
            className="absolute -left-[29.5px] top-1.5 w-3 h-3 rounded-full bg-violet-500 border border-white"
          />
          <div>
            <div className="text-xs font-bold text-slate-800">Industrial Experience base</div>
            <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
              Synthesizing {experienceYears || 3} years of industrial coding history and system development.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};



export default function App() {
  const [showPortal, setShowPortal] = useState(false);

  if (!showPortal) {
    return <RemixLandingPage onEnterApp={() => setShowPortal(true)} />;
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
    <div className="min-h-screen text-slate-900 font-sans flex overflow-hidden bg-[#F4F6F9] relative selection:bg-indigo-100 w-full z-0">
      <ConfettiGenerator active={confetti} />
      <NeuralBackground />

      {/* BACKGROUND GRAPHIC LAYER: Translucent Organic Light Blurs */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-200/40 rounded-full blur-[120px]" />
        <div className="absolute top-1/3 -right-20 w-[500px] h-[500px] bg-purple-200/30 rounded-full blur-[140px]" />
        <div className="absolute -bottom-20 left-1/3 w-80 h-80 bg-cyan-200/40 rounded-full blur-[100px]" />
      </div>

      {/* ==================== LEFT NAVIGATION SIDEBAR ==================== */}
      <aside className="w-72 bg-white/80 border-r border-slate-200/80 backdrop-blur-xl p-6 flex flex-col justify-between relative z-20 shrink-0">
        <div className="space-y-8">
          {/* Brand Header */}
          <div className="flex items-center gap-3 px-2">
            <div className="w-9 h-9 bg-gradient-to-tr from-indigo-600 to-violet-500 rounded-xl flex items-center justify-center shadow-md shadow-indigo-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-extrabold tracking-tight text-slate-900">Talent<span className="text-indigo-600">Graph</span></h1>
              <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Recruiter AI Portal</p>
            </div>
          </div>

          {/* Nav List */}
          <nav className="space-y-1">
            {[
              { id: "dashboard", label: "Matching Dashboard", icon: <LayoutDashboard className="w-4 h-4" /> },
              { id: "catalog", label: "Candidates Catalog", icon: <Users className="w-4 h-4" /> },
              { id: "benchmarks", label: "Benchmarking Harness", icon: <SlidersHorizontal className="w-4 h-4" /> },
            ].map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id as "dashboard" | "catalog" | "benchmarks");
                    setActiveCandidate(null);
                  }}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl font-medium text-sm transition-all duration-200 relative ${
                    isActive ? "text-indigo-600 font-semibold" : "text-slate-500 hover:text-slate-900 hover:bg-slate-100/60"
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="activeNavBg"
                      className="absolute inset-0 bg-indigo-50/80 border border-indigo-100/50 rounded-xl -z-10"
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    />
                  )}
                  {item.icon}
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Workspace Indicator Footer */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/60 flex flex-col gap-3">
          <div className="flex items-center justify-between text-[11px] font-medium text-slate-500">
            <span>Catalog Candidates</span>
            <span className="text-slate-800 font-bold font-mono">{candidates.length}</span>
          </div>
          <div className="flex items-center justify-between text-[11px] font-medium text-slate-500">
            <span>Active Job Roles</span>
            <span className="text-slate-800 font-bold font-mono">{jobs.length}</span>
          </div>

          <button
            onClick={seedSampleData}
            disabled={seeding}
            className="w-full bg-white border border-slate-200 hover:bg-slate-50 text-indigo-600 font-bold py-2 px-3 rounded-lg text-[11px] flex items-center justify-center gap-1.5 transition-all shadow-sm disabled:opacity-50 cursor-pointer"
          >
            {seeding ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Database className="w-3.5 h-3.5 text-indigo-500" />}
            <span>{seeding ? "Seeding..." : "Seed Database"}</span>
          </button>
          
          <div className="flex items-center gap-2 border-t border-slate-200/60 pt-3.5">
            <div className={`w-2 h-2 rounded-full ${backendHealthy ? "bg-emerald-500" : "bg-rose-500"} animate-pulse`} />
            <div className="font-mono text-[10px] text-slate-500">Host: <span className="text-slate-700 font-semibold">localhost:8000</span></div>
          </div>
        </div>
      </aside>

      {/* ==================== MAIN PANEL INTERFACE ==================== */}
      <main className="flex-1 p-8 overflow-y-auto relative z-10 flex flex-col justify-start space-y-8 min-w-0">
        
        {/* TOP SYSTEM HEADER */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/60 pb-5">
          <div>
            <h2 className="text-2xl font-black tracking-tight text-slate-900 font-heading">
              {activeTab === "dashboard" && "TalentGraph Recruiter Portal"}
              {activeTab === "catalog" && "Candidates Catalog"}
              {activeTab === "benchmarks" && "Cross-Metric Benchmark Harness"}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">Model Engine Cluster: <span className="font-mono text-indigo-600 font-semibold bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100">GEMMA-4-RELIANT</span></p>
          </div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={checkHealth}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-full border font-mono text-xs font-bold shadow-sm transition-all ${
                backendHealthy === true
                  ? "bg-emerald-50 border-emerald-200 text-emerald-700 shadow-emerald-500/5"
                  : backendHealthy === false
                  ? "bg-rose-50 border-rose-200 text-rose-700 shadow-rose-500/5 animate-pulse"
                  : "bg-slate-50 border-slate-200 text-slate-500"
              }`}
            >
              <Activity className={`w-3.5 h-3.5 ${backendHealthy === true ? "animate-pulse" : ""}`} />
              <span>API: {backendHealthy === true ? "ONLINE" : backendHealthy === false ? "OFFLINE" : "CHECKING..."}</span>
            </button>
          </div>
        </div>

        {/* HIGH-PERFORMANCE KPI GRID ROW */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          {[
            { label: "Catalog Candidates", value: candidates.length, sub: "Registered in SQLite Database", icon: <Database className="text-indigo-500 w-5 h-5" /> },
            { label: "Active Job Roles", value: jobs.length, sub: "Indexed matching criteria", icon: <Briefcase className="text-cyan-500 w-5 h-5" /> },
            { label: "AI Scoring Top Ranks", value: rankingResults.length > 0 ? `${rankingResults.length}` : "N/A", sub: rankingResults.length > 0 ? "Shortlist compiled safely" : "Shortlist evaluation idle", icon: <TrendingUp className="text-amber-500 w-5 h-5" /> },
            { label: "System Status", value: isRanking ? "RUNNING" : "STANDBY", sub: isRanking ? "LLM evaluation processing" : "Explainability pipeline ready", icon: <Sparkles className="text-purple-500 w-5 h-5" /> },
          ].map((kpi, idx) => (
            <div key={idx} className="p-5 bg-white/70 border border-slate-200/80 rounded-2xl shadow-luxe flex justify-between items-start backdrop-blur-md">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">{kpi.label}</span>
                <div className="text-2xl font-black text-slate-900 tracking-tight">{kpi.value}</div>
                <p className="text-[11px] text-slate-500 font-medium">{kpi.sub}</p>
              </div>
              <div className="p-2 bg-slate-50 border border-slate-100 rounded-xl">{kpi.icon}</div>
            </div>
          ))}
        </div>

        {/* WORKSPACE OPERATIONS GRID BLOCKS */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
              
              {/* TARGET PROFILE CARD CONFIGURATION PANEL (Left 5-Columns) */}
              <div className="lg:col-span-5 bg-white/70 border border-slate-200/80 rounded-2xl shadow-luxe p-6 flex flex-col justify-between backdrop-blur-md space-y-6">
                <div className="space-y-5">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">{"// Target Job Profile"}</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-50 border border-indigo-100/50 text-indigo-600 font-semibold">SQLite Registry</span>
                  </div>

                  {/* Native Dropdown Styled Custom Selection */}
                  <div className="relative">
                    <select 
                      value={activeJobId}
                      onChange={(e) => {
                        setActiveJobId(e.target.value);
                        setRankingResults([]);
                        setActiveCandidate(null);
                      }}
                      className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm font-semibold text-slate-800 appearance-none focus:outline-none focus:border-indigo-500/50 focus:ring-4 focus:ring-indigo-500/10 transition-all cursor-pointer font-sans"
                    >
                      <option value="">-- Select active job role --</option>
                      {jobs.map((job) => (
                        <option key={job.job_id} value={job.job_id}>
                          {job.title} ({job.job_id})
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="w-4 h-4 text-slate-400 absolute right-4 top-3.5 pointer-events-none" />
                  </div>

                  {/* Requirement Target Output Box */}
                  {activeJob ? (
                     <div className="bg-slate-900 text-slate-105 rounded-xl p-5 font-mono text-[11px] space-y-4 shadow-inner relative overflow-hidden">
                       <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/10 rounded-full blur-xl" />
                       <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                         <span className="text-slate-400 font-semibold">{activeJob.title}</span>
                         <span className="text-[10px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-1.5 py-0.5 rounded">
                           {activeJob.seniority}
                         </span>
                       </div>
                       <p className="text-slate-300 italic leading-relaxed font-mono">
                         &quot;{activeJob.raw_text.slice(0, 180)}...&quot;
                       </p>
                       <div className="space-y-2">
                         <div className="text-[10px] text-slate-400 uppercase tracking-wider font-bold font-sans">Must Have Skills:</div>
                         <div className="flex flex-wrap gap-1.5">
                           {activeJob.must_have.map((s, idx) => (
                             <span key={idx} className="px-2 py-0.5 bg-red-500/20 text-red-300 border border-red-500/30 rounded font-semibold text-[10px]">{s}</span>
                           ))}
                         </div>
                       </div>
                       <div className="space-y-2 pt-1">
                         <div className="text-[10px] text-slate-400 uppercase tracking-wider font-bold font-sans">Nice To Have Skills:</div>
                         <div className="flex flex-wrap gap-1.5">
                           {activeJob.nice_to_have.map((s, idx) => (
                             <span key={idx} className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded font-semibold text-[10px]">{s}</span>
                           ))}
                         </div>
                       </div>
                     </div>
                  ) : (
                    <div className="text-xs text-slate-400 text-center py-8 bg-white/40 rounded-xl border border-dashed border-slate-200">
                      No active job selected. Select a job profile from the registry above.
                    </div>
                  )}
                </div>

                {/* Run Pipeline Action Controller */}
                <div className="pt-4 space-y-4">
                  {/* Model selector dropdown */}
                  <div className="space-y-1">
                    <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">LLM Explanation Engine Provider</label>
                    <select
                      value={llmProvider}
                      onChange={(e) => setLlmProvider(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-semibold text-slate-700 cursor-pointer"
                    >
                      <option value="ollama">Ollama (Local Llama3/Gemma)</option>
                      <option value="gemini">Google Gemini Flash API</option>
                      <option value="claude">Anthropic Claude Sonnet API</option>
                      <option value="groq">Groq Cloud API Accelerator</option>
                    </select>
                    
                    <div className="flex space-x-2 pt-1 text-[9px] font-mono">
                      {llmProvider === "claude" && (
                        <span className={`px-2 py-0.5 rounded border ${healthInfo?.has_anthropic === "True" ? "bg-emerald-50 text-emerald-700 border-emerald-100" : "bg-rose-50 text-rose-700 border-rose-100 animate-pulse"}`}>
                          {healthInfo?.has_anthropic === "True" ? "Claude Key: Loaded" : "Claude Key: Missing in .env"}
                        </span>
                      )}
                      {llmProvider === "groq" && (
                        <span className={`px-2 py-0.5 rounded border ${healthInfo?.has_groq === "True" ? "bg-emerald-50 text-emerald-700 border-emerald-100" : "bg-rose-50 text-rose-700 border-rose-100 animate-pulse"}`}>
                          {healthInfo?.has_groq === "True" ? "Groq Key: Loaded" : "Groq Key: Missing in .env"}
                        </span>
                      )}
                      {llmProvider === "gemini" && (
                        <span className={`px-2 py-0.5 rounded border ${healthInfo?.has_gemini === "True" ? "bg-emerald-50 text-emerald-700 border-emerald-100" : "bg-rose-50 text-rose-700 border-rose-100 animate-pulse"}`}>
                          {healthInfo?.has_gemini === "True" ? "Gemini Key: Loaded" : "Gemini Key: Missing in .env"}
                        </span>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={runRanking}
                    disabled={isRanking || !activeJobId}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 active:scale-[0.98] disabled:bg-indigo-400 text-white font-bold text-sm py-3.5 px-4 rounded-xl transition-all duration-150 shadow-md shadow-indigo-600/10 flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {isRanking ? (
                      <>
                        <RefreshCw className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        <span>Analyzing Ingested Schemas...</span>
                      </>
                    ) : (
                      <>
                        <span>Run AI Candidate Scoring</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* DYNAMIC SHORTLIST RANKING ENGINE RESULTS (Right 7-Columns) */}
              <div className="lg:col-span-7 bg-white/70 border border-slate-200/80 rounded-2xl shadow-luxe p-6 flex flex-col justify-between backdrop-blur-md min-h-[400px] space-y-6">
                <div>
                  <div className="flex justify-between items-center border-b border-slate-200 pb-3 mb-4">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Ranking Results Shortlist ({rankingResults.length})</h3>
                    {rankingResults.length > 0 && (
                      <span className="text-[10px] font-mono text-emerald-600 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-md flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-emerald-500" /> MATCH SET PILEX LOGGED
                      </span>
                    )}
                  </div>

                  <div className="relative h-full flex-1 flex flex-col justify-center">
                    <AnimatePresence mode="wait">
                      {rankingResults.length === 0 && !isRanking ? (
                        <motion.div
                          key="empty-state"
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          className="text-center py-16 space-y-4"
                        >
                          <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mx-auto border border-slate-200/40 text-slate-400 shadow-inner">
                            <Search className="w-5 h-5" />
                          </div>
                          <div className="space-y-1">
                            <h4 className="text-sm font-bold text-slate-800">No Ranking Data Loaded</h4>
                            <p className="text-xs text-slate-400 max-w-xs mx-auto">Select a job profile and trigger the neural alignment engine above to generate evaluation rankings.</p>
                          </div>
                        </motion.div>
                      ) : isRanking ? (
                        <motion.div
                          key="loading-state"
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          exit={{ opacity: 0 }}
                          className="space-y-4 py-8"
                        >
                          {[1, 2, 3].map((i) => (
                            <div key={i} className="p-4 bg-slate-50/50 border border-slate-100 rounded-xl space-y-3 animate-pulse">
                              <div className="flex justify-between">
                                <div className="h-4 bg-slate-200 rounded w-1/3" />
                                <div className="h-4 bg-slate-200 rounded w-12" />
                              </div>
                              <div className="h-3 bg-slate-200 rounded w-2/3" />
                            </div>
                          ))}
                        </motion.div>
                      ) : (
                        <motion.div
                          key="results-list"
                          initial={{ opacity: 0, y: 15 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ type: "spring", stiffness: 100, damping: 15 }}
                          className="space-y-3"
                        >
                          {rankingResults.map((result) => {
                            const isSelected = activeCandidate?.candidate_id === result.candidate_id;
                            return (
                              <HolographicCandidateCard
                                key={result.candidate_id}
                                result={result}
                                isSelected={isSelected}
                                onClick={() => {
                                  setActiveCandidate(result);
                                }}
                              />
                            );
                          })}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>

                <div className="text-[10px] font-mono text-slate-400 border-t border-slate-150 pt-4">
                  * Verification layers compute contextual embedding vectors dynamically.
                </div>
              </div>
            </div>

            {/* BOTTOM CONFIGURATION SCORING TUNING MATRIX */}
            <div className="p-5 bg-white/70 border border-slate-200/80 rounded-2xl shadow-luxe backdrop-blur-md space-y-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5 font-mono">
                    <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-500" /> Scoring Configuration Tuning Matrix
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">Adjust weighting balance bias vectors mapping semantic similarities vs lexical frequency markers.</p>
                </div>
                <div className="font-mono text-xs font-bold text-indigo-650 bg-indigo-50 border border-indigo-100 px-2.5 py-1 rounded-lg shrink-0">
                  Alpha Bias Weight: {alpha}
                </div>
              </div>

              <div className="flex items-center gap-4 pt-1">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">Dense Embeddings</span>
                <input 
                  type="range" 
                  min="0.0" 
                  max="1.0" 
                  step="0.05" 
                  value={alpha}
                  onChange={(e) => setAlpha(parseFloat(e.target.value))}
                  className="flex-1 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600 focus:outline-none"
                />
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider font-mono">BM25 Keywords</span>
              </div>
            </div>

            {/* Create Job Form Section */}
            <div className="bg-white/70 border border-slate-200/80 rounded-2xl shadow-luxe p-6 backdrop-blur-md space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5 font-mono">
                <PlusCircle className="w-3.5 h-3.5 text-indigo-500" />
                <span>Create Custom Job Role</span>
              </h3>
              <form onSubmit={handleAddJob} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div>
                    <input
                      type="text"
                      placeholder="Job Title (e.g. Senior Data Analyst)"
                      value={newJobTitle}
                      onChange={(e) => setNewJobTitle(e.target.value)}
                      className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none font-sans"
                    />
                  </div>
                  <div>
                    <textarea
                      placeholder="Raw Job Description (must be > 20 characters)"
                      value={newJobDesc}
                      onChange={(e) => setNewJobDesc(e.target.value)}
                      rows={3}
                      className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none font-sans"
                    />
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                     <input
                       type="text"
                       placeholder="Must Haves (comma sep)"
                       value={newJobMust}
                       onChange={(e) => setNewJobMust(e.target.value)}
                       className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-[11px] font-medium text-slate-800 placeholder-slate-400 focus:outline-none font-sans"
                     />
                     <input
                       type="text"
                       placeholder="Nice To Haves (comma sep)"
                       value={newJobNice}
                       onChange={(e) => setNewJobNice(e.target.value)}
                       className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-[11px] font-medium text-slate-800 placeholder-slate-400 focus:outline-none font-sans"
                     />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      value={newJobSeniority}
                      onChange={(e) => setNewJobSeniority(e.target.value)}
                      className="bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-[11px] font-semibold text-slate-700 cursor-pointer font-sans"
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
                      className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-[11px] font-medium text-slate-800 placeholder-slate-400 focus:outline-none font-sans"
                    />
                  </div>
                  <button
                    type="submit"
                    className="w-full bg-indigo-50 border border-indigo-100 hover:bg-indigo-100 text-indigo-655 font-bold py-2 rounded-lg text-xs transition cursor-pointer font-sans"
                  >
                    Save Job to Registry
                  </button>
                </div>
              </form>
            </div>

            {/* Candidate Details Overlay (Drawer) */}
            <AnimatePresence>
              {activeCandidate && (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.95, y: 30 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, y: 30 }}
                  transition={{ type: "spring", damping: 20 }}
                  className="bg-white/90 backdrop-blur-2xl border border-slate-200/80 rounded-2xl p-6 shadow-2xl space-y-6"
                >
                  <div className="flex justify-between items-start border-b border-slate-200 pb-4">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] font-bold bg-indigo-600 text-white px-2 py-0.5 rounded font-mono shadow-sm">
                          RANK #{activeCandidate.rank}
                        </span>
                        <h3 className="text-lg font-black text-slate-900 font-heading">{activeCandidate.candidate_id}</h3>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">Dual-Perspective Radar Alignment &amp; Resume Highlights</p>
                    </div>
                    <button
                      onClick={() => setActiveCandidate(null)}
                      className="p-1.5 rounded-lg bg-slate-50 border border-slate-100 hover:bg-slate-100 text-slate-500 transition cursor-pointer"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Radar vs Resume preview */}
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
                    {/* Radar */}
                    <div className="lg:col-span-5 flex justify-center items-center">
                      <RadarChart features={activeCandidate.features} />
                    </div>

                    {/* Resume highlight */}
                    <div className="lg:col-span-7 bg-slate-50 border border-slate-100 rounded-xl p-5 space-y-3 h-[320px] overflow-y-auto">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5 font-mono">
                        <FileText className="w-3.5 h-3.5 text-indigo-500" />
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

                  {/* Timeline */}
                  <div className="bg-white/40 border border-slate-200/60 rounded-xl p-5 shadow-sm">
                    <CareerJourneyTimeline
                      experienceYears={
                        candidates.find(c => c.id === activeCandidate.candidate_id)?.experience_years || 5
                      }
                      skills={
                        candidates.find(c => c.id === activeCandidate.candidate_id)?.skills_raw || []
                      }
                    />
                  </div>

                  {/* AI narrative */}
                  <div className="bg-white/70 border border-slate-200/80 rounded-xl p-5 space-y-4 shadow-sm">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5 font-mono">
                      <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                      <span>AI Justification Explanation (Gemma 4)</span>
                    </h4>

                    <p className="text-xs text-indigo-700 leading-relaxed italic bg-indigo-50/50 border-l-4 border-indigo-600 p-3 rounded-r-lg font-sans font-medium">
                      &ldquo;{activeCandidate.narrative}&rdquo;
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                      {/* Matched Points */}
                      <div className="space-y-2">
                        <div className="text-[10px] uppercase font-bold text-emerald-600 flex items-center space-x-1 font-mono">
                          <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                          <span>Matched Profile Points</span>
                        </div>
                        <ul className="text-xs text-slate-600 space-y-1.5">
                          {activeCandidate.matched_points.map((p, idx) => (
                            <li key={idx} className="flex items-start space-x-1.5">
                              <span className="text-emerald-500 font-bold mt-0.5">•</span>
                              <span>{p}</span>
                            </li>
                          ))}
                          {activeCandidate.matched_points.length === 0 && (
                            <li className="text-slate-400 text-[11px] italic">No direct matches identified.</li>
                          )}
                        </ul>
                      </div>

                      {/* Missing Points */}
                      <div className="space-y-2">
                        <div className="text-[10px] uppercase font-bold text-red-500 flex items-center space-x-1 font-mono">
                          <AlertTriangle className="w-3 h-3 text-red-500" />
                          <span>Missing/Gaps Identified</span>
                        </div>
                        <ul className="text-xs text-slate-650 space-y-1.5">
                          {activeCandidate.missing_points.map((p, idx) => (
                            <li key={idx} className="flex items-start space-x-1.5">
                              <span className="text-red-500 font-bold mt-0.5">•</span>
                              <span>{p}</span>
                            </li>
                          ))}
                          {activeCandidate.missing_points.length === 0 && (
                            <li className="text-slate-400 text-[11px] italic">No gaps identified.</li>
                          )}
                        </ul>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* TABS 2: CANDIDATES CATALOG */}
        {activeTab === "catalog" && (
          <div className="space-y-6">
            <div className="bg-white/70 border border-slate-200/80 rounded-2xl shadow-luxe p-5 backdrop-blur-md flex flex-col md:flex-row items-center justify-between gap-4">
              {/* Search Bar */}
              <div className="relative w-full md:w-96">
                <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Filter catalog by ID, location, or skills (e.g. Python)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 text-xs rounded-lg pl-9 pr-4 py-2.5 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 font-sans"
                />
              </div>

              {/* Ingest Button */}
              <button
                onClick={() => setIsUploadOpen(!isUploadOpen)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold py-2.5 px-4 rounded-lg flex items-center gap-1.5 transition cursor-pointer shadow-sm shadow-indigo-650/10 font-sans"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Ingest New Candidate</span>
              </button>
            </div>

            {/* Ingest Form Panel */}
            {isUploadOpen && (
              <div className="bg-white/80 border border-slate-200/80 rounded-2xl p-6 shadow-luxe max-w-2xl backdrop-blur-md space-y-4">
                <div className="flex justify-between items-center border-b border-slate-200 pb-2">
                  <h3 className="text-sm font-bold text-slate-900 font-heading">Upload / Ingest Single Candidate</h3>
                  <button onClick={() => setIsUploadOpen(false)} className="text-slate-400 hover:text-slate-655 transition cursor-pointer">
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <form onSubmit={handleAddCandidate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div>
                      <label className="text-[10px] font-bold uppercase text-slate-400 block mb-1 font-sans">Candidate ID*</label>
                      <input
                        type="text"
                        placeholder="e.g. c_ml_specialist"
                        value={newCandId}
                        onChange={(e) => setNewCandId(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-200 text-xs rounded px-2.5 py-1.5 text-slate-800 placeholder-slate-400 focus:outline-none font-sans"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold uppercase text-slate-400 block mb-1 font-sans">Experience Years</label>
                      <input
                        type="number"
                        value={newCandExp}
                        onChange={(e) => setNewCandExp(parseFloat(e.target.value))}
                        className="w-full bg-slate-50 border border-slate-200 text-xs rounded px-2.5 py-1.5 text-slate-800 placeholder-slate-400 focus:outline-none font-sans"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold uppercase text-slate-400 block mb-1 font-sans">Skills (Comma-separated)</label>
                      <input
                        type="text"
                        placeholder="Python, PyTorch, SQL"
                        value={newCandSkills}
                        onChange={(e) => setNewCandSkills(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-200 text-xs rounded px-2.5 py-1.5 text-slate-800 placeholder-slate-400 focus:outline-none font-sans"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold uppercase text-slate-400 block mb-1 font-sans">Location</label>
                      <input
                        type="text"
                        placeholder="e.g. Remote, San Francisco"
                        value={newCandLoc}
                        onChange={(e) => setNewCandLoc(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-200 text-xs rounded px-2.5 py-1.5 text-slate-800 placeholder-slate-400 focus:outline-none font-sans"
                      />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="text-[10px] font-bold uppercase text-slate-400 block mb-1 font-sans">Education</label>
                      <input
                        type="text"
                        placeholder="e.g. M.S. in Computer Science"
                        value={newCandEdu}
                        onChange={(e) => setNewCandEdu(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-200 text-xs rounded px-2.5 py-1.5 text-slate-800 placeholder-slate-400 focus:outline-none font-sans"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold uppercase text-slate-400 block mb-1 font-sans">GitHub URL</label>
                      <input
                        type="text"
                        placeholder="https://github.com/octocat"
                        value={newCandGit}
                        onChange={(e) => setNewCandGit(e.target.value)}
                        className="w-full bg-slate-50 border border-slate-200 text-xs rounded px-2.5 py-1.5 text-slate-800 placeholder-slate-400 focus:outline-none font-sans"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold uppercase text-slate-400 block mb-1 font-sans">Raw Resume Text*</label>
                      <textarea
                        placeholder="Paste full raw resume details here..."
                        value={newCandResume}
                        onChange={(e) => setNewCandResume(e.target.value)}
                        rows={3}
                        className="w-full bg-slate-50 border border-slate-200 text-xs rounded px-2.5 py-1.5 text-slate-800 placeholder-slate-400 focus:outline-none font-sans"
                      />
                    </div>
                  </div>

                  <div className="md:col-span-2 pt-2">
                    <button
                      type="submit"
                      className="w-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold py-2 rounded-lg transition cursor-pointer font-sans"
                    >
                      Ingest &amp; Index Candidate
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Candidates Table */}
            <div className="bg-white/70 border border-slate-200/80 rounded-2xl overflow-hidden shadow-luxe backdrop-blur-md">
              <table className="w-full border-collapse text-left">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase text-slate-500 tracking-wider">
                    <th className="p-4">Candidate ID</th>
                    <th className="p-4">Experience</th>
                    <th className="p-4">Location</th>
                    <th className="p-4">Extracted Skills</th>
                    <th className="p-4">GitHub Portfolio</th>
                  </tr>
                </thead>
                <tbody className="text-xs divide-y divide-slate-150 text-slate-700">
                  {filteredCandidates.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50/50 transition-all">
                      <td className="p-4 font-bold text-indigo-600 font-mono">{c.id}</td>
                      <td className="p-4 font-semibold text-slate-800 font-sans">
                        {c.experience_years ? `${c.experience_years.toFixed(1)} yrs` : "N/A"}
                      </td>
                      <td className="p-4 text-slate-500 font-medium font-sans">{c.location || "Remote"}</td>
                      <td className="p-4">
                        <div className="flex flex-wrap gap-1.5 max-w-lg">
                          {c.skills_raw.map((s, idx) => (
                            <span key={idx} className="text-[9px] bg-slate-50 text-indigo-600 border border-slate-100 px-2 py-0.5 rounded-full font-bold">
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
                            className="text-slate-400 hover:text-indigo-600 flex items-center space-x-1 font-mono transition"
                          >
                            <span>{c.github_url.replace("https://", "")}</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : (
                          <span className="text-slate-300 font-mono">None</span>
                        )}
                      </td>
                    </tr>
                  ))}
                  {filteredCandidates.length === 0 && (
                    <tr>
                      <td colSpan={5} className="text-center py-12 text-slate-400 font-medium">
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
            <div className="bg-white/70 border border-slate-200/80 rounded-2xl p-6 shadow-luxe backdrop-blur-md space-y-3">
              <div className="flex items-center space-x-2.5">
                <Layers className="w-5 h-5 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900 font-heading">Candidate Trade-Off Matrix</h3>
              </div>
              <p className="text-xs text-slate-500 leading-relaxed font-sans">
                Compare candidate features side-by-side. This dashboard visualizes individual quantitative scores 
                (retrieved via the Hybrid Retrieval engine and Knowledge Graph distance index) across all ranked candidates.
              </p>
            </div>

            {rankingResults.length > 0 ? (
              <div className="bg-white/70 border border-slate-200/80 rounded-2xl overflow-hidden shadow-luxe backdrop-blur-md">
                <table className="w-full border-collapse text-left font-sans">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase text-slate-500 tracking-wider">
                      <th className="p-4">Rank</th>
                      <th className="p-4">Candidate ID</th>
                      <th className="p-4">Blended Score</th>
                      <th className="p-4">Skill Overlap</th>
                      <th className="p-4">Semantic Match</th>
                      <th className="p-4">Keyword Match</th>
                      <th className="p-4">Behavioral Signal</th>
                    </tr>
                  </thead>
                  <tbody className="text-xs divide-y divide-slate-150 font-mono text-slate-700">
                    {rankingResults.map((result) => (
                      <tr key={result.candidate_id} className="hover:bg-slate-50/50 transition">
                        <td className="p-4 font-bold text-indigo-600">#{result.rank}</td>
                        <td className="p-4 font-sans text-slate-800 font-bold">{result.candidate_id}</td>
                        <td className="p-4 text-indigo-650 font-black">
                          {Math.round(result.final_score * 100)}%
                        </td>
                        <td className="p-4">
                          <div className="flex items-center space-x-2">
                            <span className="text-slate-600">{(result.features.skill_overlap ?? 0).toFixed(2)}</span>
                            <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
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
                            <span className="text-slate-600">{(result.features.dense_similarity ?? 0).toFixed(2)}</span>
                            <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
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
                            <span className="text-slate-600">{(result.features.bm25_score ?? 0).toFixed(2)}</span>
                            <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
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
                            <span className="text-slate-600">{(result.features.behavioral_score ?? 0).toFixed(2)}</span>
                            <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
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
              <div className="py-12 border border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center text-slate-400 space-y-3 bg-white/40 backdrop-blur-md font-sans">
                <Layers className="w-10 h-10 text-slate-350" />
                <div className="text-center font-sans">
                  <p className="text-sm font-semibold text-slate-500">No Benchmark Data Available</p>
                  <p className="text-xs text-slate-400 mt-0.5">Please run candidates ranking under Matching Dashboard first.</p>
                </div>
              </div>
            )}
          </div>
        )}

      </main>
    </div>
  );
}
