import React, { useEffect, useMemo, useRef, useState } from 'react'
import { gsap } from 'gsap'
import FilamentSculpture from './FilamentSculpture.jsx'
import { AnimatedContent, GlareHover, Magnet } from './ReactBitsMotion.jsx'

const outbreaks = ['West Africa (2014-2016)', 'DRC North Kivu / Ituri (2018-2020)']

function LandingIcon({ name, size = 18 }) {
  const paths = {
    pulse: <><path d="M2 12h4l3-8 5 16 3-8h5" /></>,
    chart: <><path d="M3 3v18h18" /><path d="m7 14 4-4 4 3 6-7" /></>,
    sun: <><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" /></>,
    moon: <path d="M20.9 13A9 9 0 0 1 11 3.1 9 9 0 1 0 20.9 13Z" />,
    arrow: <><path d="M5 12h14" /><path d="m12 5 7 7-7 7" /></>,
  }
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

function OutbreakField({ series, dataset, theme, loading }) {
  const canvasRef = useRef(null)
  const drawRef = useRef(null)
  const activeIndexRef = useRef(null)
  const progressRef = useRef(1)
  const [activeIndex, setActiveIndex] = useState(null)
  const [dragging, setDragging] = useState(false)
  const points = useMemo(() => {
    if (!series?.dates?.length || !series?.cases?.length) return []
    const count = Math.min(96, series.dates.length)
    return Array.from({ length: count }, (_, index) => {
      const sourceIndex = Math.round(index * (series.dates.length - 1) / Math.max(count - 1, 1))
      return { date: series.dates[sourceIndex], value: Math.max(0, Number(series.cases[sourceIndex]) || 0) }
    })
  }, [series])
  const peakIndex = useMemo(() => points.reduce((best, point, index) => point.value > (points[best]?.value ?? -1) ? index : best, 0), [points])
  const currentIndex = activeIndex ?? peakIndex
  const current = points[currentIndex]

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return undefined
    const context = canvas.getContext('2d', { alpha: true })
    if (!context) return undefined

    const draw = (progress = progressRef.current) => {
      const bounds = canvas.getBoundingClientRect()
      const width = Math.max(1, bounds.width)
      const height = Math.max(1, bounds.height)
      const ratio = Math.min(window.devicePixelRatio || 1, 2)
      if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
        canvas.width = Math.round(width * ratio)
        canvas.height = Math.round(height * ratio)
      }
      context.setTransform(ratio, 0, 0, ratio, 0, 0)
      context.clearRect(0, 0, width, height)

      const style = getComputedStyle(canvas)
      const signal = style.getPropertyValue('--landing-accent').trim()
      const ink = style.getPropertyValue('--landing-ink').trim()
      const rule = style.getPropertyValue('--landing-rule').trim()
      const left = width * 0.045
      const right = width * 0.965
      const base = height * 0.79
      const peakHeight = height * 0.62
      const maximum = Math.max(...points.map((point) => point.value), 1)
      const visible = Math.min(points.length, Math.max(2, Math.ceil(points.length * Math.max(0.015, progress))))
      const xAt = (index, depth = 0) => left + index / Math.max(points.length - 1, 1) * (right - left) + depth * width * 0.0022
      const yAt = (index, depth = 0) => base - points[index].value / maximum * peakHeight + depth * height * 0.008

      context.lineWidth = 1
      context.strokeStyle = rule
      context.globalAlpha = 0.72
      for (let line = 0; line < 5; line += 1) {
        const y = height * (0.28 + line * 0.13)
        context.beginPath()
        context.moveTo(left, y)
        context.lineTo(right, y)
        context.stroke()
      }

      // Each contour is a real repetition of the selected outbreak's case curve.
      // Their offset makes one restrained, topographic relief instead of abstract decoration.
      for (let depth = 17; depth >= 0; depth -= 1) {
        context.beginPath()
        for (let index = 0; index < visible; index += 1) {
          const x = xAt(index, depth)
          const y = yAt(index, depth)
          if (index === 0) context.moveTo(x, y)
          else context.lineTo(x, y)
        }
        context.lineWidth = depth === 0 ? 2.8 : 1.05
        context.strokeStyle = depth === 0 ? signal : ink
        context.globalAlpha = depth === 0 ? 1 : 0.09 + (17 - depth) * 0.011
        context.stroke()
      }

      if (points.length && activeIndexRef.current !== null) {
        const index = Math.min(activeIndexRef.current, visible - 1)
        const x = xAt(index)
        const y = yAt(index)
        context.globalAlpha = 0.78
        context.strokeStyle = signal
        context.lineWidth = 1
        context.setLineDash([3, 6])
        context.beginPath()
        context.moveTo(x, Math.max(8, y - 12))
        context.lineTo(x, height * 0.91)
        context.stroke()
        context.setLineDash([])
        context.globalAlpha = 1
        context.beginPath()
        context.arc(x, y, 7, 0, Math.PI * 2)
        context.fillStyle = signal
        context.fill()
        context.beginPath()
        context.arc(x, y, 13, 0, Math.PI * 2)
        context.strokeStyle = signal
        context.lineWidth = 1.5
        context.stroke()
      }
      context.globalAlpha = 1
    }
    drawRef.current = draw
    const shouldAnimate = points.length && !window.matchMedia('(prefers-reduced-motion: reduce)').matches
    progressRef.current = shouldAnimate ? 0.035 : 1
    draw(progressRef.current)
    const resize = new ResizeObserver(() => draw())
    resize.observe(canvas)

    if (shouldAnimate) {
      const playhead = { progress: progressRef.current }
      const entrance = gsap.to(playhead, {
        progress: 1,
        duration: 1.9,
        ease: 'power3.inOut',
        onUpdate: () => {
          progressRef.current = playhead.progress
          draw(playhead.progress)
        },
      })
      return () => { entrance.kill(); resize.disconnect(); drawRef.current = null }
    }
    progressRef.current = 1
    draw(1)
    return () => { resize.disconnect(); drawRef.current = null }
  }, [points])

  useEffect(() => { drawRef.current?.() }, [theme])

  useEffect(() => {
    activeIndexRef.current = activeIndex
    drawRef.current?.()
  }, [activeIndex])

  useEffect(() => {
    setActiveIndex(points.length ? peakIndex : null)
  }, [points, peakIndex])

  const selectAt = (event) => {
    if (!points.length) return
    const bounds = event.currentTarget.getBoundingClientRect()
    const ratio = Math.max(0, Math.min(1, (event.clientX - bounds.left) / bounds.width))
    setActiveIndex(Math.round(ratio * (points.length - 1)))
  }
  const moveWithKey = (event) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key) || !points.length) return
    event.preventDefault()
    if (event.key === 'Home') setActiveIndex(0)
    else if (event.key === 'End') setActiveIndex(points.length - 1)
    else setActiveIndex(Math.max(0, Math.min(points.length - 1, currentIndex + (event.key === 'ArrowRight' ? 1 : -1))))
  }

  return <div className={`outbreak-field ${points.length ? 'has-series' : ''} ${dragging ? 'is-scrubbing' : ''}`}>
    <canvas ref={canvasRef} className="outbreak-canvas" role="img" tabIndex="0" aria-label={`Interactive view of reported Ebola cases for ${dataset}. Use left and right arrows to inspect the timeline.`} onPointerMove={(event) => { if (event.pointerType !== 'touch' || dragging) selectAt(event) }} onPointerDown={(event) => { if (event.pointerType === 'touch') { setDragging(true); event.currentTarget.setPointerCapture(event.pointerId); selectAt(event) } }} onPointerUp={() => setDragging(false)} onPointerCancel={() => setDragging(false)} onPointerLeave={() => { if (!dragging) setActiveIndex(null) }} onKeyDown={moveWithKey} />
    {!points.length && <div className="outbreak-field-empty" role="status"><span className="field-empty-mark"><LandingIcon name="chart" size={23} /></span><span>{loading ? 'Loading reported cases for this outbreak…' : 'Historical case data appears when the research API is connected.'}</span></div>}
    {points.length > 0 && <>
      <div className="field-axis field-axis-start"><span>{series.start}</span><i /></div>
      <div className="field-axis field-axis-end"><i /><span>{series.end}</span></div>
      <div className="field-readout" aria-live="polite" aria-atomic="true">
        <span>{activeIndex === null ? 'Series peak' : 'Selected observation'}</span>
        <strong>{Math.round(current?.value || 0).toLocaleString()}<small> cases</small></strong>
        <time dateTime={current?.date}>{current?.date}</time>
      </div>
    </>}
  </div>
}

export default function LandingPage({ theme, onThemeToggle, apiStatus, onEnter }) {
  const [dataset, setDataset] = useState(outbreaks[0])
  const [series, setSeries] = useState(null)
  const [loading, setLoading] = useState(true)
  const pageRef = useRef(null)
  const wipeRef = useRef(null)
  const [launching, setLaunching] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    fetch(`/api/series?dataset=${encodeURIComponent(dataset)}`, { signal: controller.signal })
      .then((response) => { if (!response.ok) throw new Error('Outbreak series unavailable'); return response.json() })
      .then((data) => setSeries(data))
      .catch((error) => { if (error.name !== 'AbortError') setSeries(null) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [dataset])

  useEffect(() => {
    const root = pageRef.current
    if (!root || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined
    const context = gsap.context(() => {
      const intro = gsap.timeline({ defaults: { ease: 'power4.out' } })
      intro.fromTo('.landing-nav', { y: -18, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.7 })
        .fromTo('.landing-title-line', { yPercent: 115, rotate: 2, autoAlpha: 0 }, { yPercent: 0, rotate: 0, autoAlpha: 1, duration: 0.9, stagger: 0.1 }, '-=0.28')
        .fromTo('.landing-deck, .landing-actions, .landing-series-control', { y: 18, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: 0.65, stagger: 0.09 }, '-=0.38')

      gsap.fromTo('.landing-hero-art',
        { clipPath: 'inset(10% 0 10% 12% round 2px)', scale: 0.94, autoAlpha: 0 },
        { clipPath: 'inset(0% 0 0% 0% round 2px)', scale: 1, autoAlpha: 1, duration: 1.2, ease: 'power3.inOut', delay: 0.32 },
      )

    }, root)
    return () => context.revert()
  }, [])

  const enter = (mode) => {
    if (launching) return
    setLaunching(true)
    if (!wipeRef.current || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      onEnter(mode)
      return
    }
    gsap.to(wipeRef.current, { scaleY: 1, transformOrigin: 'bottom center', duration: 0.55, ease: 'power3.inOut', onComplete: () => onEnter(mode) })
  }

  return <main ref={pageRef} className="brand-landing">
    <section className="landing-hero" aria-labelledby="landing-title">
      <header className="landing-nav">
        <a className="landing-wordmark" href="#landing-title" aria-label="EbolaVF home">
          <span className="landing-mark"><LandingIcon name="pulse" size={18} /></span>
          <span>EBOLA<span>VF</span></span>
        </a>
        <div className="landing-nav-meta"><span className={`landing-status-dot ${apiStatus ? 'is-ready' : ''}`} /><span>{apiStatus ? 'Research API ready' : 'Research prototype'}</span></div>
        <button className="landing-theme-toggle" type="button" aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`} onClick={onThemeToggle}><LandingIcon name={theme === 'dark' ? 'sun' : 'moon'} size={18} /><span>{theme === 'dark' ? 'Light' : 'Dark'} mode</span></button>
      </header>

      <div className="landing-main">
        <div className="landing-copy">
          <h1 id="landing-title" className="landing-title">
            <span className="landing-title-line"><span>Ebola</span></span>
            <span className="landing-title-line"><span>Prediction</span></span>
            <span className="landing-title-line landing-title-line-last"><span>and Forecasting</span></span>
          </h1>
          <p className="landing-deck">Patient risk and outbreak trends, brought into one research workspace.</p>
          <div className="landing-actions">
            <Magnet className="landing-magnet" strength={7} range={80}>
              <GlareHover as="button" className="landing-primary" type="button" disabled={launching} onClick={() => enter('risk')}><span>Explore patient risk</span><LandingIcon name="arrow" size={18} /></GlareHover>
            </Magnet>
            <button className="landing-secondary" type="button" disabled={launching} onClick={() => enter('forecast')}><LandingIcon name="chart" size={17} /><span>Open forecasting</span></button>
          </div>
        </div>

        <div className="landing-hero-art"><FilamentSculpture theme={theme} /></div>
      </div>
      <div className="landing-bottomline"><span>Historical outbreak data · Experimental research models</span><a href="#landing-routes">Scroll to choose a workspace <span aria-hidden="true">↓</span></a></div>
    </section>

    <section className="landing-history" aria-labelledby="history-title"><h2 id="history-title">Historical outbreak observations</h2>
        <div className="landing-hero-art">
          <div className="landing-art-label"><span>REPORTED CASES</span><span>{loading ? 'Loading series' : series ? `${series.observations.toLocaleString()} observations` : 'Data unavailable'}</span></div>
          <OutbreakField series={series} dataset={dataset} theme={theme} loading={loading} />
          <div className="landing-series-control" role="group" aria-label="Choose historical outbreak series">
            {outbreaks.map((name, index) => <button type="button" key={name} className={dataset === name ? 'selected' : ''} aria-pressed={dataset === name} onClick={() => { if (dataset !== name) { setSeries(null); setLoading(true); setDataset(name) } }}>
              <span className="series-radio"><i /></span><span>{index === 0 ? 'West Africa' : 'North Kivu / Ituri'}</span><small>{index === 0 ? '2014—16' : '2018—20'}</small>
            </button>)}
          </div>
        </div>
    </section>

    <section className="landing-routes" id="landing-routes" aria-labelledby="landing-routes-title">
      <AnimatedContent as="div" className="landing-routes-inner" motion="data">
        <div className="landing-routes-heading"><h2 id="landing-routes-title">Choose your workspace.</h2></div>
        <div className="landing-route-list">
          <button className="landing-route-row" type="button" disabled={launching} onClick={() => enter('risk')}><span className="route-icon"><LandingIcon name="pulse" size={20} /></span><span className="route-copy"><strong>Patient risk</strong><small>Review clinical and exposure factors in an individual assessment.</small></span><LandingIcon name="arrow" size={21} /></button>
          <button className="landing-route-row" type="button" disabled={launching} onClick={() => enter('forecast')}><span className="route-icon"><LandingIcon name="chart" size={20} /></span><span className="route-copy"><strong>Ebola forecasting</strong><small>Explore reported outbreak cases and compare experimental model projections.</small></span><LandingIcon name="arrow" size={21} /></button>
        </div>
      </AnimatedContent>
      <footer className="landing-footer"><span>EBOLAVF</span><p>Research prototype. Outputs are experimental and are not for clinical or public health decisions.</p></footer>
    </section>
    <div ref={wipeRef} className="landing-wipe" aria-hidden="true" />
  </main>
}
