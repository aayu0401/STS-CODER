/* STS Coder v2.0 — Dual-Model App Logic (Light Theme & Z-CMD) */
(function () {
  'use strict';

  const API = 'http://127.0.0.1:8100';
  const $ = (s) => document.querySelector(s);

  // DOM refs
  const textarea      = $('#entry-input');
  const charCount     = $('#char-count');
  const fileInput     = $('#file-input');
  const btnGenerate   = $('#btn-generate');
  const btnClear      = $('#btn-clear-input');
  const chatHistory   = $('#chat-history');
  const btnCopy       = $('#btn-copy');
  const btnDownload   = $('#btn-download');
  const entryName     = $('#entry-name');
  const llmToggle     = $('#llm-toggle');
  const placeholder   = $('#output-placeholder');
  const processing    = $('#output-processing');
  const procStep      = $('#processing-step');
  const procFill      = $('#processing-fill');
  const procLabel     = $('#processing-model-label');
  const toast         = $('#toast');
  const ollamaDot     = $('#ollama-dot');
  const ollamaText    = $('#ollama-text');
  const llmBadge      = $('#llm-mode-badge');

  let mode = 'FULL', activeTab = 'analysis', lastResult = null;

  // ── Mode buttons ──
  document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.mode-btn').forEach(b => { b.classList.remove('active'); b.setAttribute('aria-checked','false'); });
      btn.classList.add('active'); btn.setAttribute('aria-checked','true');
      mode = btn.dataset.mode;
      
      // Update button title based on mode
      if (mode === 'ZCMD') {
        btnGenerate.title = 'Explain Z-Command';
      } else if (mode === 'CHAT') {
        btnGenerate.title = 'Send Chat Message';
      } else {
        btnGenerate.title = 'Generate Documentation';
      }
    });
  });

  // ── Tabs ──
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      if (!lastResult) return;
      document.querySelectorAll('.tab').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected','false'); });
      tab.classList.add('active'); tab.setAttribute('aria-selected','true');
      activeTab = tab.dataset.tab;
      showTab(activeTab);
    });
  });

  // ── Upload ──
  fileInput.addEventListener('change', () => { if (fileInput.files[0]) readFile(fileInput.files[0]); });

  function readFile(f) {
    const r = new FileReader();
    r.onload = e => { textarea.value = e.target.result; charCount.textContent = textarea.value.length + ' chars'; showToast('Loaded: ' + f.name); };
    r.readAsText(f);
  }

  // ── Textarea ──
  textarea.addEventListener('input', () => charCount.textContent = textarea.value.length + ' chars');
  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      btnGenerate.click();
    }
  });

  // ── Clear ──
  btnClear.addEventListener('click', () => {
    textarea.value = ''; entryName.value = ''; 
    charCount.textContent = '0 chars'; lastResult = null;
    chatHistory.innerHTML = `<div class="chat-message ai">
      <div class="msg-avatar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10H12V2z"/><path d="M12 12 2.1 12"/><path d="M12 12l8.6 5"/></svg>
      </div>
      <div class="msg-content">
        <p>Hello! I am your <strong>STS Copilot</strong>.</p>
        <p>Paste your IBM z/TPF assembly, REXX exec, or Z Command below. I will work with the Advisor to generate your VAR/TDR documentation and check for risks.</p>
      </div>
    </div>`;
    resetOutput(); llmBadge.classList.add('hidden');
  });

  // ── Copy / Download ──
  btnCopy.addEventListener('click', () => {
    const p = $('#result-' + activeTab);
    if (p) navigator.clipboard.writeText(p.innerText).then(() => showToast('Copied.'));
  });
  btnDownload.addEventListener('click', () => {
    const p = $('#result-' + activeTab);
    if (!p) return;
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([p.innerText], {type:'text/plain'}));
    a.download = 'STS_' + activeTab.toUpperCase() + '_' + (entryName.value||'OUTPUT') + '.txt';
    a.click(); URL.revokeObjectURL(a.href);
    showToast('Downloaded.');
  });

  // ── Generate ──
  btnGenerate.addEventListener('click', () => {
    const raw = textarea.value.trim();
    if (!raw) { showToast('Please enter a message or paste code.'); return; }
    
    // Validator: entry name must be exactly 5 characters
    const ename = entryName.value.trim();
    if (ename.length > 0 && ename.length !== 5) {
      showToast('ZTPF entry must be exactly 5 characters.');
      return;
    }
    
    // Append User Message to Chat
    const userMsg = document.createElement('div');
    userMsg.className = 'chat-message user';
    userMsg.innerHTML = `<div class="msg-avatar"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>
    <div class="msg-content">${esc(raw)}</div>`;
    chatHistory.appendChild(userMsg);
    chatHistory.scrollTop = chatHistory.scrollHeight;

    textarea.value = '';
    charCount.textContent = '0 chars';

    runGeneration(raw);
  });

  // ── Model status check ──
  $('#btn-check-models').addEventListener('click', checkModels);

  async function checkModels() {
    ollamaDot.className = 'status-dot'; ollamaText.textContent = 'Checking…';
    try {
      const r = await fetch(API + '/api/models', {signal: AbortSignal.timeout(5000)});
      if (!r.ok) throw new Error();
      const d = await r.json();
      if (d.ollama_available) {
        ollamaDot.className = 'status-dot ok'; ollamaText.textContent = 'Ollama Online';
        updatePill('pill-coder',   d.coder_ready);
        updatePill('pill-advisor', d.advisor_ready);
      } else {
        ollamaDot.className = 'status-dot warn'; ollamaText.textContent = 'Ollama Offline';
        updatePill('pill-coder', false); updatePill('pill-advisor', false);
      }
    } catch {
      ollamaDot.className = 'status-dot err'; ollamaText.textContent = 'API Offline';
    }
  }

  function updatePill(id, ready) {
    const el = $('#' + id);
    if (!el) return;
    el.classList.toggle('ready', ready);
    el.classList.toggle('offline', !ready);
  }

  // Check on load
  checkModels();

  // ── Toast ──
  function showToast(msg) {
    toast.textContent = msg; toast.classList.remove('hidden');
    clearTimeout(toast._t); toast._t = setTimeout(() => toast.classList.add('hidden'), 2600);
  }

  // ── Helpers ──
  function resetOutput() {
    placeholder.classList.remove('hidden');
    processing.classList.add('hidden');
    document.querySelectorAll('.result-panel').forEach(p => p.classList.add('hidden'));
    btnCopy.disabled = true; btnDownload.disabled = true;
  }

  function hideAll() {
    placeholder.classList.add('hidden');
    processing.classList.add('hidden');
    document.querySelectorAll('.result-panel').forEach(p => p.classList.add('hidden'));
  }

  function showTab(tab) {
    document.querySelectorAll('.result-panel').forEach(p => p.classList.add('hidden'));
    const p = $('#result-' + tab);
    if (p) p.classList.remove('hidden');
  }

  function activateTab(tab) {
    activeTab = tab;
    document.querySelectorAll('.tab').forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected','false'); });
    const t = $('[data-tab="' + tab + '"]');
    if (t) { t.classList.add('active'); t.setAttribute('aria-selected','true'); }
    showTab(tab);
  }

  function delay(ms) { return new Promise(r => setTimeout(r, ms)); }
  function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
  function pad(s, n) { return String(s).padEnd(n, ' '); }
  function metaCard(label, val) {
    return `<div class="meta-card"><div class="meta-card-label">${esc(label)}</div><div class="meta-card-value">${esc(String(val))}</div></div>`;
  }

  // ── Steps per mode ──
  const STEPS = {
    FULL:    ['Connecting to STS Coder API…', 'AI Engine: Analysing entry…', 'AI Engine: Generating VAR…', 'AI Engine: Generating TDRV…', 'AI Engine: Generating TDR + REXX…', 'AI Advisor: Engineering recommendations…', 'Finalising…'],
    ANALYZE: ['Connecting…', 'Parsing entry…', 'AI Engine: Classifying…', 'AI Advisor: Recommending…', 'Done.'],
    VAR:     ['Connecting…', 'Parsing entry…', 'AI Engine: VAR generation…', 'Done.'],
    TDRV:    ['Connecting…', 'Parsing entry…', 'AI Engine: TDRV generation…', 'Done.'],
    TDR:     ['Connecting…', 'Parsing entry…', 'AI Engine: TDR generation…', 'Done.'],
    REXX:    ['Connecting…', 'Parsing entry…', 'AI Engine: REXX/RAVEN generation…', 'Done.'],
    ZCMD:    ['Connecting…', 'AI Engine: Analyzing Z Command…', 'Generating explanation…', 'Done.'],
    CHAT:    ['Connecting…', 'AI Copilot: Thinking…', 'Typing response…', 'Done.'],
  };

  async function runGeneration(raw) {
    const useLLM = llmToggle ? llmToggle.checked : true;

    // ── Streaming path for ZCMD and CHAT ──
    if (mode === 'ZCMD' || mode === 'CHAT') {
      btnGenerate.disabled = true;
      hideAll(); // hide placeholder / processing

      const streamEndpoint = mode === 'ZCMD'
        ? `${API}/api/stream/zcmd?command=${encodeURIComponent(raw)}`
        : `${API}/api/stream/chat?query=${encodeURIComponent(raw)}`;

      // Create typing bubble immediately
      const streamBubble = document.createElement('div');
      streamBubble.className = 'chat-message ai';
      streamBubble.innerHTML = `<div class="msg-avatar"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10H12V2z"/><path d="M12 12 2.1 12"/><path d="M12 12l8.6 5"/></svg></div><div class="msg-content stream-content"><span class="cursor-blink">|</span></div>`;
      chatHistory.appendChild(streamBubble);
      chatHistory.scrollTop = chatHistory.scrollHeight;
      const contentEl = streamBubble.querySelector('.stream-content');
      let accumulated = '';

      const evtSource = new EventSource(streamEndpoint);
      evtSource.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.token) {
            accumulated += data.token;
            contentEl.innerHTML = accumulated
              .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
              .replace(/\n/g, '<br>') + '<span class="cursor-blink">|</span>';
            chatHistory.scrollTop = chatHistory.scrollHeight;
          }
          if (data.done) {
            evtSource.close();
            contentEl.innerHTML = (accumulated || 'No response received.')
              .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
              .replace(/\n/g, '<br>');
            btnGenerate.disabled = false;
            showToast('\u2713 Done.');
          }
        } catch(err) { /* ignore parse errors */ }
      };
      evtSource.onerror = () => {
        evtSource.close();
        if (!accumulated) {
          contentEl.innerHTML = '\u26a0 Could not reach AI server. Check Ollama is running at localhost:11434.';
        } else {
          contentEl.innerHTML = accumulated
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>');
        }
        btnGenerate.disabled = false;
      };
      return; // done — no blocking fetch needed
    }

    // ── Blocking path for all other modes ──
    hideAll();
    processing.classList.remove('hidden');
    btnGenerate.disabled = true;

    const steps = STEPS[mode] || STEPS.FULL;
    for (let i = 0; i < steps.length; i++) {
      procStep.textContent = steps[i];
      procFill.style.width = ((i + 1) / steps.length * 100) + '%';
      if (steps[i].includes('AI Engine')) procLabel.textContent = '⚡ AI Engine';
      else if (steps[i].includes('AI Advisor')) procLabel.textContent = '🧠 AI Advisor';
      else procLabel.textContent = 'Processing…';
      await delay(400 + Math.random() * 200);
    }

    let apiResult = null;
    const endpoint =
      mode === 'ANALYZE' ? '/api/analyze'
      : mode === 'VAR'   ? '/api/generate/var'
      : mode === 'TDRV'  ? '/api/generate/tdrv'
      : mode === 'TDR'   ? '/api/generate/tdr'
      : mode === 'REXX'  ? '/api/generate/rexx'
      : '/api/generate/full';

    try {
      const resp = await fetch(API + endpoint, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({
          raw_text: raw,
          entry_name: entryName.value.trim(),
          segment: "",
          mode,
          use_llm: useLLM,
        }),
      });
      if (resp.ok) apiResult = await resp.json();
    } catch { /* backend offline */ }

    hideAll();
    lastResult = apiResult || {_fallback: true};

    if (apiResult) {
      renderFromAPI(apiResult);
      const lm = apiResult.llm_mode || 'static';
      llmBadge.textContent = lm === 'static' ? '⚙ Static' : '🤖 ' + lm.replace('_',' ');
      llmBadge.className = 'llm-badge' + (lm === 'static' ? ' static' : '');
    } else {
      const parsed = localParse(raw);
      renderFallback(parsed, raw);
      llmBadge.textContent = '⚙ Local fallback'; llmBadge.className = 'llm-badge static';
    }

    activateTab(
      mode === 'ANALYZE' ? 'analysis'
      : mode === 'VAR'   ? 'var'
      : mode === 'TDRV'  ? 'tdrv'
      : mode === 'TDR'   ? 'tdr'
      : mode === 'REXX'  ? 'rexx'
      : mode === 'ZCMD'  ? 'zcmd'
      : 'analysis'
    );

    btnCopy.disabled = false; btnDownload.disabled = false; btnGenerate.disabled = false;
    showToast(apiResult ? '✓ Generated successfully.' : '⚠ Generated locally (API offline).');

    // Append AI Response to Chat
    const aiMsg = document.createElement('div');
    aiMsg.className = 'chat-message ai';
    let aiText = '';
    
    if (apiResult && (mode === 'ZCMD' || mode === 'CHAT')) {
      // Render full response directly in chat bubble
      const raw = apiResult.chat_response || apiResult.output || '';
      aiText = raw
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n•/g, '<br>•')
        .replace(/\n/g, '<br>');
    } else if (apiResult && apiResult.chat_response) {
      aiText = apiResult.chat_response;
    } else {
      aiText = `Documentation generated in <strong>${mode}</strong> mode. `;
      if (apiResult && apiResult.recommendations && apiResult.recommendations.length > 0) {
        aiText += `The Advisor found <strong>${apiResult.recommendations.length} recommendations</strong>. `;
      }
      aiText += 'Check the output tabs on the right.';
    }
    
    aiMsg.innerHTML = `<div class="msg-avatar"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10H12V2z"/><path d="M12 12 2.1 12"/><path d="M12 12l8.6 5"/></svg></div>
    <div class="msg-content">${aiText || 'Response complete. Check the output tabs.'}</div>`;
    chatHistory.appendChild(aiMsg);
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }

  // ── API Renderer ──
  function renderFromAPI(d) {
    if (mode === 'CHAT' || d.file_type === 'CHAT') {
       // Just chat, we can optionally switch to a generic tab or stay on analysis
       if (d.output) {
         $('#result-analysis').innerHTML = '<div class="result-section"><div class="result-section-title">Copilot Conversation</div><div class="zcmd-block"><pre>' + esc(d.output) + '</pre></div></div>';
       }
       return;
    }

    if (mode === 'ZCMD' || d.file_type === 'ZCMD') {
      $('#result-zcmd').innerHTML = '<div class="result-section"><div class="result-section-title">ZTPF Z Command Explanation</div><div class="zcmd-block"><pre>' + esc(d.output) + '</pre></div></div>';
      return;
    }

    // Analysis
    if (d.analysis) {
      const a = d.analysis;
      let h = '<div class="result-section"><div class="result-section-title">Entry Analysis</div>';
      h += '<div class="result-meta">';
      h += metaCard('Entry', a.entry_name || 'UNKNOWN');
      h += metaCard('Segment', a.segment || '—');
      h += metaCard('Variables', a.statistics?.variables ?? 0);
      h += metaCard('Macros', a.statistics?.macros ?? 0);
      h += metaCard('Branches', a.statistics?.branches ?? 0);
      h += metaCard('Complexity', a.complexity_score?.level ?? 'N/A');
      h += '</div></div>';
      h += section('Purpose', a.purpose || '—');
      h += section('Inputs', (a.inputs||[]).map(i=>'- '+i).join('\n'));
      h += section('Outputs', (a.outputs||[]).map(o=>'- '+o).join('\n'));
      if (a.macros_called?.length) h += section('Macros Called', a.macros_called.join('\n'));
      if (d.llm_analysis?.z_commands_applicable?.length) {
        h += section('Z Commands (AI)', d.llm_analysis.z_commands_applicable.join('\n'));
      }
      if (d.llm_analysis?.rexx_integration !== undefined) {
        h += section('REXX Integration', d.llm_analysis.rexx_integration ? 'Yes — RAVEN exec integration detected' : 'No REXX integration detected');
      }
      if (d.ml_prediction) {
        const ml = d.ml_prediction;
        h += '<div class="result-section"><div class="result-section-title">ML Classification</div><div class="result-meta">';
        h += metaCard('Type', ml.entry_type);
        h += metaCard('Confidence', (ml.entry_type_confidence * 100).toFixed(1) + '%');
        h += metaCard('Risk', ml.risk_level);
        h += metaCard('Risk Conf.', (ml.risk_level_confidence * 100).toFixed(1) + '%');
        h += '</div></div>';
      }
      $('#result-analysis').innerHTML = h;
    }

    const varText  = d.var_file  || (d.output && d.file_type==='VAR'  ? d.output : '');
    const tdrvText = d.tdrv_file || (d.output && d.file_type==='TDRV' ? d.output : '');
    const tdrText  = d.tdr_file  || (d.output && d.file_type==='TDR'  ? d.output : '');
    const rexxText = d.rexx_exec || (d.output && d.file_type==='REXX' ? d.output : '');

    if (varText)  $('#result-var').innerHTML  = section('VAR File',  varText);
    if (tdrvText) $('#result-tdrv').innerHTML = section('TDRV File', tdrvText);
    if (tdrText)  $('#result-tdr').innerHTML  = section('TDR File',  tdrText);
    if (rexxText) {
      $('#result-rexx').innerHTML = '<div class="result-section"><div class="result-section-title">REXX / RAVEN Exec — AI Engine</div><pre class="rexx-block">' + esc(rexxText) + '</pre></div>';
    }

    if (d.recommendations?.length) {
      let h = '<div class="result-section"><div class="result-section-title">Engineering Recommendations — AI Advisor</div>';
      d.recommendations.forEach(r => {
        const cls = r.severity==='ERROR' ? 'badge-error' : r.severity==='WARNING' ? 'badge-warning' : r.severity==='OPTIMIZATION' ? 'badge-optimization' : 'badge-info';
        h += `<div class="rec-item"><span class="result-badge ${cls}">${esc(r.severity)}</span><div class="rec-body">`;
        if (r.category) h += `<span class="rec-category">${esc(r.category)}</span>`;
        h += `<span class="rec-text">${esc(r.text)}</span>`;
        if (r.code_hint) h += `<code class="rec-code">${esc(r.code_hint)}</code>`;
        h += '</div></div>';
      });
      h += '</div>';
      $('#result-recommendations').innerHTML = h;
    }

    if (d.llm_errors?.length) {
      const panel = $('#result-analysis');
      if (panel) {
        d.llm_errors.forEach(e => {
          panel.innerHTML += `<div class="llm-error-banner">⚠ ${esc(e)}</div>`;
        });
      }
    }
  }

  function section(title, content) {
    return `<div class="result-section"><div class="result-section-title">${esc(title)}</div><pre>${esc(content)}</pre></div>`;
  }

  // ── Local Fallback ──
  function localParse(raw) {
    const lines = raw.split('\n').map(l => l.trim()).filter(Boolean);
    const p = { name: entryName.value.trim() || extractName(lines), segment: 'UNKNOWN', variables: [], macros: [], branches: [], files: [], errors: [], purpose: 'TPF transaction processing', inputs: ['UNKNOWN — requires TPF validation'], outputs: ['UNKNOWN — requires TPF validation'] };
    const varRe  = /^(\w+)\s+(DS|DC|EQU)\s+(.*)$/i;
    const macRe  = /\b(ENTER|EXITC|EXITN|BACKC|FILEC|FINDA|CRUSA|CRUSC|SERVC|GETCC|RELCC|GLOBZ|PNRCC|TIMEC|SENDC)\b/i;
    const brRe   = /\s+(B|BE|BNE|BH|BL|BC)\s+(\w+)/i;
    const fileRe = /\b(FILEC|FILEM|FINDA|FINDC)\b/i;
    for (const l of lines) {
      const vm = l.match(varRe); if (vm) p.variables.push({name:vm[1], type:'CHAR', len:'??'});
      const mm = l.match(macRe); if (mm) p.macros.push(mm[1].toUpperCase());
      const bm = l.match(brRe);  if (bm) p.branches.push(bm[2]);
      const fm = l.match(fileRe);if (fm) p.files.push(fm[1].toUpperCase());
      if (/ERR|FAIL|ABORT/i.test(l)) p.errors.push(l);
    }
    p.macros = [...new Set(p.macros)]; p.files = [...new Set(p.files)];
    if (p.macros.includes('FILEC')||p.macros.includes('FINDA')) p.purpose = 'File access and record retrieval';
    else if (p.macros.includes('CRUSA')) p.purpose = 'Record creation/update processing';
    else if (p.macros.includes('SERVC')) p.purpose = 'Service call processing';
    else if (/RAVEN|ADDRESS/i.test(raw)) p.purpose = 'REXX RAVEN exec processing';
    else if (/Z\s+(ENTRY|TPFDF|STAT|DUMP)/i.test(raw)) p.purpose = 'Z operator command handler';
    return p;
  }

  function extractName(lines) {
    for (const l of lines) { const m = l.match(/^(\w+)\s+CSECT/i); if (m) return m[1]; }
    return 'UNKNOWN';
  }

  function renderFallback(p, raw) {
    if (mode === 'ZCMD') {
      $('#result-zcmd').innerHTML = '<div class="result-section"><div class="result-section-title">ZTPF Z Command Explanation (Local)</div><div class="zcmd-block"><pre>Cannot explain Z-Command without AI model connectivity. Ensure Ollama is running.\n\nCommand requested: ' + esc(raw) + '</pre></div></div>';
      return;
    }

    let h = '<div class="result-section"><div class="result-section-title">Entry Analysis (Local)</div><div class="result-meta">';
    h += metaCard('Entry', p.name) + metaCard('Segment', p.segment) + metaCard('Variables', p.variables.length) + metaCard('Macros', p.macros.length) + metaCard('Branches', p.branches.length) + metaCard('File Ops', p.files.length);
    h += '</div></div>';
    h += section('Purpose', p.purpose);
    h += section('Inputs', p.inputs.join('\n'));
    h += section('Outputs', p.outputs.join('\n'));
    if (p.macros.length) h += section('Macros Called', p.macros.join('\n'));
    $('#result-analysis').innerHTML = h;

    let vOut = '═'.repeat(80) + '\n  VAR FILE — ' + p.name + '\n  Generated locally | ' + new Date().toISOString().slice(0,19) + '\n' + '═'.repeat(80) + '\n\n';
    vOut += pad('VAR_NAME',18)+pad('TYPE',8)+pad('LEN',6)+pad('SOURCE',14)+pad('DEFAULT',12)+pad('VALIDATION',18)+'DESCRIPTION\n' + '─'.repeat(80) + '\n';
    const vars = p.variables.length ? p.variables : [{name:'ENTRY_ID',type:'CHAR',len:'08'},{name:'ERR_CODE',type:'CHAR',len:'04'},{name:'RET_CODE',type:'BIN',len:'04'}];
    vars.forEach(v => { vOut += pad(v.name,18)+pad(v.type,8)+pad(v.len,6)+pad('SYSTEM',14)+pad('SPACES',12)+pad('NONE',18)+(v.name)+'\n'; });
    vOut += '─'.repeat(80) + '\nTOTAL: ' + vars.length;
    $('#result-var').innerHTML = section('VAR File (Local)', vOut);

    let tOut = '═'.repeat(70) + '\n  TDRV FILE — ' + p.name + '\n' + '═'.repeat(70) + '\n\n';
    tOut += pad('STEP',6)+pad('ACTION',22)+pad('ENTRY',12)+pad('CONDITION',20)+'NEXT\n' + '─'.repeat(70) + '\n';
    tOut += pad('01',6)+pad('RECEIVE REQUEST',22)+pad(p.name,12)+pad('INPUT OK',20)+'02\n';
    if (p.files.length) tOut += pad('02',6)+pad('FILE ACCESS',22)+pad(p.name+'_F',12)+pad('RECORD FOUND',20)+'03\n';
    tOut += pad('03',6)+pad('PROCESS DATA',22)+pad(p.name+'_P',12)+pad('SUCCESS',20)+'04\n';
    if (p.errors.length) tOut += pad('04',6)+pad('ERROR HANDLING',22)+pad(p.name+'_E',12)+pad('ERROR',20)+'05\n';
    tOut += pad('05',6)+pad('RETURN RESPONSE',22)+pad(p.name+'_R',12)+pad('COMPLETE',20)+'END\n';
    tOut += '─'.repeat(70);
    $('#result-tdrv').innerHTML = section('TDRV File (Local)', tOut);

    let rOut = '═'.repeat(70) + '\n  TDR FILE — ' + p.name + '\n' + '═'.repeat(70) + '\n\n';
    rOut += 'TDR NAME:    ' + p.name + ' — ' + p.purpose + '\nENTRY:       ' + p.name + '\nSEGMENT:     ' + p.segment + '\n\n';
    rOut += 'PURPOSE:\n  ' + p.purpose + '\n\nINPUT:\n' + p.inputs.map(i=>'  - '+i).join('\n') + '\n\nOUTPUT:\n' + p.outputs.map(o=>'  - '+o).join('\n');
    rOut += '\n\nDEPENDENCIES:\n' + (p.macros.length ? p.macros.map(m=>'  - '+m).join('\n') : '  UNKNOWN') + '\n\nEXCEPTIONS:\n' + (p.errors.length ? p.errors.slice(0,5).map(e=>'  - '+e.slice(0,60)).join('\n') : '  UNKNOWN');
    rOut += '\n\nZ COMMANDS:\n  Validate applicable Z ENTRY / Z TPFDF commands against this entry.\n\nREXX INTERFACE:\n  Assess RAVEN exec integration requirements.';
    $('#result-tdr').innerHTML = section('TDR File (Local)', rOut);

    const rexxOut = `/* IBM z/TPF REXX RAVEN Exec — ${p.name} */\n/* Purpose: ${p.purpose} */\nADDRESS RAVEN\n\nPARSE ARG entry_input\n\nIF entry_input = '' THEN DO\n  SAY 'ERR: No input provided'\n  EXIT 8\nEND\n\n/* TODO: Implement ${p.name} logic */\n/* Macros used: ${p.macros.join(', ')||'NONE'} */\n\nSAY 'OK: ${p.name} processing complete'\nEXIT 0`;
    $('#result-rexx').innerHTML = '<div class="result-section"><div class="result-section-title">REXX / RAVEN Exec (Local Template)</div><pre class="rexx-block">' + esc(rexxOut) + '</pre></div>';

    const recs = [];
    if (!p.errors.length) recs.push({severity:'WARNING',category:'ERROR_HANDLING',text:'No error handling detected. Add ERR label paths.',code_hint:null});
    if (!p.macros.includes('EXITC')&&!p.macros.includes('EXITN')) recs.push({severity:'WARNING',category:'EXIT_LOGIC',text:'No EXIT macro found. Ensure EXITC/BACKC on all paths.',code_hint:'EXITC TRDR'});
    if (p.variables.length < 3) recs.push({severity:'WARNING',category:'COMPLETENESS',text:'Few variables detected. Manual review recommended.',code_hint:null});
    if (p.files.length && !p.macros.some(m=>['CLI','CLC'].includes(m))) recs.push({severity:'WARNING',category:'VALIDATION',text:'File access without input validation.',code_hint:'CLI 0(R3),X\'00\'\nBE INVALID'});
    recs.push({severity:'INFO',category:'Z_COMMAND',text:'Verify applicable Z operator commands: Z ENTRY, Z TPFDF, Z STAT.',code_hint:null});
    recs.push({severity:'INFO',category:'VALIDATION',text:'Validate all generated artifacts against live z/TPF system.',code_hint:null});

    let rh = '<div class="result-section"><div class="result-section-title">Engineering Recommendations (Local)</div>';
    recs.forEach(r => {
      const cls = r.severity==='ERROR'?'badge-error':r.severity==='WARNING'?'badge-warning':r.severity==='OPTIMIZATION'?'badge-optimization':'badge-info';
      rh += `<div class="rec-item"><span class="result-badge ${cls}">${esc(r.severity)}</span><div class="rec-body">`;
      if (r.category) rh += `<span class="rec-category">${esc(r.category)}</span>`;
      rh += `<span class="rec-text">${esc(r.text)}</span>`;
      if (r.code_hint) rh += `<code class="rec-code">${esc(r.code_hint)}</code>`;
      rh += '</div></div>';
    });
    rh += '</div>';
    $('#result-recommendations').innerHTML = rh;
  }
})();
