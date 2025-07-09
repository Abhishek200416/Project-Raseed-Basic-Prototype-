/* ───── CONFIG ───── */
const api = window.location.origin;
let lastItems = [];

/* ───── ELEMENTS ───── */
const receiptInput = document.getElementById('receipt');
const dropZone = document.getElementById('dropZone');
const fileLabel = document.getElementById('fileLabel');
const preview = document.getElementById('preview');
const uploadBtn = document.getElementById('uploadBtn');
const uploadProgress = document.getElementById('uploadProgress');
const formatter = document.getElementById('formatter');
const historyList = document.getElementById('historyList');
const qField = document.getElementById('q');
const askBtn = document.getElementById('askBtn');
const insightPre = document.getElementById('insight');
const clearInsight = document.getElementById('clearInsight');
const passLink = document.getElementById('passLink');
const toast = document.getElementById('toast');
const themeToggle = document.getElementById('themeToggle');

/* ───── THEME TOGGLE ───── */
themeToggle.addEventListener('change', () => {
    document.body.classList.toggle('dark', themeToggle.checked);
    toast.labelText = themeToggle.checked ? 'Dark mode on' : 'Light mode on';
    toast.show();
});

/* ───── DRAG & DROP ───── */
['dragenter', 'dragover'].forEach(evt =>
    dropZone.addEventListener(evt, e => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    })
);
['dragleave', 'drop'].forEach(evt =>
    dropZone.addEventListener(evt, e => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (evt === 'drop') {
            receiptInput.files = e.dataTransfer.files;
            showFile();
        }
    })
);
dropZone.addEventListener('click', () => receiptInput.click());
receiptInput.addEventListener('change', showFile);

function showFile() {
    const f = receiptInput.files[0];
    fileLabel.textContent = f ? f.name : 'Click or drop receipt here';
    preview.hidden = !f;
    if (f) preview.src = URL.createObjectURL(f);
}

/* ───── FORMAT ITEMS AS TABLE ───── */
const fmt = items =>
    !items.length ?
    'No items detected.' :
    `<table class="fmt-table">
         <thead><tr><th>Item</th><th>Price</th></tr></thead>
         <tbody>${items.map(i=>`<tr><td>${i.name}</td><td>${i.price}</td></tr>`).join('')}</tbody>
       </table>`;

/* ───── UPLOAD FLOW (XHR + progress) ───── */
uploadBtn.addEventListener('click', () => {
  if (!receiptInput.files.length) {
    toast.labelText = 'Pick a file first'; toast.show(); return;
  }
  uploadBtn.disabled = true;
  formatter.textContent = '';
  uploadProgress.hidden = false; uploadProgress.value = 0;

  const form = new FormData();
  form.append('file', receiptInput.files[0]);

  const xhr = new XMLHttpRequest();
  xhr.open('POST', `${api}/upload-receipt`);

  xhr.upload.onprogress = e => {
    if (e.lengthComputable) uploadProgress.value = (e.loaded / e.total) * 100;
  };

  xhr.onload = () => {
    uploadProgress.hidden = true;
    if (xhr.status>=200 && xhr.status<300) {
      const { items } = JSON.parse(xhr.responseText);
      lastItems   = items;
      formatter.innerHTML = fmt(items);
      saveHistory(items);
      toast.labelText = 'Receipt parsed & saved';
      preview.hidden = true;
    } else {
      let msg='Upload failed';
      try { msg = JSON.parse(xhr.responseText).detail || msg; }
      catch { msg = xhr.responseText; }
      toast.labelText = msg;
    }
    toast.show(); uploadBtn.disabled = false;
    renderHistory();
  };

  xhr.onerror = () => {
    uploadProgress.hidden = true;
    toast.labelText = 'Network error'; toast.show();
    uploadBtn.disabled = false;
  };

  xhr.send(form);
});

/* ───── HISTORY STORAGE ───── */
function saveHistory(items){
  const key  = 'praseed_history';
  const hist = JSON.parse(localStorage.getItem(key) || '[]');
  hist.unshift({ ts: new Date().toISOString(), items });
  localStorage.setItem(key, JSON.stringify(hist.slice(0,20)));
}

/* ───── RENDER HISTORY (robust) ───── */
function renderHistory() {
  const hist = JSON.parse(localStorage.getItem('praseed_history') || '[]');

  if (!hist.length) { historyList.innerHTML='<p>No history yet</p>'; return; }

  historyList.innerHTML = hist.map(entry => {
    //  ✨ guarantee items is always an array
    const safeItems = Array.isArray(entry.items) ? entry.items : [];
    const total     = safeItems.reduce((s,i)=>s+parseFloat(i.price||0),0).toFixed(2);
    const dt        = new Date(entry.ts).toLocaleString();

    const itemsHtml = safeItems.map((it,idx)=>`
      <li>
        <input class="edit-name"
               data-ts="${entry.ts}" data-idx="${idx}"
               value="${it.name}">
        <input class="edit-price price-input"
               data-ts="${entry.ts}" data-idx="${idx}"
               value="${it.price}">
        <button class="delete-item" data-ts="${entry.ts}" data-idx="${idx}">×</button>
      </li>`).join('');

    return `
      <details>
        <summary>
          <span>${dt} – ₹${total}</span>
          <button class="delete-entry" data-ts="${entry.ts}">🗑</button>
        </summary>
        <ul class="item-list">${itemsHtml}</ul>
        <div class="entry-total">Total: ₹<span>${total}</span></div>
      </details>`;
  }).join('');

  /* -- listeners ----- */
  historyList.querySelectorAll('.delete-entry')
             .forEach(btn => btn.addEventListener('click', onDeleteEntry));
  historyList.querySelectorAll('.delete-item')
             .forEach(btn => btn.addEventListener('click', onDeleteItem));
  historyList.querySelectorAll('.edit-name, .edit-price')
             .forEach(inp => inp.addEventListener('change', onEditItem));
}

function onDeleteEntry(e){
  const ts  = e.currentTarget.dataset.ts;
  const key = 'praseed_history';
  const hist = JSON.parse(localStorage.getItem(key)||'[]')
                    .filter(h => h.ts !== ts);
  localStorage.setItem(key, JSON.stringify(hist));
  renderHistory();
}

function onDeleteItem(e){
  const ts  = e.currentTarget.dataset.ts;
  const idx = +e.currentTarget.dataset.idx;
  const key = 'praseed_history';
  const hist = JSON.parse(localStorage.getItem(key)||'[]');
  const ent  = hist.find(h=>h.ts===ts);
  if (ent && Array.isArray(ent.items)) ent.items.splice(idx,1);
  localStorage.setItem(key, JSON.stringify(hist));
  renderHistory();
}

function onEditItem(e){
  const ts  = e.target.dataset.ts;
  const idx = +e.target.dataset.idx;
  const key = 'praseed_history';
  const hist= JSON.parse(localStorage.getItem(key)||'[]');
  const ent = hist.find(h=>h.ts===ts);
  if (!ent || !Array.isArray(ent.items) || !ent.items[idx]) return;
  if (e.target.classList.contains('edit-name')) {
    ent.items[idx].name  = e.target.value;
  } else {
    ent.items[idx].price = e.target.value;
  }
  localStorage.setItem(key, JSON.stringify(hist));
  renderHistory();
}

renderHistory();

/* ───── INSIGHT CHAT ───── */
askBtn.addEventListener('click', async () => {
  const q = qField.value.trim();
  if (!q){ toast.labelText='Enter a wallet query'; toast.show(); return; }

  askBtn.disabled = true;
  insightPre.textContent = 'Thinking…'; clearInsight.hidden = true;

  const allItems = JSON.parse(localStorage.getItem('praseed_history')||'[]')
                     .flatMap(h => Array.isArray(h.items)?h.items:[]);

  try {
    const res = await fetch(`${api}/insight`, {
      method: 'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ items: allItems, question: q })
    });
    if (!res.ok) {
      const err = await res.json().catch(()=>({}));
      throw new Error(err.detail||'Insight failed');
    }
    insightPre.textContent = (await res.json()).insight;
    clearInsight.hidden = false;
    passLink.hidden = false;
  } catch (err) {
    insightPre.textContent = '';
    toast.labelText = err.message; toast.show();
  } finally {
    askBtn.disabled = false;
  }
});

/* ───── CLEAR INSIGHT ───── */
clearInsight.addEventListener('click', ()=>{
  insightPre.textContent=''; clearInsight.hidden = true;
});