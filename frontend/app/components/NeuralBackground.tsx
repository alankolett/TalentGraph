"use client";

import React, { useEffect, useRef } from "react";
import * as THREE from "three";

const NeuralBackground = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 0, 8);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.5);
    dirLight.position.set(5, 5, 5);
    scene.add(dirLight);

    // Create 3D network group
    const group = new THREE.Group();
    scene.add(group);

    const nodeCount = 30;
    const geometry = new THREE.SphereGeometry(0.08, 8, 8);
    const nodes: THREE.Mesh[] = [];
    const basePositions: THREE.Vector3[] = [];

    // Distribute nodes randomly
    for (let i = 0; i < nodeCount; i++) {
      const isCandidate = i % 7 === 0;
      const isJob = i % 11 === 0;
      
      let color = 0x4f46e5; // Indigo default
      if (isCandidate) color = 0x10b981; // Emerald
      else if (isJob) color = 0x8b5cf6; // Violet
      
      const mat = new THREE.MeshPhongMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.35,
        transparent: true,
        opacity: 0.7
      });
      const mesh = new THREE.Mesh(geometry, mat);
      
      const pos = new THREE.Vector3(
        (Math.random() - 0.5) * 14,
        (Math.random() - 0.5) * 9,
        (Math.random() - 0.5) * 6
      );
      mesh.position.copy(pos);
      group.add(mesh);
      nodes.push(mesh);
      basePositions.push(pos.clone());
    }

    // Connect close nodes with lines
    const lineMat = new THREE.LineBasicMaterial({
      color: 0x4f46e5,
      transparent: true,
      opacity: 0.1
    });

    const lines: THREE.Line[] = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dist = nodes[i].position.distanceTo(nodes[j].position);
        if (dist < 3.2) {
          const points = [nodes[i].position, nodes[j].position];
          const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
          const line = new THREE.Line(lineGeo, lineMat);
          group.add(line);
          lines.push(line);
        }
      }
    }

    // Resize handling
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener("resize", handleResize);

    // Theme integration
    const updateThemeColors = (dark: boolean) => {
      if (dark) {
        lineMat.color.setHex(0x818cf8);
        lineMat.opacity = 0.14;
      } else {
        lineMat.color.setHex(0x4f46e5);
        lineMat.opacity = 0.08;
      }
    };
    
    const isDark = document.documentElement.classList.contains("dark");
    updateThemeColors(isDark);

    const observer = new MutationObserver(() => {
      const dark = document.documentElement.classList.contains("dark");
      updateThemeColors(dark);
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });

    // Animation variables
    let animationId = 0;
    let mouseX = 0;
    let mouseY = 0;
    
    const handleMouseMove = (e: MouseEvent) => {
      mouseX = (e.clientX / window.innerWidth) * 2 - 1;
      mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener("mousemove", handleMouseMove);

    const clock = new THREE.Clock();
    const tick = () => {
      const elapsed = clock.getElapsedTime();
      
      // Floating wave animation of nodes
      nodes.forEach((node, idx) => {
        const base = basePositions[idx];
        node.position.x = base.x + Math.sin(elapsed * 0.4 + base.y) * 0.12;
        node.position.y = base.y + Math.cos(elapsed * 0.4 + base.x) * 0.12;
      });

      // Subtle rotation
      group.rotation.y = elapsed * 0.015 + mouseX * 0.04;
      group.rotation.x = elapsed * 0.008 + mouseY * 0.04;

      renderer.render(scene, camera);
      animationId = requestAnimationFrame(tick);
    };
    tick();

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
      observer.disconnect();
      cancelAnimationFrame(animationId);
      
      geometry.dispose();
      lineMat.dispose();
      nodes.forEach((mesh) => (mesh.material as THREE.Material).dispose());
      renderer.dispose();
    };
  }, []);

  return <canvas ref={canvasRef} className="fixed inset-0 -z-10 pointer-events-none" />;
};

export default NeuralBackground;
