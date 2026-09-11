import { useEffect, useMemo, useState } from 'react'
import './App.css'

/* ==========================================================================
   DukaanAI — premium concept UI
   One long, airy page. Floating nav. Stock Advisor as the centerpiece.
   ========================================================================== */

const NAV_LINKS = [
  { id: 'overview', label: 'Overview', dot: 'var(--lavender)' },
  { id: 'stock', label: 'Stock Advisor', dot: 'var(--coral)' },
  { id: 'insights', label: 'AI Insights', dot: 'var(--blue)' },
  { id: 'sales', label: 'Sales Story', dot: 'var(--mint)' },
  { id: 'ask', label: 'Ask DukaanAI', dot: 'var(--yellow)' },
]

/* --- tiny inline icons --------------------------------------------------- */

const Icon = {
  sparkle: (props) => (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" {...props}>
      <path d="M12 2l1.9 5.7a2 2 0 0 0 1.3 1.3L21 11l-5.8 1.9a2 2 0 0 0-1.3 1.3L12 20l-1.9-5.8a2 2 0 0 0-1.3-1.3L3 11l5.8-2a2 2 0 0 0 1.3-1.3L12 2z" />
      <circle cx="19" cy="4.5" r="1.3" opacity=".7" />
    </svg>
  ),
  arrow: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  ),
  cart: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M3 4h2l2.4 12.2a1.5 1.5 0 0 0 1.5 1.3h7.9a1.5 1.5 0 0 0 1.5-1.2L20 8H6" />
      <circle cx="10" cy="21" r="1.4" />
      <circle cx="17.5" cy="21" r="1.4" />
    </svg>
  ),
  box: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M21 8l-9-5-9 5v8l9 5 9-5V8z" />
      <path d="M3 8l9 5 9-5M12 13v8" />
    </svg>
  ),
  mic: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <rect x="9" y="2.5" width="6" height="11.5" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18.5V21.5" />
    </svg>
  ),
  wave: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true" {...props}>
      <path d="M4 10v4M8 7v10M12 4v16M16 7v10M20 10v4" />
    </svg>
  ),
  up: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M12 19V5M6 11l6-6 6 6" />
    </svg>
  ),
  money: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <rect x="2.5" y="6" width="19" height="12" rx="2.5" />
      <circle cx="12" cy="12" r="2.6" />
    </svg>
  ),
  alert: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M12 3.5 2.8 19.5h18.4L12 3.5z" />
      <path d="M12 10v4.5M12 17.4v.2" />
    </svg>
  ),
  plus: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" aria-hidden="true" {...props}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  ),
  rupee: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M7 4h10M7 9h10M15.5 4c0 5-4 5-8.5 5l7 11" />
    </svg>
  ),
}

/* --- background graphics -------------------------------------------------- */

const DOTS = [
  { top: '14%', left: '6%' }, { top: '24%', left: '88%' }, { top: '38%', left: '14%' },
  { top: '52%', left: '80%' }, { top: '64%', left: '8%' }, { top: '8%', left: '62%' },
  { top: '76%', left: '90%' }, { top: '86%', left: '18%' }, { top: '46%', left: '48%' },
  { top: '94%', left: '58%' }, { top: '30%', left: '38%' }, { top: '70%', left: '66%' },
]

const PARTICLES = [
  { top: '20%', left: '12%', d: '0s', s: 5 },
  { top: '34%', left: '84%', d: '1.4s', s: 4 },
  { top: '56%', left: '6%', d: '2.6s', s: 6 },
  { top: '66%', left: '92%', d: '0.8s', s: 4 },
  { top: '82%', left: '10%', d: '2s', s: 5 },
  { top: '90%', left: '86%', d: '3.2s', s: 6 },
  { top: '12%', left: '72%', d: '1s', s: 4 },
  { top: '46%', left: '58%', d: '2.2s', s: 5 },
]

function BackgroundFX() {
  return (
    <div className="bg-fx" aria-hidden="true">
      <div className="bg-blob bg-blob-lavender" />
      <div className="bg-blob bg-blob-mint" />
      <div className="bg-blob bg-blob-coral" />
      <div className="bg-blob bg-blob-yellow" />
      <div className="bg-grid" />
      {DOTS.map((p, i) => (
        <span key={i} className="bg-dot" style={{ top: p.top, left: p.left, animationDelay: `${i * 0.7}s` }} />
      ))}
      {PARTICLES.map((p, i) => (
        <span
          key={i}
          className="bg-particle"
          style={{ top: p.top, left: p.left, animationDelay: p.d, width: p.s, height: p.s }}
        />
      ))}
      <svg className="bg-doodle bg-doodle-cart" viewBox="0 0 24 24">
        <path d="M3 4h2l2.4 12.2a1.5 1.5 0 0 0 1.5 1.3h7.9a1.5 1.5 0 0 0 1.5-1.2L20 8H6" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
      <svg className="bg-doodle bg-doodle-box" viewBox="0 0 24 24">
        <path d="M21 8l-9-5-9 5v8l9 5 9-5V8zM3 8l9 5 9-5M12 13v8" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
      </svg>
      <svg className="bg-doodle bg-doodle-wave" viewBox="0 0 120 32">
        <path d="M2 26 Q 12 6 22 22 T 42 18 T 62 24 T 82 12 T 102 20 T 118 10" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    </div>
  )
}

/* --- floating nav ---------------------------------------------------------- */

function FloatingNav() {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && setOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const go = (id) => {
    setOpen(false)
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <nav className={`float-nav ${open ? 'open' : ''}`}>
      {open && <button className="float-nav-scrim" onClick={() => setOpen(false)} aria-label="Close navigation" />}
      <div className="float-nav-panel" role="menu">
        <span className="float-nav-title">DukaanAI</span>
        {NAV_LINKS.map((l) => (
          <button key={l.id} role="menuitem" className="float-nav-link" onClick={() => go(l.id)}>
            <span className="float-nav-dot" style={{ background: l.dot }} />
            {l.label}
            <Icon.arrow className="float-nav-arrow" />
          </button>
        ))}
        <button role="menuitem" className="float-nav-cta" onClick={() => go('ask')}>
          <Icon.sparkle className="float-nav-cta-icon" />
          Talk to DukaanAI
        </button>
      </div>
      <button
        className="float-nav-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-label={open ? 'Close navigation' : 'Open navigation'}
      >
        <span className={`float-nav-burger ${open ? 'x' : ''}`}>
          <span /><span /><span />
        </span>
        <span className="float-nav-label">Menu</span>
      </button>
    </nav>
  )
}

/* --- hero ------------------------------------------------------------------- */

function Hero() {
  return (
    <section className="hero" id="overview">
      <div className="hero-copy">
        <span className="eyebrow">
          <Icon.sparkle className="eyebrow-icon" />
          Your AI co-shopkeeper
        </span>
        <h1 className="hero-title">
          Your shop.
          <br />
          <span className="hero-title-accent">Smarter every day.</span>
        </h1>
        <p className="hero-sub">
          DukaanAI understands your sales, stock and customers — and helps you decide what to do next.
        </p>
        <div className="hero-actions">
          <button className="btn btn-primary">
            Explore my shop
            <Icon.arrow className="btn-arrow" />
          </button>
          <button className="btn btn-ghost">
            <Icon.sparkle className="btn-sparkle" />
            Talk to DukaanAI
          </button>
        </div>
      </div>

      <div className="hero-art">
        {/* --- shop awning --- */}
        <div className="shop-awning">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <span key={i} className={`awning-stripe ${i % 2 ? 'alt' : ''}`} />
          ))}
        </div>
        {/* --- shop front --- */}
        <div className="shop-front">
          <div className="shop-shelves">
            <span className="jar jar-mint"><i /></span>
            <span className="jar jar-yellow"><i /></span>
            <span className="jar jar-lavender"><i /></span>
            <span className="jar jar-coral"><i /></span>
          </div>
          <div className="shop-counter">
            <span className="shop-scale" />
            <span className="shop-til">
              <Icon.money className="shop-til-icon" />
            </span>
          </div>
          <div className="shop-signboard">Sharma Kirana</div>
        </div>
        {/* --- floating AI chips --- */}
        <div className="float-chip float-chip-top">
          <span className="float-chip-dot" />
          <Icon.sparkle className="float-chip-spark" />
          AI watching your shelf
        </div>
        <div className="float-chip float-chip-bottom">
          <Icon.up className="float-chip-up" />
          +18% this week
        </div>
        <span className="hero-glow" aria-hidden="true" />
      </div>
    </section>
  )
}

/* --- AI Stock Advisor (centerpiece) ------------------------------------------ */

const ADVISOR_STAGES = [
  { key: 'today', label: 'TODAY', sub: '18 on shelf' },
  { key: 'order', label: 'ORDER', sub: 'today · 35 packs', active: true },
  { key: 'delivery', label: 'DELIVERY', sub: 'in ~2 days' },
  { key: 'risk', label: 'STOCKOUT RISK', sub: 'in 1.5 days' },
]

function StockAdvisor() {
  return (
    <section className="advisor" id="stock">
      <span className="section-tag">AI Stock Advisor</span>
      <h2 className="section-title">
        Know when you&rsquo;ll run out — <em>before you do.</em>
      </h2>

      <article className="advisor-card">
        {/* product header */}
        <header className="advisor-head">
          <div className="advisor-product">
            <span className="advisor-product-glyph">
              <Icon.box />
            </span>
            <div>
              <h3 className="advisor-product-name">MAGGI 2-MINUTE NOODLES</h3>
              <p className="advisor-product-meta">Masala · 70g · Nestlé</p>
            </div>
          </div>
          <span className="advisor-verdict">
            <span className="advisor-verdict-pulse" />
            Recommended action
            <strong>ORDER TODAY</strong>
          </span>
        </header>

        {/* stats */}
        <div className="advisor-stats">
          <div className="stat">
            <span className="stat-label">Current stock</span>
            <span className="stat-value">18 <small>packs</small></span>
          </div>
          <div className="stat">
            <span className="stat-label">Selling</span>
            <span className="stat-value">
              12<small>/day</small>
              <em className="stat-trend"><Icon.up className="stat-trend-icon" />22%</em>
            </span>
          </div>
          <div className="stat stat-warn">
            <span className="stat-label">Expected to run out</span>
            <span className="stat-value">in 1.5 days</span>
          </div>
          <div className="stat">
            <span className="stat-label">Supplier delivery</span>
            <span className="stat-value">~2 days</span>
          </div>
          <div className="stat stat-action">
            <span className="stat-label">Recommended quantity</span>
            <span className="stat-value">35 <small>packs</small></span>
          </div>
        </div>

        {/* timeline */}
        <div className="advisor-timeline">
          <div className="advisor-track">
            <span className="advisor-track-fill" />
            <span className="advisor-track-marker" />
          </div>
          <ol className="advisor-stages">
            {ADVISOR_STAGES.map((s) => (
              <li key={s.key} className={`advisor-stage ${s.active ? 'active' : ''} ${s.key === 'risk' ? 'risk' : ''}`}>
                <span className="advisor-stage-label">{s.label}</span>
                <span className="advisor-stage-sub">{s.sub}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* AI explanation */}
        <p className="advisor-explain">
          <Icon.sparkle className="advisor-explain-spark" />
          Demand is rising faster than usual. Ordering today keeps a safety buffer before your next delivery.
        </p>
      </article>
    </section>
  )
}

/* --- AI insights -------------------------------------------------------------- */

const INSIGHTS = [
  {
    tone: 'mint',
    icon: Icon.up,
    title: 'Demand is rising',
    line: 'Cold drinks are selling 30% faster since Monday — you may need a bigger order.',
  },
  {
    tone: 'blue',
    icon: Icon.money,
    title: '₹6,240 tied up in slow stock',
    line: 'Three shelf items haven’t moved in 3 weeks. Consider a combo offer.',
  },
  {
    tone: 'coral',
    icon: Icon.alert,
    title: '5 products need attention',
    line: 'Two are about to run out, three are overstocked. One tap to fix all five.',
  },
]

function Insights() {
  return (
    <section className="insights" id="insights">
      <span className="section-tag">AI Insights</span>
      <h2 className="section-title">Three things worth knowing today.</h2>
      <div className="insight-row">
        {INSIGHTS.map((ins, i) => (
          <article key={i} className={`insight-bubble insight-${ins.tone}`}>
            <span className="insight-icon"><ins.icon /></span>
            <h3 className="insight-title">{ins.title}</h3>
            <p className="insight-line">{ins.line}</p>
            <button className="insight-more">
              See why
              <Icon.arrow className="insight-more-arrow" />
            </button>
          </article>
        ))}
      </div>
    </section>
  )
}

/* --- sales story ----------------------------------------------------------------- */

const SALES_DATA = [4100, 4300, 4200, 4650, 4800, 4700, 5150, 5350, 5200, 5650, 5850, 6100]

function smoothPath(values, w, h, pad) {
  const min = Math.min(...values)
  const max = Math.max(...values)
  const px = (i) => pad + (i / (values.length - 1)) * (w - pad * 2)
  const py = (v) => h - pad - ((v - min) / (max - min)) * (h - pad * 2)
  const pts = values.map((v, i) => [px(i), py(v)])
  let d = `M ${pts[0][0]},${pts[0][1]}`
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1]
    const [x1, y1] = pts[i]
    const cx = (x0 + x1) / 2
    d += ` C ${cx},${y0} ${cx},${y1} ${x1},${y1}`
  }
  return { d, pts }
}

function SalesStory() {
  const W = 960
  const H = 340
  const PAD = 34
  const { d, pts } = useMemo(() => smoothPath(SALES_DATA, W, H, PAD), [])
  const area = `${d} L ${pts[pts.length - 1][0]},${H - 8} L ${pts[0][0]},${H - 8} Z`

  return (
    <section className="sales" id="sales">
      <div className="sales-copy">
        <span className="section-tag">Sales Story</span>
        <h2 className="section-title">Your shop is growing.</h2>
        <p className="sales-statement">
          Sales are up <strong>18%</strong> compared with last week.
        </p>
        <div className="sales-note">
          <span className="sales-note-dot" />
          Best week in the last three months — Sunday evening alone crossed ₹1,100.
        </div>
      </div>

      <div className="sales-chart-card">
        <div className="sales-chart-head">
          <span className="sales-amount">₹6,100</span>
          <span className="sales-chip"><Icon.up className="sales-chip-icon" />18%</span>
        </div>
        <svg className="sales-chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Weekly sales, rising for twelve weeks">
          <defs>
            <linearGradient id="sales-line" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="var(--lavender)" />
              <stop offset="55%" stopColor="var(--blue)" />
              <stop offset="100%" stopColor="var(--mint-deep)" />
            </linearGradient>
            <linearGradient id="sales-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(79,125,249,0.22)" />
              <stop offset="100%" stopColor="rgba(79,125,249,0)" />
            </linearGradient>
          </defs>

          {[0.25, 0.5, 0.75].map((f) => (
            <line key={f} className="sales-grid" x1={PAD} x2={W - PAD} y1={PAD + f * (H - PAD * 2)} y2={PAD + f * (H - PAD * 2)} />
          ))}

          <path d={area} fill="url(#sales-fill)" className="sales-area" />
          <path d={d} fill="none" stroke="url(#sales-line)" strokeWidth="4" strokeLinecap="round" className="sales-line" />

          {pts.map(([x, y], i) => (
            <circle key={i} className="sales-point" cx={x} cy={y} r={i === pts.length - 1 ? 7 : 4.5} />
          ))}
          <circle className="sales-last-glow" cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]} r="7" />
        </svg>
        <div className="sales-axis">
          <span>12 wks ago</span>
          <span>8 wks</span>
          <span>4 wks</span>
          <span>This week</span>
        </div>
      </div>
    </section>
  )
}

/* --- voice AI ------------------------------------------------------------------ */

const VOICE_EXAMPLES = [
  { text: '“What should I order tomorrow?”', pos: 'a' },
  { text: '“Who owes me money?”', pos: 'b' },
  { text: '“How much Maggi did I sell this week?”', pos: 'c' },
]

function VoiceAI() {
  return (
    <section className="voice" id="ask">
      <div className="voice-stage">
        <div className="voice-orb">
          <span className="voice-wave w1" />
          <span className="voice-wave w2" />
          <span className="voice-wave w3" />
          <span className="voice-core">
            <Icon.mic className="voice-mic" />
          </span>
        </div>
        <div className="voice-commands">
          {VOICE_EXAMPLES.map((v) => (
            <span key={v.pos} className={`voice-command voice-command-${v.pos}`}>{v.text}</span>
          ))}
        </div>
      </div>
      <span className="section-tag">Voice AI</span>
      <h2 className="section-title">Just ask.</h2>
      <p className="voice-sub">
        No forms, no menus. Speak in Hindi, English or Hinglish — DukaanAI answers in seconds.
      </p>
      <button className="btn btn-primary voice-btn">
        <Icon.wave className="btn-wave" />
        Hold to talk
      </button>
    </section>
  )
}

/* --- quick actions ---------------------------------------------------------------- */

const ACTIONS = [
  { label: 'New Sale', tone: 'mint', icon: Icon.plus },
  { label: 'Add Stock', tone: 'blue', icon: Icon.box },
  { label: 'Record Payment', tone: 'yellow', icon: Icon.rupee },
  { label: 'Ask DukaanAI', tone: 'lavender', icon: Icon.sparkle, sparkle: true },
]

function QuickActions() {
  return (
    <section className="actions">
      <div className="action-row">
        {ACTIONS.map((a) => (
          <button key={a.label} className={`action-chip action-${a.tone} ${a.sparkle ? 'action-sparkle' : ''}`}>
            <span className="action-icon"><a.icon /></span>
            {a.label}
          </button>
        ))}
      </div>
    </section>
  )
}

/* --- closing ------------------------------------------------------------------------ */

function Closing() {
  return (
    <section className="closing">
      <div className="closing-illustration" aria-hidden="true">
        <svg viewBox="0 0 420 150" className="closing-svg">
          <path className="closing-line l1" d="M10 130 C 80 128, 120 96, 180 92 S 300 60, 410 22" fill="none" stroke="var(--mint)" strokeWidth="2.5" strokeLinecap="round" />
          <path className="closing-line l2" d="M10 138 C 90 136, 150 118, 220 112 S 330 92, 410 64" fill="none" stroke="var(--lavender)" strokeWidth="2" strokeLinecap="round" opacity=".55" />
          <g className="closing-box b1" fill="none" stroke="var(--ink)" strokeWidth="2.2" strokeLinejoin="round">
            <path d="M96 78l26-13 26 13v26l-26 13-26-13z M96 78l26 13 26-13 M122 91v26" />
          </g>
          <g className="closing-box b2" fill="none" stroke="var(--ink)" strokeWidth="2.2" strokeLinejoin="round">
            <path d="M196 60l20-10 20 10v20l-20 10-20-10z M196 60l20 10 20-10 M216 70v20" />
          </g>
          <g className="closing-box b3" fill="none" stroke="var(--ink)" strokeWidth="2.2" strokeLinejoin="round">
            <path d="M268 44l14-7 14 7v14l-14 7-14-7z M268 44l14 7 14-7 M282 51v14" />
          </g>
          <g stroke="var(--ink)" strokeWidth="2" strokeLinecap="round">
            <path className="closing-arrow" d="M355 40l22-20M377 20h-11M377 20v11" />
          </g>
        </svg>
      </div>
      <h2 className="closing-title">
        Less guessing.
        <br />
        <span className="closing-title-accent">More growing.</span>
      </h2>
      <p className="closing-sub">DukaanAI turns everyday shop data into smarter decisions.</p>
      <button className="btn btn-primary">
        Open my DukaanAI
        <Icon.arrow className="btn-arrow" />
      </button>
    </section>
  )
}

/* --- footer --------------------------------------------------------------------------- */

function Footer() {
  return (
    <footer className="footer">
      <span className="footer-brand"><Icon.sparkle className="footer-spark" /> DukaanAI</span>
      <span className="footer-note">Made in India, for every neighbourhood shop.</span>
      <span className="footer-links">
        <button>Privacy</button>
        <button>Support</button>
      </span>
    </footer>
  )
}

/* --- app --------------------------------------------------------------------------------- */

export default function App() {
  return (
    <div className="page">
      <BackgroundFX />
      <FloatingNav />

      <header className="brand-bar">
        <span className="brand-mark">
          <span className="brand-mark-glyph">
            <Icon.cart className="brand-mark-icon" />
          </span>
          DukaanAI
        </span>
        <span className="brand-tag">AI for Indian retail</span>
      </header>

      <main>
        <Hero />
        <StockAdvisor />
        <Insights />
        <SalesStory />
        <VoiceAI />
        <QuickActions />
        <Closing />
      </main>

      <Footer />
    </div>
  )
}
