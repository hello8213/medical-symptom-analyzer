
const analyzeBtn = document.getElementById("analyzeBtn");
const resetBtn = document.getElementById("resetBtn");
const resultsEl = document.getElementById("results");
const errorEl = document.getElementById("error");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[char]));
}

function renderDisease(disease) {
  const sources = (disease.sources || []).map(source => {
    const label = escapeHtml(source[0]);
    const url = escapeHtml(source[1]);

    return `<a href="${url}" target="_blank"
      rel="noopener noreferrer">${label}</a>`;
  }).join("");

  return `
    <article class="result-card">
      <div class="result-head">
        <div>
          <h3>${escapeHtml(disease.name)}</h3>
          <span class="pill">${escapeHtml(disease.category)}</span>
        </div>
        <div class="score">
          规则匹配参考分：${escapeHtml(disease.score)} / 100
          <br>不是患病概率
        </div>
      </div>

      <div class="detail">
        <h4>匹配到的症状</h4>
        <p>${(disease.matched || []).map(escapeHtml).join("、")}</p>
      </div>

      <div class="detail">
        <h4>发病原因与机制</h4>
        <p>${escapeHtml(disease.causes)}</p>
      </div>

      <div class="detail">
        <h4>常见症状</h4>
        <p>${escapeHtml(disease.symptom_detail)}</p>
      </div>

      <div class="detail">
        <h4>可能需要的医学检查</h4>
        <p>${escapeHtml(disease.tests)}</p>
      </div>

      <div class="detail">
        <h4>规范治疗信息</h4>
        <p>${escapeHtml(disease.treatment)}</p>
      </div>

      <div class="detail sources">
        <h4>医学参考资料</h4>
        ${sources || "暂无参考链接"}
      </div>
    </article>
  `;
}

analyzeBtn.addEventListener("click", async () => {
  errorEl.textContent = "";
  resultsEl.innerHTML = "";

  const age = document.getElementById("age").value;
  const sex = document.getElementById("sex").value;
  const duration = document.getElementById("duration").value;

  const symptoms = [
    ...document.querySelectorAll(
      'input[name="symptom"]:checked'
    )
  ].map(element => element.value);

  const red_flags = [
    ...document.querySelectorAll(
      'input[name="redflag"]:checked'
    )
  ].map(element => element.value);

  if (age === "" || !Number.isInteger(Number(age)) ||
      Number(age) < 0 || Number(age) > 120) {
    errorEl.textContent = "请输入 0 到 120 岁之间的有效年龄。";
    return;
  }

  if (symptoms.length === 0) {
    errorEl.textContent = "请至少选择一个症状。";
    return;
  }

  // 如果已经勾选危险信号，先提醒，不要求等待分析。
  if (red_flags.length > 0) {
    const emergencyNotice = document.createElement("div");
    emergencyNotice.className = "warning";
    emergencyNotice.textContent =
      "你已勾选危险信号。如果症状正在发生或情况严重，" +
      "请立即联系当地急救服务，不要等待网页分析。";
    resultsEl.appendChild(emergencyNotice);
  }

  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "正在分析…";

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        age,
        sex,
        duration,
        symptoms,
        red_flags
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "分析失败，请重试。");
    }

    let html = `
      <h2>分析结果</h2>
      <div class="notice">
        <strong>重要说明：</strong>
        ${escapeHtml(data.disclaimer)}
      </div>
      <p class="muted">
        年龄：${escapeHtml(data.age)} 岁；
        症状持续时间：${escapeHtml(data.duration)}
      </p>
    `;

    if (data.emergency_warning) {
      html += `
        <div class="warning">
          <strong>危险信号提醒</strong>
          <p>
            你勾选了：
            ${data.red_flags.map(flag =>
              escapeHtml(flag.label)
            ).join("、")}
          </p>
          <p>
            如果这些症状正在发生或情况严重，请立即联系当地急救服务。
            在加拿大或美国，急救电话为 911。
          </p>
        </div>
      `;
    }

    if (!data.results || data.results.length === 0) {
      html += `
        <div class="empty">
          当前示例数据库没有找到明显匹配项。
          这不代表没有疾病，也不代表症状安全。
          如果症状持续、加重或让你担心，请联系医疗专业人员。
        </div>
      `;
    } else {
      html += `
        <p class="muted">
          以下项目按简单的症状重合规则排序。
          排序不等于临床诊断，也不是患病概率。
        </p>
      `;

      html += data.results.map(renderDisease).join("");
    }

    resultsEl.innerHTML += html;
    resultsEl.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });

  } catch (error) {
    errorEl.textContent =
      error.message || "服务器连接失败，请检查应用是否正在运行。";
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "分析症状";
  }
});

resetBtn.addEventListener("click", () => {
  document.getElementById("age").value = "";
  document.getElementById("sex").value = "unspecified";
  document.getElementById("duration").value = "unknown";

  document.querySelectorAll('input[type="checkbox"]')
    .forEach(element => {
      element.checked = false;
    });

  resultsEl.innerHTML = "";
  errorEl.textContent = "";
});

