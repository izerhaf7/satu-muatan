/** Truk low-poly three.js — hero landing (K12 butir 4: landing dikecualikan dari
 *  batas animasi §10). HANYA primitif kode (boxGeometry/cylinderGeometry/planeGeometry/
 *  circleGeometry), palet PERSIS 5 warna resmi (../palet.ts), meshStandardMaterial
 *  flatShading. Tanpa shadow-map (bayangan dibuat lewat ellipse gelap datar, murah).
 *
 *  Gerak: rotasi idle pelan + parallax pointer (±0.15 rad) + tilt/dolly kamera
 *  mengikuti progres scroll. frameloop="demand": kanvas TIDAK menggambar tiap frame
 *  begitu saja — hanya saat di-invalidate (event pointer/scroll, atau loop RAF ringan
 *  yang jalan HANYA selagi hero terlihat di viewport, lihat komponen `Invalidator`).
 *  Dipanggil lewat React.lazy dari Hero.tsx, jadi `three` masuk chunk terpisah. */

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useEffect, useRef } from "react";
import type { Group } from "three";
import { DoubleSide } from "three";

import { PALET } from "../palet";

/** Loop RAF yang HANYA memanggil invalidate() selagi `aktif` true (hero di viewport).
 *  Ini yang menghidupkan rotasi idle di bawah frameloop="demand" — begitu discroll
 *  lewat, loop berhenti dan kanvas kembali diam (hemat baterai/CPU). */
function Invalidator({ aktif }: { aktif: boolean }) {
  const { invalidate } = useThree();
  useEffect(() => {
    if (!aktif) return;
    let id: number;
    const tick = () => {
      invalidate();
      id = requestAnimationFrame(tick);
    };
    id = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(id);
  }, [aktif, invalidate]);
  return null;
}

/** Dolly + tilt kamera halus mengikuti progres scroll hero (0 di puncak, 1 setelah
 *  hero lewat). Progres diukur dari luar (bounding rect wrapper), dituang ke ref
 *  supaya tidak memicu re-render React tiap piksel scroll. */
function KameraRig({ progres }: { progres: React.MutableRefObject<number> }) {
  useFrame(({ camera }) => {
    const p = progres.current ?? 0;
    camera.position.y = 2.05 + p * 0.45;
    camera.position.z = 4.7 - p * 0.7;
    camera.lookAt(0, 0.75, 0);
  });
  return null;
}

/** Dengar scroll window, tulis progres ke ref, dan invalidate supaya KameraRig
 *  langsung menggambar ulang satu frame (frameloop="demand"). */
function PendengarScroll({
  wadahRef,
  progres,
}: {
  wadahRef: React.RefObject<HTMLDivElement>;
  progres: React.MutableRefObject<number>;
}) {
  const { invalidate } = useThree();
  useEffect(() => {
    function hitung() {
      const elemen = wadahRef.current;
      if (!elemen) return;
      const rect = elemen.getBoundingClientRect();
      const tinggiLayar = window.innerHeight || 1;
      const mentah = 1 - rect.top / tinggiLayar;
      progres.current = Math.min(1, Math.max(0, mentah));
      invalidate();
    }
    hitung();
    window.addEventListener("scroll", hitung, { passive: true });
    window.addEventListener("resize", hitung);
    return () => {
      window.removeEventListener("scroll", hitung);
      window.removeEventListener("resize", hitung);
    };
  }, [wadahRef, progres, invalidate]);
  return null;
}

/** Truk itu sendiri: rotasi idle pelan pada sumbu Y + parallax pointer (tilt X/Z
 *  dilerp menuju posisi kursor, dibatasi ±0.15 rad). */
function TrukModel() {
  const grup = useRef<Group>(null);
  const targetPointer = useRef({ x: 0, y: 0 });
  const { invalidate } = useThree();

  useEffect(() => {
    function onMove(e: PointerEvent) {
      targetPointer.current = {
        x: (e.clientX / window.innerWidth) * 2 - 1,
        y: (e.clientY / window.innerHeight) * 2 - 1,
      };
      invalidate();
    }
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => window.removeEventListener("pointermove", onMove);
  }, [invalidate]);

  useFrame((_, delta) => {
    const g = grup.current;
    if (!g) return;
    g.rotation.y += delta * 0.15; // rotasi idle pelan, berputar terus
    const tiltX = targetPointer.current.y * 0.15;
    const tiltZ = -targetPointer.current.x * 0.15;
    g.rotation.x += (tiltX - g.rotation.x) * 0.06;
    g.rotation.z += (tiltZ - g.rotation.z) * 0.06;
  });

  const bahanTanah = { color: PALET.tanah, flatShading: true, roughness: 0.9 } as const;
  const bahanKertas = { color: PALET.kertas, flatShading: true, roughness: 0.85 } as const;
  const bahanDaun = { color: PALET.daun, flatShading: true, roughness: 0.85 } as const;
  const bahanKabut = { color: PALET.kabut, flatShading: true, roughness: 0.8 } as const;

  return (
    <group ref={grup}>
      {/* bayangan tanah — ellipse datar, TANPA shadow-map */}
      <mesh position={[0, -0.01, 0]} rotation={[-Math.PI / 2, 0, 0]} scale={[1, 0.55, 1]}>
        <circleGeometry args={[1.95, 28]} />
        <meshBasicMaterial color={PALET.tanah} transparent opacity={0.14} />
      </mesh>

      {/* roda */}
      {[
        [-1.3, 0.32, 0.62],
        [-1.3, 0.32, -0.62],
        [1.0, 0.32, 0.62],
        [1.0, 0.32, -0.62],
      ].map((pos, i) => (
        <mesh key={i} position={pos as [number, number, number]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.32, 0.32, 0.28, 12]} />
          <meshStandardMaterial {...bahanTanah} />
        </mesh>
      ))}

      {/* rangka bawah */}
      <mesh position={[0, 0.55, 0]}>
        <boxGeometry args={[3.2, 0.18, 1.15]} />
        <meshStandardMaterial {...bahanTanah} />
      </mesh>

      {/* kabin */}
      <mesh position={[-1.35, 1.065, 0]}>
        <boxGeometry args={[1.05, 0.85, 1.05]} />
        <meshStandardMaterial {...bahanDaun} />
      </mesh>
      {/* kaca depan */}
      <mesh position={[-1.9, 1.12, 0]}>
        <boxGeometry args={[0.06, 0.5, 0.92]} />
        <meshStandardMaterial {...bahanKabut} />
      </mesh>

      {/* bak terbuka: lantai + dinding samping + dinding belakang */}
      <mesh position={[0.85, 0.72, 0]}>
        <boxGeometry args={[1.7, 0.16, 1.15]} />
        <meshStandardMaterial {...bahanKertas} />
      </mesh>
      <mesh position={[1.65, 1.03, 0]}>
        <boxGeometry args={[0.1, 0.55, 1.15]} />
        <meshStandardMaterial {...bahanKertas} />
      </mesh>
      <mesh position={[0.85, 1.0, 0.575]}>
        <boxGeometry args={[1.7, 0.4, 0.08]} />
        <meshStandardMaterial {...bahanKertas} />
      </mesh>
      <mesh position={[0.85, 1.0, -0.575]}>
        <boxGeometry args={[1.7, 0.4, 0.08]} />
        <meshStandardMaterial {...bahanKertas} />
      </mesh>

      {/* karung hasil panen di dalam bak */}
      {[
        { pos: [0.5, 1.075, -0.25], r: 0.4 },
        { pos: [0.92, 1.075, 0.18], r: -0.3 },
        { pos: [1.28, 1.075, -0.08], r: 0.15 },
      ].map((karung, i) => (
        <mesh key={i} position={karung.pos as [number, number, number]} rotation={[0, karung.r, 0]}>
          <cylinderGeometry args={[0.22, 0.3, 0.55, 8]} />
          <meshStandardMaterial {...bahanTanah} />
        </mesh>
      ))}

      {/* daun mengambang */}
      <mesh position={[0.85, 1.85, 0.1]} rotation={[-0.35, 0.5, 0.3]}>
        <planeGeometry args={[0.55, 0.36]} />
        <meshStandardMaterial color={PALET.daun} flatShading side={DoubleSide} />
      </mesh>
    </group>
  );
}

interface HeroTigaProps {
  aktif: boolean;
  wadahRef: React.RefObject<HTMLDivElement>;
}

export default function HeroTiga({ aktif, wadahRef }: HeroTigaProps) {
  const progresScroll = useRef(0);

  return (
    <Canvas
      frameloop="demand"
      dpr={[1, 2]}
      gl={{ antialias: true, alpha: true }}
      camera={{ fov: 38, position: [3.4, 2.05, 4.7] }}
      style={{ touchAction: "pan-y" }}
    >
      <ambientLight color={PALET.kertas} intensity={0.75} />
      <directionalLight color={PALET.kertas} position={[3, 4.5, 2.5]} intensity={1.1} />
      <Invalidator aktif={aktif} />
      <KameraRig progres={progresScroll} />
      <PendengarScroll wadahRef={wadahRef} progres={progresScroll} />
      <TrukModel />
    </Canvas>
  );
}
