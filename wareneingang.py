#!/usr/bin/env python3
"""
weclapp Wareneingang – lokaler Proxy-Server
Starten: python wareneingang.py
Dann im Browser: http://localhost:8080
"""

import json
import gzip
import urllib.request
import urllib.error
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

import os

TENANT     = os.environ.get("WECLAPP_TENANT",  "fxnkvvkfhuynqzn.weclapp.com")
API_KEY    = os.environ.get("WECLAPP_API_KEY", "3d4e814f-6d2f-4f55-983b-f804a96b7324")
PORT       = int(os.environ.get("PORT", 8080))

# E-Mail Konfiguration
EMAIL_FROM = os.environ.get("EMAIL_FROM", "nextwavegmbh@gmail.com")
EMAIL_TO   = os.environ.get("EMAIL_TO",   "mustafa@next-wave.tech")
EMAIL_SMTP = os.environ.get("EMAIL_SMTP", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 465))
EMAIL_USER = os.environ.get("EMAIL_USER", "nextwavegmbh@gmail.com")
EMAIL_PASS = os.environ.get("EMAIL_PASS", "ljfgxikfgfqppbmf")

JSESSIONID = os.environ.get("JSESSIONID", "")

HTML = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>weclapp – Wareneingang</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f3ef;color:#1a1a1a;min-height:100vh;padding:2rem 1rem}
.container{max-width:800px;margin:0 auto}
h1{font-size:22px;font-weight:600;margin-bottom:4px}
.subtitle{font-size:13px;color:#666;margin-bottom:1.5rem}
.card{background:#fff;border:1px solid #e0deda;border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:1rem}
.card-title{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#888;margin-bottom:12px}
button{padding:8px 18px;border:1px solid #d0ceca;border-radius:8px;font-size:13px;background:transparent;color:#111;cursor:pointer;transition:background .12s}
button:hover{background:#f0ede8}
button.primary{background:#185FA5;color:#fff;border-color:#185FA5;font-weight:500}
button.primary:hover{background:#0C447C}
button:disabled{opacity:.4;cursor:not-allowed}
.order-list{display:flex;flex-direction:column;gap:8px}
.order-card{border:1px solid #e0deda;border-radius:10px;padding:12px 14px;cursor:pointer;transition:border-color .15s,background .15s}
.order-card:hover{border-color:#bbb;background:#faf9f7}
.order-card.selected{border-color:#185FA5;background:#eef4fb}
.order-meta{display:flex;justify-content:space-between;align-items:center}
.order-num{font-size:14px;font-weight:600}
.order-sub{font-size:12px;color:#777;margin-top:3px}
.badge{font-size:11px;padding:2px 8px;border-radius:6px;font-weight:500}
.badge-confirmed{background:#FAEEDA;color:#854F0B}
.badge-partial{background:#E6F1FB;color:#185FA5}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:#777;font-weight:500;padding:6px 10px;border-bottom:1px solid #eee}
td{padding:10px;border-bottom:1px solid #f0ede8;vertical-align:top}
tr:last-child td{border-bottom:none}
.sn-row{display:flex;gap:6px;align-items:center}
.sn-input{flex:1;padding:5px 8px;border:1px solid #d8d6d1;border-radius:6px;font-size:12px;background:#faf9f7;color:#111;outline:none}
.sn-input:focus{border-color:#185FA5;background:#fff}
.sn-add{padding:5px 10px;font-size:12px}
.sn-tags{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.sn-tag{display:inline-flex;align-items:center;gap:3px;background:#E6F1FB;color:#0C447C;font-size:11px;padding:2px 8px;border-radius:6px}
.sn-tag button{background:none;border:none;color:#185FA5;cursor:pointer;font-size:14px;padding:0 1px;line-height:1}
.sn-count{font-size:11px;color:#aaa;margin-top:3px}
.msg{font-size:13px;padding:10px 14px;border-radius:8px;margin-top:12px}
.msg-ok{background:#EAF3DE;color:#3B6D11}
.msg-err{background:#FCEBEB;color:#A32D2D}
.actions{display:flex;gap:8px;margin-top:1rem}
.spinner{display:inline-block;width:13px;height:13px;border:2px solid #cce0f5;border-top-color:#185FA5;border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle}
@keyframes spin{to{transform:rotate(360deg)}}
.empty{text-align:center;padding:24px 0;font-size:13px;color:#aaa}
</style>
</head>
<body>
<div class="container">
  <h1>Wareneingang erfassen</h1>
  <p class="subtitle">Bestätigte Bestellungen · Seriennummern erfassen · Wareneingang buchen</p>

  <div class="card">
    <div class="card-title">Verbindung</div>
    <p style="font-size:13px;color:#555;margin-bottom:8px">Tenant: <strong>fxnkvvkfhuynqzn.weclapp.com</strong></p>
    <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap">
      <button class="primary" onclick="loadOrders()">Bestellungen laden</button>
    </div>

    <div id="conn-msg"></div>
  </div>

  <div class="card">
    <div class="card-title">Bestellungen</div>
    <div class="order-list" id="order-list">
      <div class="empty">Bestellungen laden um zu starten.</div>
    </div>
  </div>

  <div class="card" id="items-card" style="display:none">
    <div class="card-title" id="items-title">Positionen</div>
    <table>
      <thead><tr><th style="width:38%">Artikel</th><th style="width:12%;text-align:center">Ausstehend</th><th>Seriennummern</th></tr></thead>
      <tbody id="items-body"></tbody>
    </table>
    <div class="actions">
      <button class="primary" id="book-btn" onclick="bookGoodsReceipt()">Wareneingang buchen</button>
      <button onclick="clearSelection()">Abbrechen</button>
    </div>
    <div id="book-msg"></div>
  </div>
</div>

<script>
let selectedOrder = null;
let serialNumbers  = {};

async function api(path, method, body) {
  const opts = { method: method||'GET', headers:{'Content-Type':'application/json'} };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch('/proxy?path=' + encodeURIComponent(path), opts);
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || JSON.stringify(data).slice(0,300));
  return data;
}

async function saveEmailPass() {
  const pass = document.getElementById('email-pass').value;
  if (!pass) return;
  const r = await fetch('/set_email_pass?pass=' + encodeURIComponent(pass));
  const d = await r.json();
  const msg = document.getElementById('email-pass-msg');
  msg.textContent = d.success ? '✓ Gespeichert' : 'Fehler';
  msg.style.color = d.success ? '#3B6D11' : '#A32D2D';
}

function showSessionInput() {
  const row = document.getElementById('session-row');
  row.style.display = row.style.display === 'none' ? 'block' : 'none';
}

async function saveSession() {
  const sid = document.getElementById('session-input').value.trim();
  if (!sid) return;
  const r = await fetch('/set_session?sid=' + encodeURIComponent(sid));
  const d = await r.json();
  const msg = document.getElementById('session-msg');
  if (d.success) {
    msg.innerHTML = '<div class="msg msg-ok" style="margin-top:6px">Session gespeichert!</div>';
    document.getElementById('session-btn').style.background = '#EAF3DE';
    document.getElementById('session-btn').style.borderColor = '#EAF3DE';
    document.getElementById('session-btn').style.color = '#3B6D11';
    document.getElementById('session-btn').textContent = '✓ Session aktiv';
    setTimeout(() => { document.getElementById('session-row').style.display='none'; }, 1500);
  } else {
    msg.innerHTML = '<div class="msg msg-err" style="margin-top:6px">Fehler: ' + d.error + '</div>';
  }
}

async function loadOrders() {
  const list = document.getElementById('order-list');
  document.getElementById('conn-msg').innerHTML = '';
  document.getElementById('items-card').style.display = 'none';
  list.innerHTML = '<div class="empty"><span class="spinner"></span>&nbsp;Lade...</div>';
  const OPEN = ['ORDER_CONFIRMATION_RECEIVED','ORDERED','CONFIRMED','PARTIALLY_DELIVERED','IN_PROGRESS'];
  try {
    // Alle Seiten durchladen bis keine Ergebnisse mehr (max 10 Seiten = 1000 Bestellungen)
    let found = [];
    for (let page = 1; page <= 10; page++) {
      const data = await api(`purchaseOrder?orderByField=createdDate&orderByType=DESC&pageSize=100&page=${page}`);
      const batch = data.result || [];
        if (batch.length === 0) break;
      found = found.concat(batch.filter(o => OPEN.includes(o.status)));
      if (batch.length < 100) break; // letzte Seite erreicht
    }
    if (!found.length) {
      list.innerHTML='<div class="empty">Keine offenen/bestätigten Bestellungen gefunden.</div>';
      return;
    }
    // Neueste zuerst sortieren
    found.sort((a,b) => (parseInt(b.orderDate)||0) - (parseInt(a.orderDate)||0));

    // Debug: alle Felder der ersten Bestellung loggen
    if (found[0]) {
      const strFields = Object.entries(found[0]).filter(([k,v])=>typeof v==='string'&&v).map(([k,v])=>`${k}=${v}`);
      console.log('Bestellfelder (strings):', strFields.join(' | '));
    }

    list.innerHTML='';
    // Lieferantennamen parallel laden (max 5 gleichzeitig)
    const supplierIds = [...new Set(found.map(o => o.supplierId).filter(Boolean))];
    const supplierMap = {};
    // In Batches von 5 laden
    for (let i = 0; i < supplierIds.length; i += 5) {
      const batch = supplierIds.slice(i, i + 5);
      await Promise.all(batch.map(async sid => {
        try { const s = await api(`supplier/id/${sid}`); supplierMap[sid] = s.company || s.name || ''; } catch(e) {}
      }));
    }
    found.forEach(o => {
      const d = document.createElement('div');
      d.className='order-card'; d.dataset.id=o.id;
      const num = o.purchaseOrderNumber || o.orderNumber || o.id;
      const supplier = supplierMap[o.supplierId] || '—';
      const dateStr = o.orderDate ? new Date(parseInt(o.orderDate)).toLocaleDateString('de-DE') : '—';
      const bc = o.status==='PARTIALLY_DELIVERED' ? 'badge-partial' : 'badge-confirmed';
      const bl = o.status==='PARTIALLY_DELIVERED' ? 'Teillieferung' : 'Bestätigt';
      o._supplierName = supplier;
      d.innerHTML=`<div class="order-meta"><span class="order-num">${num}</span><span class="badge ${bc}">${bl}</span></div><div class="order-sub"><span style="font-weight:500;color:#333">${supplier}</span> &middot; ${dateStr}</div>`;
      d.onclick=()=>selectOrder(o);
      list.appendChild(d);
    });
  } catch(e) {
    list.innerHTML=`<div class="empty" style="color:#A32D2D">Fehler: ${e.message}</div>`;
    console.error(e);
  }
}

async function selectOrder(order) {
  document.querySelectorAll('.order-card').forEach(c=>c.classList.remove('selected'));
  document.querySelector(`.order-card[data-id="${order.id}"]`)?.classList.add('selected');
  selectedOrder=order; serialNumbers={};
  // Lieferantenname bereits beim Laden gesetzt via order._supplierName
  document.getElementById('book-msg').innerHTML='';
  document.getElementById('items-card').style.display='block';
  const num = order.orderNumber || order.purchaseOrderNumber || order.number || order.id;
  document.getElementById('items-title').textContent=`Positionen – ${num}`;
  const tbody=document.getElementById('items-body');
  tbody.innerHTML='<tr><td colspan="3" style="text-align:center;padding:20px"><span class="spinner"></span></td></tr>';
  try {
    const data=await api(`purchaseOrder/id/${order.id}`);
    console.log('Detail Top-Level:', Object.keys(data).join(', '));
    if (data.purchaseOrderItems?.[0]) {
      const item0 = data.purchaseOrderItems[0];
      const strFields = Object.entries(item0).filter(([k,v])=>typeof v==='string'&&v).map(([k,v])=>`${k}=${v}`);
    }
    const items=(data.purchaseOrderItems||[]).filter(i=>(i.quantity||0)-(i.receivedQuantity||0)>0);
    if (!items.length){tbody.innerHTML='<tr><td colspan="3" style="text-align:center;color:#aaa;padding:20px">Alle Positionen bereits geliefert.</td></tr>';return;}
    tbody.innerHTML='';
    for (const item of items) {
      const out=Math.round((item.quantity||0)-(item.receivedQuantity||0));
      serialNumbers[item.id]=[];
      const artNr = item.articleNumber || '';
      // Eigene Artikelbezeichnung via article API
      let desc = item.title || '';
      try {
        const art = await api(`article/id/${item.articleId}`);
        desc = art.name || art.description || desc;
        item._articleName = desc;
      } catch(e) {}
      const tr=document.createElement('tr');
      tr.innerHTML=`<td><div style="font-weight:600">${artNr}</div><div style="font-size:12px;color:#555;margin-top:2px;font-weight:500">${desc}</div></td><td style="text-align:center;font-weight:600;color:#185FA5">${out}</td><td><div class="sn-row"><input class="sn-input" id="sn-inp-${item.id}" placeholder="Seriennummer (Enter oder mehrere einfügen)" 
  onkeydown="if(event.key==='Enter'){event.preventDefault();addSN('${item.id}',${out})}"
  onpaste="event.preventDefault();const txt=event.clipboardData.getData('text');txt.split(/[\\n\\r,;\\t]+/).map(s=>s.trim()).filter(Boolean).forEach(s=>{document.getElementById('sn-inp-${item.id}').value=s;addSN('${item.id}',${out});});"/><button class="sn-add" onclick="addSN('${item.id}',${out})">+ Add</button></div><div class="sn-tags" id="sn-tags-${item.id}"></div><div class="sn-count" id="sn-count-${item.id}"></div></td>`;
      tbody.appendChild(tr);
    }
    selectedOrder._items=items;
    document.getElementById('items-card').scrollIntoView({behavior:'smooth',block:'start'});
  } catch(e){tbody.innerHTML=`<tr><td colspan="3" style="color:#A32D2D;padding:12px">Fehler: ${e.message}</td></tr>`;console.error(e);}
}

function addSN(itemId,max){
  const inp=document.getElementById(`sn-inp-${itemId}`);
  const val=inp.value.trim(); if(!val)return;
  if(serialNumbers[itemId].length>=max){inp.style.borderColor='#E24B4A';setTimeout(()=>inp.style.borderColor='',1000);return;}
  if(serialNumbers[itemId].includes(val)){inp.style.borderColor='#EF9F27';setTimeout(()=>inp.style.borderColor='',800);inp.value='';return;}
  serialNumbers[itemId].push(val); inp.value=''; inp.style.borderColor='';
  renderTags(itemId,max); inp.focus();
}
function removeSN(itemId,sn){
  serialNumbers[itemId]=serialNumbers[itemId].filter(s=>s!==sn);
  const item=(selectedOrder._items||[]).find(i=>i.id===itemId);
  const max=item?Math.round((item.quantity||0)-(item.receivedQuantity||0)):0;
  renderTags(itemId,max);
}
function renderTags(itemId,max){
  document.getElementById(`sn-tags-${itemId}`).innerHTML=serialNumbers[itemId].map(sn=>`<span class="sn-tag">${sn}<button onclick="removeSN('${itemId}','${sn}')">&times;</button></span>`).join('');
  const n=serialNumbers[itemId].length;
  document.getElementById(`sn-count-${itemId}`).textContent=n>0?`${n} / ${max} erfasst`:'';
}
function clearSelection(){
  selectedOrder=null;serialNumbers={};
  document.getElementById('items-card').style.display='none';
  document.querySelectorAll('.order-card').forEach(c=>c.classList.remove('selected'));
}
async function bookGoodsReceipt(){
  const btn=document.getElementById('book-btn');
  const msgEl=document.getElementById('book-msg');
  msgEl.innerHTML='';
  const items=selectedOrder._items||[];
  const receiptItems=items.filter(i=>serialNumbers[i.id]&&serialNumbers[i.id].length>0).map(i=>({purchaseOrderItemId:i.id,quantity:serialNumbers[i.id].length,serialNumbers:serialNumbers[i.id].map(sn=>({serialNumber:sn}))}));
  if(!receiptItems.length){msgEl.innerHTML='<div class="msg msg-err">Bitte mindestens eine Seriennummer erfassen.</div>';return;}
  btn.disabled=true; btn.innerHTML='<span class="spinner"></span>&nbsp;Buche...';
  try{
    // Schritt 1: Wareneingang mit S/N erstellen
    // serialNumbers sind Strings ["SN123", "SN456"]
    // S/N via serialNumbers direkt bei createIncomingGoods übergeben
    const payload = {
      purchaseOrderItems: receiptItems.map(i => ({
        purchaseOrderItemId: i.purchaseOrderItemId,
        quantity: i.quantity,
        serialNumbers: i.serialNumbers.map(sn => ({
          serialNumber: typeof sn === 'string' ? sn : sn.serialNumber
        }))
      }))
    };
    console.log('Payload:', JSON.stringify(payload));
    const result = await api(`purchaseOrder/id/${selectedOrder.id}/createIncomingGoods`,'POST',payload);
    console.log('Antwort:', JSON.stringify(result));

    // Schritt 2: S/N setzen + Abschluss
    const incomingId = result.id || (result.result && result.result.id);
    if (incomingId) {
      console.log('incomingGoods ID:', incomingId);

      // Detail abrufen um incomingGoodsItems IDs zu bekommen
      const igDetail = await api(`incomingGoods/id/${incomingId}`);
      console.log('Status:', igDetail.status);
      console.log('incomingGoodsItems:', JSON.stringify(igDetail.incomingGoodsItems));

      // S/N via separaten PUT auf jedes incomingGoodsItem setzen
      console.log('incomingGoodsItems:', JSON.stringify(igDetail.incomingGoodsItems));
      // S/N wurde via serialNumbers in createIncomingGoods übergeben
      console.log('Antwort incomingGoodsItems:', JSON.stringify(igDetail.incomingGoodsItems?.[0]));
      // E-Mail mit Link senden
      const orderNum = selectedOrder.purchaseOrderNumber || selectedOrder.id;
      const supplierName = selectedOrder._supplierName || selectedOrder.supplierNumber || '';
      const snList = receiptItems.flatMap(i => i.serialNumbers.map(sn => typeof sn === 'string' ? sn : sn.serialNumber)).join('\n');
      // Artikelnamen direkt aus _items holen
      const articleNames = (selectedOrder._items || [])
        .filter(i => serialNumbers[i.id] && serialNumbers[i.id].length > 0)
        .map(i => i._articleName || i.description || i.title || i.articleNumber || '')
        .filter(Boolean)
        .join(', ');
      await fetch(`/send_email?incomingId=${incomingId}&purchaseOrderId=${selectedOrder.id}&orderNum=${encodeURIComponent(orderNum)}&supplier=${encodeURIComponent(supplierName)}&sns=${encodeURIComponent(snList)}&articles=${encodeURIComponent(articleNames)}`);
    } else {
      console.warn('Keine incomingGoods ID in Antwort:', JSON.stringify(result));
    }
        const rid = result && (result.id || (result.result && result.result.id));
    if(rid || result){
      const snDisplay = receiptItems.map(i => i.serialNumbers.map(sn => typeof sn === 'string' ? sn : sn.serialNumber).join(', ')).join(' | ');
      msgEl.innerHTML=`<div class="msg msg-ok">
        ✅ Wareneingang erstellt – E-Mail wurde an den Admin gesendet.<br>
        <span style="font-size:12px;color:#555">S/N: <strong>${snDisplay}</strong> – bitte dem Admin mitteilen falls nötig.</span>
      </div>`;
      setTimeout(()=>{loadOrders();clearSelection();},2200);
    } else {
      msgEl.innerHTML=`<div class="msg msg-err">Fehler: ${result.error||result.detail||result.message||JSON.stringify(result).slice(0,300)}</div>`;
    }
  }catch(e){
    if (e.message.includes('SESSION_EXPIRED')) {
      msgEl.innerHTML='<div class="msg msg-err">⚠ Session abgelaufen! Bitte oben auf <strong>"Session erneuern"</strong> klicken und neue JSESSIONID aus weclapp (F12 → Application → Cookies) einfügen.</div>';
    } else {
      msgEl.innerHTML=`<div class="msg msg-err">Fehler: ${e.message}</div>`;
    }
    console.error(e);
  }
  btn.disabled=false; btn.innerHTML='Wareneingang buchen';
}
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"  {args[0]} {args[1]}")

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode("utf-8"))
        elif self.path.startswith("/proxy"):
            self._proxy("GET", None)
        elif self.path.startswith("/jsf_book"):
            self._jsf_book()
        elif self.path.startswith("/set_session"):
            self._set_session()
        elif self.path.startswith("/send_email"):
            self._send_email()
        elif self.path.startswith("/webhook"):
            self._handle_webhook()
        elif self.path.startswith("/copy_sn"):
            self._copy_sn()
        elif self.path.startswith("/debug_ig"):
            self._debug_ig()
        elif self.path.startswith("/swagger"):
            self._get_swagger()
        elif self.path.startswith("/test_sn"):
            self._test_sn()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith("/webhook"):
            self._handle_webhook()
        elif self.path.startswith("/proxy"):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else None
            self._proxy("POST", body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        if self.path.startswith("/proxy"):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else None
            self._proxy("PUT", body)
        else:
            self.send_response(404)
            self.end_headers()

    def _test_sn(self):
        results = {}
        tests = [
            ("GET", "serialNumber?pageSize=3"),
            ("GET", "article/id/5328"),
            ("GET", "incomingGoods?orderByField=createdDate&orderByType=DESC&pageSize=1"),
        ]
        for method, path in tests:
            url = f"https://{TENANT}/webapp/api/v1/{path}"
            req = urllib.request.Request(url, method=method)
            req.add_header("AuthenticationToken", API_KEY)
            req.add_header("Accept", "application/json")
            try:
                with urllib.request.urlopen(req) as r:
                    data = r.read()
                    if r.headers.get("Content-Encoding") == "gzip":
                        data = gzip.decompress(data)
                    parsed = json.loads(data)
                    results[path] = {"status": r.status, "keys": list(parsed.keys()) if isinstance(parsed, dict) else str(parsed)[:200]}
                    print(f"  {method} {path}: {r.status}")
                    if path.startswith("serialNumber"):
                        print(f"  Seriennummern: {json.dumps(parsed)[:500]}")
                    if path.startswith("article"):
                        art = parsed
                        print(f"  Artikel serialNumberRequired: {art.get('serialNumberRequired')}")
                        print(f"  Artikel useSerialnumbers: {art.get('useSerialnumbers')}")
                        print(f"  Artikel Keys: {list(art.keys())}")
            except urllib.error.HTTPError as e:
                results[path] = {"status": e.code}
                print(f"  {method} {path}: HTTP {e.code}")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(results).encode())

    def _get_swagger(self):
        try:
            url = f"https://{TENANT}/webapp/api/v1/incomingGoods/swagger.json"
            req = urllib.request.Request(url)
            req.add_header("AuthenticationToken", API_KEY)
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req) as r:
                data = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)
            # Suche nach createIncomingGoods und serialNumbers
            text = data.decode('utf-8')
            # Zeige relevante Teile
            idx = text.find('createIncomingGoods')
            print(f"createIncomingGoods Kontext: {text[max(0,idx-100):idx+500]}")
            idx2 = text.find('serialNumber')
            print(f"serialNumber Kontext: {text[max(0,idx2-100):idx2+300]}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data[:5000])
        except Exception as e:
            print(f"Swagger Fehler: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _debug_ig(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        ig_id = qs.get("id", [""])[0]
        try:
            # Detail abrufen
            url = f"https://{TENANT}/webapp/api/v1/incomingGoods/id/{ig_id}"
            req = urllib.request.Request(url)
            req.add_header("AuthenticationToken", API_KEY)
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req) as r:
                data = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)
                detail = json.loads(data)
            print(f"  incomingGoods {ig_id}:")
            print(f"    status: {detail.get('status')}")
            print(f"    incomingGoodsType: {detail.get('incomingGoodsType')}")
            print(f"    version: {detail.get('version')}")
            print(f"    warehouseId: {detail.get('warehouseId')}")
            # Alle möglichen Action-Endpunkte testen
            actions = ['postToWarehouse','finishIncomingGoods','finish','complete','book','setStatusToFinished','markAsFinished','post']
            results = {}
            for action in actions:
                try:
                    aurl = f"https://{TENANT}/webapp/api/v1/incomingGoods/id/{ig_id}/{action}"
                    areq = urllib.request.Request(aurl, data=b'{}', method='POST')
                    areq.add_header("AuthenticationToken", API_KEY)
                    areq.add_header("Content-Type", "application/json")
                    areq.add_header("Accept", "application/json")
                    with urllib.request.urlopen(areq) as ar:
                        adata = ar.read()
                        results[action] = f"SUCCESS {ar.status}"
                        print(f"    ACTION {action}: SUCCESS {ar.status}")
                except urllib.error.HTTPError as he:
                    results[action] = f"HTTP {he.code}"
                    print(f"    ACTION {action}: HTTP {he.code}")
                except Exception as ae:
                    results[action] = str(ae)[:50]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": detail.get("status"), "actions": results}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _copy_sn(self):
        """Kopiert S/N in Clipboard und sendet Enter-Taste ans aktive Fenster"""
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        sn = qs.get("sn", [""])[0]
        try:
            # Clipboard setzen
            import subprocess
            # Windows: clip.exe
            proc = subprocess.Popen(['clip'], stdin=subprocess.PIPE, shell=True)
            proc.communicate(input=sn.encode('utf-16-le'))
            print(f"  S/N in Clipboard: {sn}")
            result = {"success": True, "sn": sn}
        except Exception as e:
            print(f"  Clipboard Fehler: {e}")
            result = {"success": False, "error": str(e)}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _handle_webhook(self):
        """weclapp Webhook - wird aufgerufen wenn Wareneingang ins Lager gebucht wird"""
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b""
            data = json.loads(body) if body else {}
            print(f"  Webhook empfangen: {json.dumps(data)[:200]}")

            # Prüfe ob es ein incomingGoods FINISHED Event ist
            entity_type = data.get("entityType", "")
            event_type = data.get("eventType", "")
            entity = data.get("entity", {})

            if "incomingGoods" in entity_type.lower() and entity.get("status") in ["FINISHED", "BOOKED", "POSTED"]:
                incoming_num = entity.get("incomingGoodsNumber", "")
                purchase_order_num = entity.get("purchaseOrderNumber", "")
                warehouse = entity.get("warehouseName", "Hauptlager")

                # E-Mail an Werkstudenten
                STUDENT_EMAIL = os.environ.get("STUDENT_EMAIL", "")
                if STUDENT_EMAIL:
                    subject = f"✅ Wareneingang {incoming_num} wurde ins Lager gebucht!"
                    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto">
  <div style="background:#28a745;padding:20px;border-radius:8px 8px 0 0">
    <h2 style="color:white;margin:0">✅ Ware eingebucht!</h2>
  </div>
  <div style="background:#f9f9f9;padding:24px;border:1px solid #e0e0e0;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse">
      <tr><td style="padding:8px;color:#666;width:160px">Wareneingang</td><td style="padding:8px;font-weight:bold">#{incoming_num}</td></tr>
      <tr><td style="padding:8px;color:#666">Bestellung</td><td style="padding:8px">{purchase_order_num}</td></tr>
      <tr><td style="padding:8px;color:#666">Lager</td><td style="padding:8px">{warehouse}</td></tr>
    </table>
    <p style="color:#555;margin-top:16px">Die Ware wurde erfolgreich ins Lager gebucht. Der Vorgang ist abgeschlossen.</p>
    <p style="color:#999;font-size:12px;text-align:center;margin-top:24px">Wareneingang App · NEXTWAVE GmbH</p>
  </div>
</body></html>"""
                    self._send_email_direct(STUDENT_EMAIL, subject, html)
                    print(f"  Benachrichtigung an Werkstudenten gesendet: {STUDENT_EMAIL}")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"received": True}).encode())
        except Exception as e:
            print(f"  Webhook Fehler: {e}")
            self.send_response(500)
            self.end_headers()

    def _send_email_direct(self, to_email, subject, html_body):
        """Sendet E-Mail via SendGrid"""
        SENDGRID_KEY = os.environ.get("SENDGRID_API_KEY", "")
        if not SENDGRID_KEY:
            return
        payload = json.dumps({
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": EMAIL_FROM},
            "subject": subject,
            "content": [{"type": "text/html", "value": html_body}]
        }).encode("utf-8")
        req = urllib.request.Request("https://api.sendgrid.com/v3/mail/send", data=payload, method="POST")
        req.add_header("Authorization", f"Bearer {SENDGRID_KEY}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as r:
                print(f"  E-Mail an {to_email} gesendet: {r.status}")
        except Exception as e:
            print(f"  E-Mail Fehler: {e}")

    def _set_email_pass(self):
        from urllib.parse import urlparse, parse_qs
        global EMAIL_PASS
        qs = parse_qs(urlparse(self.path).query)
        EMAIL_PASS = qs.get("pass", [""])[0]
        print(f"  E-Mail Passwort gesetzt")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"success": True}).encode())

    def _send_email(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        incoming_id       = qs.get("incomingId",       [""])[0]
        purchase_order_id = qs.get("purchaseOrderId", [""])[0]
        order_num         = qs.get("orderNum",         [""])[0]
        articles          = qs.get("articles",         [""])[0]
        supplier    = qs.get("supplier",   [""])[0]
        sns         = qs.get("sns",        [""])[0]

        weclapp_url = f"https://{TENANT}/app/incoming-goods/{incoming_id}"
        subject = f"Wareneingang {order_num} - Bitte ins Lager buchen"

        # S/N untereinander formatieren
        sn_list = sns.replace(" | ", "\n").replace(", ", "\n").replace(",", "\n")
        # sn_lines nicht mehr benötigt

        copy_script = """<script>
        function copyAllSN() {
            var el = document.getElementById('all-sns');
            var txt = el.innerText || el.textContent;
            navigator.clipboard.writeText(txt).then(function() {
                var btn = document.getElementById('copy-btn');
                btn.innerText = '\u2705 Kopiert!';
                btn.style.background = '#28a745';
                setTimeout(function(){ 
                    btn.innerText = '\U0001f4cb Alle S/N kopieren';
                    btn.style.background = '#185FA5';
                }, 2000);
            });
        }
        </script>"""

        # S/N als URL-encoded für mailto Link (Desktop Fallback)
        sn_mailto = "%0A".join(sn_list.split("\n"))  # %0A = Zeilenumbruch in URL

        html_body = f"""<html><head>{copy_script}</head><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
  <div style="background:#185FA5;padding:20px;border-radius:8px 8px 0 0">
    <h2 style="color:white;margin:0">&#128230; Wareneingang erfasst</h2>
  </div>
  <div style="background:#f9f9f9;padding:24px;border:1px solid #e0e0e0;border-radius:0 0 8px 8px">
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
      <tr><td style="padding:8px;color:#666;width:140px">Bestellung</td><td style="padding:8px;font-weight:bold">{order_num}</td></tr>
      <tr><td style="padding:8px;color:#666">Lieferant</td><td style="padding:8px">{supplier}</td></tr>
      <tr><td style="padding:8px;color:#666">Artikel</td><td style="padding:8px;font-weight:500">{articles}</td></tr>
      <tr><td style="padding:8px;color:#666">Wareneingang</td><td style="padding:8px">#{incoming_id}</td></tr>
    </table>
    <div style="margin-bottom:20px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <p style="font-weight:bold;color:#333;margin:0">&#128196; Seriennummern:</p>
        <span>
          <!-- Mobile: JavaScript Button -->
          <button id="copy-btn" onclick="copyAllSN()" 
                  style="background:#185FA5;color:white;border:none;padding:8px 14px;border-radius:6px;
                         font-size:12px;cursor:pointer;font-weight:bold">
            &#128203; Alle S/N kopieren
          </button>
        </span>
      </div>
      <pre id="all-sns" style="background:#eef6ff;border:2px solid #185FA5;border-radius:4px;
                                padding:12px 16px;margin-top:8px;font-family:monospace;font-size:15px;
                                color:#0C447C;white-space:pre;line-height:2.0;
                                user-select:all;-webkit-user-select:all">{sn_list}</pre>
      <p style="font-size:11px;color:#555;margin-top:6px;background:#fff3cd;padding:6px 10px;border-radius:4px;border-left:3px solid #ffc107">
        &#128161; <strong>Desktop:</strong> Klicke in den blauen S/N-Block oben → Strg+A → Strg+C &nbsp;|&nbsp;
        <strong>Handy:</strong> "Alle S/N kopieren" Button
      </p>
    </div>
    <div style="text-align:center;margin:24px 0">
      <a href="{weclapp_url}" style="background:#28a745;color:white;padding:14px 32px;border-radius:8px;text-decoration:none;font-size:16px;font-weight:bold;display:inline-block">
        &#128279; Wareneingang in weclapp öffnen
      </a>
    </div>
    <p style="color:#999;font-size:12px;text-align:center">Wareneingang App · NEXTWAVE GmbH</p>
  </div>
</body></html>"""

        try:
            # E-Mail via SendGrid API (HTTPS) - Railway-kompatibel
            SENDGRID_KEY = os.environ.get("SENDGRID_API_KEY", "")
            if SENDGRID_KEY:
                sg_payload = json.dumps({
                    "personalizations": [{"to": [{"email": EMAIL_TO}]}],
                    "from": {"email": EMAIL_FROM},
                    "subject": subject,
                    "content": [{"type": "text/html", "value": html_body}]
                }).encode("utf-8")
                sg_req = urllib.request.Request(
                    "https://api.sendgrid.com/v3/mail/send",
                    data=sg_payload, method="POST"
                )
                sg_req.add_header("Authorization", f"Bearer {SENDGRID_KEY}")
                sg_req.add_header("Content-Type", "application/json")
                with urllib.request.urlopen(sg_req) as sg_r:
                    print(f"  E-Mail via SendGrid gesendet: {sg_r.status}")
            else:
                # Fallback: SMTP
                import smtplib, ssl
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = EMAIL_FROM
                msg["To"] = EMAIL_TO
                msg.attach(MIMEText(html_body, "html"))
                context = ssl.create_default_context()
                with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.login(EMAIL_USER, EMAIL_PASS)
                    server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
            print(f"  E-Mail gesendet an {EMAIL_TO}")
            result = {"success": True}
        except Exception as e:
            print(f"  E-Mail Fehler: {e}")
            result = {"success": False, "error": str(e)}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _set_session(self):
        from urllib.parse import urlparse, parse_qs
        global JSESSIONID
        qs = parse_qs(urlparse(self.path).query)
        new_sid = qs.get("sid", [""])[0]
        if new_sid:
            JSESSIONID = new_sid
            print(f"  JSESSIONID aktualisiert: {new_sid[:20]}...")
            result = {"success": True}
        else:
            result = {"success": False, "error": "Kein sid Parameter"}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _jsf_book(self):
        from urllib.parse import urlparse, parse_qs
        import http.cookiejar, re
        qs = parse_qs(urlparse(self.path).query)
        incoming_id = qs.get("incomingId", [""])[0]

        try:
            global JSESSIONID
            if not JSESSIONID:
                raise Exception('SESSION_EXPIRED')

            # Schritt 1: Seite laden um ViewState zu holen
            page_url = f"https://{TENANT}/webapp/view/shipment/ShipmentDetailArrival.page?id={incoming_id}&entityName=IncomingGoods"
            req1 = urllib.request.Request(page_url)
            req1.add_header("Cookie", f"JSESSIONID={JSESSIONID}")
            req1.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
            req1.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            req1.add_header("Accept-Language", "de-DE,de;q=0.9")

            opener = urllib.request.build_opener()

            try:
                with opener.open(req1) as resp1:
                    html = resp1.read()
                    print(f"  HTTP Status: {resp1.status}")
                    print(f"  Content-Encoding: {resp1.headers.get('Content-Encoding')}")
                    print(f"  Content-Type: {resp1.headers.get('Content-Type')}")
                    if resp1.headers.get("Content-Encoding") == "gzip":
                        html = gzip.decompress(html)
                    html_str = html.decode("utf-8", errors="replace")
            except urllib.error.HTTPError as he:
                print(f"  HTTP Fehler beim Laden: {he.code} {he.reason}")
                err_body = he.read()
                print(f"  Fehler Body: {repr(err_body[:300])}")
                raise Exception(f"Seite nicht erreichbar: HTTP {he.code}")
            print(f"  Seite geladen: {len(html_str)} Zeichen")
            # Debug: HTML speichern und Anfang zeigen
            print(f"  HTML komplett: {repr(html_str)}")
            if "ViewState" in html_str:
                idx = html_str.find("ViewState")
                print(f"  ViewState-Kontext: {repr(html_str[max(0,idx-50):idx+200])}")

            # ViewState extrahieren
            vs_match = re.search(r'id="jakarta\.faces\.ViewState"[^>]*value="([^"]+)"', html_str)
            if not vs_match:
                vs_match = re.search(r'jakarta\.faces\.ViewState["\s]+value="([^"]+)"', html_str)
            if not vs_match:
                raise Exception("ViewState nicht gefunden in HTML")
            view_state = vs_match.group(1)
            print(f"  ViewState gefunden: {view_state[:30]}...")

            # Schritt 2: Form-POST mit idCompleteIncomingShipment
            form_data = urllib.parse.urlencode({
                "AJAXREQUEST": "_viewRoot",
                "pageForm": "pageForm",
                "files[]": "",
                "jakarta.faces.ViewState": view_state,
                "pageForm:idCompleteIncomingShipment": "pageForm:idCompleteIncomingShipment",
                "longTx": "900",
                "ajaxSingle": "pageForm:idCompleteIncomingShipment",
                "AJAX:EVENTS_COUNT": "1",
            }).encode("utf-8")

            post_url = f"https://{TENANT}/webapp/view/shipment/ShipmentDetailArrival.page"
            req2 = urllib.request.Request(post_url, data=form_data, method="POST")
            req2.add_header("Cookie", f"JSESSIONID={JSESSIONID}")
            req2.add_header("Content-Type", "application/x-www-form-urlencoded")
            req2.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            req2.add_header("Accept", "application/xml, text/xml, */*; q=0.01")
            req2.add_header("Referer", page_url)
            req2.add_header("X-Requested-With", "XMLHttpRequest")

            with opener.open(req2) as resp2:
                resp_data = resp2.read()
                if resp2.headers.get("Content-Encoding") == "gzip":
                    resp_data = gzip.decompress(resp_data)
                status_code = resp2.status
                print(f"  JSF POST Status: {status_code}")

            result = {"success": True, "status": status_code}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            print(f"  JSF Fehler: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())

    def _proxy(self, method, body):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        weclapp_path = qs.get("path", [""])[0]
        url = f"https://{TENANT}/webapp/api/v1/{weclapp_path}"

        print(f"  -> {method} {url}")

        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("AuthenticationToken", API_KEY)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")

        try:
            with urllib.request.urlopen(req) as resp:
                data = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    data = gzip.decompress(data)
                print(f"  <- {resp.status} ({len(data)} bytes)")
                self.send_response(resp.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            if e.headers.get("Content-Encoding") == "gzip":
                data = gzip.decompress(data)
            print(f"  <- HTTP {e.code}: {data[:300]}")
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            print(f"  <- Fehler: {e}")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"\n  weclapp Wareneingang gestartet")
    print(f"  Tenant : {TENANT}")
    print(f"  Oeffne : http://localhost:{PORT}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server gestoppt.")
