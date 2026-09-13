import { useEffect, useMemo, useRef, useState } from 'react'
import { BrowserMultiFormatReader } from '@zxing/browser'
import './App.css'
import { api, ensureShop, scrollToSection, sendVoiceCommand, scanBarcode, getProductAdvice, getInvoiceByNumber, invoicePdfUrl, getCustomerSummaries, API_BASE } from './api'

/* ==========================================================================
   DukaanAI — premium concept UI
   One long, airy page. Floating nav. Stock Advisor as the centerpiece.
   ========================================================================== */

const NAV_LINKS = [
  { id: 'overview', label: 'Overview', dot: 'var(--lavender)' },
  { id: 'today', label: 'Right Now', dot: 'var(--coral)' },
  { id: 'stock', label: 'Stock Advisor', dot: 'var(--coral)' },
  { id: 'radar', label: 'Dukaan Radar', dot: 'var(--coral)' },
  { id: 'products', label: 'Products', dot: 'var(--blue)' },
  { id: 'insights', label: 'AI Insights', dot: 'var(--blue)' },
  { id: 'sales', label: 'Sales Story', dot: 'var(--mint)' },
  { id: 'udhaar', label: 'Udhaar', dot: 'var(--yellow)' },
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
  x: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true" {...props}>
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  ),
  barcode: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true" {...props}>
      <path d="M3 5v14M7 5v14M10 5v14M13 5v14M15 5v14M19 5v14M21 5v14" />
    </svg>
  ),
  download: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M12 3v12m0 0-4.5-4.5M12 15l4.5-4.5" />
      <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
    </svg>
  ),
  receipt: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M6 2.5h12v19l-2.5-1.5L13 21l-2.5-1.5L8 21l-2-1.5V2.5Z" />
      <path d="M9 8h6M9 12h6M9 16h3.5" />
    </svg>
  ),
  radar: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.3-4.3" />
    </svg>
  ),
  down: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M12 5v14M6 13l6 6 6-6" />
    </svg>
  ),
  check: (props) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      <path d="M5 12.5l4.5 4.5L19 7" />
    </svg>
  ),
}

/* --- helpers -------------------------------------------------------------- */

const fmtRupee = (v) => `₹${Number(v || 0).toLocaleString('en-IN')}`

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
    scrollToSection(id)
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

function Hero({ onExplore, onTalk }) {
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
          DukaanAI watches your business, understands what&rsquo;s happening, and helps you decide what to do next.
        </p>
        <div className="hero-actions">
          <button className="btn btn-primary" onClick={onExplore}>
            Explore my shop
            <Icon.arrow className="btn-arrow" />
          </button>
          <button className="btn btn-ghost" onClick={onTalk}>
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

/* --- Command Center: "what matters right now", built from real advisor,
   radar and udhaar data — never hardcoded. ---------------------------------- */

const BUCKET_META = {
  urgent: { icon: '🔴', label: 'Needs attention' },
  comingUp: { icon: '🟡', label: 'Coming up' },
  healthy: { icon: '🟢', label: 'Healthy' },
  opportunity: { icon: '✨', label: 'AI opportunities' },
}

function useCommandCenterData(advisor, radar, creditSummaries) {
  return useMemo(() => {
    const insights = advisor?.insights || {}
    const orderToday = insights.order_today || []
    const orderWeek = insights.order_this_week || []
    const atRisk = insights.at_risk || []
    const oversupplied = insights.oversupplied || []
    const signals = radar?.signals || []
    const owingCustomers = creditSummaries.filter((c) => c.balance > 0)
    const totalUdhaar = owingCustomers.reduce((sum, c) => sum + c.balance, 0)

    const urgent = []
    for (const o of orderToday.slice(0, 2)) {
      urgent.push({
        text: `${o.display_name} may run out — order ${o.order_quantity} units today.`,
        command: `Add ${o.order_quantity} units of ${o.display_name}`,
        actionLabel: 'Reorder',
      })
    }
    for (const s of signals.filter((sig) => sig.cause === 'stockout').slice(0, 2)) {
      urgent.push({ text: s.headline, scrollTo: 'radar', actionLabel: 'View' })
    }
    if (urgent.length === 0) {
      for (const a of atRisk.slice(0, 2)) urgent.push({ text: a, scrollTo: 'stock', actionLabel: 'View' })
    }

    const comingUp = []
    for (const o of orderWeek.slice(0, 2)) {
      comingUp.push({
        text: `${o.display_name} — order by ${o.order_by_date || 'soon'}.`,
        command: `Add ${o.order_quantity} units of ${o.display_name}`,
        actionLabel: 'Reorder',
      })
    }
    if (totalUdhaar > 0) {
      comingUp.push({
        text: `${fmtRupee(totalUdhaar)} outstanding udhaar across ${owingCustomers.length} customer${owingCustomers.length === 1 ? '' : 's'}.`,
        scrollTo: 'udhaar',
        actionLabel: 'Follow up',
      })
    }

    const opportunity = []
    for (const s of signals.filter((sig) => sig.direction === 'up').slice(0, 2)) {
      opportunity.push({ text: s.headline, scrollTo: 'radar', actionLabel: 'View' })
    }
    for (const name of oversupplied.slice(0, 1)) {
      opportunity.push({ text: `${name} — slow mover, consider a combo offer.`, scrollTo: 'stock', actionLabel: 'View' })
    }

    const healthy = []
    if (urgent.length === 0 && comingUp.length === 0) {
      healthy.push({ text: insights.headline || 'Stock levels look healthy across the shop.' })
    } else {
      const healthyCount = (advisor?.products || []).filter((p) => !p.needs_attention).length
      if (healthyCount > 0) {
        healthy.push({ text: `${healthyCount} product${healthyCount === 1 ? '' : 's'} healthy, no action needed.` })
      }
    }

    return { urgent, comingUp, healthy, opportunity, totalUdhaar }
  }, [advisor, radar, creditSummaries])
}

function CommandCenter({ advisor, radar, creditSummaries, loading, onRunCommand }) {
  const data = useCommandCenterData(advisor, radar, creditSummaries)
  const buckets = [
    { key: 'urgent', items: data.urgent },
    { key: 'comingUp', items: data.comingUp },
    { key: 'healthy', items: data.healthy },
    { key: 'opportunity', items: data.opportunity },
  ]
  const nextActions = [...data.urgent, ...data.comingUp, ...data.opportunity].slice(0, 3)

  const runItem = (item) => {
    if (item.command) onRunCommand(item.command)
    else if (item.scrollTo) scrollToSection(item.scrollTo)
  }

  return (
    <section className="command-center" id="today">
      <span className="section-tag">Right now</span>
      <h2 className="section-title">
        What matters <em>today.</em>
      </h2>

      {loading ? (
        <div className="cc-grid">
          {[0, 1, 2, 3].map((i) => <div key={i} className="cc-card cc-skeleton" />)}
        </div>
      ) : (
        <>
          <div className="cc-grid">
            {buckets.map((b) => (
              <div key={b.key} className={`cc-card cc-${b.key}`}>
                <span className="cc-card-icon" aria-hidden="true">{BUCKET_META[b.key].icon}</span>
                <h3 className="cc-card-title">{BUCKET_META[b.key].label}</h3>
                {b.items.length === 0 ? (
                  <p className="cc-card-empty">Nothing here right now.</p>
                ) : (
                  <ul className="cc-card-list">
                    {b.items.map((it, i) => (
                      <li key={i}>
                        <span>{it.text}</span>
                        {it.actionLabel && (
                          <button className="cc-item-action" onClick={() => runItem(it)}>
                            {it.actionLabel}
                          </button>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>

          {nextActions.length > 0 && (
            <div className="nba">
              <h3 className="nba-title">
                <Icon.sparkle className="nba-title-icon" />
                What should I do next?
              </h3>
              <ol className="nba-list">
                {nextActions.map((a, i) => (
                  <li key={i} className="nba-item">
                    <span className="nba-rank">{i + 1}</span>
                    <span className="nba-text">{a.text}</span>
                    {a.actionLabel && (
                      <button className="btn btn-ghost btn-sm nba-action" onClick={() => runItem(a)}>
                        {a.actionLabel}
                      </button>
                    )}
                  </li>
                ))}
              </ol>
            </div>
          )}
        </>
      )}
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

/* Fallback while the backend is connecting — the real data takes over once loaded. */
const MOCK_ADVISOR = {
  name: 'MAGGI 2-MINUTE NOODLES',
  meta: 'Masala · 70g · Nestlé',
  stock: 18,
  sell: 12,
  trend: 22,
  stockout: 1.5,
  lead: 2,
  qty: 35,
  verdict: 'ORDER TODAY',
  urgency: 'critical',
  explain: 'Demand is rising faster than usual. Ordering today keeps a safety buffer before your next delivery.',
  order_by_date: null,
}

const VERDICT_LABELS = {
  'ORDER NOW': 'ORDER TODAY',
  'BUY MORE': 'ORDER MORE',
  WAIT: 'WAIT',
  HOLD: 'HOLD STOCK',
  'BUY LESS': 'SKIP THIS ORDER',
  'INSUFFICIENT DATA': 'NEED MORE SALES DATA',
}

function StockAdvisor({ advisor, loading, error, onRetry, onAddFirst }) {
  const allProducts = advisor?.products || []
  // The advisor only ever surfaces products with a genuine issue — low/
  // about-to-finish stock, a reorder that looks delayed, or heavy overstock
  // worth a return. A product that was just restocked, or never had a
  // problem, does not belong here even though it's still in the shop.
  const products = allProducts.filter((p) => p.needs_attention)
  const [selectedId, setSelectedId] = useState(null)

  const selected =
    products.find((p) => p.product_id === selectedId) ||
    products.find((p) => p.urgency === 'critical') ||
    products.find((p) => p.urgency === 'order-soon') ||
    products[0]

  const useMock = !advisor
  const healthy = !useMock && allProducts.length > 0 && products.length === 0
  const d = useMock
    ? MOCK_ADVISOR
    : {
        name: selected?.display_name || 'YOUR PRODUCTS',
        meta: [selected?.brand, selected?.variant, selected?.pack_size].filter(Boolean).join(' · '),
        stock: selected?.current_stock ?? 0,
        sell: selected?.avg_daily_sales ?? 0,
        trend: selected?.sales_growth_percent ?? null,
        stockout: selected?.days_until_stockout ?? null,
        lead: advisor.lead_time_days,
        qty: selected?.recommended_order_quantity ?? 0,
        verdict: selected?.recommendation || 'HOLD',
        urgency: selected?.urgency || 'ok',
        explain:
          selected?.explanation ||
          'Add a few more sales and I will start predicting stockouts for this product.',
        order_by_date: selected?.order_by_date || null,
      }

  const stages = useMock
    ? ADVISOR_STAGES
    : [
        {
          key: 'today',
          label: 'TODAY',
          sub: `${d.stock} on shelf`,
          active: d.urgency === 'critical',
        },
        {
          key: 'order',
          label: 'ORDER',
          sub: d.order_by_date ? `by ${d.order_by_date}` : `order ${d.qty}`,
          active: d.urgency === 'order-soon' || d.urgency === 'watch',
        },
        { key: 'delivery', label: 'DELIVERY', sub: `in ~${d.lead} days` },
        {
          key: 'risk',
          label: 'STOCKOUT RISK',
          sub: d.stockout != null ? `in ${d.stockout} days` : 'no sales yet',
        },
      ]

  return (
    <section className="advisor" id="stock">
      <span className="section-tag">AI Stock Advisor</span>
      <h2 className="section-title">
        Know when you&rsquo;ll run out — <em>before you do.</em>
      </h2>

      {!healthy && products.length > 1 && (
        <div className="advisor-tabs" role="tablist" aria-label="Choose product">
          {products.map((p) => (
            <button
              key={p.product_id}
              role="tab"
              aria-selected={selected?.product_id === p.product_id}
              className={`advisor-tab ${selected?.product_id === p.product_id ? 'active' : ''}`}
              onClick={() => setSelectedId(p.product_id)}
            >
              {p.display_name}
            </button>
          ))}
        </div>
      )}

      {healthy ? (
        <article className="advisor-card advisor-card-healthy">
          <header className="advisor-head">
            <div className="advisor-product">
              <span className="advisor-product-glyph">
                <Icon.box />
              </span>
              <div>
                <h3 className="advisor-product-name">All stocked up</h3>
                <p className="advisor-product-meta">
                  {allProducts.length} product{allProducts.length === 1 ? '' : 's'} monitored
                </p>
              </div>
            </div>
            <span className="advisor-verdict">
              <span className="advisor-verdict-pulse" />
              Status
              <strong>HEALTHY</strong>
            </span>
          </header>
          <p className="advisor-explain">
            <Icon.sparkle className="advisor-explain-spark" />
            {advisor?.insights?.headline ||
              'Stock levels look healthy across the shop — nothing needs ordering right now.'}
          </p>
          <p className="advisor-disclaimer">{advisor?.disclaimer}</p>
        </article>
      ) : (
      <article className="advisor-card">
        {/* product header */}
        <header className="advisor-head">
          <div className="advisor-product">
            <span className="advisor-product-glyph">
              <Icon.box />
            </span>
            <div>
              <h3 className="advisor-product-name">{d.name}</h3>
              {d.meta ? <p className="advisor-product-meta">{d.meta}</p> : null}
            </div>
          </div>
          <span className={`advisor-verdict ${!useMock && d.urgency === 'critical' ? 'danger' : ''}`}>
            <span className="advisor-verdict-pulse" />
            Recommended action
            <strong>{VERDICT_LABELS[d.verdict] || d.verdict}</strong>
          </span>
        </header>

        {/* stats */}
        <div className="advisor-stats">
          <div className="stat">
            <span className="stat-label">Current stock</span>
            <span className="stat-value">{d.stock} <small>packs</small></span>
          </div>
          <div className="stat">
            <span className="stat-label">Selling</span>
            <span className="stat-value">
              {d.sell}<small>/day</small>
              {d.trend != null && d.trend !== 0 && (
                <em className="stat-trend">
                  <Icon.up className="stat-trend-icon" />
                  {Math.abs(Math.round(d.trend))}%
                </em>
              )}
            </span>
          </div>
          <div className={`stat ${d.stockout != null && d.stockout <= (d.lead || 2) ? 'stat-warn' : ''}`}>
            <span className="stat-label">Expected to run out</span>
            <span className="stat-value">{d.stockout != null ? `in ${d.stockout} days` : 'no sales yet'}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Supplier delivery</span>
            <span className="stat-value">~{d.lead} days</span>
          </div>
          <div className="stat stat-action">
            <span className="stat-label">Recommended quantity</span>
            <span className="stat-value">{d.qty} <small>packs</small></span>
          </div>
        </div>

        {/* timeline */}
        <div className="advisor-timeline">
          <div className="advisor-track">
            <span className="advisor-track-fill" />
            <span className="advisor-track-marker" />
          </div>
          <ol className="advisor-stages">
            {stages.map((s) => (
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
          {d.explain}
        </p>
        <p className="advisor-disclaimer">
          {useMock
            ? 'Demo data — connect the FastAPI backend to see live advice for your own products.'
            : advisor?.disclaimer}
        </p>
      </article>
      )}

      {allProducts.length === 0 && !loading && (
        <div className="advisor-empty">
          <p className="advisor-status">
            {error
              ? `Could not reach the backend (${error}).`
              : 'No products in your shop yet — add your first product to unlock AI stock analysis.'}
          </p>
          {error ? (
            <button className="btn btn-ghost btn-sm" onClick={onRetry}>
              Try again
            </button>
          ) : (
            <button className="btn btn-primary btn-sm" onClick={onAddFirst}>
              <Icon.plus className="btn-sparkle" />
              Add first product
            </button>
          )}
        </div>
      )}
    </section>
  )
}

/* --- Products: full catalog browse, status derived from the same real AI
   analysis the Stock Advisor uses (advisor.products) — no separate fetch. */

function productStatus(p) {
  if (p.urgency === 'critical') return { emoji: '🔴', label: 'Urgent', tone: 'urgent' }
  if (p.urgency === 'order-soon' || p.urgency === 'watch') return { emoji: '🟡', label: 'Order soon', tone: 'soon' }
  if (p.recommendation === 'INSUFFICIENT DATA') {
    if (p.avg_daily_sales === 0 && p.current_stock > 0) return { emoji: '💀', label: 'Dead stock', tone: 'dead' }
    return { emoji: '⚪', label: 'New / limited data', tone: 'unknown' }
  }
  if (p.demand_trend === 'increasing') return { emoji: '🔥', label: 'Hot', tone: 'hot' }
  if (p.demand_trend === 'decreasing') return { emoji: '❄️', label: 'Slow', tone: 'slow' }
  return { emoji: '🟢', label: 'Healthy', tone: 'healthy' }
}

function ProductsGrid({ advisor, loading, onAskAbout }) {
  const [query, setQuery] = useState('')
  const products = advisor?.products || []
  const filtered = query.trim()
    ? products.filter((p) => p.display_name.toLowerCase().includes(query.trim().toLowerCase()))
    : products

  return (
    <section className="products" id="products">
      <span className="section-tag">Products</span>
      <h2 className="section-title">Your whole catalog, <em>at a glance.</em></h2>
      <p className="voice-sub">
        Every SKU, with the same live AI read the Stock Advisor uses — never confusing two pack sizes for the same product.
      </p>

      {products.length > 0 && (
        <input
          className="modal-input products-search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search products…"
        />
      )}

      {loading ? (
        <div className="products-grid">
          {[0, 1, 2, 3, 4, 5].map((i) => <div key={i} className="product-card cc-skeleton" />)}
        </div>
      ) : filtered.length === 0 ? (
        <p className="radar-empty">{products.length === 0 ? 'No products yet.' : 'No products match your search.'}</p>
      ) : (
        <div className="products-grid">
          {filtered.map((p) => {
            const status = productStatus(p)
            return (
              <div key={p.product_id} className={`product-card product-${status.tone}`}>
                <div className="product-card-head">
                  <div>
                    <h3 className="product-card-name">{p.display_name}</h3>
                    <p className="product-card-meta">
                      {[p.brand, p.pack_size].filter(Boolean).join(' · ') || 'No brand info'}
                    </p>
                  </div>
                  <span className={`product-badge product-badge-${status.tone}`}>
                    {status.emoji} {status.label}
                  </span>
                </div>
                <div className="product-card-stats">
                  <div>
                    <span className="product-stat-label">Stock</span>
                    <span className="product-stat-value">{p.current_stock}</span>
                  </div>
                  <div>
                    <span className="product-stat-label">Selling</span>
                    <span className="product-stat-value">{p.avg_daily_sales}/day</span>
                  </div>
                  <div>
                    <span className="product-stat-label">Margin</span>
                    <span className="product-stat-value">
                      {p.margin != null ? fmtRupee(p.margin) : '—'}
                    </span>
                  </div>
                  <div>
                    <span className="product-stat-label">Runs out</span>
                    <span className="product-stat-value">
                      {p.days_until_stockout != null ? `${p.days_until_stockout}d` : '—'}
                    </span>
                  </div>
                </div>
                <button className="product-ask-btn" onClick={() => onAskAbout(p)}>
                  <Icon.sparkle className="btn-sparkle" />
                  Ask AI about this
                </button>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

/* --- Dukaan Radar: continuous anomaly detection on today's sales ---------- */

function RadarBadge({ active }) {
  return (
    <span className={`radar-badge ${active ? 'radar-badge-active' : ''}`} aria-hidden="true">
      <span className="radar-ring radar-ring-1" />
      <span className="radar-ring radar-ring-2" />
      <span className="radar-sweep" />
      <Icon.radar className="radar-badge-icon" />
    </span>
  )
}

function DukaanRadar({ radar, loading }) {
  const signals = radar?.signals || []

  return (
    <section className="radar" id="radar">
      <span className="section-tag">Dukaan Radar</span>
      <h2 className="section-title">
        Something changed? <em>DukaanAI is watching.</em>
      </h2>
      <p className="voice-sub">
        AI continuously compares today&rsquo;s sales against what&rsquo;s normal for each product,
        so you find out the moment something looks unusual — without staring at a dashboard.
      </p>

      <div className="radar-panel">
        <RadarBadge active={signals.length > 0} />

        {signals.length === 0 ? (
          <p className="radar-empty">
            {loading ? 'Scanning today’s sales…' : (radar?.headline || 'All quiet — nothing unusual today.')}
          </p>
        ) : (
          <div className="radar-list">
            {signals.map((s) => (
              <div key={`${s.product_id}-${s.direction}`} className={`radar-card radar-card-${s.direction}`}>
                <span className="radar-card-icon">
                  {s.direction === 'up' ? <Icon.up /> : <Icon.down />}
                </span>
                <div className="radar-card-body">
                  <p className="radar-card-headline">{s.headline}</p>
                  {s.direction === 'up' ? (
                    <p className="radar-card-detail">
                      {s.days_until_stockout != null &&
                        `At the current rate, you'll run out in ~${s.days_until_stockout} days. `}
                      {s.recommended_order_quantity > 0 &&
                        `Recommended: add ${s.recommended_order_quantity} units to your next order.`}
                    </p>
                  ) : (
                    <p className="radar-card-detail">{s.cause_note}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}

/* --- AI insights -------------------------------------------------------------- */

const STATIC_INSIGHTS = [
  {
    tone: 'mint',
    icon: Icon.up,
    title: 'Demand is rising',
    line: 'Cold drinks are selling 30% faster since Monday — you may need a bigger order.',
    detail: 'I compare the last 7 days of sales with the week before. This is demo data — connect the backend to see it live.',
  },
  {
    tone: 'blue',
    icon: Icon.money,
    title: '₹6,240 tied up in slow stock',
    line: 'Three shelf items haven’t moved in 3 weeks. Consider a combo offer.',
    detail: 'Slow stock means falling demand plus far more inventory than the reorder point. This is demo data — connect the backend to see it live.',
  },
  {
    tone: 'coral',
    icon: Icon.alert,
    title: '5 products need attention',
    line: 'Two are about to run out, three are overstocked. One tap to fix all five.',
    detail: 'Urgent products would run out before the next supplier delivery arrives. This is demo data — connect the backend to see it live.',
  },
]

function Insights({ cards }) {
  const [openIdx, setOpenIdx] = useState(null)

  return (
    <section className="insights" id="insights">
      <span className="section-tag">AI Insights</span>
      <h2 className="section-title">Three things worth knowing today.</h2>
      <div className="insight-row">
        {cards.map((ins, i) => (
          <article key={i} className={`insight-bubble insight-${ins.tone}`}>
            <span className="insight-icon"><ins.icon /></span>
            <h3 className="insight-title">{ins.title}</h3>
            <p className="insight-line">{ins.line}</p>
            <button
              className={`insight-more ${openIdx === i ? 'open' : ''}`}
              onClick={() => setOpenIdx(openIdx === i ? null : i)}
              aria-expanded={openIdx === i}
            >
              {openIdx === i ? 'Close' : 'See why'}
              <Icon.arrow className="insight-more-arrow" />
            </button>
            {openIdx === i && <p className="insight-detail">{ins.detail}</p>}
          </article>
        ))}
      </div>
    </section>
  )
}

/* --- sales story ----------------------------------------------------------------- */

const SALES_DATA = [4100, 4300, 4200, 4650, 4800, 4700, 5150, 5350, 5200, 5650, 5850, 6100]

/* Weekly sales totals for the last `weeks` weeks, oldest first. */
function weeklyTotals(sales, weeks = 12) {
  const buckets = new Array(weeks).fill(0)
  const now = Date.now()
  const WEEK = 7 * 24 * 60 * 60 * 1000
  for (const s of sales || []) {
    const t = new Date(s.created_at).getTime()
    if (Number.isNaN(t)) continue
    const ago = Math.floor((now - t) / WEEK)
    if (ago >= 0 && ago < weeks) buckets[weeks - 1 - ago] += Number(s.total_amount) || 0
  }
  return buckets
}

function smoothPath(values, w, h, pad) {
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const px = (i) => pad + (i / (values.length - 1)) * (w - pad * 2)
  const py = (v) => h - pad - ((v - min) / range) * (h - pad * 2)
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

function SalesStory({ sales }) {
  const W = 960
  const H = 340
  const PAD = 34

  const { values, live, saleCount } = useMemo(() => {
    const weeks = weeklyTotals(sales)
    const isLive = (sales || []).length > 0 && weeks.some((v) => v > 0)
    return { values: isLive ? weeks : SALES_DATA, live: isLive, saleCount: (sales || []).length }
  }, [sales])

  const { d, pts } = useMemo(() => smoothPath(values, W, H, PAD), [values])
  const area = `${d} L ${pts[pts.length - 1][0]},${H - 8} L ${pts[0][0]},${H - 8} Z`

  const last = values[values.length - 1]
  const prev = values[values.length - 2]
  const growth = live && prev > 0 ? Math.round((last - prev) / prev * 100) : null

  return (
    <section className="sales" id="sales">
      <div className="sales-copy">
        <span className="section-tag">Sales Story</span>
        <h2 className="section-title">Your shop is growing.</h2>
        <p className="sales-statement">
          {live && growth == null ? (
            <>Live from your backend — <strong>{fmtRupee(last)}</strong> this week.</>
          ) : live ? (
            <>Sales are <strong>{growth >= 0 ? 'up' : 'down'} {Math.abs(growth)}%</strong> compared with last week.</>
          ) : (
            <>Sales are up <strong>18%</strong> compared with last week.</>
          )}
        </p>
        <div className="sales-note">
          <span className="sales-note-dot" />
          {live
            ? `Live data — ${saleCount} sale${saleCount === 1 ? '' : 's'} recorded in the last 12 weeks.`
            : 'Best week in the last three months — Sunday evening alone crossed ₹1,100.'}
        </div>
      </div>

      <div className="sales-chart-card">
        <div className="sales-chart-head">
          <span className="sales-amount">{fmtRupee(last)}</span>
          <span className="sales-chip">
            <Icon.up className="sales-chip-icon" />
            {growth != null ? `${Math.abs(growth)}%` : '18%'}
          </span>
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

/* --- Udhaar: real customer credit, humanized ------------------------------- */

function fmtDate(iso) {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

function UdhaarView({ summaries, loading, onRecordPayment }) {
  const owing = summaries.filter((c) => c.balance > 0)
  const settled = summaries.filter((c) => c.balance <= 0)
  const total = owing.reduce((sum, c) => sum + c.balance, 0)

  return (
    <section className="udhaar" id="udhaar">
      <span className="section-tag">Udhaar</span>
      <h2 className="section-title">Who owes what — <em>at a glance.</em></h2>
      {owing.length > 0 && (
        <p className="voice-sub">
          {fmtRupee(total)} outstanding across {owing.length} customer{owing.length === 1 ? '' : 's'}.
        </p>
      )}

      {loading ? (
        <div className="udhaar-list">
          {[0, 1, 2].map((i) => <div key={i} className="udhaar-row cc-skeleton" />)}
        </div>
      ) : summaries.length === 0 ? (
        <p className="radar-empty">No customers yet — add one from a sale or the quick actions below.</p>
      ) : (
        <div className="udhaar-list">
          {[...owing, ...settled].map((c) => (
            <div key={c.customer_id} className={`udhaar-row ${c.balance > 0 ? 'udhaar-row-owing' : ''}`}>
              <div className="udhaar-row-who">
                <span className="udhaar-avatar">{c.name.slice(0, 1).toUpperCase()}</span>
                <div>
                  <p className="udhaar-name">{c.name}</p>
                  {c.phone && <p className="udhaar-phone">{c.phone}</p>}
                </div>
              </div>
              <div className="udhaar-row-history">
                <span>
                  Last purchase: {c.last_purchase ? `${fmtRupee(c.last_purchase.amount)} · ${fmtDate(c.last_purchase.created_at)}` : '—'}
                </span>
                <span>
                  Last payment: {c.last_payment ? `${fmtRupee(c.last_payment.amount)} · ${fmtDate(c.last_payment.created_at)}` : '—'}
                </span>
              </div>
              <div className="udhaar-row-balance">
                <span className={`udhaar-balance ${c.balance > 0 ? 'owing' : 'settled'}`}>
                  {c.balance > 0 ? fmtRupee(c.balance) : 'Settled'}
                </span>
                {c.balance > 0 && (
                  <button className="btn btn-ghost btn-sm" onClick={() => onRecordPayment(c.customer_id)}>
                    Record payment
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

/* --- voice AI ------------------------------------------------------------------ */

const VOICE_EXAMPLES = [
  { text: '“What should I order tomorrow?”', pos: 'a' },
  { text: '“Who owes me money?”', pos: 'b' },
  { text: '“How much Maggi did I sell this week?”', pos: 'c' },
]

/* Speak a reply out loud using the browser's speech synthesis, when available. */
function speak(text) {
  try {
    if (typeof window === 'undefined' || !window.speechSynthesis || !text) return
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'en-IN'
    utterance.rate = 1.02
    window.speechSynthesis.speak(utterance)
  } catch {
    /* speech synthesis unavailable — the transcript still shows the reply */
  }
}

function useVoiceCommands(supported, onResult) {
  const [listening, setListening] = useState(false)
  const recRef = useRef(null)
  const finalChunksRef = useRef([])
  const sentRef = useRef(false)

  /* Speech recognition segments a held-down utterance into several results as
     the speaker pauses between words/phrases. We run in continuous mode and
     collect every *final* segment as it arrives, but only hand the whole
     thing to the caller once — when recognition actually ends — so one
     spoken command always becomes exactly one message, never several. */
  const finish = () => {
    setListening(false)
    if (sentRef.current) return
    sentRef.current = true
    const heard = finalChunksRef.current.join(' ').replace(/\s+/g, ' ').trim()
    finalChunksRef.current = []
    if (heard) onResult(heard)
  }

  const start = () => {
    if (!supported || listening) return
    try {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition
      const rec = new SR()
      rec.lang = 'en-IN'
      rec.continuous = true
      rec.interimResults = true
      rec.maxAlternatives = 1
      finalChunksRef.current = []
      sentRef.current = false
      rec.onresult = (e) => {
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const result = e.results[i]
          if (result.isFinal) {
            const piece = result[0].transcript.trim()
            if (piece) finalChunksRef.current.push(piece)
          }
        }
      }
      rec.onend = finish
      rec.onerror = finish
      recRef.current = rec
      setListening(true)
      rec.start()
    } catch {
      setListening(false)
    }
  }

  const stop = () => {
    try {
      recRef.current?.stop()
    } catch {
      /* already stopped */
    }
  }

  useEffect(() => () => stop(), [])

  return { listening, start, stop }
}

const VOICE_STATE_LABEL = {
  listening: 'Listening…',
  processing: 'Thinking…',
  success: 'Done',
  error: "Didn't catch that",
  idle: 'Ready',
}

function VoiceAI({ supported, listening, status, onStart, onStop, transcript, busy, onSendText, onUnsupported }) {
  const [typed, setTyped] = useState('')
  const transcriptRef = useRef(null)

  const voiceState = listening ? 'listening' : busy ? 'processing' : status

  useEffect(() => {
    const el = transcriptRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [transcript, busy])

  const submitTyped = (e) => {
    e.preventDefault()
    const text = typed.trim()
    if (!text) return
    setTyped('')
    onSendText(text)
  }

  return (
    <section className="voice" id="ask">
      <div className="voice-stage">
        <div className={`voice-orb voice-orb-${voiceState}`}>
          <span className="voice-wave w1" />
          <span className="voice-wave w2" />
          <span className="voice-wave w3" />
          <span className="voice-core">
            {voiceState === 'processing' ? (
              <span className="voice-spinner" />
            ) : voiceState === 'success' ? (
              <Icon.check className="voice-mic voice-state-icon" />
            ) : voiceState === 'error' ? (
              <Icon.x className="voice-mic voice-state-icon" />
            ) : (
              <Icon.mic className="voice-mic" />
            )}
          </span>
        </div>
        <span className="voice-state-label">{VOICE_STATE_LABEL[voiceState] || 'Ready'}</span>
        <div className="voice-commands">
          {VOICE_EXAMPLES.map((v) => (
            <span key={v.pos} className={`voice-command voice-command-${v.pos}`}>{v.text}</span>
          ))}
        </div>
      </div>
      <span className="section-tag">Voice AI</span>
      <h2 className="section-title">Just ask.</h2>
      <p className="voice-sub">
        No forms, no menus. Speak — or type — in Hindi, English or Hinglish. DukaanAI understands, acts, and reports back.
      </p>

      {transcript.length > 0 && (
        <div className="voice-transcript" ref={transcriptRef} role="log" aria-live="polite">
          {transcript.map((m, i) => (
            <div key={i} className={`voice-msg voice-msg-${m.role}`}>
              <span className="voice-msg-role">{m.role === 'user' ? 'You' : 'DukaanAI'}</span>
              {m.text}
              {m.downloads?.length > 0 && (
                <div className="voice-downloads">
                  {m.downloads.map((d) => (
                    <a
                      key={d.url}
                      className="voice-download-link"
                      href={`${API_BASE}${d.url}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Icon.download className="voice-download-icon" />
                      Download {d.invoice_number} PDF
                    </a>
                  ))}
                </div>
              )}
            </div>
          ))}
          {busy && (
            <div className="voice-typing" aria-label="DukaanAI is working on it">
              <span /><span /><span />
            </div>
          )}
        </div>
      )}

      <button
        className="btn btn-primary voice-btn"
        onPointerDown={supported ? onStart : undefined}
        onPointerUp={supported ? onStop : undefined}
        onPointerLeave={supported ? onStop : undefined}
        onClick={supported ? undefined : onUnsupported}
      >
        <Icon.wave className="btn-wave" />
        {listening ? 'Listening… release to finish' : 'Hold to talk'}
      </button>
      {!supported && (
        <p className="advisor-disclaimer voice-hint">
          Voice input needs Chrome or Edge — type a command below, or use the quick actions further down.
        </p>
      )}

      <form className="voice-textform" onSubmit={submitTyped}>
        <input
          className="voice-textinput"
          type="text"
          placeholder="Or type a command… “Sell 2 Maggi 70g to Ramesh on credit”"
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
        />
        <button className="btn btn-ghost voice-send" type="submit" disabled={busy || !typed.trim()}>
          Send
        </button>
      </form>
    </section>
  )
}

/* --- quick actions ---------------------------------------------------------------- */

const ACTIONS = [
  { label: 'Scan', tone: 'coral', icon: Icon.barcode, key: 'scan', sparkle: true },
  { label: 'New Sale', tone: 'mint', icon: Icon.plus, key: 'new-sale' },
  { label: 'Add Stock', tone: 'blue', icon: Icon.box, key: 'add-stock' },
  { label: 'Record Payment', tone: 'yellow', icon: Icon.rupee, key: 'record-payment' },
  { label: 'Print Invoice', tone: 'mint', icon: Icon.receipt, key: 'invoice' },
  { label: 'Ask DukaanAI', tone: 'lavender', icon: Icon.sparkle, key: 'ask', sparkle: true },
]

function QuickActions({ onAction }) {
  return (
    <section className="actions">
      <div className="action-row">
        {ACTIONS.map((a) => (
          <button
            key={a.label}
            className={`action-chip action-${a.tone} ${a.sparkle ? 'action-sparkle' : ''}`}
            onClick={() => onAction(a.key)}
          >
            <span className="action-icon"><a.icon /></span>
            {a.label}
          </button>
        ))}
      </div>
    </section>
  )
}

/* --- closing ------------------------------------------------------------------------ */

function Closing({ onOpen }) {
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
      <button className="btn btn-primary" onClick={onOpen}>
        Open my DukaanAI
        <Icon.arrow className="btn-arrow" />
      </button>
    </section>
  )
}

/* --- footer --------------------------------------------------------------------------- */

function Footer({ onPrivacy, onSupport }) {
  return (
    <footer className="footer">
      <span className="footer-brand"><Icon.sparkle className="footer-spark" /> DukaanAI</span>
      <span className="footer-note">Made in India, for every neighbourhood shop.</span>
      <span className="footer-links">
        <button onClick={onPrivacy}>Privacy</button>
        <button onClick={onSupport}>Support</button>
      </span>
    </footer>
  )
}

/* --- modal for the quick actions -------------------------------------------------------- */

const MODAL_TITLES = {
  'new-sale': 'New Sale',
  'add-stock': 'Add Stock',
  'record-payment': 'Record Payment',
}

function ActionModal({ type, shop, products, customers, prefillBarcode, prefillCustomerId, onClose, onSaleDone, onProductDone, onPaymentDone, onGoAddStock }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  /* new sale state */
  const [rows, setRows] = useState([{ product_id: '', quantity: 1, unit_price: '' }])
  const [customerId, setCustomerId] = useState('')
  const [payMethod, setPayMethod] = useState('cash')

  /* add stock state */
  const [pf, setPf] = useState({
    name: '', brand: '', variant: '', pack_size: '',
    selling_price: '', purchase_price: '', current_stock: '', minimum_stock: 5,
    barcode: prefillBarcode || '',
  })

  /* record payment state */
  const [customerIdPay, setCustomerIdPay] = useState(prefillCustomerId ? String(prefillCustomerId) : '')
  const [newName, setNewName] = useState('')
  const [newPhone, setNewPhone] = useState('')
  const [amount, setAmount] = useState('')
  const [note, setNote] = useState('')

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const opt = (v) => (v && String(v).trim() ? String(v).trim() : null)

  const setRow = (idx, patch) =>
    setRows(rows.map((row, i) => (i === idx ? { ...row, ...patch } : row)))

  const saleTotal = rows.reduce(
    (sum, r) => sum + (Number(r.quantity) || 0) * (Number(r.unit_price) || 0),
    0,
  )

  const submit = async () => {
    setError(null)
    setBusy(true)
    try {
      if (type === 'new-sale') {
        const items = rows
          .map((r) => ({
            product_id: Number(r.product_id),
            quantity: Number(r.quantity),
            unit_price: Number(r.unit_price),
          }))
          .filter((r) => r.product_id && r.quantity > 0)
        if (!items.length) throw new Error('Pick a product and a quantity first.')
        if (items.some((i) => !(i.unit_price >= 0) || i.unit_price === 0)) {
          throw new Error('Set a unit price for every item.')
        }
        const res = await api.post('/sales/', {
          shop_id: shop.id,
          customer_id: customerId ? Number(customerId) : null,
          payment_method: payMethod,
          items,
        })
        onSaleDone(res)
      } else if (type === 'add-stock') {
        if (!pf.name.trim()) throw new Error('Product name is required.')
        if (pf.selling_price === '' || Number.isNaN(Number(pf.selling_price))) {
          throw new Error('Selling price is required.')
        }
        const res = await api.post('/products/', {
          shop_id: shop.id,
          brand: opt(pf.brand),
          name: pf.name.trim(),
          variant: opt(pf.variant),
          pack_size: opt(pf.pack_size),
          barcode: opt(pf.barcode),
          selling_price: Number(pf.selling_price),
          purchase_price: pf.purchase_price !== '' ? Number(pf.purchase_price) : null,
          current_stock: Number(pf.current_stock) || 0,
          minimum_stock: Number(pf.minimum_stock) || 0,
        })
        onProductDone(res)
      } else {
        let cid = customerIdPay ? Number(customerIdPay) : null
        if (!cid && !newName.trim()) throw new Error('Pick an existing customer or enter a name.')
        const amt = Number(amount)
        if (!amt || amt <= 0) throw new Error('Amount must be greater than zero.')
        if (!cid) {
          const c = await api.post('/customers/', {
            shop_id: shop.id,
            name: newName.trim(),
            phone: opt(newPhone),
          })
          cid = c.id
        }
        await api.post('/credit/', {
          shop_id: shop.id,
          customer_id: cid,
          amount: amt,
          transaction_type: 'payment',
          note: opt(note),
        })
        onPaymentDone(amt, cid)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className="modal-scrim"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="modal" role="dialog" aria-modal="true" aria-label={MODAL_TITLES[type]}>
        <div className="modal-head">
          <h3 className="modal-title">{MODAL_TITLES[type]}</h3>
          <button className="modal-close" onClick={onClose} aria-label="Close dialog">
            <Icon.x />
          </button>
        </div>

        {error && <p className="modal-error">{error}</p>}

        {type === 'new-sale' && (
          <>
            {products.length === 0 ? (
              <div className="advisor-empty">
                <p className="advisor-status">No products yet — add stock first, then record sales.</p>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => {
                    onClose()
                    onGoAddStock()
                  }}
                >
                  <Icon.plus className="btn-sparkle" />
                  Add a product
                </button>
              </div>
            ) : (
              <>
                {rows.map((r, idx) => (
                  <div className="modal-item-row" key={idx}>
                    <select
                      className="modal-select"
                      value={r.product_id}
                      onChange={(e) => {
                        const pid = e.target.value
                        const p = products.find((x) => String(x.id) === pid)
                        setRow(idx, { product_id: pid, unit_price: p ? p.selling_price : r.unit_price })
                      }}
                    >
                      <option value="">Product…</option>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                          {p.pack_size ? ` ${p.pack_size}` : ''}
                          {p.brand ? ` · ${p.brand}` : ''} ({p.current_stock} in stock)
                        </option>
                      ))}
                    </select>
                    <input
                      className="modal-input"
                      type="number"
                      min="1"
                      placeholder="Qty"
                      value={r.quantity}
                      onChange={(e) => setRow(idx, { quantity: e.target.value })}
                    />
                    <input
                      className="modal-input"
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="₹/unit"
                      value={r.unit_price}
                      onChange={(e) => setRow(idx, { unit_price: e.target.value })}
                    />
                    <button
                      type="button"
                      className="modal-row-remove"
                      onClick={() => setRows(rows.filter((_, i) => i !== idx))}
                      disabled={rows.length === 1}
                      aria-label="Remove item"
                    >
                      <Icon.x />
                    </button>
                  </div>
                ))}
                <button type="button" className="modal-add-row" onClick={() => setRows([...rows, { product_id: '', quantity: 1, unit_price: '' }])}>
                  <Icon.plus /> Add item
                </button>

                <div className="modal-row">
                  <label className="modal-field">
                    <span className="modal-label">Customer (optional)</span>
                    <select className="modal-select" value={customerId} onChange={(e) => setCustomerId(e.target.value)}>
                      <option value="">Walk-in</option>
                      {customers.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}{c.phone ? ` · ${c.phone}` : ''}</option>
                      ))}
                    </select>
                  </label>
                  <label className="modal-field">
                    <span className="modal-label">Payment method</span>
                    <select className="modal-select" value={payMethod} onChange={(e) => setPayMethod(e.target.value)}>
                      <option value="cash">Cash</option>
                      <option value="upi">UPI</option>
                      <option value="card">Card</option>
                      <option value="credit">Udhaar (credit)</option>
                    </select>
                  </label>
                </div>
                <p className="modal-total">Total: <strong>{fmtRupee(saleTotal)}</strong></p>
              </>
            )}
          </>
        )}

        {type === 'add-stock' && (
          <>
            <label className="modal-field">
              <span className="modal-label">Product name *</span>
              <input className="modal-input" value={pf.name} onChange={(e) => setPf({ ...pf, name: e.target.value })} placeholder="Maggi 2-Minute Noodles" />
            </label>
            <div className="modal-row">
              <label className="modal-field">
                <span className="modal-label">Brand</span>
                <input className="modal-input" value={pf.brand} onChange={(e) => setPf({ ...pf, brand: e.target.value })} placeholder="Nestlé" />
              </label>
              <label className="modal-field">
                <span className="modal-label">Variant</span>
                <input className="modal-input" value={pf.variant} onChange={(e) => setPf({ ...pf, variant: e.target.value })} placeholder="Masala" />
              </label>
            </div>
            <div className="modal-row">
              <label className="modal-field">
                <span className="modal-label">Pack size</span>
                <input className="modal-input" value={pf.pack_size} onChange={(e) => setPf({ ...pf, pack_size: e.target.value })} placeholder="70g" />
              </label>
              <label className="modal-field">
                <span className="modal-label">Units on shelf</span>
                <input className="modal-input" type="number" min="0" value={pf.current_stock} onChange={(e) => setPf({ ...pf, current_stock: e.target.value })} placeholder="24" />
              </label>
            </div>
            <div className="modal-row">
              <label className="modal-field">
                <span className="modal-label">Selling price (₹) *</span>
                <input className="modal-input" type="number" min="0" step="0.01" value={pf.selling_price} onChange={(e) => setPf({ ...pf, selling_price: e.target.value })} placeholder="14" />
              </label>
              <label className="modal-field">
                <span className="modal-label">Purchase price (₹)</span>
                <input className="modal-input" type="number" min="0" step="0.01" value={pf.purchase_price} onChange={(e) => setPf({ ...pf, purchase_price: e.target.value })} placeholder="12" />
              </label>
            </div>
            <label className="modal-field">
              <span className="modal-label">Minimum stock alert</span>
              <input className="modal-input" type="number" min="0" value={pf.minimum_stock} onChange={(e) => setPf({ ...pf, minimum_stock: e.target.value })} />
            </label>
            <label className="modal-field">
              <span className="modal-label">Barcode</span>
              <input className="modal-input" value={pf.barcode} onChange={(e) => setPf({ ...pf, barcode: e.target.value })} placeholder="8901234567890" />
            </label>
          </>
        )}

        {type === 'record-payment' && (
          <>
            <label className="modal-field">
              <span className="modal-label">Customer</span>
              <select className="modal-select" value={customerIdPay} onChange={(e) => setCustomerIdPay(e.target.value)}>
                <option value="">New customer…</option>
                {customers.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}{c.phone ? ` · ${c.phone}` : ''}</option>
                ))}
              </select>
            </label>
            {!customerIdPay && (
              <div className="modal-row">
                <label className="modal-field">
                  <span className="modal-label">New customer name *</span>
                  <input className="modal-input" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Ramesh" />
                </label>
                <label className="modal-field">
                  <span className="modal-label">Phone</span>
                  <input className="modal-input" value={newPhone} onChange={(e) => setNewPhone(e.target.value)} placeholder="98765 43210" />
                </label>
              </div>
            )}
            <label className="modal-field">
              <span className="modal-label">Amount received (₹) *</span>
              <input className="modal-input" type="number" min="0" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="500" />
            </label>
            <label className="modal-field">
              <span className="modal-label">Note</span>
              <input className="modal-input" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Part payment for March udhaar" />
            </label>
          </>
        )}

        <div className="modal-actions">
          <button className="btn btn-ghost btn-sm" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary btn-sm" onClick={submit} disabled={busy}>
            {busy ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

/* --- DukaanAI Scan: point the camera at a barcode, get instant business
   intelligence on that exact product, then act on it by voice. ------------- */

function ScanModal({ shop, onClose, onVoiceCommand, onAddNewProduct }) {
  const [phase, setPhase] = useState('scan') // 'scan' | 'loading' | 'found' | 'not-found'
  const [product, setProduct] = useState(null)
  const [notFoundCode, setNotFoundCode] = useState('')
  const [manual, setManual] = useState('')
  const [error, setError] = useState(null)
  const [cameraError, setCameraError] = useState(null)
  const [lastReply, setLastReply] = useState(null)
  const [asking, setAsking] = useState(false)
  const [typed, setTyped] = useState('')

  const videoRef = useRef(null)
  const controlsRef = useRef(null)

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const handleBarcode = async (code) => {
    const trimmed = (code || '').trim()
    if (!trimmed) return
    controlsRef.current?.stop()
    setPhase('loading')
    setError(null)
    try {
      const data = await scanBarcode(shop.id, trimmed)
      setProduct(data)
      setLastReply(null)
      setPhase('found')
    } catch (e) {
      if (e.status === 404) {
        setNotFoundCode(trimmed)
        setPhase('not-found')
      } else {
        setError(e.message || 'Could not look up that barcode.')
        setPhase('scan')
      }
    }
  }

  /* Camera scanning — active only while we're actually waiting for a scan.
     Always paired with the manual entry field below, since camera support
     (and shopkeeper permission) varies across phones and browsers. */
  useEffect(() => {
    if (phase !== 'scan') return
    let cancelled = false

    ;(async () => {
      try {
        const reader = new BrowserMultiFormatReader()
        const controls = await reader.decodeFromConstraints(
          { video: { facingMode: 'environment' } },
          videoRef.current,
          (result) => {
            if (result && !cancelled) {
              cancelled = true
              controlsRef.current?.stop()
              handleBarcode(result.getText())
            }
          },
        )
        if (cancelled) controls.stop()
        else controlsRef.current = controls
      } catch {
        if (!cancelled) setCameraError('Camera unavailable — enter the barcode below instead.')
      }
    })()

    return () => {
      cancelled = true
      controlsRef.current?.stop()
      controlsRef.current = null
    }
  }, [phase])

  const resetToScan = () => {
    setProduct(null)
    setNotFoundCode('')
    setError(null)
    setCameraError(null)
    setLastReply(null)
    setManual('')
    setPhase('scan')
  }

  const submitManual = (e) => {
    e.preventDefault()
    handleBarcode(manual)
  }

  const askAboutProduct = async (text) => {
    if (!text || !text.trim() || !product) return
    setAsking(true)
    setLastReply(null)
    try {
      const res = await onVoiceCommand(text, product.product_id)
      if (res) {
        setLastReply(res.reply)
        try {
          setProduct(await getProductAdvice(shop.id, product.product_id))
        } catch {
          /* keep showing the numbers we already have */
        }
      }
    } finally {
      setAsking(false)
    }
  }

  const submitTyped = (e) => {
    e.preventDefault()
    const text = typed.trim()
    if (!text) return
    setTyped('')
    askAboutProduct(text)
  }

  const voiceSupported =
    typeof window !== 'undefined' &&
    !!(window.SpeechRecognition || window.webkitSpeechRecognition)
  const { listening, start: micStart, stop: micStop } = useVoiceCommands(voiceSupported, askAboutProduct)

  return (
    <div className="modal-scrim" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal modal-scan" role="dialog" aria-modal="true" aria-label="DukaanAI Scan">
        <div className="modal-head">
          <h3 className="modal-title">DukaanAI Scan</h3>
          <button className="modal-close" onClick={onClose} aria-label="Close dialog">
            <Icon.x />
          </button>
        </div>

        {error && <p className="modal-error">{error}</p>}

        {phase === 'scan' && (
          <>
            <div className="scan-camera">
              {!cameraError ? (
                <video ref={videoRef} className="scan-video" muted playsInline autoPlay />
              ) : (
                <div className="scan-camera-fallback">
                  <Icon.barcode className="scan-camera-fallback-icon" />
                  <p>{cameraError}</p>
                </div>
              )}
              {!cameraError && <div className="scan-camera-frame" aria-hidden="true" />}
            </div>
            <p className="scan-hint">Point your camera at a product&rsquo;s barcode — or enter it below.</p>
            <form className="scan-manual-form" onSubmit={submitManual}>
              <input
                className="modal-input"
                value={manual}
                onChange={(e) => setManual(e.target.value)}
                placeholder="Enter barcode number"
                inputMode="numeric"
              />
              <button className="btn btn-primary btn-sm" type="submit" disabled={!manual.trim()}>
                Look up
              </button>
            </form>
          </>
        )}

        {phase === 'loading' && (
          <div className="scan-loading">
            <span className="scan-spinner" aria-hidden="true" />
            <p>Identifying product…</p>
          </div>
        )}

        {phase === 'not-found' && (
          <div className="scan-empty">
            <Icon.barcode className="scan-empty-icon" />
            <p className="advisor-status">No product in your shop has barcode &ldquo;{notFoundCode}&rdquo;.</p>
            <div className="scan-empty-actions">
              <button className="btn btn-primary btn-sm" onClick={() => onAddNewProduct(notFoundCode)}>
                <Icon.plus className="btn-sparkle" />
                Add as new product
              </button>
              <button className="btn btn-ghost btn-sm" onClick={resetToScan}>
                Scan again
              </button>
            </div>
          </div>
        )}

        {phase === 'found' && product && (
          <div className="scan-result">
            <header className="advisor-head">
              <div className="advisor-product">
                <span className="advisor-product-glyph">
                  <Icon.box />
                </span>
                <div>
                  <h3 className="advisor-product-name">{product.display_name}</h3>
                  <p className="advisor-product-meta">Barcode identified</p>
                </div>
              </div>
              <span className={`advisor-verdict ${product.urgency === 'critical' ? 'danger' : ''}`}>
                <span className="advisor-verdict-pulse" />
                Recommended action
                <strong>{VERDICT_LABELS[product.recommendation] || product.recommendation}</strong>
              </span>
            </header>

            <div className="advisor-stats">
              <div className="stat">
                <span className="stat-label">Current stock</span>
                <span className="stat-value">{product.current_stock} <small>units</small></span>
              </div>
              <div className="stat">
                <span className="stat-label">Selling price</span>
                <span className="stat-value">{fmtRupee(product.selling_price)}</span>
              </div>
              <div className="stat stat-action">
                <span className="stat-label">Margin</span>
                <span className="stat-value">
                  {product.margin != null ? fmtRupee(product.margin) : '—'}
                  {product.margin_percent != null && <small> · {product.margin_percent}%</small>}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Selling</span>
                <span className="stat-value">
                  {product.avg_daily_sales}<small>/day</small>
                  {product.sales_growth_percent != null && product.sales_growth_percent !== 0 && (
                    <em className="stat-trend">
                      <Icon.up className="stat-trend-icon" />
                      {Math.abs(Math.round(product.sales_growth_percent))}%
                    </em>
                  )}
                </span>
              </div>
              <div className={`stat ${product.needs_attention ? 'stat-warn' : ''}`}>
                <span className="stat-label">Expected to run out</span>
                <span className="stat-value">
                  {product.days_until_stockout != null ? `in ${product.days_until_stockout} days` : 'no sales yet'}
                </span>
              </div>
              {product.recommended_order_quantity > 0 && (
                <div className="stat stat-action">
                  <span className="stat-label">Recommended order</span>
                  <span className="stat-value">{product.recommended_order_quantity} <small>units</small></span>
                </div>
              )}
            </div>

            <p className="advisor-explain">
              <Icon.sparkle className="advisor-explain-spark" />
              {product.explanation}
            </p>

            <div className="scan-ask">
              <p className="modal-label">Ask or tell DukaanAI about this product</p>
              {lastReply && <p className="scan-reply">{lastReply}</p>}
              <button
                type="button"
                className={`btn btn-primary scan-mic ${listening ? 'listening' : ''}`}
                onPointerDown={voiceSupported ? micStart : undefined}
                onPointerUp={voiceSupported ? micStop : undefined}
                onPointerLeave={voiceSupported ? micStop : undefined}
                disabled={asking}
              >
                <Icon.mic className="scan-mic-icon" />
                {listening ? 'Listening… release to finish' : 'Hold to talk'}
              </button>
              <form className="voice-textform" onSubmit={submitTyped}>
                <input
                  className="voice-textinput"
                  value={typed}
                  onChange={(e) => setTyped(e.target.value)}
                  placeholder={'e.g. "Add 40 units" or "Sell 2"'}
                />
                <button className="btn btn-ghost voice-send" type="submit" disabled={asking || !typed.trim()}>
                  Send
                </button>
              </form>
            </div>

            <div className="scan-actions">
              <button className="btn btn-ghost btn-sm" onClick={resetToScan}>
                Scan another
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

/* --- Invoice lookup: type an invoice number, get the AI-designed PDF ------- */

function InvoiceModal({ shop, onClose }) {
  const [number, setNumber] = useState('')
  const [phase, setPhase] = useState('idle') // 'idle' | 'loading' | 'found' | 'not-found'
  const [invoice, setInvoice] = useState(null)
  const [error, setError] = useState(null)

  const lookup = async (e) => {
    e.preventDefault()
    const trimmed = number.trim()
    if (!trimmed) return
    setPhase('loading')
    setError(null)
    try {
      const data = await getInvoiceByNumber(shop.id, trimmed)
      setInvoice(data)
      setPhase('found')
    } catch (err) {
      if (err.status === 404) {
        setPhase('not-found')
      } else {
        setError(err.message || 'Could not look up that invoice.')
        setPhase('idle')
      }
    }
  }

  const reset = () => {
    setInvoice(null)
    setError(null)
    setNumber('')
    setPhase('idle')
  }

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="modal-scrim" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label="Print Invoice">
        <div className="modal-head">
          <h3 className="modal-title">Print Invoice</h3>
          <button className="modal-close" onClick={onClose} aria-label="Close dialog">
            <Icon.x />
          </button>
        </div>

        {error && <p className="modal-error">{error}</p>}

        {phase !== 'found' && (
          <form className="scan-manual-form" onSubmit={lookup}>
            <input
              className="modal-input"
              value={number}
              onChange={(e) => setNumber(e.target.value)}
              placeholder="Invoice number, e.g. INV-000006"
              autoFocus
            />
            <button className="btn btn-primary btn-sm" type="submit" disabled={!number.trim() || phase === 'loading'}>
              {phase === 'loading' ? 'Looking…' : 'Find'}
            </button>
          </form>
        )}

        {phase === 'not-found' && (
          <div className="scan-empty">
            <Icon.receipt className="scan-empty-icon" />
            <p className="advisor-status">No invoice numbered &ldquo;{number.trim()}&rdquo; was found.</p>
            <button className="btn btn-ghost btn-sm" onClick={reset}>
              Try another number
            </button>
          </div>
        )}

        {phase === 'found' && invoice && (
          <div className="scan-result">
            <header className="advisor-head">
              <div className="advisor-product">
                <span className="advisor-product-glyph">
                  <Icon.receipt />
                </span>
                <div>
                  <h3 className="advisor-product-name">{invoice.invoice_number}</h3>
                  <p className="advisor-product-meta">{(invoice.created_at || '').slice(0, 10)}</p>
                </div>
              </div>
              <span className={`advisor-verdict invoice-status-${invoice.status}`}>
                <span className="advisor-verdict-pulse" />
                Status
                <strong>{(invoice.status || '').toUpperCase()}</strong>
              </span>
            </header>

            <div className="advisor-stats">
              <div className="stat">
                <span className="stat-label">Billed to</span>
                <span className="stat-value" style={{ fontSize: 16 }}>
                  {invoice.customer ? invoice.customer.name : 'Walk-in customer'}
                </span>
              </div>
              <div className="stat">
                <span className="stat-label">Payment</span>
                <span className="stat-value" style={{ fontSize: 16 }}>{(invoice.payment_method || '').replace(/^./, (c) => c.toUpperCase())}</span>
              </div>
              <div className="stat stat-action">
                <span className="stat-label">Total</span>
                <span className="stat-value">{fmtRupee(invoice.total_amount)}</span>
              </div>
            </div>

            <a
              className="btn btn-primary scan-mic"
              href={invoicePdfUrl(shop.id, invoice.invoice_number)}
              target="_blank"
              rel="noreferrer"
            >
              <Icon.download className="scan-mic-icon" />
              Download PDF
            </a>

            <div className="scan-actions">
              <button className="btn btn-ghost btn-sm" onClick={reset}>
                Look up another
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

/* --- app --------------------------------------------------------------------------------- */

export default function App() {
  const [shop, setShop] = useState(null)
  const [advisor, setAdvisor] = useState(null)
  const [sales, setSales] = useState(null)
  const [products, setProducts] = useState([])
  const [customers, setCustomers] = useState([])
  const [advisorLoading, setAdvisorLoading] = useState(true)
  const [advisorError, setAdvisorError] = useState(null)
  const [radar, setRadar] = useState(null)
  const [radarLoading, setRadarLoading] = useState(true)
  const [modal, setModal] = useState(null)
  const [scanOpen, setScanOpen] = useState(false)
  const [invoiceModalOpen, setInvoiceModalOpen] = useState(false)
  const [prefillBarcode, setPrefillBarcode] = useState(null)
  const [prefillCustomerId, setPrefillCustomerId] = useState(null)
  const [toast, setToast] = useState(null)
  const [voiceSessionId, setVoiceSessionId] = useState(null)
  const [voiceTranscript, setVoiceTranscript] = useState([])
  const [voiceBusy, setVoiceBusy] = useState(false)
  const [voiceStatus, setVoiceStatus] = useState('idle') // 'idle' | 'success' | 'error'
  const [creditSummaries, setCreditSummaries] = useState([])
  const [creditLoading, setCreditLoading] = useState(true)
  const bootedRef = useRef(false)
  const seenRadarKeysRef = useRef(new Set())

  const notify = (msg, tone = 'ink') => setToast({ msg, tone })

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 5000)
    return () => clearTimeout(t)
  }, [toast])

  const loadAdvisor = async (shopId) => {
    setAdvisorLoading(true)
    setAdvisorError(null)
    try {
      setAdvisor(await api.get(`/stock-advisor/?shop_id=${shopId}`))
    } catch (e) {
      setAdvisorError(e.message)
    } finally {
      setAdvisorLoading(false)
    }
  }

  const loadSales = async (shopId) => {
    try {
      setSales(await api.get(`/sales/?shop_id=${shopId}`))
    } catch {
      setSales(null)
    }
  }

  const loadProducts = async (shopId) => {
    try {
      setProducts(await api.get(`/products/?shop_id=${shopId}`))
    } catch {
      setProducts([])
    }
  }

  const loadCustomers = async (shopId) => {
    try {
      setCustomers(await api.get(`/customers/?shop_id=${shopId}`))
    } catch {
      setCustomers([])
    }
  }

  const loadCreditSummaries = async (shopId) => {
    try {
      setCreditSummaries(await getCustomerSummaries(shopId))
    } catch {
      setCreditSummaries([])
    } finally {
      setCreditLoading(false)
    }
  }

  /* Dukaan Radar: continuous anomaly detection, polled while the app is
     open. New signals (ones this session hasn't already surfaced) get a
     toast; every signal — new or not — stays visible in the Radar panel. */
  const loadRadar = async (shopId) => {
    try {
      const data = await api.get(`/radar/?shop_id=${shopId}`)
      setRadar(data)
      for (const s of data.signals || []) {
        const key = `${s.product_id}-${s.direction}`
        if (!seenRadarKeysRef.current.has(key)) {
          seenRadarKeysRef.current.add(key)
          notify(s.headline, s.direction === 'down' ? 'coral' : 'ink')
        }
      }
    } catch {
      /* keep showing the last known radar state rather than clearing it */
    } finally {
      setRadarLoading(false)
    }
  }

  /* Bootstrap: reuse or create the shop, then load everything once. */
  useEffect(() => {
    if (bootedRef.current) return
    bootedRef.current = true
    ;(async () => {
      try {
        const s = await ensureShop()
        setShop(s)
        await Promise.all([
          loadAdvisor(s.id),
          loadSales(s.id),
          loadProducts(s.id),
          loadCustomers(s.id),
          loadRadar(s.id),
          loadCreditSummaries(s.id),
        ])
      } catch (e) {
        setAdvisorLoading(false)
        setRadarLoading(false)
        notify(`Backend unreachable at ${API_BASE} — ${e.message}`, 'coral')
      }
    })()
  }, [])

  /* Poll Radar every 90s while the app stays open — this is the "continuous
     watching" the feature is named for, without needing a websocket/push
     backend. */
  useEffect(() => {
    if (!shop) return
    const interval = setInterval(() => loadRadar(shop.id), 90000)
    return () => clearInterval(interval)
  }, [shop])

  /* Voice: real speech recognition, piped to the backend voice assistant,
     which executes real operations via the same services the buttons use. */
  const voiceSupported =
    typeof window !== 'undefined' &&
    !!(window.SpeechRecognition || window.webkitSpeechRecognition)

  const flashVoiceStatus = (status) => {
    setVoiceStatus(status)
    setTimeout(() => setVoiceStatus('idle'), 1800)
  }

  const runVoiceCommand = async (text, contextProductId) => {
    if (!text || !text.trim()) return
    if (!shop) {
      notify('Backend is still connecting — try again in a moment.', 'coral')
      return
    }

    setVoiceTranscript((t) => [...t, { role: 'user', text }])
    setVoiceBusy(true)

    try {
      const res = await sendVoiceCommand(shop.id, voiceSessionId, text, contextProductId)
      setVoiceSessionId(res.session_id)
      setVoiceTranscript((t) => [...t, { role: 'assistant', text: res.reply, downloads: res.downloads }])
      speak(res.reply)
      notify(res.reply)
      flashVoiceStatus('success')

      const updated = res.updated || []
      const tasks = []
      if (updated.includes('products') || updated.includes('sales')) {
        tasks.push(loadProducts(shop.id), loadSales(shop.id), loadAdvisor(shop.id), loadRadar(shop.id))
      }
      if (updated.includes('customers')) tasks.push(loadCustomers(shop.id))
      if (updated.includes('credit') || updated.includes('customers')) tasks.push(loadCreditSummaries(shop.id))
      if (tasks.length) await Promise.all(tasks)
      return res
    } catch (e) {
      setVoiceTranscript((t) => [...t, { role: 'assistant', text: e.message || 'Something went wrong reaching DukaanAI.' }])
      flashVoiceStatus('error')
      return null
    } finally {
      setVoiceBusy(false)
    }
  }

  const { listening, start: voiceStart, stop: voiceStop } = useVoiceCommands(
    voiceSupported,
    (heard) => runVoiceCommand(heard),
  )

  const openModal = (key) => {
    if (key === 'ask') return scrollToSection('ask')
    if (!shop) return notify('Backend is still connecting — try again in a moment.', 'coral')
    if (key === 'scan') return setScanOpen(true)
    if (key === 'invoice') return setInvoiceModalOpen(true)
    setModal(key)
  }

  /* Scan found no product for that barcode — hand off to Add Stock with the
     barcode pre-filled, so the very next scan of the same item resolves. */
  const addProductFromScan = (barcode) => {
    setScanOpen(false)
    setPrefillBarcode(barcode)
    setModal('add-stock')
  }

  const recordPaymentFor = (customerId) => {
    setPrefillCustomerId(customerId)
    setModal('record-payment')
  }

  const askAboutProductFromGrid = (product) => {
    scrollToSection('ask')
    runVoiceCommand(`How is ${product.display_name} doing?`, product.product_id)
  }

  const afterSale = async (res) => {
    setModal(null)
    notify(`Sale recorded — total ${fmtRupee(res.total_amount)}`)
    if (!shop) return
    await Promise.all([loadAdvisor(shop.id), loadSales(shop.id)])
  }

  const afterProduct = async (res) => {
    setModal(null)
    setPrefillBarcode(null)
    notify(`${res.name} added — ${res.current_stock} units on shelf`)
    if (!shop) return
    await Promise.all([loadAdvisor(shop.id), loadProducts(shop.id)])
  }

  const afterPayment = async (amt, cid) => {
    setModal(null)
    setPrefillCustomerId(null)
    const c = customers.find((x) => x.id === cid)
    notify(`Payment of ${fmtRupee(amt)} recorded for ${c ? c.name : 'customer'}.`)
    if (!shop) return
    await Promise.all([loadCreditSummaries(shop.id), loadCustomers(shop.id)])
  }

  /* Insight bubbles built from the live advisor data (static demo until it loads). */
  const insightCards = useMemo(() => {
    if (!advisor) return STATIC_INSIGHTS

    const ins = advisor.insights || {}
    const ups = (advisor.products || [])
      .filter((p) => p.demand_trend === 'increasing' && p.sales_growth_percent != null)
      .sort((a, b) => (b.sales_growth_percent || 0) - (a.sales_growth_percent || 0))
    const topUp = ups[0]
    const over = ins.oversupplied || []
    const urgent = [...(ins.order_today || []), ...(ins.order_this_week || [])]
    const risky = ins.at_risk || []

    return [
      {
        tone: 'mint',
        icon: Icon.up,
        title: topUp ? 'Demand is rising' : 'Demand is steady',
        line: topUp
          ? `${topUp.display_name} is selling ${Math.abs(Math.round(topUp.sales_growth_percent))}% faster than last week — consider a bigger order.`
          : ins.headline || 'No big demand shifts in the last 7 days.',
        detail: topUp
          ? topUp.explanation
          : 'I compare the last 7 days of sales with the week before to spot rising demand.',
      },
      {
        tone: 'blue',
        icon: Icon.money,
        title: over.length ? `${over.length} slow mover${over.length > 1 ? 's' : ''} on your shelf` : 'Stock looks healthy',
        line: over.length
          ? 'Money is sitting in slow stock — consider a combo offer to move it.'
          : 'Nothing is badly overstocked right now.',
        detail: over.length
          ? over.join(' · ')
          : 'A “slow mover” means falling demand plus far more stock than the reorder point — none found.',
      },
      {
        tone: urgent.length ? 'coral' : 'mint',
        icon: Icon.alert,
        title: urgent.length ? `${urgent.length} product${urgent.length > 1 ? 's' : ''} need attention` : 'No urgent stock issues',
        line: urgent.length
          ? `${urgent[0].display_name} — order ${urgent[0].order_quantity} units soon.`
          : ins.headline || 'Everything is comfortably above its reorder point.',
        detail: urgent.length
          ? urgent.map((u) => `${u.display_name}: order ${u.order_quantity} by ${u.order_by_date || 'soon'} (stockout ~${u.stockout_date}).`).join(' ')
          : risky.length
            ? risky.join(' ')
            : 'Nothing critical — I will flag anything that nears its reorder point.',
      },
    ]
  }, [advisor])

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
        <Hero
          onExplore={() => scrollToSection('stock')}
          onTalk={() => scrollToSection('ask')}
        />
        <CommandCenter
          advisor={advisor}
          radar={radar}
          creditSummaries={creditSummaries}
          loading={advisorLoading || radarLoading}
          onRunCommand={runVoiceCommand}
        />
        <StockAdvisor
          advisor={advisor}
          loading={advisorLoading}
          error={advisorError}
          onRetry={() => shop && loadAdvisor(shop.id)}
          onAddFirst={() => openModal('add-stock')}
        />
        <ProductsGrid advisor={advisor} loading={advisorLoading} onAskAbout={askAboutProductFromGrid} />
        <DukaanRadar radar={radar} loading={radarLoading} />
        <Insights cards={insightCards} />
        <SalesStory sales={sales} />
        <UdhaarView summaries={creditSummaries} loading={creditLoading} onRecordPayment={recordPaymentFor} />
        <VoiceAI
          supported={voiceSupported}
          listening={listening}
          status={voiceStatus}
          onStart={voiceStart}
          onStop={voiceStop}
          transcript={voiceTranscript}
          busy={voiceBusy}
          onSendText={runVoiceCommand}
          onUnsupported={() => notify('Voice input needs Chrome or Edge — type a command below or use the quick actions.', 'coral')}
        />
        <QuickActions onAction={openModal} />
        <Closing onOpen={() => scrollToSection('stock')} />
      </main>

      <Footer
        onPrivacy={() => notify('Privacy: your data never leaves this machine — it lives in your local FastAPI + SQLite backend.')}
        onSupport={() => notify('Support: no support desk in this build yet — use “Ask DukaanAI” above for help with your shop.')}
      />

      {modal && shop && (
        <ActionModal
          type={modal}
          shop={shop}
          products={products}
          customers={customers}
          prefillBarcode={prefillBarcode}
          prefillCustomerId={prefillCustomerId}
          onClose={() => { setModal(null); setPrefillBarcode(null); setPrefillCustomerId(null) }}
          onSaleDone={afterSale}
          onProductDone={afterProduct}
          onPaymentDone={afterPayment}
          onGoAddStock={() => setModal('add-stock')}
        />
      )}

      {scanOpen && shop && (
        <ScanModal
          shop={shop}
          onClose={() => setScanOpen(false)}
          onVoiceCommand={runVoiceCommand}
          onAddNewProduct={addProductFromScan}
        />
      )}

      {invoiceModalOpen && shop && (
        <InvoiceModal shop={shop} onClose={() => setInvoiceModalOpen(false)} />
      )}

      {voiceSupported && (
        <button
          type="button"
          className={`floating-mic floating-mic-${listening ? 'listening' : voiceBusy ? 'processing' : voiceStatus}`}
          onPointerDown={voiceStart}
          onPointerUp={voiceStop}
          onPointerLeave={voiceStop}
          aria-label="Hold to talk to DukaanAI"
          title="Hold to talk to DukaanAI — works from anywhere on the page"
        >
          <Icon.mic className="floating-mic-icon" />
        </button>
      )}

      {toast && (
        <div className={`toast toast-${toast.tone}`} role="status">
          {toast.msg}
        </div>
      )}
    </div>
  )
}
