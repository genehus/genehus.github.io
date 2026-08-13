const SAMPLE_NOTE =
  "Sample data. Preview only. Not for clinical use. These numbers use simple demo rules, not the GeneHus v1 model.";

const CASES = [
  {
    id: "kwame",
    name: "Kwame A.",
    label: "Typical late presentation",
    age: 68,
    psa: 87,
    gleason: 9,
    stage: "T4",
    family: true,
    genomic: true
  },
  {
    id: "ibrahim",
    name: "Ibrahim T.",
    label: "Unclear PSA",
    age: 55,
    psa: 8.4,
    gleason: 7,
    stage: "T2",
    family: true,
    genomic: true
  },
  {
    id: "emmanuel",
    name: "Emmanuel K.",
    label: "High grade, rising PSA",
    age: 72,
    psa: 22,
    gleason: 8,
    stage: "T3",
    family: false,
    genomic: true
  },
  {
    id: "samuel",
    name: "Samuel O.",
    label: "Borderline clinical picture",
    age: 61,
    psa: 12,
    gleason: 7,
    stage: "T2",
    family: true,
    genomic: false
  },
  {
    id: "benjamin",
    name: "Benjamin A.",
    label: "Modest PSA, genomic flag on",
    age: 58,
    psa: 5.2,
    gleason: 6,
    stage: "T1c",
    family: false,
    genomic: true
  },
  {
    id: "joseph",
    name: "Joseph N.",
    label: "Lower-risk sample",
    age: 49,
    psa: 3.1,
    gleason: 6,
    stage: "T1",
    family: false,
    genomic: false
  }
];

function psaOnly(psa) {
  if (psa >= 20) return { level: "high", n: 78 };
  if (psa >= 10) return { level: "high", n: 62 };
  if (psa >= 4) return { level: "medium", n: 44 };
  return { level: "low", n: 18 };
}

function combined(p) {
  const why = [];
  let n = Math.min(36, p.psa * 0.7);

  if (p.psa >= 20) why.push("PSA is very high");
  else if (p.psa >= 10) why.push("PSA is raised");
  else if (p.psa >= 4) why.push("PSA is in a grey zone (not enough on its own)");

  if (p.gleason >= 9) {
    n += 28;
    why.push("Gleason 9–10 is high-grade disease");
  } else if (p.gleason >= 8) {
    n += 22;
    why.push("Gleason 8 is high-grade disease");
  } else if (p.gleason >= 7) {
    n += 12;
    why.push("Gleason 7 adds clinical concern");
  } else {
    n += 4;
  }

  const stage = String(p.stage || "T1").toUpperCase();
  if (stage.includes("T4") || stage.includes("N1") || stage.includes("M1")) {
    n += 24;
    why.push("Stage suggests locally advanced or spreading disease");
  } else if (stage.includes("T3")) {
    n += 16;
    why.push("Stage T3 suggests the cancer has grown beyond the prostate");
  } else if (stage.includes("T2")) {
    n += 8;
  }

  if (p.age >= 70) n += 5;
  else if (p.age >= 55) n += 2;

  if (p.family) {
    n += 8;
    why.push("Family history is present");
  }

  if (p.genomic) {
    n += 14;
    why.push("Sample African genomic profile is switched on");
  }

  n = Math.max(8, Math.min(99, Math.round(n)));
  const level = n >= 62 ? "high" : n >= 38 ? "medium" : "low";
  if (!why.length) why.push("Inputs sit in a lower-risk range on this preview");
  return { level, n, why };
}

function suggestion(level) {
  if (level === "high") {
    return "Suggestion only: consider earlier staging and specialist review. The doctor decides next steps.";
  }
  if (level === "medium") {
    return "Suggestion only: do not rely on PSA alone; consider closer follow-up. The doctor decides next steps.";
  }
  return "Suggestion only: routine pathway may be appropriate. The doctor decides next steps.";
}

function rankedCases() {
  return CASES.map((c) => ({ ...c, result: combined(c), psa: psaOnly(c.psa) })).sort(
    (a, b) => b.result.n - a.result.n
  );
}

function readForm(form) {
  return {
    id: "custom",
    name: "New sample case",
    label: "Typed by you (still fictional)",
    age: Number(form.age.value),
    psa: Number(form.psa.value),
    gleason: Number(form.gleason.value),
    stage: form.stage.value,
    family: form.family.checked,
    genomic: form.genomic.checked
  };
}

function renderQueue(activeId) {
  const list = document.getElementById("queue-list");
  list.innerHTML = rankedCases()
    .map((c) => {
      const row = CASES.find((x) => x.id === c.id);
      return `
      <li>
        <button class="queue-item${c.id === activeId ? " is-active" : ""}" type="button" data-id="${c.id}">
          <span class="name">${c.name}</span>
          <span class="badge badge-${c.result.level}">${c.result.level}</span>
          <span class="meta">${c.label} · PSA ${row.psa} · Gleason ${row.gleason}</span>
        </button>
      </li>`;
    })
    .join("");
}

function resultCard(patient) {
  const gene = combined(patient);
  const psa = psaOnly(patient.psa);
  return `
    <div class="result-hero">
      <div>
        <p class="eyebrow">GeneHus combined preview</p>
        <h3>${gene.level} risk</h3>
      </div>
      <span class="badge badge-${gene.level}">Aggressive disease · sample</span>
    </div>
    <div class="compare">
      <div>
        <span>PSA alone</span>
        <strong class="badge badge-${psa.level}">${psa.level}</strong>
      </div>
      <div>
        <span>GeneHus combined</span>
        <strong class="badge badge-${gene.level}">${gene.level}</strong>
      </div>
    </div>
    <p class="sub" style="margin-bottom:8px">Why this preview flagged him</p>
    <ul class="why">${gene.why.map((w) => `<li>${w}</li>`).join("")}</ul>
    <p class="suggest">${suggestion(gene.level)}</p>
    <p class="loop-note">Clinician in the loop: this screen does not diagnose and does not replace the doctor.</p>
    <p class="fineprint">${SAMPLE_NOTE}</p>
  `;
}

function renderCase(patient, isNew) {
  const panel = document.getElementById("case-panel");
  panel.innerHTML = `
    <div class="case-grid">
      <section class="card">
        <h2>${isNew ? "New sample case" : patient.name}</h2>
        <p class="sub">${patient.label}. Fictional. Not a real patient.</p>
        <form id="case-form">
          <div class="fields">
            <label>Age (years)
              <input name="age" type="number" min="30" max="90" value="${patient.age}" required>
            </label>
            <label>PSA (ng/mL)
              <input name="psa" type="number" min="0" max="200" step="0.1" value="${patient.psa}" required>
            </label>
            <label>Gleason
              <select name="gleason">
                ${[6, 7, 8, 9, 10]
                  .map((g) => `<option value="${g}"${g === patient.gleason ? " selected" : ""}>${g}</option>`)
                  .join("")}
              </select>
            </label>
            <label>Stage
              <select name="stage">
                ${["T1", "T1c", "T2", "T3", "T4", "N1", "M1"]
                  .map((s) => `<option value="${s}"${s === patient.stage ? " selected" : ""}>${s}</option>`)
                  .join("")}
              </select>
            </label>
            <label class="check span-2">
              <input name="family" type="checkbox"${patient.family ? " checked" : ""}>
              Family history of prostate cancer
            </label>
            <label class="check span-2">
              <input name="genomic" type="checkbox"${patient.genomic ? " checked" : ""}>
              Sample African genomic profile on file (preview switch — not a real gene file)
            </label>
          </div>
          <button class="btn" type="submit" style="margin-top:16px">Update preview</button>
        </form>
        <p class="loop-note">Hospital or partner lab would sequence. GeneHus would only analyse. This preview does not accept real DNA files.</p>
      </section>
      <section class="card" id="result-card">
        ${resultCard(patient)}
      </section>
    </div>
  `;

  panel.querySelector("#case-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const next = readForm(e.target);
    document.getElementById("result-card").innerHTML = resultCard(next);
  });

  renderQueue(isNew ? null : patient.id);
}

function openCase(id) {
  const patient = CASES.find((c) => c.id === id);
  if (patient) renderCase(patient, false);
}

function startApp() {
  const list = document.getElementById("queue-list");
  const newBtn = document.getElementById("new-case-btn");
  if (!list || !newBtn) return;

  const first = rankedCases()[0];
  renderQueue(first.id);
  openCase(first.id);

  list.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-id]");
    if (btn) openCase(btn.dataset.id);
  });

  newBtn.addEventListener("click", () => {
    renderCase(
      {
        id: "custom",
        name: "New sample case",
        label: "Typed by you (still fictional)",
        age: 60,
        psa: 6,
        gleason: 7,
        stage: "T2",
        family: false,
        genomic: true
      },
      true
    );
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", startApp);
} else {
  startApp();
}
