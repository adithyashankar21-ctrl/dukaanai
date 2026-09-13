export const API_BASE = 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (typeof body?.detail === 'string') detail = body.detail
    } catch {
      /* non-JSON error body */
    }
    const err = new Error(detail)
    err.status = res.status
    throw err
  }
  return res.json()
}

export const api = {
  get: (path) => request(path),
  post: (path, body) =>
    request(path, { method: 'POST', body: JSON.stringify(body) }),
}

/* --- shop bootstrap -------------------------------------------------------
   The app is single-shop: reuse the existing shop if the backend has one,
   otherwise create it via the existing POST /shops/ endpoint. */
export async function ensureShop() {
  const shops = await api.get('/shops/')
  if (Array.isArray(shops) && shops.length > 0) return shops[0]
  return api.post('/shops/', {
    name: 'Sharma Kirana',
    owner_name: 'Shopkeeper',
    language: 'English',
  })
}

/* --- voice command --------------------------------------------------------
   Sends a transcript (from speech or typed) to the backend voice assistant,
   which resolves entities and executes real business operations through the
   exact same services the UI buttons use, then replies in natural language.
   contextProductId (optional) tells the assistant which product is on
   screen right now — e.g. just scanned — so "add 40 units" or "sell 2"
   resolve without the shopkeeper having to name it. */
export function sendVoiceCommand(shopId, sessionId, text, contextProductId) {
  return api.post('/voice/command', {
    shop_id: shopId,
    session_id: sessionId,
    text,
    context_product_id: contextProductId ?? null,
  })
}

/* --- barcode scan -----------------------------------------------------------
   Looks a product up by barcode and returns the same live AI analysis as the
   stock advisor for it — stock, margin, velocity, predicted stockout — in
   one call. Throws (404) if no product in this shop has that barcode. */
export function scanBarcode(shopId, barcode) {
  return api.get(`/stock-advisor/scan?shop_id=${shopId}&barcode=${encodeURIComponent(barcode)}`)
}

/* Re-fetch one product's AI analysis by ID — used to refresh a scanned
   product's card after a voice command changes its stock. */
export function getProductAdvice(shopId, productId) {
  return api.get(`/stock-advisor/product/${productId}?shop_id=${shopId}`)
}

/* --- Dukaan Radar ------------------------------------------------------------
   Anomaly detection: products selling meaningfully more or less than their
   normal pace today. */
export function getRadarAlerts(shopId) {
  return api.get(`/radar/?shop_id=${shopId}`)
}

/* --- invoices --------------------------------------------------------------
   Look an invoice up by its human-facing number (e.g. "INV-000006") and get
   a printable, AI-personalized PDF for it. */
export function getInvoiceByNumber(shopId, invoiceNumber) {
  return api.get(`/invoices/by-number/${encodeURIComponent(invoiceNumber)}?shop_id=${shopId}`)
}

export function invoicePdfUrl(shopId, invoiceNumber) {
  return `${API_BASE}/invoices/by-number/${encodeURIComponent(invoiceNumber)}/pdf?shop_id=${shopId}`
}

/* --- udhaar / customer summaries --------------------------------------------
   Every customer with real balance, last payment and last purchase data —
   the Udhaar view's data source. */
export function getCustomerSummaries(shopId) {
  return api.get(`/credit/summaries?shop_id=${shopId}`)
}

/* --- smooth scroll to a page section ------------------------------------- */
export function scrollToSection(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

/* --- push into view for modals -------------------------------------------- */
export function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
