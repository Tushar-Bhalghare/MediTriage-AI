// MediTriage AI - Frontend Application Logic

document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    lucide.createIcons();
  }

  // State Management
  const state = {
    mode: 'sample', // 'sample' or 'upload'
    currentSampleId: 'sample_diabetes_lipid',
    uploadedUrl: '',
    uploadedFilename: '',
    currentLanguage: 'en',
    currentData: null,
    isSpeaking: false,
  };

  // DOM Elements
  const sampleBtns = document.querySelectorAll('.sample-btn');
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const reportPreviewImg = document.getElementById('reportPreviewImg');
  const reportLabel = document.getElementById('reportLabel');
  const symptomsInput = document.getElementById('symptomsInput');
  const symptomTags = document.querySelectorAll('.symptom-tag');
  const btnAnalyze = document.getElementById('btnAnalyze');
  const progressBox = document.getElementById('progressBox');
  const pipelineBar = document.getElementById('pipelineBar');
  const pipelinePct = document.getElementById('pipelinePct');
  const pipelineStepText = document.getElementById('pipelineStepText');
  const triageAlertCard = document.getElementById('triageAlertCard');
  const triageIconWrap = document.getElementById('triageIconWrap');
  const urgencyBadge = document.getElementById('urgencyBadge');
  const triageTimeframe = document.getElementById('triageTimeframe');
  const riskScoreVal = document.getElementById('riskScoreVal');
  const plainExplanationBox = document.getElementById('plainExplanationBox');
  const currentLangTag = document.getElementById('currentLangTag');
  const biomarkerTableBody = document.getElementById('biomarkerTableBody');
  const doctorQuestionsList = document.getElementById('doctorQuestionsList');
  const dietEatText = document.getElementById('dietEatText');
  const dietAvoidText = document.getElementById('dietAvoidText');
  const btnExportSummary = document.getElementById('btnExportSummary');
  const btnVoiceRead = document.getElementById('btnVoiceRead');
  const btnSpeaker = document.getElementById('btnSpeaker');
  const langBtns = document.querySelectorAll('.lang-btn');

  // Lightbox elements
  const lightboxModal = document.getElementById('lightboxModal');
  const lightboxImg = document.getElementById('lightboxImg');
  const btnZoomReport = document.getElementById('btnZoomReport');
  const btnCloseLightbox = document.getElementById('btnCloseLightbox');

  // Sample Switcher Handlers
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
        symptomsInput.value = 'Frequent thirst, polyuria, lethargy after meals, mild foot tingling.';
      } else if (sampleId === 'sample_cbc_infection') {
        reportPreviewImg.src = '/static/samples/sample_cbc_infection.png';
        reportLabel.textContent = 'Complete Blood Count (Pooja Patel)';
        symptomsInput.value = 'Persistent low-grade fever, chills, dizziness, pallor, fatigue.';
      } else {
        reportPreviewImg.src = '/static/samples/sample_normal_baseline.png';
        reportLabel.textContent = 'Annual Wellness Screen (Amit Deshmukh)';
        symptomsInput.value = 'Routine annual checkup. Energetic, asymptomatic.';
      }

      runAnalysis();
    });
  });

  // Symptom quick pills
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

  // File Upload Handlers (Drag & Drop + Click)
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
        reportLabel.textContent = `Uploaded Report: ${file.name}`;

        sampleBtns.forEach(b => {
          b.classList.remove('border-rose-500/40', 'bg-rose-500/10');
          b.querySelector('.check-icon').classList.add('hidden');
        });

        showToast('✅ Report uploaded! Running AI clinical triage pipeline...');
        runAnalysis();
      } else {
        alert(data.message || 'Upload failed');
      }
    } catch (err) {
      console.error(err);
      alert('Error uploading medical report');
    }
  }

  // Trigger analysis button
  btnAnalyze.addEventListener('click', () => {
    runAnalysis();
  });

  // Main Automated Analysis Pipeline
  async function runAnalysis() {
    btnAnalyze.disabled = true;
    btnAnalyze.classList.add('opacity-70', 'cursor-not-allowed');
    progressBox.classList.remove('hidden');

    const steps = [
      { pct: 25, text: 'Step 1: Extracting Biomarkers via Vision OCR & Calibration...', step: 1 },
      { pct: 50, text: 'Step 2: Normalizing against Standard Clinical Reference Intervals...', step: 2 },
      { pct: 75, text: 'Step 3: Pathological Anomaly Detection & Risk Stratification...', step: 3 },
      { pct: 100, text: 'Step 4: Compiling Multi-Language Patient Explanations & Action Plan...', step: 4 }
    ];

    for (const s of steps) {
      pipelinePct.textContent = `${s.pct}%`;
      pipelineBar.style.width = `${s.pct}%`;
      pipelineStepText.textContent = s.text;

      for (let i = 1; i <= 4; i++) {
        const el = document.getElementById(`pStep${i}`);
        if (i <= s.step) {
          el.className = 'text-teal-400 font-semibold';
        } else {
          el.className = 'text-slate-500';
        }
      }
      await new Promise(r => setTimeout(r, 350));
    }

    try {
      const payload = {
        mode: state.mode,
        sample_id: state.currentSampleId,
        uploaded_url: state.uploadedUrl,
        symptoms: symptomsInput.value
      };

      const res = await fetch('/api/analyze-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.status === 'success') {
        state.currentData = data;
        renderTriageResults(data);
        progressBox.classList.add('hidden');
        btnAnalyze.disabled = false;
        btnAnalyze.classList.remove('opacity-70', 'cursor-not-allowed');
        showToast('✨ Automated Medical Report Triage Complete!');
      }
    } catch (err) {
      console.error(err);
      progressBox.classList.add('hidden');
      btnAnalyze.disabled = false;
      btnAnalyze.classList.remove('opacity-70', 'cursor-not-allowed');
    }
  }

  // Render Triage Results to UI
  function renderTriageResults(data) {
    const triage = data.triage;

    // 1. Triage Urgency Alert Card
    riskScoreVal.innerHTML = `${triage.risk_score} <span class="text-xs font-normal text-slate-500">/ 100</span>`;
    triageTimeframe.textContent = triage.timeframe;

    if (triage.urgency_color === 'red') {
      triageAlertCard.className = 'p-5 rounded-xl border border-red-500/40 bg-red-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4';
      triageIconWrap.className = 'w-10 h-10 rounded-xl bg-red-500/20 text-red-400 flex items-center justify-center shrink-0 border border-red-500/30';
      urgencyBadge.className = 'text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-red-500 text-white shadow-sm';
      urgencyBadge.textContent = triage.urgency_label;
      riskScoreVal.className = 'text-2xl font-bold font-display text-red-400';
    } else if (triage.urgency_color === 'amber') {
      triageAlertCard.className = 'p-5 rounded-xl border border-amber-500/40 bg-amber-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4';
      triageIconWrap.className = 'w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0 border border-amber-500/30';
      urgencyBadge.className = 'text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-amber-500 text-slate-950 shadow-sm';
      urgencyBadge.textContent = triage.urgency_label;
      riskScoreVal.className = 'text-2xl font-bold font-display text-amber-400';
    } else {
      triageAlertCard.className = 'p-5 rounded-xl border border-emerald-500/40 bg-emerald-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4';
      triageIconWrap.className = 'w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/30';
      urgencyBadge.className = 'text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-500 text-white shadow-sm';
      urgencyBadge.textContent = triage.urgency_label;
      riskScoreVal.className = 'text-2xl font-bold font-display text-emerald-400';
    }

    // 2. Multilingual Explanation
    renderLanguageExplanation(state.currentLanguage);

    // 3. Extracted Biomarker Table
    biomarkerTableBody.innerHTML = '';
    data.biomarkers.forEach(b => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-800/40 transition-colors';

      let statusBadge = '';
      if (b.status === 'CRITICAL HIGH') {
        statusBadge = '<span class="px-2 py-0.5 rounded bg-red-600 text-white font-bold text-[10px]">CRITICAL</span>';
      } else if (b.status === 'HIGH') {
        statusBadge = '<span class="px-2 py-0.5 rounded bg-red-500/20 text-red-400 font-bold border border-red-500/30 text-[10px]">HIGH</span>';
      } else if (b.status === 'LOW') {
        statusBadge = '<span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 font-bold border border-blue-500/30 text-[10px]">LOW</span>';
      } else {
        statusBadge = '<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-medium border border-emerald-500/30 text-[10px]">NORMAL</span>';
      }

      tr.innerHTML = `
        <td class="p-2.5 font-sans font-medium text-slate-200">${b.name}</td>
        <td class="p-2.5 font-bold ${b.status.includes('HIGH') ? 'text-red-400' : (b.status === 'LOW' ? 'text-blue-400' : 'text-emerald-400')}">
          ${b.value} <span class="text-[10px] text-slate-500">${b.unit}</span>
        </td>
        <td class="p-2.5 text-slate-400">${b.ref}</td>
        <td class="p-2.5">${statusBadge}</td>
      `;
      biomarkerTableBody.appendChild(tr);
    });

    // 4. Questions for Doctor Visit
    doctorQuestionsList.innerHTML = '';
    triage.doctor_questions.forEach(q => {
      const li = document.createElement('li');
      li.className = 'flex items-start gap-2';
      li.innerHTML = `<span class="text-amber-400 font-bold">›</span><span>${q}</span>`;
      doctorQuestionsList.appendChild(li);
    });

    // 5. Dietary & Lifestyle Guidelines
    dietEatText.textContent = triage.diet_lifestyle.recommended_foods.join(', ');
    dietAvoidText.textContent = triage.diet_lifestyle.foods_to_avoid.join(', ');

    if (window.lucide) lucide.createIcons();
  }

  // Language switcher logic
  langBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const lang = btn.getAttribute('data-lang');
      state.currentLanguage = lang;

      langBtns.forEach(b => {
        b.className = 'lang-btn px-2.5 py-1 rounded-lg text-slate-400 hover:text-white transition-all';
      });
      btn.className = 'lang-btn px-2.5 py-1 rounded-lg bg-teal-500 text-slate-950 font-bold transition-all';

      const langMap = { en: 'English', hi: 'हिंदी (Hindi)', mr: 'मराठी (Marathi)', es: 'Español' };
      currentLangTag.textContent = langMap[lang];

      renderLanguageExplanation(lang);
    });
  });

  function renderLanguageExplanation(lang) {
    if (!state.currentData) return;
    const expList = state.currentData.triage.explanations[lang] || state.currentData.triage.explanations['en'];
    
    plainExplanationBox.innerHTML = '';
    expList.forEach(text => {
      const p = document.createElement('p');
      p.textContent = text;
      plainExplanationBox.appendChild(p);
    });
  }

  // Web Speech API: Voice Narration
  function speakSummary() {
    if (!('speechSynthesis' in window)) {
      alert('Speech synthesis is not supported in your browser.');
      return;
    }

    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      state.isSpeaking = false;
      btnVoiceRead.querySelector('span').textContent = 'Voice Readout';
      btnSpeaker.querySelector('span').textContent = 'Listen Aloud';
      return;
    }

    const paragraphs = plainExplanationBox.querySelectorAll('p');
    let fullText = `Patient Clinical Summary. ${urgencyBadge.textContent}. `;
    paragraphs.forEach(p => fullText += `${p.textContent} `);

    const utterance = new SpeechSynthesisUtterance(fullText);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    if (state.currentLanguage === 'hi') utterance.lang = 'hi-IN';
    else if (state.currentLanguage === 'mr') utterance.lang = 'mr-IN';
    else if (state.currentLanguage === 'es') utterance.lang = 'es-ES';
    else utterance.lang = 'en-US';

    utterance.onstart = () => {
      state.isSpeaking = true;
      btnVoiceRead.querySelector('span').textContent = 'Stop Voice';
      btnSpeaker.querySelector('span').textContent = 'Stop Reading';
    };

    utterance.onend = () => {
      state.isSpeaking = false;
      btnVoiceRead.querySelector('span').textContent = 'Voice Readout';
      btnSpeaker.querySelector('span').textContent = 'Listen Aloud';
    };

    window.speechSynthesis.speak(utterance);
  }

  btnVoiceRead.addEventListener('click', speakSummary);
  btnSpeaker.addEventListener('click', speakSummary);

  // Export Summary Sheet
  btnExportSummary.addEventListener('click', async () => {
    btnExportSummary.innerHTML = '<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i><span>Exporting...</span>';
    if (window.lucide) lucide.createIcons();

    try {
      const res = await fetch('/api/export-patient-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sample_id: state.currentSampleId
        })
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `MediTriage_Clinical_Report_${state.currentSampleId}.jpg`;
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
      btnExportSummary.innerHTML = '<i data-lucide="download" class="w-3.5 h-3.5"></i><span>Export Patient Report</span>';
      if (window.lucide) lucide.createIcons();
    }
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
    toast.className = 'fixed bottom-5 right-5 z-50 px-4 py-2.5 rounded-xl bg-slate-900 border border-teal-500/50 text-white text-xs font-semibold shadow-2xl flex items-center space-x-2 transition-all transform translate-y-10 opacity-0';
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
