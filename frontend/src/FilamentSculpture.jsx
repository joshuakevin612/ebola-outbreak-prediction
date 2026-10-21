import React, { useEffect, useRef, useState } from 'react'

// A tube swept through a curled three-dimensional centreline, with surface studs.
const center = (t) => {
  const a = t * Math.PI * 2.15
  return [Math.sin(a) * (0.72 + t * 0.3), (t - 0.5) * 3.5, Math.cos(a) * 0.48]
}
const mesh = Array.from({ length: 181 }, (_, i) => {
  const t = i / 180, p = center(t), q = center(Math.min(1, t + 0.001)), prev = center(Math.max(0, t - 0.001))
  const tangent = q.map((v, j) => v - prev[j])
  const length = Math.hypot(...tangent)
  const axis = tangent.map(v => v / length)
  const nLength = Math.hypot(axis[1], axis[0])
  const n = [axis[1] / nLength, -axis[0] / nLength, 0]
  const b = [axis[1] * n[2] - axis[2] * n[1], axis[2] * n[0] - axis[0] * n[2], axis[0] * n[1] - axis[1] * n[0]]
  const radius = 0.105 * Math.min(1, Math.sqrt(Math.max(0.015, Math.sin(Math.PI * t))) * 3)
  return Array.from({ length: 16 }, (_, j) => {
    const a = j / 16 * Math.PI * 2
    const normal = n.map((v, k) => v * Math.cos(a) + b[k] * Math.sin(a))
    return { point: p.map((v, k) => v + normal[k] * radius), normal }
  })
})

export default function FilamentSculpture({ theme }) {
  const canvasRef = useRef(null)
  const view = useRef({ x: -0.12, y: 0.4, zoom: 1, drag: null, hoverX: 0, hoverY: 0, targetX: 0, targetY: 0 })
  const repaint = useRef(() => {})
  const [available, setAvailable] = useState(true)

  useEffect(() => {
    const canvas = canvasRef.current, ctx = canvas.getContext('2d')
    if (!ctx) { setAvailable(false); return }
    let frame, visible = true
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
    const rotate = ([x, y, z]) => {
      const v = view.current, cy = Math.cos(v.y + v.hoverY), sy = Math.sin(v.y + v.hoverY), cx = Math.cos(v.x + v.hoverX), sx = Math.sin(v.x + v.hoverX)
      const rx = x * cy + z * sy, rz = z * cy - x * sy
      return [rx, y * cx - rz * sx, y * sx + rz * cx]
    }
    const draw = () => {
      const { width, height } = canvas.getBoundingClientRect()
      if (!width || !height) return
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      if (canvas.width !== Math.round(width * dpr) || canvas.height !== Math.round(height * dpr)) {
        canvas.width = Math.round(width * dpr); canvas.height = Math.round(height * dpr)
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, width, height)
      const scale = Math.min(width / 3.4, height / 4.5) * view.current.zoom
      const project = ([x, y, z]) => { const p = 6 / (6 - z); return [width / 2 + x * scale * p, height / 2 + y * scale * p] }
      const rings = mesh.map(ring => ring.map(v => ({ p: rotate(v.point), n: rotate(v.normal) })))
      const faces = []
      for (let i = 0; i < rings.length - 1; i++) for (let j = 0; j < 16; j++) {
        const k = (j + 1) % 16
        const vertices = [rings[i][j], rings[i + 1][j], rings[i + 1][k], rings[i][k]]
        faces.push({ vertices, depth: vertices.reduce((s, v) => s + v.p[2], 0) / 4, stud: i % 4 === 0 && j % 2 === 0 })
      }
      faces.sort((a, b) => a.depth - b.depth)
      for (const face of faces) {
        const normal = face.vertices[0].n
        const light = Math.max(0, normal[0] * -0.45 + normal[1] * -0.45 + normal[2] * 0.76)
        const sheen = Math.pow(light, 12)
        ctx.fillStyle = `hsl(174  ${28 + light * 16}% ${ (theme === 'light' ? 19 : 18) + light * 46 + sheen * 19}%)`
        ctx.beginPath()
        face.vertices.forEach((v, i) => { const p = project(v.p); i ? ctx.lineTo(...p) : ctx.moveTo(...p) })
        ctx.closePath(); ctx.fill(); ctx.strokeStyle = ctx.fillStyle; ctx.lineWidth = 0.5; ctx.stroke()
        if (face.stud && normal[2] > 0.05) {
          const start = face.vertices[0].p, end = start.map((v, k) => v + normal[k] * 0.045)
          const p = project(start), q = project(end)
          ctx.strokeStyle = `hsl(174 35% ${35 + light * 40}%)`; ctx.lineWidth = Math.max(1, scale * 0.018)
          ctx.beginPath(); ctx.moveTo(...p); ctx.lineTo(...q); ctx.stroke()
          ctx.beginPath(); ctx.arc(...q, Math.max(1, scale * 0.016), 0, Math.PI * 2); ctx.fillStyle = ctx.strokeStyle; ctx.fill()
        }
      }
    }
    const tick = () => {
      frame = null
      if (!visible || document.hidden) return
      const v = view.current
      const ease = reducedMotion.matches ? 1 : 0.12
      v.hoverX += (v.targetX - v.hoverX) * ease
      v.hoverY += (v.targetY - v.hoverY) * ease
      draw()
      if (Math.abs(v.targetX - v.hoverX) + Math.abs(v.targetY - v.hoverY) > 0.001) frame = requestAnimationFrame(tick)
    }
    repaint.current = () => { if (frame == null) frame = requestAnimationFrame(tick) }
    const resize = new ResizeObserver(draw); resize.observe(canvas)
    const observer = new IntersectionObserver(entries => { visible = entries[0].isIntersecting }); observer.observe(canvas)
    draw()
    return () => { cancelAnimationFrame(frame); resize.disconnect(); observer.disconnect(); repaint.current = () => {} }
  }, [theme])
  const zoom = amount => { view.current.zoom = Math.max(0.65, Math.min(1.4, view.current.zoom + amount)); repaint.current() }
  const reset = () => { Object.assign(view.current, { x: -0.12, y: 0.4, zoom: 1 }); repaint.current() }
  return <section className="filament-sculpture" aria-label="Interactive Ebola filament sculpture">
    <div className="sculpture-caption"><strong>Ebola filament</strong><span>Illustrative 3D study</span></div>
    <canvas ref={canvasRef} className="filament-canvas" tabIndex={0} role="img" aria-label="Three-dimensional curled Ebola filament. Move your mouse to tilt, drag to rotate, use arrow keys to turn, plus and minus to zoom, or Home to reset."
      onPointerDown={e => { view.current.drag = [e.clientX, e.clientY]; e.currentTarget.setPointerCapture(e.pointerId) }}
      onPointerMove={e => {
        const v = view.current, d = v.drag
        if (d) {
          v.y += (e.clientX - d[0]) * 0.009; v.x += (e.clientY - d[1]) * 0.009
          v.drag = [e.clientX, e.clientY]
        } else if (e.pointerType === 'mouse' || e.pointerType === 'pen') {
          const bounds = e.currentTarget.getBoundingClientRect()
          v.targetY = ((e.clientX - bounds.left) / bounds.width - 0.5) * 1.4
          v.targetX = -((e.clientY - bounds.top) / bounds.height - 0.5) * 0.8
        }
        repaint.current()
      }}
      onPointerLeave={() => { view.current.targetX = 0; view.current.targetY = 0; repaint.current() }}
      onPointerUp={() => { view.current.drag = null }} onPointerCancel={() => { view.current.drag = null }} onLostPointerCapture={() => { view.current.drag = null }}
      onKeyDown={e => { if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '=', '-', 'Home'].includes(e.key)) return; e.preventDefault(); if (e.key === 'Home') reset(); else if (['+', '=', '-'].includes(e.key)) zoom(e.key === '-' ? -0.1 : 0.1); else { view.current[e.key === 'ArrowLeft' || e.key === 'ArrowRight' ? 'y' : 'x'] += ['ArrowLeft', 'ArrowUp'].includes(e.key) ? -0.12 : 0.12; repaint.current() } }} />
    {!available && <p>Interactive drawing is unavailable in this browser.</p>}
    <div className="sculpture-controls"><span>Move to tilt · Drag to rotate</span><div><button type="button" onClick={() => zoom(-0.1)} aria-label="Zoom out">−</button><button type="button" onClick={() => zoom(0.1)} aria-label="Zoom in">+</button></div></div>
  </section>
}
