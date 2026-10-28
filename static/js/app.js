// MediTriage AI - Frontend Application Logic (Interactive Clinical Engine)

document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    lucide.createIcons();
  }

  // Application State
  const state = {
    mode: 'sample', // 'sample', 'upload', 'text', 'custom'
    currentSampleId: 'sample_diabetes_lipid',
    uploadedUrl: '',
    uploadedFilename: '',
    currentLanguage: 'en',
    currentData: null,
    biomarkers: [],
    biomarkerDb: {},
    isSpeaking: false,
  };

  // DOM Elements - Patient Context
  const patientNameInput = document.getElementById('patientNameInput');
  const patientAgeInput = document.getElementById('patientAgeInput');
  const patientGenderInput = document.getElementById('patientGenderInput');
  const triageSubTitle = document.getElementById('triageSubTitle');

  // DOM Elements - Tabs
  const tabPresetsBtn = document.getElementById('tabPresetsBtn');
  const tabUploadBtn = document.getElementById('tabUploadBtn');
  const tabTextBtn = document.getElementById('tabTextBtn');
  const tabPresetsContent = document.getElementById('tabPresetsContent');
  const tabUploadContent = document.getElementById('tabUploadContent');
  const tabTextContent = document.getElementById('tabTextContent');

  // DOM Elements - Presets & Upload
  const sampleBtns = document.querySelectorAll('.sample-btn');
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const cameraInput = document.getElementById('cameraInput');
  const btnSnapCamera = document.getElementById('btnSnapCamera');
  const rawReportTextArea = document.getElementById('rawReportTextArea');
  const btnExtractRawText = document.getElementById('btnExtractRawText');
  const reportPreviewImg = document.getElementById('reportPreviewImg');
  const reportLabel = document.getElementById('reportLabel');
  const symptomsInput = document.getElementById('symptomsInput');
  const symptomTags = document.querySelectorAll('.symptom-tag');
  const btnAnalyze = document.getElementById('btnAnalyze');

  // DOM Elements - Pipeline & Triage Results
  const progressBox = document.getElementById('progressBox');
  const pipelineBar = document.getElementById('pipelineBar');
  const pipelinePct = document.getElementById('pipelinePct');
  const pipelineStepText = document.getElementById('pipelineStepText');
  const triageAlertCard = document.getElementById('triageAlertCard');
  const triageIconWrap = document.getElementById('triageIconWrap');
  const urgencyBadge = document.getElementById('urgencyBadge');
  const triageTimeframe = document.getElementById('triageTimeframe');
  const riskScoreVal = document.getElementById('riskScoreVal');
  const emergencyHotlineBox = document.getElementById('emergencyHotlineBox');
  const plainExplanationBox = document.getElementById('plainExplanationBox');
  const currentLangTag = document.getElementById('currentLangTag');

  // DOM Elements - Biomarkers Table & Controls
  const biomarkerTableBody = document.getElementById('biomarkerTableBody');
  const btnAddBiomarkerBtn = document.getElementById('btnAddBiomarkerBtn');
  const addBiomarkerDrawer = document.getElementById('addBiomarkerDrawer');
  const selectNewBiomarker = document.getElementById('selectNewBiomarker');
  const inputNewBiomarkerVal = document.getElementById('inputNewBiomarkerVal');
  const btnConfirmAddBiomarker = document.getElementById('btnConfirmAddBiomarker');
  const btnRecalculateBiomarkers = document.getElementById('btnRecalculateBiomarkers');

  // DOM Elements - Diet Plan & Actions
  const dietPlanTitle = document.getElementById('dietPlanTitle');
  const dietCalories = document.getElementById('dietCalories');
  const dietHydration = document.getElementById('dietHydration');
  const mealScheduleList = document.getElementById('mealScheduleList');
  const dietSuperfoodsText = document.getElementById('dietSuperfoodsText');
  const dietAvoidFoodsText = document.getElementById('dietAvoidFoodsText');
  const doctorQuestionsList = document.getElementById('doctorQuestionsList');
  const btnExportSummary = document.getElementById('btnExportSummary');
  const btnDownloadDietPdf = document.getElementById('btnDownloadDietPdf');
  const btnDownloadDietPlanQuick = document.getElementById('btnDownloadDietPlanQuick');
  const btnPrintReport = document.getElementById('btnPrintReport');
  const btnVoiceRead = document.getElementById('btnVoiceRead');
  const btnSpeaker = document.getElementById('btnSpeaker');
  const langBtns = document.querySelectorAll('.lang-btn');

  // Lightbox Zoom
  const lightboxModal = document.getElementById('lightboxModal');
  const lightboxImg = document.getElementById('lightboxImg');
  const btnZoomReport = document.getElementById('btnZoomReport');
  const btnCloseLightbox = document.getElementById('btnCloseLightbox');

  // Load Biomarker DB on Start
  fetchBiomarkerDb();

  async function fetchBiomarkerDb() {
    try {
      const res = await fetch('/api/biomarker-db');
      const data = await res.json();
      if (data.status === 'success') {
        state.biomarkerDb = data.database;
        populateBiomarkerSelect(data.database);
      }
    } catch (e) {
      console.warn('Could not fetch biomarker database:', e);
    }
  }

  function populateBiomarkerSelect(db) {
    selectNewBiomarker.innerHTML = '';
    for (const [key, meta] of Object.entries(db)) {
      const opt = document.createElement('option');
      opt.value = key;
      opt.textContent = `${meta.name} (${meta.unit})`;
      selectNewBiomarker.appendChild(opt);
    }
  }

  // Tab Switcher Handling
  function switchTab(activeTab) {
    const tabs = [
      { id: 'presets', btn: tabPresetsBtn, content: tabPresetsContent },
      { id: 'upload', btn: tabUploadBtn, content: tabUploadContent },
      { id: 'text', btn: tabTextBtn, content: tabTextContent },
    ];

    tabs.forEach(t => {
      if (t.id === activeTab) {
        t.btn.classList.add('bg-teal-500', 'text-slate-950', 'font-bold');
        t.btn.classList.remove('text-slate-400');
        t.content.classList.remove('hidden');
      } else {
        t.btn.classList.remove('bg-teal-500', 'text-slate-950', 'font-bold');
        t.btn.classList.add('text-slate-400');
        t.content.classList.add('hidden');
      }
    });

    if (window.lucide) lucide.createIcons();
  }

  tabPresetsBtn.addEventListener('click', () => switchTab('presets'));
  tabUploadBtn.addEventListener('click', () => switchTab('upload'));
  tabTextBtn.addEventListener('click', () => switchTab('text'));

  // Preset Selection Handlers
  sampleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const sampleId = btn.getAttribute('data-id');
      state.mode = 'sample';
      state.currentSampleId = sampleId;

      sampleBtns.forEach(b => {
        b.classList.remove('border-rose-500/40', 'bg-rose-500/10');
        b.classList.add('border-slate-800', 'bg-slate-900/60');
        b.querySelector('.check-icon').classList.add('hidden');
      });

      btn.classList.add('border-rose-500/40', 'bg-rose-500/10');
      btn.classList.remove('border-slate-800', 'bg-slate-900/60');
      btn.querySelector('.check-icon').classList.remove('hidden');

      if (sampleId === 'sample_diabetes_lipid') {
        reportPreviewImg.src = '/static/samples/sample_diabetes_lipid.png';
        reportLabel.textContent = 'Diabetic & Lipid Panel (Rahul Sharma)';
        patientNameInput.value = 'Rahul Sharma';
        patientAgeInput.value = 48;
        patientGenderInput.value = 'Male';
        symptomsInput.value = 'Frequent thirst, polyuria, lethargy after meals, mild foot tingling.';
      } else if (sampleId === 'sample_cbc_infection') {
        reportPreviewImg.src = '/static/samples/sample_cbc_infection.png';
        reportLabel.textContent = 'Complete Blood Count (Pooja Patel)';
        patientNameInput.value = 'Pooja Patel';
        patientAgeInput.value = 26;
        patientGenderInput.value = 'Female';
        symptomsInput.value = 'Persistent low-grade fever, chills, dizziness, pallor, fatigue.';
      } else {
        reportPreviewImg.src = '/static/samples/sample_normal_baseline.png';
        reportLabel.textContent = 'Annual Wellness Screen (Amit Deshmukh)';
        patientNameInput.value = 'Amit Deshmukh';
        patientAgeInput.value = 32;
        patientGenderInput.value = 'Male';
        symptomsInput.value = 'Routine annual checkup. Energetic, asymptomatic.';
      }

      runAnalysis();
    });
  });

  // Quick Symptom Pills
  symptomTags.forEach(tag => {
    tag.addEventListener('click', () => {
      const text = tag.textContent.replace('+', '').trim();
      if (symptomsInput.value) {
        symptomsInput.value += `, ${text}`;
      } else {
        symptomsInput.value = text;
      }
    });
  });

  // File Upload Handlers (Drag & Drop + Input)
  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('border-teal-400', 'bg-teal-500/10');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('border-teal-400', 'bg-teal-500/10');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('border-teal-400', 'bg-teal-500/10');
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });

  // Camera Snap Handlers
  btnSnapCamera.addEventListener('click', () => cameraInput.click());
  cameraInput.addEventListener('change', () => {
    if (cameraInput.files.length > 0) {
      handleFileUpload(cameraInput.files[0]);
    }
  });

  async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('report_file', file);
    reportLabel.textContent = `Uploading ${file.name}...`;

    try {
      const res = await fetch('/api/upload-file', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.status === 'success') {
        state.mode = 'upload';
        state.uploadedUrl = data.url;
        state.uploadedFilename = data.filename;

        reportPreviewImg.src = data.url;
        reportLabel.textContent = `Uploaded: ${file.name}`;

        sampleBtns.forEach(b => {
          b.classList.remove('border-rose-500/40', 'bg-rose-500/10');
          b.querySelector('.check-icon').classList.add('hidden');
        });

        showToast('✅ Report uploaded to Antigravity AI! Extracting biomarkers...');
        runAnalysis();
      } else {
        alert(data.message || 'Upload failed');
      }
    } catch (err) {
      console.error(err);
      alert('Error uploading medical report');
    }
  }

  // Auto-Extract from Raw Text
  btnExtractRawText.addEventListener('click', async () => {
    const text = rawReportTextArea.value.trim();
    if (!text) {
      alert('Please paste some report text or prescription to analyze.');
      return;
    }

    btnExtractRawText.innerHTML = '<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i><span>Extracting...</span>';
    if (window.lucide) lucide.createIcons();

    try {
      const res = await fetch('/api/parse-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await res.json();

      if (data.status === 'success' && data.biomarkers.length > 0) {
        state.mode = 'custom';
        state.biomarkers = data.biomarkers;
        
        if (data.patient && data.patient.name !== 'Patient') {
          patientNameInput.value = data.patient.name;
          patientAgeInput.value = data.patient.age;
          patientGenderInput.value = data.patient.gender;
        }

        renderBiomarkerTable(data.biomarkers);
        reportLabel.textContent = `Extracted ${data.count} biomarkers from text`;
        showToast(`✨ Successfully extracted ${data.count} biomarkers!`);
        
        // Run full analysis on extracted values
        runAnalysis();
      } else {
        alert('Could not detect numeric lab values from text. Enter values manually or upload an image.');
      }
    } catch (err) {
      console.error(err);
      alert('Error parsing lab report text');
    } finally {
      btnExtractRawText.innerHTML = '<i data-lucide="zap" class="w-3.5 h-3.5"></i><span>Auto-Extract Biomarkers from Text</span>';
      if (window.lucide) lucide.createIcons();
    }
  });

  // Biomarker Add / Edit Controls
  btnAddBiomarkerBtn.addEventListener('click', () => {
    addBiomarkerDrawer.classList.toggle('hidden');
  });

  btnConfirmAddBiomarker.addEventListener('click', () => {
    const key = selectNewBiomarker.value;
    const val = parseFloat(inputNewBiomarkerVal.value);

    if (isNaN(val)) {
      alert('Please enter a valid numeric test value.');
      return;
    }

    const meta = state.biomarkerDb[key] || { name: key.toUpperCase(), unit: '', min: 0, max: 100 };
    let status = 'NORMAL';
    if (val > meta.max * 1.35) status = 'CRITICAL HIGH';
    else if (val > meta.max) status = 'HIGH';
    else if (meta.min > 0 && val < meta.min) status = 'LOW';

    const ref = meta.min > 0 ? `${meta.min} - ${meta.max}` : `< ${meta.max}`;

    // Replace if existing or add new
    const existingIdx = state.biomarkers.findIndex(b => b.key === key);
    const newEntry = {
      key: key,
      name: meta.name,
      value: val,
      unit: meta.unit,
      ref: ref,
      status: status,
      category: meta.category || 'Diagnostic'
    };

    if (existingIdx >= 0) {
      state.biomarkers[existingIdx] = newEntry;
    } else {
      state.biomarkers.push(newEntry);
    }

    state.mode = 'custom';
    renderBiomarkerTable(state.biomarkers);
    addBiomarkerDrawer.classList.add('hidden');
    inputNewBiomarkerVal.value = '';
    showToast(`Added ${meta.name} (${val} ${meta.unit}) to matrix`);

    // Recalculate
    runAnalysis();
  });

  btnRecalculateBiomarkers.addEventListener('click', () => {
    state.mode = 'custom';
    runAnalysis();
  });

  btnAnalyze.addEventListener('click', () => {
    runAnalysis();
  });

  // Main Automated Clinical Analysis Pipeline
  async function runAnalysis() {
    btnAnalyze.disabled = true;
    btnAnalyze.classList.add('opacity-70', 'cursor-not-allowed');
    progressBox.classList.remove('hidden');

    const steps = [
      { pct: 25, text: 'Step 1: Antigravity AI Optical Extraction & Biomarker Normalization...', step: 1 },
      { pct: 50, text: 'Step 2: Calibrating against Biological Reference Intervals...', step: 2 },
      { pct: 75, text: 'Step 3: Detecting Pathological Anomalies & Clinical Triage...', step: 3 },
      { pct: 100, text: 'Step 4: Synthesizing Personalized 24h Food & Diet Protocol...', step: 4 }
    ];

    for (const s of steps) {
      pipelinePct.textContent = `${s.pct}%`;
      pipelineBar.style.width = `${s.pct}%`;
      pipelineStepText.textContent = s.text;

      for (let i = 1; i <= 4; i++) {
        const el = document.getElementById(`pStep${i}`);
        if (el) {
          if (i <= s.step) {
            el.className = 'text-teal-400 font-semibold';
          } else {
            el.className = 'text-slate-500';
          }
        }
      }
      await new Promise(r => setTimeout(r, 220));
    }

    try {
      const patient = {
        name: patientNameInput.value.trim() || 'Patient',
        age: parseInt(patientAgeInput.value) || 45,
        gender: patientGenderInput.value || 'Male',
        id: state.currentData ? state.currentData.patient.id : `P-${Date.now() % 1000000}`
      };

      const payload = {
        mode: state.mode,
        sample_id: state.currentSampleId,
        uploaded_url: state.uploadedUrl,
        uploaded_filename: state.uploadedFilename,
        symptoms: symptomsInput.value,
        patient: patient,
        biomarkers: (state.mode === 'custom' && state.biomarkers.length > 0) ? state.biomarkers : undefined
      };

      const res = await fetch('/api/analyze-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.status === 'success') {
        state.currentData = data;
        state.biomarkers = data.biomarkers;
        renderTriageResults(data);
        progressBox.classList.add('hidden');
        btnAnalyze.disabled = false;
        btnAnalyze.classList.remove('opacity-70', 'cursor-not-allowed');
        showToast('✨ Antigravity AI Medical Analysis & Diet Protocol Updated!');
      }
    } catch (err) {
      console.error(err);
      progressBox.classList.add('hidden');
      btnAnalyze.disabled = false;
      btnAnalyze.classList.remove('opacity-70', 'cursor-not-allowed');
    }
  }

  // Render Triage and Diet Results
  function renderTriageResults(data) {
    const triage = data.triage;
    const patient = data.patient;

    triageSubTitle.textContent = `Patient: ${patient.name} (${patient.age}Y/${patient.gender}) • ID: ${patient.id}`;

    // 1. Triage Urgency Alert Banner
    riskScoreVal.innerHTML = `${triage.risk_score} <span class="text-xs font-normal text-slate-500">/ 100</span>`;
    triageTimeframe.textContent = triage.timeframe;

    if (triage.urgency === 'EMERGENCY_CRITICAL') {
      emergencyHotlineBox.classList.remove('hidden');
      triageAlertCard.className = 'p-5 rounded-xl border border-red-500 bg-red-950/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-pulse-slow';
      triageIconWrap.className = 'w-10 h-10 rounded-xl bg-red-500 text-white flex items-center justify-center shrink-0 shadow-lg shadow-red-500/50';
      urgencyBadge.className = 'text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-red-600 text-white shadow-md';
      urgencyBadge.textContent = triage.urgency_label;
      riskScoreVal.className = 'text-2xl font-bold font-display text-red-400';
    } else if (triage.urgency_color === 'red') {
      emergencyHotlineBox.classList.add('hidden');
      triageAlertCard.className = 'p-5 rounded-xl border border-red-500/40 bg-red-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4';
      triageIconWrap.className = 'w-10 h-10 rounded-xl bg-red-500/20 text-red-400 flex items-center justify-center shrink-0 border border-red-500/30';
      urgencyBadge.className = 'text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-red-500 text-white shadow-sm';
      urgencyBadge.textContent = triage.urgency_label;
      riskScoreVal.className = 'text-2xl font-bold font-display text-red-400';
    } else if (triage.urgency_color === 'amber') {
      emergencyHotlineBox.classList.add('hidden');
      triageAlertCard.className = 'p-5 rounded-xl border border-amber-500/40 bg-amber-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4';
      triageIconWrap.className = 'w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 border border-amber-500/30';
      urgencyBadge.className = 'text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-amber-500 text-slate-950 shadow-sm';
      urgencyBadge.textContent = triage.urgency_label;
      riskScoreVal.className = 'text-2xl font-bold font-display text-amber-400';
    } else {
      emergencyHotlineBox.classList.add('hidden');
      triageAlertCard.className = 'p-5 rounded-xl border border-emerald-500/40 bg-emerald-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4';
      triageIconWrap.className = 'w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/30';
      urgencyBadge.className = 'text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-500 text-white shadow-sm';
      urgencyBadge.textContent = triage.urgency_label;
      riskScoreVal.className = 'text-2xl font-bold font-display text-emerald-400';
    }

    // 2. Multilingual Explanation
    renderExplanation(triage.explanations, state.currentLanguage);

    // 3. Render Biomarkers Table
    renderBiomarkerTable(data.biomarkers);

    // 4. Render Antigravity Food & Diet Plan
    const diet = triage.diet_plan;
    dietPlanTitle.textContent = diet.title;
    dietCalories.textContent = `🎯 ${diet.calories}`;
    dietHydration.textContent = `💧 ${diet.hydration}`;

    mealScheduleList.innerHTML = '';
    diet.schedule.forEach(item => {
      const row = document.createElement('div');
      row.className = 'p-2.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start gap-3';
      row.innerHTML = `
        <span class="text-xs font-mono font-bold text-amber-400 shrink-0 mt-0.5">${item.time}</span>
        <div>
          <div class="text-xs font-semibold text-teal-300">${item.meal}</div>
          <div class="text-[11px] text-slate-300 mt-0.5 leading-relaxed">${item.items}</div>
        </div>
      `;
      mealScheduleList.appendChild(row);
    });

    dietSuperfoodsText.textContent = diet.superfoods.join(', ');
    dietAvoidFoodsText.textContent = diet.avoid_foods.join(', ');

    // 5. Doctor Questions
    doctorQuestionsList.innerHTML = '';
    triage.doctor_questions.forEach(q => {
      const li = document.createElement('li');
      li.className = 'text-xs text-slate-200';
      li.textContent = q;
      doctorQuestionsList.appendChild(li);
    });

    if (window.lucide) lucide.createIcons();
  }

  // Render Biomarkers Matrix (with live inline editing)
  function renderBiomarkerTable(biomarkers) {
    biomarkerTableBody.innerHTML = '';

    biomarkers.forEach((b, idx) => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-800/40 transition-colors';

      let statusBadge = '';
      if (b.status === 'CRITICAL HIGH') {
        statusBadge = '<span class="px-2 py-0.5 rounded-full bg-red-600/30 text-red-300 font-bold border border-red-500/50">CRITICAL</span>';
      } else if (b.status === 'HIGH') {
        statusBadge = '<span class="px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 font-semibold border border-red-500/30">HIGH</span>';
      } else if (b.status === 'LOW') {
        statusBadge = '<span class="px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-semibold border border-blue-500/30">LOW</span>';
      } else {
        statusBadge = '<span class="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-semibold border border-emerald-500/30">NORMAL</span>';
      }

      tr.innerHTML = `
        <td class="p-2.5 font-medium text-slate-200">
          <div class="font-sans font-semibold">${b.name}</div>
          <div class="text-[10px] text-slate-500">${b.category || ''}</div>
        </td>
        <td class="p-2.5 font-bold">
          <div class="flex items-center gap-1.5">
            <input type="number" step="any" value="${b.value}" data-index="${idx}" class="biomarker-val-input w-20 bg-slate-950 border border-slate-700 rounded px-1.5 py-0.5 text-xs text-white focus:outline-none focus:border-teal-400 font-mono">
            <span class="text-[10px] text-slate-400 font-normal">${b.unit}</span>
          </div>
        </td>
        <td class="p-2.5 text-slate-400 text-[11px]">${b.ref}</td>
        <td class="p-2.5">${statusBadge}</td>
        <td class="p-2.5 text-right no-print">
          <button type="button" data-index="${idx}" class="btn-remove-biomarker p-1 rounded hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 transition-all" title="Remove Test">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </td>
      `;

      biomarkerTableBody.appendChild(tr);
    });

    // Attach inline value change listeners
    document.querySelectorAll('.biomarker-val-input').forEach(input => {
      input.addEventListener('change', (e) => {
        const idx = parseInt(e.target.getAttribute('data-index'));
        const newVal = parseFloat(e.target.value);
        if (!isNaN(newVal) && state.biomarkers[idx]) {
          state.biomarkers[idx].value = newVal;
          state.mode = 'custom';
        }
      });
    });

    // Attach remove listeners
    document.querySelectorAll('.btn-remove-biomarker').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const btnEl = e.currentTarget;
        const idx = parseInt(btnEl.getAttribute('data-index'));
        if (state.biomarkers[idx]) {
          state.biomarkers.splice(idx, 1);
          state.mode = 'custom';
          renderBiomarkerTable(state.biomarkers);
          runAnalysis();
        }
      });
    });

    if (window.lucide) lucide.createIcons();
  }

  // Explanation in Selected Language
  function renderExplanation(explanations, lang) {
    const list = explanations[lang] || explanations['en'] || [];
    plainExplanationBox.innerHTML = '';

    const langNames = { en: 'English', hi: 'Hindi (हिंदी)', mr: 'Marathi (मराठी)', es: 'Spanish (Español)' };
    currentLangTag.textContent = langNames[lang] || 'English';

    list.forEach(p => {
      const div = document.createElement('p');
      div.className = 'text-xs text-slate-200 leading-relaxed';
      div.textContent = p;
      plainExplanationBox.appendChild(div);
    });
  }

  // Language Switcher Handlers
  langBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const lang = btn.getAttribute('data-lang');
      state.currentLanguage = lang;

      langBtns.forEach(b => {
        b.className = 'lang-btn px-2.5 py-1 rounded-lg text-slate-400 hover:text-white transition-all';
      });
      btn.className = 'lang-btn px-2.5 py-1 rounded-lg bg-teal-500 text-slate-950 font-bold transition-all';

      if (state.currentData && state.currentData.triage) {
        renderExplanation(state.currentData.triage.explanations, lang);
      }
    });
  });

  // Voice Narration (TTS)
  function speakSummary() {
    if (!('speechSynthesis' in window)) {
      alert('Text-to-speech is not supported by your browser.');
      return;
    }

    if (state.isSpeaking) {
      window.speechSynthesis.cancel();
      state.isSpeaking = false;
      btnVoiceRead.innerHTML = '<i data-lucide="volume-2" class="w-3.5 h-3.5 text-teal-400"></i><span class="hidden md:inline">Voice Readout</span>';
      if (window.lucide) lucide.createIcons();
      return;
    }

    const paras = Array.from(plainExplanationBox.querySelectorAll('p')).map(p => p.textContent).join('. ');
    if (!paras) return;

    const utterance = new SpeechSynthesisUtterance(paras);
    const langCode = { en: 'en-US', hi: 'hi-IN', mr: 'mr-IN', es: 'es-ES' }[state.currentLanguage] || 'en-US';
    utterance.lang = langCode;
    utterance.rate = 0.95;

    state.isSpeaking = true;
    btnVoiceRead.innerHTML = '<i data-lucide="square" class="w-3.5 h-3.5 text-rose-400"></i><span class="hidden md:inline">Stop Audio</span>';
    if (window.lucide) lucide.createIcons();

    utterance.onend = () => {
      state.isSpeaking = false;
      btnVoiceRead.innerHTML = '<i data-lucide="volume-2" class="w-3.5 h-3.5 text-teal-400"></i><span class="hidden md:inline">Voice Readout</span>';
      if (window.lucide) lucide.createIcons();
    };

    window.speechSynthesis.speak(utterance);
  }

  btnVoiceRead.addEventListener('click', speakSummary);
  btnSpeaker.addEventListener('click', speakSummary);

  // Download Full Food & Diet Plan (PDF/Sheet)
  async function downloadDietPdf() {
    btnDownloadDietPdf.innerHTML = '<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i><span>Generating Diet PDF...</span>';
    if (window.lucide) lucide.createIcons();

    try {
      const payload = {
        patient: state.currentData ? state.currentData.patient : { name: patientNameInput.value, age: parseInt(patientAgeInput.value), gender: patientGenderInput.value },
        biomarkers: state.biomarkers,
        diet_plan: state.currentData ? state.currentData.triage.diet_plan : null,
        sample_id: state.currentSampleId
      };

      const res = await fetch('/api/download-diet-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const pId = state.currentData ? state.currentData.patient.id : 'patient';
        a.download = `Antigravity_Food_Diet_Plan_${pId}.jpg`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        showToast('🥗 Antigravity AI Full Food & Diet Chart downloaded!');
      } else {
        alert('Could not export Diet PDF');
      }
    } catch (err) {
      console.error(err);
      alert('Error downloading Diet Plan');
    } finally {
      btnDownloadDietPdf.innerHTML = '<i data-lucide="utensils" class="w-3.5 h-3.5"></i><span>Download Diet PDF</span>';
      if (window.lucide) lucide.createIcons();
    }
  }

  btnDownloadDietPdf.addEventListener('click', downloadDietPdf);
  btnDownloadDietPlanQuick.addEventListener('click', downloadDietPdf);

  // Export Clinical Summary Sheet
  btnExportSummary.addEventListener('click', async () => {
    btnExportSummary.innerHTML = '<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i><span>Exporting...</span>';
    if (window.lucide) lucide.createIcons();

    try {
      const payload = {
        patient: state.currentData ? state.currentData.patient : { name: patientNameInput.value, age: parseInt(patientAgeInput.value), gender: patientGenderInput.value },
        biomarkers: state.biomarkers,
        triage: state.currentData ? state.currentData.triage : null,
        sample_id: state.currentSampleId
      };

      const res = await fetch('/api/export-patient-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const pId = state.currentData ? state.currentData.patient.id : 'patient';
        a.download = `MediTriage_Clinical_Report_${pId}.jpg`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        showToast('📄 Clinical Patient Summary Sheet exported!');
      } else {
        alert('Could not export patient summary');
      }
    } catch (err) {
      console.error(err);
      alert('Error exporting report');
    } finally {
      btnExportSummary.innerHTML = '<i data-lucide="file-text" class="w-3.5 h-3.5"></i><span>Clinical Report</span>';
      if (window.lucide) lucide.createIcons();
    }
  });

  // Print Hospital Report (Print-to-PDF)
  btnPrintReport.addEventListener('click', () => {
    window.print();
  });

  // Lightbox Zoom
  btnZoomReport.addEventListener('click', () => {
    lightboxImg.src = reportPreviewImg.src;
    lightboxModal.classList.remove('hidden');
  });

  btnCloseLightbox.addEventListener('click', () => lightboxModal.classList.add('hidden'));
  lightboxModal.addEventListener('click', (e) => {
    if (e.target === lightboxModal) lightboxModal.classList.add('hidden');
  });

  // Toast Notification
  function showToast(msg) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-5 right-5 z-50 px-4 py-2.5 rounded-xl bg-slate-900 border border-teal-500/50 text-white text-xs font-semibold shadow-2xl flex items-center space-x-2 transition-all transform translate-y-10 opacity-0 no-print';
    toast.innerHTML = `<span class="w-2 h-2 rounded-full bg-teal-400 animate-ping"></span><span>${msg}</span>`;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.classList.remove('translate-y-10', 'opacity-0');
    }, 10);

    setTimeout(() => {
      toast.classList.add('translate-y-10', 'opacity-0');
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // Run initial analysis on load
  runAnalysis();
});
