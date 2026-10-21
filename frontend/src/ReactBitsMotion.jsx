import { useEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

// Adapted from React Bits AnimatedContent, GlareHover, and Magnet.
// https://reactbits.dev/animations/animated-content
// https://reactbits.dev/animations/glare-hover
// https://reactbits.dev/animations/magnet
const revealPresets = {
  profile: { x: -30, y: 18, scale: 0.99 },
  symptoms: { x: 0, y: 42, scale: 0.985 },
  encounter: { x: 30, y: 22, scale: 0.99 },
  controls: { x: 0, y: 32, scale: 0.985, clip: 'inset(0 0 12% 0 round 10px)' },
  data: { x: 0, y: 44, scale: 0.985, clip: 'inset(0 0 14% 0 round 12px)' },
  results: { x: 0, y: 28, scale: 0.99 },
}

export function AnimatedContent({ as: Element = 'section', className = '', motion = 'symptoms', children, ...props }) {
  const ref = useRef(null)

  useEffect(() => {
    const element = ref.current
    if (!element || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const preset = revealPresets[motion] || revealPresets.symptoms
    const context = gsap.context(() => {
      gsap.fromTo(element,
        { autoAlpha: 0, x: preset.x, y: preset.y, scale: preset.scale, clipPath: preset.clip || 'inset(0 0 0 0)' },
        {
          autoAlpha: 1,
          x: 0,
          y: 0,
          scale: 1,
          clipPath: 'inset(0 0 0 0)',
          duration: 1.05,
          ease: 'power3.out',
          clearProps: 'transform,opacity,visibility,clipPath',
          scrollTrigger: {
            trigger: element,
            start: 'top 86%',
            once: true,
            invalidateOnRefresh: true,
          },
        },
      )
    }, element)

    return () => context.revert()
  }, [motion])

  return <Element ref={ref} className={`animated-content ${className}`} {...props}>{children}</Element>
}

export function GlareHover({
  as: Element = 'div',
  children,
  width = 'auto',
  height = 'auto',
  background = 'transparent',
  borderRadius = '8px',
  borderColor = 'transparent',
  glareColor = 'color-mix(in oklab, var(--accent-bright) 42%, transparent)',
  glareOpacity = 0.4,
  glareAngle = -45,
  glareSize = 260,
  transitionDuration = 720,
  playOnce = false,
  className = '',
  style = {},
  ...props
}) {
  const hex = glareColor.replace('#', '')
  let rgba = glareColor
  if (/^[0-9A-Fa-f]{6}$/.test(hex)) {
    const [r, g, b] = [0, 2, 4].map((index) => parseInt(hex.slice(index, index + 2), 16))
    rgba = `rgba(${r}, ${g}, ${b}, ${glareOpacity})`
  } else if (/^[0-9A-Fa-f]{3}$/.test(hex)) {
    const [r, g, b] = [0, 1, 2].map((index) => parseInt(hex[index] + hex[index], 16))
    rgba = `rgba(${r}, ${g}, ${b}, ${glareOpacity})`
  }

  const vars = {
    '--gh-width': width,
    '--gh-height': height,
    '--gh-bg': background,
    '--gh-br': borderRadius,
    '--gh-angle': `${glareAngle}deg`,
    '--gh-duration': `${transitionDuration}ms`,
    '--gh-size': `${glareSize}%`,
    '--gh-rgba': rgba,
    '--gh-border': borderColor,
  }

  return <Element className={`glare-hover ${playOnce ? 'glare-hover--play-once' : ''} ${className}`} style={{ ...vars, ...style }} {...props}>{children}</Element>
}

export function Magnet({ children, className = '', innerClassName = '', range = 104, strength = 5, disabled = false }) {
  const ref = useRef(null)

  useEffect(() => {
    const element = ref.current
    const canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches
    if (!element || disabled || !canHover || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const moveX = gsap.quickTo(element, 'x', { duration: 0.3, ease: 'power3.out' })
    const moveY = gsap.quickTo(element, 'y', { duration: 0.3, ease: 'power3.out' })
    const onPointerMove = (event) => {
      const rect = element.getBoundingClientRect()
      const dx = event.clientX - (rect.left + rect.width / 2)
      const dy = event.clientY - (rect.top + rect.height / 2)
      if (Math.abs(dx) < rect.width / 2 + range && Math.abs(dy) < rect.height / 2 + range) {
        moveX(gsap.utils.clamp(-8, 8, dx / strength))
        moveY(gsap.utils.clamp(-6, 6, dy / strength))
      } else {
        moveX(0)
        moveY(0)
      }
    }
    const onPointerLeave = () => { moveX(0); moveY(0) }

    window.addEventListener('pointermove', onPointerMove, { passive: true })
    window.addEventListener('pointerleave', onPointerLeave)
    return () => {
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('pointerleave', onPointerLeave)
      gsap.killTweensOf(element)
    }
  }, [disabled, range, strength])

  return <span ref={ref} className={`magnet-wrap ${className}`}><span className={`magnet-inner ${innerClassName}`}>{children}</span></span>
}

