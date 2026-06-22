"use client";

import React, { useEffect, useRef, useState } from "react";
import Lenis from "@studio-freight/lenis";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import * as THREE from "three";
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

    let rafId: number;
    function updateScroll(time: number) {
      lenis.raf(time);
      rafId = requestAnimationFrame(updateScroll);
    }
    rafId = requestAnimationFrame(updateScroll);

    lenis.on("scroll", ScrollTrigger.update);

    const tickerUpdate = (time: number) => {
      lenis.raf(time * 1000);
    };
    gsap.ticker.add(tickerUpdate);
    gsap.ticker.lagSmoothing(0);

    return () => {
      cancelAnimationFrame(rafId);
      lenis.destroy();
      gsap.ticker.remove(tickerUpdate);
    };
  }, []);

  // ==================== THREE.JS WEBGL BACKGROUND ====================
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Renderer
    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
      powerPreference: "high-performance",
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);

    // Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 0, 5);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.65);
    dirLight.position.set(5, 5, 5);
    scene.add(dirLight);

    // 1. Constellation Starfield System
    const starCount = 1500;
    const starGeometry = new THREE.BufferGeometry();
    const starPositions = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i++) {
      starPositions[i] = (Math.random() - 0.5) * 22;
    }
    starGeometry.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));

    const starMaterial = new THREE.PointsMaterial({
      color: 0x4f46e5,
      size: 0.05,
      transparent: true,
      opacity: 0.12,
      sizeAttenuation: true,
    });
    const starField = new THREE.Points(starGeometry, starMaterial);
    scene.add(starField);

    // 2. The 3D Floating Talent Network Graph
    const networkGroup = new THREE.Group();
    scene.add(networkGroup);

    // Nodes data
    const nodesData = [
      // Jobs (Center/core)
      { id: "job-backend", name: "Job: Senior Backend Engineer", type: "job", size: 0.26, color: "#4F46E5", pos: new THREE.Vector3(0, 0, 0) },
      { id: "job-mlops", name: "Job: Lead MLOps Platform Architect", type: "job", size: 0.26, color: "#10B981", pos: new THREE.Vector3(1.6, 0.9, -0.6) },
      { id: "job-frontend", name: "Job: Senior React Developer", type: "job", size: 0.26, color: "#8B5CF6", pos: new THREE.Vector3(-1.6, -0.9, 0.6) },
      
      // Candidates
      { id: "cand-elena", name: "Elena Rostova (Match: 98.4%)", type: "candidate", size: 0.18, color: "#6366F1", pos: new THREE.Vector3(0.8, -1.1, 0.7) },
      { id: "cand-marcus", name: "Marcus Vance (Match: 94.1%)", type: "candidate", size: 0.18, color: "#8B5CF6", pos: new THREE.Vector3(2.4, 0.2, -0.9) },
      { id: "cand-siddharth", name: "Siddharth Nair (Match: 89.7%)", type: "candidate", size: 0.18, color: "#EF4444", pos: new THREE.Vector3(-0.6, 1.3, -0.5) },
      { id: "cand-octocat", name: "Structured Sandbox Profile", type: "candidate", size: 0.16, color: "#3B82F6", pos: new THREE.Vector3(-2.4, -0.2, 0.9) },

      // Skills (Branching out)
      { id: "skill-python", name: "Skill: Python", type: "skill", size: 0.08, color: "#10B981", pos: new THREE.Vector3(1.7, -1.8, 0.3) },
      { id: "skill-fastapi", name: "Skill: FastAPI", type: "skill", size: 0.08, color: "#4F46E5", pos: new THREE.Vector3(0.3, -2.1, 0.9) },
      { id: "skill-qdrant", name: "Skill: Qdrant", type: "skill", size: 0.08, color: "#EF4444", pos: new THREE.Vector3(1.0, -0.5, 1.7) },
      { id: "skill-pytorch", name: "Skill: PyTorch", type: "skill", size: 0.08, color: "#EC4899", pos: new THREE.Vector3(3.2, 0.8, -1.3) },
      { id: "skill-transformers", name: "Skill: Transformers", type: "skill", size: 0.08, color: "#8B5CF6", pos: new THREE.Vector3(2.9, -0.6, -0.4) },
      { id: "skill-react", name: "Skill: React", type: "skill", size: 0.08, color: "#06B6D4", pos: new THREE.Vector3(-1.9, -1.9, 1.3) },
      { id: "skill-typescript", name: "Skill: TypeScript", type: "skill", size: 0.08, color: "#3B82F6", pos: new THREE.Vector3(-2.9, -1.1, 0.3) }
    ];

    // Links data
    const linksData = [
      { from: "job-backend", to: "cand-elena" },
      { from: "job-mlops", to: "cand-marcus" },
      { from: "job-backend", to: "cand-siddharth" },
      { from: "job-frontend", to: "cand-octocat" },
      
      { from: "cand-elena", to: "skill-python" },
      { from: "cand-elena", to: "skill-fastapi" },
      { from: "cand-elena", to: "skill-qdrant" },
      
      { from: "cand-marcus", to: "skill-python" },
      { from: "cand-marcus", to: "skill-pytorch" },
      { from: "cand-marcus", to: "skill-transformers" },
      
      { from: "cand-siddharth", to: "skill-python" },
      { from: "cand-siddharth", to: "skill-fastapi" },
      
      { from: "cand-octocat", to: "skill-react" },
      { from: "cand-octocat", to: "skill-typescript" }
    ];

    const nodeMeshes: THREE.Mesh[] = [];
    const sphereGeo = new THREE.SphereGeometry(1, 16, 16);

    nodesData.forEach((node) => {
      const nodeMat = new THREE.MeshPhongMaterial({
        color: new THREE.Color(node.color),
        emissive: new THREE.Color(node.color),
        emissiveIntensity: 0.4,
        shininess: 90,
        transparent: true,
        opacity: 0.9
      });
      
      const mesh = new THREE.Mesh(sphereGeo, nodeMat);
      mesh.scale.setScalar(node.size);
      mesh.position.copy(node.pos);
      mesh.userData = { id: node.id, name: node.name, type: node.type, baseScale: node.size, baseColor: node.color };
      networkGroup.add(mesh);
      nodeMeshes.push(mesh);
    });

    const linkLines: THREE.Line[] = [];
    const linkMaterials: THREE.LineBasicMaterial[] = [];

    linksData.forEach((link) => {
      const fromNode = nodesData.find((n) => n.id === link.from);
      const toNode = nodesData.find((n) => n.id === link.to);
      if (!fromNode || !toNode) return;

      const points = [fromNode.pos, toNode.pos];
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      
      const lineMat = new THREE.LineBasicMaterial({
        color: 0x4f46e5,
        transparent: true,
        opacity: 0.12,
        linewidth: 1
      });
      
      const line = new THREE.Line(lineGeo, lineMat);
      networkGroup.add(line);
      linkLines.push(line);
      linkMaterials.push(lineMat);
    });

    // Set initial network position
    networkGroup.position.set(1.4, -0.6, 0.0);

    // ==================== GSAP SCROLL RIGGING ====================
    const webglTimeline = gsap.timeline({
      scrollTrigger: {
        trigger: "body",
        start: "top top",
        end: "bottom bottom",
        scrub: true,
        invalidateOnRefresh: true,
      }
    });

    webglTimeline.to(camera.position, {
      y: -3.6,
      x: -0.1,
      z: 4.2,
      ease: "none",
    }, 0);

    webglTimeline.to(camera.rotation, {
      x: THREE.MathUtils.degToRad(8),
      y: THREE.MathUtils.degToRad(-12),
      ease: "none",
    }, 0);

    webglTimeline.to(networkGroup.position, {
      x: -0.6,
      y: -1.9,
      z: 1.6,
      ease: "none",
    }, 0);

    webglTimeline.to(networkGroup.rotation, {
      y: THREE.MathUtils.degToRad(180),
      x: THREE.MathUtils.degToRad(35),
      ease: "none",
    }, 0);

    // ==================== WINDOW RESIZE ====================
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    };
    window.addEventListener("resize", handleResize);

    // ==================== MUTATION OBSERVER (THEME SYNC) ====================
    const updateWebGLTheme = (dark: boolean) => {
      if (dark) {
        starMaterial.color.setHex(0xffffff);
        starMaterial.opacity = 0.18;
        linkMaterials.forEach((mat) => {
          mat.color.setHex(0x818cf8);
          mat.opacity = 0.20;
        });
      } else {
        starMaterial.color.setHex(0x4f46e5);
        starMaterial.opacity = 0.12;
        linkMaterials.forEach((mat) => {
          mat.color.setHex(0x4f46e5);
          mat.opacity = 0.12;
        });
      }
    };

    const isDarkTheme = document.documentElement.classList.contains("dark");
    updateWebGLTheme(isDarkTheme);

    const observer = new MutationObserver(() => {
      const dark = document.documentElement.classList.contains("dark");
      updateWebGLTheme(dark);
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

    // ==================== RAYCAST HOVER ====================
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let hoveredNode: THREE.Mesh | null = null;

    const tooltip = document.createElement("div");
    tooltip.className = "fixed pointer-events-none bg-slate-900/90 text-white text-[10px] font-bold px-2.5 py-1.5 rounded-lg border border-slate-700 shadow-xl opacity-0 transition-opacity duration-200 font-sans z-50";
    document.body.appendChild(tooltip);

    const handleCanvasMouseMove = (e: MouseEvent) => {
      mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
      
      tooltip.style.left = `${e.clientX + 15}px`;
      tooltip.style.top = `${e.clientY + 15}px`;
    };
    window.addEventListener("mousemove", handleCanvasMouseMove);

    // ==================== ANIMATION LOOP ====================
    let animationId = 0;
    const clock = new THREE.Clock();

    const tick = () => {
      const elapsedTime = clock.getElapsedTime();

      // Idle Rotation of Constellation Starfield & Network Graph
      starField.rotation.y = elapsedTime * 0.012;
      starField.rotation.x = elapsedTime * 0.003;
      
      networkGroup.rotation.y = elapsedTime * 0.05 + (webglTimeline.scrollTrigger ? webglTimeline.scrollTrigger.progress * Math.PI : 0);

      // Raycast intersections
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(nodeMeshes);

      if (intersects.length > 0) {
        const hitNode = intersects[0].object as THREE.Mesh;
        if (hoveredNode !== hitNode) {
          if (hoveredNode) {
            gsap.to(hoveredNode.scale, { x: hoveredNode.userData.baseScale, y: hoveredNode.userData.baseScale, z: hoveredNode.userData.baseScale, duration: 0.15 });
            (hoveredNode.material as THREE.MeshPhongMaterial).emissiveIntensity = 0.4;
          }
          hoveredNode = hitNode;
          gsap.to(hoveredNode.scale, { x: hoveredNode.userData.baseScale * 1.4, y: hoveredNode.userData.baseScale * 1.4, z: hoveredNode.userData.baseScale * 1.4, duration: 0.15 });
          (hoveredNode.material as THREE.MeshPhongMaterial).emissiveIntensity = 0.9;
          
          tooltip.textContent = hoveredNode.userData.name;
          tooltip.style.opacity = "1";
        }
      } else {
        if (hoveredNode) {
          gsap.to(hoveredNode.scale, { x: hoveredNode.userData.baseScale, y: hoveredNode.userData.baseScale, z: hoveredNode.userData.baseScale, duration: 0.15 });
          (hoveredNode.material as THREE.MeshPhongMaterial).emissiveIntensity = 0.4;
          hoveredNode = null;
          tooltip.style.opacity = "0";
        }
      }

      renderer.render(scene, camera);
      animationId = requestAnimationFrame(tick);
    };
    tick();

    // ==================== CLEANUP ====================
    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleCanvasMouseMove);
      if (document.body.contains(tooltip)) {
        document.body.removeChild(tooltip);
      }
      observer.disconnect();
      cancelAnimationFrame(animationId);
      
      starGeometry.dispose();
      starMaterial.dispose();
      sphereGeo.dispose();
      nodeMeshes.forEach((mesh) => {
        (mesh.material as THREE.Material).dispose();
      });
      linkMaterials.forEach((mat) => mat.dispose());
      renderer.dispose();
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
    <div className="relative bg-[#F8FAFC] text-slate-900 font-sans selection:bg-indigo-100 min-h-screen">
      {/* 3D Viewport Hardware-Accelerated Canvas */}
      <canvas ref={canvasRef} className="webgl-canvas fixed top-0 left-0 w-full h-screen pointer-events-none z-10" />

      {/* BACKGROUND ORGANIC BLURS */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-200/40 rounded-full blur-[120px]" />
        <div className="absolute top-1/3 -right-20 w-[500px] h-[500px] bg-emerald-200/30 rounded-full blur-[140px]" />
        <div className="absolute -bottom-20 left-1/3 w-80 h-80 bg-cyan-200/30 rounded-full blur-[100px]" />
      </div>

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
        <section className="min-h-[70vh] flex items-center justify-center">
          <div className="bento-glass-card p-8 md:p-12 w-full max-w-3xl text-center space-y-6">
            <span className="text-[11px] font-bold tracking-[0.25em] text-slate-400 uppercase block font-mono">
              {"// Neural Recruiter Suite"}
            </span>
            <h2 className="text-4xl md:text-6xl font-black text-slate-900 tracking-[-0.04em] leading-[1.1] font-heading">
              A Crystalline Graph Matrix For Talent Telemetry
            </h2>
            <p className="text-slate-500 text-sm md:text-base max-w-xl mx-auto leading-relaxed">
              Synthesize resume semantic distances, commit velocities, and cross-functional skill ontologies directly on the GPU canvas.
            </p>

            <div className="pt-4 flex justify-center">
              <button 
                ref={magneticRef}
                onClick={onEnterApp}
                className="magnetic-cta relative bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm px-8 py-4 rounded-xl shadow-luxe transition-all duration-300 active:scale-95 flex items-center gap-2 group cursor-pointer"
              >
                <span>Launch Recruiter Portal</span>
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>
        </section>

        {/* TALENTGRAPH FEATURE GRID */}
        <section className="space-y-8">
          <div className="text-center space-y-2">
            <h3 className="text-3xl font-black tracking-tight text-slate-900">
              Core Vector Subsystems
            </h3>
            <p className="text-slate-500 text-sm max-w-md mx-auto">
              Four low-latency ranking components running concurrently over sqlite and vector databases.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              {
                title: "Knowledge Graph",
                icon: <Database className="w-5 h-5 text-indigo-500" />,
                text: "Calculates synoymic skill node distances dynamically.",
              },
              {
                title: "Hybrid Retrieval",
                icon: <Activity className="w-5 h-5 text-emerald-500" />,
                text: "Merges BM25 lexical frequency with Qdrant vector scores.",
              },
              {
                title: "Behavioral Signals",
                icon: <Zap className="w-5 h-5 text-amber-500" />,
                text: "Telemetry indexing candidates OSS commits and velocities.",
              },
              {
                title: "Explainability Matrix",
                icon: <Sparkles className="w-5 h-5 text-purple-500" />,
                text: "Generates narratives detailing exactly why profiles align.",
              },
            ].map((card, i) => (
              <div 
                key={i} 
                className="bento-glass-card p-6 flex flex-col justify-between h-56 hover:border-indigo-500/30 transition-all duration-300 bg-white/50"
              >
                <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center shadow-sm">
                  {card.icon}
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-slate-900 font-heading">{card.title}</h4>
                  <p className="text-[11px] text-slate-400 leading-relaxed">{card.text}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

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
              
              <pre className="text-slate-400 select-none overflow-x-auto text-[10px] md:text-[11px] leading-relaxed">
                <code>
                  <span className="text-indigo-400">import</span> {"{ rankCandidate, cosineDistance }"} <span className="text-indigo-400">from</span> <span className="text-emerald-400">&apos;talentgraph/core&apos;</span>;<br />
                  <span className="text-indigo-400">function</span> <span className="text-amber-300">AnalyzeCandidateSignals</span>(id) {"{"}<br />
                  &nbsp;&nbsp;<span className="text-slate-500">{"// Compute semantic vector weights"}</span><br />
                  &nbsp;&nbsp;<span className="text-indigo-400">const</span> dist = <span className="text-amber-300">cosineDistance</span>(cand, job);<br />
                  &nbsp;&nbsp;<span className="text-indigo-400">return</span> <span className="text-amber-300">rankCandidate</span>(id, dist, <span className="text-emerald-500">0.5</span>);<br />
                  {"}"}
                </code>
              </pre>

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
