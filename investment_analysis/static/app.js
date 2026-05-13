const exampleHoldings = [
  {
    snapshot_date: "2025-05-07",
    user_id: "U001",
    account_id: "A001",
    symbol: "600000",
    stock_name: "示例银行",
    quantity: 3000,
    market_price: 7.8,
    market_value: 23400,
    position_weight: 0.39,
    unrealized_pnl: -2500,
    unrealized_pnl_pct: -0.1,
    sector: "金融"
  }
];

let latestResult = null;
let authToken = localStorage.getItem("investment_auth_token") || "";
let currentUser = JSON.parse(localStorage.getItem("investment_user") || "null");

const $ = (id) => document.getElementById(id);

function setMessage(text, isError = false) {
  const message = $("message");
  message.textContent = text;
  message.classList.toggle("hidden", !text);
  message.style.color = isError ? "var(--danger)" : "var(--warn)";
}

function formatJson(value) {
  return JSON.stringify(value, null, 2);
}

function percent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `${(Number(value) * 100).toFixed(1)}%`;
}

async function requestJson(url, options = {}) {
  const headers = {"Content-Type": "application/json", ...(options.headers || {})};
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }
  const response = await fetch(url, {
    headers,
    ...options
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(data.error || `请求失败：${response.status}`);
  }
  return data;
}

async function sendCode() {
  const contact = $("contactInput").value.trim();
  if (!contact) {
    setMessage("请输入邮箱或手机号", true);
    return;
  }
  try {
    const result = await requestJson("/api/v1/auth/request-code", {
      method: "POST",
      body: JSON.stringify({contact})
    });
    $("codeInput").value = result.dev_code || "";
    setMessage(`验证码已生成：${result.dev_code}。本地版本直接回填，接入短信/邮件后这里会改为发送。`);
  } catch (error) {
    setMessage(error.message, true);
  }
}

async function login() {
  const contact = $("contactInput").value.trim();
  const code = $("codeInput").value.trim();
  if (!contact || !code) {
    setMessage("请输入联系方式和验证码", true);
    return;
  }
  try {
    const result = await requestJson("/api/v1/auth/verify-code", {
      method: "POST",
      body: JSON.stringify({contact, code})
    });
    authToken = result.token;
    currentUser = result.user;
    localStorage.setItem("investment_auth_token", authToken);
    localStorage.setItem("investment_user", JSON.stringify(currentUser));
    applyAuthState();
    setMessage("登录成功。后续分析报告会按当前用户持久化。");
    refreshReports();
  } catch (error) {
    setMessage(error.message, true);
  }
}

function logout() {
  authToken = "";
  currentUser = null;
  localStorage.removeItem("investment_auth_token");
  localStorage.removeItem("investment_user");
  applyAuthState();
  setMessage("已退出登录。");
}

function applyAuthState() {
  const loggedIn = Boolean(authToken && currentUser);
  $("authBox").classList.toggle("hidden", loggedIn);
  $("userBox").classList.toggle("hidden", !loggedIn);
  $("userLabel").textContent = loggedIn ? `${currentUser.contact_type}: ${currentUser.contact}` : "";
  if (loggedIn) {
    $("userId").value = currentUser.user_id;
    $("accountId").value = currentUser.contact;
  }
}

async function checkHealth() {
  try {
    const data = await requestJson("/health");
    $("serviceStatus").textContent = data.status === "ok" ? "服务正常" : "状态未知";
    $("serviceStatus").className = "status ok";
  } catch (error) {
    $("serviceStatus").textContent = "服务异常";
    $("serviceStatus").className = "status error";
  }
}

function loadExample() {
  $("userId").value = "U001";
  $("accountId").value = "A001";
  $("tradeFilePath").value = "examples/trades.csv";
  $("accountAsset").value = "60000";
  $("holdingsInput").value = formatJson(exampleHoldings);
}

function buildPayload() {
  let holdings = [];
  const holdingsText = $("holdingsInput").value.trim();
  if (holdingsText) {
    holdings = JSON.parse(holdingsText);
    if (!Array.isArray(holdings)) {
      throw new Error("当前持仓 JSON 必须是数组");
    }
  }
  return {
    user_id: currentUser?.user_id || $("userId").value.trim(),
    account_id: $("accountId").value.trim() || currentUser?.contact || "DEFAULT",
    trade_file_path: $("tradeFilePath").value.trim(),
    account_asset: Number($("accountAsset").value || 0) || undefined,
    current_holdings: holdings
  };
}

async function runAnalysis() {
  const button = $("runBtn");
  button.disabled = true;
  button.textContent = "分析中";
  setMessage("");
  try {
    const result = await requestJson("/api/v1/analysis/run", {
      method: "POST",
      body: JSON.stringify(buildPayload())
    });
    latestResult = result;
    renderResult(result);
    setMessage(`分析完成。报告已保存为 ${result.report_id || "R_001"}。`);
    if (authToken) {
      refreshReports();
    }
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "一键分析";
  }
}

async function checkCompliance() {
  const text = $("complianceText").value;
  try {
    const result = await requestJson("/api/v1/llm/compliance/check", {
      method: "POST",
      body: JSON.stringify({text})
    });
    $("complianceResult").textContent = formatJson(result);
  } catch (error) {
    $("complianceResult").textContent = error.message;
  }
}

function renderResult(result) {
  const selectedSegments = result.selected_segments || [];
  const candidateSegments = result.candidate_segments || [];
  const displaySegments = selectedSegments.length ? selectedSegments : candidateSegments;
  const showingCandidates = selectedSegments.length === 0 && candidateSegments.length > 0;

  $("parseStatus").textContent = result.parse_result?.status || "--";
  $("validRows").textContent = result.parse_result?.valid_rows ?? "--";
  $("segmentCount").textContent = displaySegments.length;
  $("suitabilityScore").textContent = result.suitability?.scores?.overall_suitability_score ?? "--";
  renderPersona(result.persona);
  renderLlm(result.llm_enrichment);
  renderConflicts(result.suitability?.risk_conflicts || []);
  renderSegments(displaySegments, result.llm_enrichment?.behavior_summaries || [], showingCandidates);
  renderQuestions(result.questions || []);
  renderMarkdown(result.report?.markdown || "");
  $("rawJson").textContent = formatJson(result);
  if (result.report_url) {
    const tokenSuffix = authToken && result.report_id !== "R_001" ? `?token=${encodeURIComponent(authToken)}` : "";
    $("reportLink").href = `${result.report_url}${tokenSuffix}`;
  }
}

function renderPersona(persona) {
  if (!persona) {
    $("personaBox").textContent = "暂无画像";
    return;
  }
  const scores = persona.scores || {};
  $("personaBox").innerHTML = `
    <p><strong>${escapeHtml(persona.primary_persona || "--")}</strong></p>
    <p class="muted">${escapeHtml(persona.summary || "")}</p>
    <div class="kv">
      <div>损失厌恶<strong>${scores.loss_aversion ?? "--"}</strong></div>
      <div>纪律性<strong>${scores.discipline ?? "--"}</strong></div>
      <div>踏空焦虑<strong>${scores.fomo_tendency ?? "--"}</strong></div>
      <div>持仓耐心<strong>${scores.holding_patience ?? "--"}</strong></div>
    </div>
  `;
}

function renderLlm(llm) {
  if (!llm) {
    $("llmBox").textContent = "暂无 LLM 状态";
    return;
  }
  $("llmBox").innerHTML = `
    <div class="kv">
      <div>模型<strong>${escapeHtml(llm.model_name || "--")}</strong></div>
      <div>状态<strong>${escapeHtml(llm.status || "--")}</strong></div>
      <div>Prompt<strong>${escapeHtml(llm.prompt_version || "--")}</strong></div>
      <div>行为总结<strong>${llm.behavior_summaries?.length ?? 0}</strong></div>
    </div>
  `;
}

function renderConflicts(conflicts) {
  const list = $("conflictList");
  list.innerHTML = "";
  if (!conflicts.length) {
    list.innerHTML = "<li class=\"muted\">暂无风险冲突</li>";
    return;
  }
  for (const item of conflicts) {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  }
}

function renderSegments(segments, summaries, showingCandidates = false) {
  const byId = new Map(summaries.map((item) => [item.segment_id, item]));
  const target = $("segmentsList");
  $("segmentsTitle").textContent = showingCandidates ? "可复盘行为线索" : "代表性行为片段";
  target.innerHTML = "";
  if (!segments.length) {
    target.innerHTML = "<div class=\"empty\">暂无代表性行为片段</div>";
    return;
  }
  for (const segment of segments) {
    const summary = byId.get(segment.segment_id);
    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `
      <div class="card-head">
        <div>
          <h2>${escapeHtml(segment.behavior_name || segment.behavior_type)}</h2>
          <p class="muted">${escapeHtml(segment.stock_name || segment.symbol)} · ${escapeHtml(segment.start_date)} 至 ${escapeHtml(segment.end_date)}</p>
        </div>
        <span class="badge">${Math.round(segment.scores?.segment_score || 0)} 分</span>
      </div>
      <p>${escapeHtml(summary?.behavior_observation || segment.summary || "")}</p>
      <p class="muted">${escapeHtml(summary?.potential_risk || "")}</p>
      <div class="kv">
        <div>最高仓位<strong>${percent(segment.evidence?.max_position_weight)}</strong></div>
        <div>最大浮亏<strong>${percent(segment.evidence?.max_drawdown_pct)}</strong></div>
        <div>置信度<strong>${escapeHtml(segment.confidence || "--")}</strong></div>
      </div>
    `;
    target.appendChild(card);
  }
}

function renderQuestions(questions) {
  const target = $("questionsList");
  target.innerHTML = "";
  if (!questions.length) {
    target.innerHTML = "<div class=\"empty\">暂无问题</div>";
    return;
  }
  for (const question of questions) {
    const card = document.createElement("article");
    card.className = "card";
    const options = (question.options || []).map((item) => `<li>${escapeHtml(item.key)}. ${escapeHtml(item.text)}</li>`).join("");
    card.innerHTML = `
      <div class="card-head">
        <h2>${escapeHtml(question.question_id)} · ${escapeHtml(question.question_type)}</h2>
        <span class="badge">${escapeHtml(question.segment_id)}</span>
      </div>
      <p>${escapeHtml(question.question_text)}</p>
      <ul class="list">${options}</ul>
    `;
    target.appendChild(card);
  }
}

function renderMarkdown(markdown) {
  if (!markdown) {
    $("reportMarkdown").textContent = "等待分析结果";
    return;
  }
  const lines = markdown.split("\n");
  const html = lines.map((line) => {
    if (line.startsWith("# ")) return `<h1>${escapeHtml(line.slice(2))}</h1>`;
    if (line.startsWith("## ")) return `<h2>${escapeHtml(line.slice(3))}</h2>`;
    if (line.startsWith("- ")) return `<p>• ${escapeHtml(line.slice(2))}</p>`;
    if (/^\d+\./.test(line.trim())) return `<p>${escapeHtml(line)}</p>`;
    if (!line.trim()) return "";
    return `<p>${escapeHtml(line)}</p>`;
  }).join("");
  $("reportMarkdown").innerHTML = html;
}

function clearResult() {
  latestResult = null;
  setMessage("");
  $("parseStatus").textContent = "--";
  $("validRows").textContent = "--";
  $("segmentCount").textContent = "--";
  $("suitabilityScore").textContent = "--";
  $("personaBox").textContent = "等待分析结果";
  $("llmBox").textContent = "等待分析结果";
  $("conflictList").innerHTML = "";
  $("segmentsTitle").textContent = "代表性行为片段";
  $("segmentsList").innerHTML = "";
  $("questionsList").innerHTML = "";
  $("reportMarkdown").textContent = "等待分析结果";
  $("rawJson").textContent = "";
}

async function refreshReports() {
  const target = $("reportHistory");
  if (!authToken) {
    target.innerHTML = "<div class=\"empty\">登录后可查看历史报告</div>";
    return;
  }
  try {
    const result = await requestJson("/api/v1/reports");
    const reports = result.reports || [];
    if (!reports.length) {
      target.innerHTML = "<div class=\"empty\">暂无历史报告</div>";
      return;
    }
    target.innerHTML = "";
    for (const report of reports) {
      const card = document.createElement("article");
      card.className = "card";
      const url = report.report_url?.includes("?") ? report.report_url : `${report.report_url}?token=${encodeURIComponent(authToken)}`;
      card.innerHTML = `
        <div class="card-head">
          <div>
            <h2>${escapeHtml(report.artifact_id)}</h2>
            <p class="muted">${escapeHtml(report.created_at)} · ${escapeHtml(report.account_id)}</p>
          </div>
          <a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">打开</a>
        </div>
        <p>${escapeHtml(report.summary || "暂无摘要")}</p>
      `;
      target.appendChild(card);
    }
  } catch (error) {
    target.innerHTML = `<div class="empty">${escapeHtml(error.message)}</div>`;
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function setupTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".tab-view").forEach((item) => item.classList.remove("active"));
      tab.classList.add("active");
      $(tab.dataset.tab).classList.add("active");
    });
  });
}

function setup() {
  setupTabs();
  loadExample();
  applyAuthState();
  $("loadExampleBtn").addEventListener("click", loadExample);
  $("runBtn").addEventListener("click", runAnalysis);
  $("clearBtn").addEventListener("click", clearResult);
  $("checkComplianceBtn").addEventListener("click", checkCompliance);
  $("sendCodeBtn").addEventListener("click", sendCode);
  $("loginBtn").addEventListener("click", login);
  $("logoutBtn").addEventListener("click", logout);
  $("refreshReportsBtn").addEventListener("click", refreshReports);
  checkHealth();
  refreshReports();
}

setup();
