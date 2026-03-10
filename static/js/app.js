/**
 * Customer Support Email Agent — Frontend Logic
 */

const API_BASE = '';

// ─── State ───
let emailHistory = [];
let allReviews = [];
let stats = { total: 0, auto: 0, reviewed: 0, followups: 0 };

// ─── Utility: Populate Dropdowns Dynamically ───
function populateFilter(selectId, data, key, defaultLabel) {
    const select = document.getElementById(selectId);
    if (!select) return;

    // Save current selection
    const currentVal = select.value;

    // Get unique non-null values
    const uniqueVals = [...new Set(data.map(item => item[key]).filter(v => v))].sort();

    // Reset and populate
    select.innerHTML = `<option value="">${defaultLabel}</option>` +
        uniqueVals.map(v => `<option value="${v.toLowerCase()}">${v.charAt(0).toUpperCase() + v.slice(1)}</option>`).join('');

    // Restore selection if it still exists
    if (uniqueVals.map(v => v.toLowerCase()).includes(currentVal)) {
        select.value = currentVal;
    }
}

// ─── DOM Ready ───
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    setInterval(checkHealth, 15000);
    loadPendingReviews();
    loadHistoryAndStats();

    // Theme Toggle Logic
    const themeBtn = document.getElementById('themeToggle');
    const currentTheme = localStorage.getItem('theme') || 'dark';
    if (currentTheme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
        if (themeBtn) themeBtn.innerHTML = '🌙 Dark Theme';
    }

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            const isLight = document.documentElement.getAttribute('data-theme') === 'light';
            if (isLight) {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('theme', 'dark');
                themeBtn.innerHTML = '🌓 Light Theme';
            } else {
                document.documentElement.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
                themeBtn.innerHTML = '🌙 Dark Theme';
            }
        });
    }

    // Search Logic
    const searchReviewsInput = document.getElementById('searchReviews');
    if (searchReviewsInput) {
        searchReviewsInput.addEventListener('input', () => {
            renderReviews();
        });
    }

    const searchHistoryInput = document.getElementById('searchHistory');
    if (searchHistoryInput) {
        searchHistoryInput.addEventListener('input', () => {
            renderHistory();
        });
    }

    // Filter Logic
    ['filterReviewReason', 'filterHistoryCategory', 'filterHistoryPriority', 'filterHistoryStatus', 'filterHistoryType'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', () => {
            if (id.includes('Review')) renderReviews();
            else renderHistory();
        });
    });
});

// ─── Tab Navigation ───
function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');

    if (tabId === 'reviews') loadPendingReviews();
}

// ─── Health Check ───
async function checkHealth() {
    const badge = document.getElementById('healthBadge');
    try {
        const res = await fetch(`${API_BASE}/health`);
        if (res.ok) {
            badge.innerHTML = '<span class="dot"></span> System Online';
            badge.className = 'health-badge';
        } else {
            throw new Error();
        }
    } catch {
        badge.innerHTML = '<span class="dot"></span> System Offline';
        badge.className = 'health-badge offline';
    }
}

// ─── Submit Email ───
async function submitEmail(e) {
    e.preventDefault();
    const btn = document.getElementById('submitBtn');
    const resultPanel = document.getElementById('resultPanel');

    const payload = {
        sender: document.getElementById('sender').value.trim(),
        subject: document.getElementById('subject').value.trim(),
        body: document.getElementById('body').value.trim(),
    };

    if (!payload.sender || !payload.subject || !payload.body) {
        showToast('Please fill in all fields', 'error');
        return;
    }

    // Show loading state
    btn.classList.add('loading');
    btn.disabled = true;
    resultPanel.classList.remove('visible');

    // Animate pipeline starting state
    resetPipeline();
    syncPipelineNode('retrieve'); // Start with first node

    try {
        const res = await fetch(`${API_BASE}/api/emails/test/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Server error: ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep last incomplete line

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = JSON.parse(line.slice(6));

                    if (data.node) {
                        syncPipelineNode(data.node);
                    } else if (data.complete) {
                        const finalData = data.result;
                        displayResult(finalData);
                        completePipeline(finalData);
                        addToHistory(finalData, payload);
                        updateStats(finalData);
                        showToast('Email processed successfully!', 'success');
                    } else if (data.error) {
                        throw new Error(data.error);
                    }
                }
            }
        }

    } catch (err) {
        showToast(err.message || 'Failed to process email', 'error');
        resetPipeline();
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

// ─── Display Result ───
function displayResult(data) {
    const panel = document.getElementById('resultPanel');

    // Badges
    const badgesHtml = `
        <span class="badge badge-category">📂 ${data.category || 'unknown'}</span>
        <span class="badge badge-priority ${data.priority || ''}">${getPriorityIcon(data.priority)} ${data.priority || 'unknown'}</span>
        <span class="badge badge-status ${getStatusClass(data.status)}">${getStatusIcon(data.status)} ${data.status || 'unknown'}</span>
        ${data.needs_human_review ? `<span class="badge badge-review">👁 Human Review: ${data.review_reason || 'Required'}</span>` : ''}
        ${data.followup_scheduled ? '<span class="badge badge-status">📅 Follow-up Scheduled</span>' : ''}
    `;
    document.getElementById('resultBadges').innerHTML = badgesHtml;

    // Processing time
    if (data.processing_time_ms) {
        document.getElementById('processingTime').textContent = `${data.processing_time_ms.toFixed(0)}ms`;
    }

    // Confidence
    const confEl = document.getElementById('confidenceScore');
    if (data.confidence_score !== null && data.confidence_score !== undefined) {
        confEl.textContent = `Confidence: ${(data.confidence_score * 100).toFixed(0)}%`;
        confEl.style.display = 'inline';
    } else {
        confEl.style.display = 'none';
    }

    // Response
    const responseText = document.getElementById('responseText');
    if (data.generated_response) {
        responseText.textContent = data.generated_response;
        document.getElementById('responseBox').style.display = 'block';
    } else {
        document.getElementById('responseBox').style.display = 'none';
    }

    panel.classList.add('visible');
}

// ─── Pipeline Animation ───
const PIPELINE_NODES = [
    'retrieve', 'guardrails', 'classify', 'context', 'review_check',
    'generate', 'review_route', 'human_review', 'send', 'followup'
];

const NODE_MAP = {
    'email_retrieval': 'retrieve',
    'guardrails': 'guardrails',
    'classification': 'classify',
    'context_analysis': 'context',
    'review_check': 'review_check',
    'response_generation': 'generate',
    'review_routing': 'review_route',
    'human_review': 'human_review',
    'response_sending': 'send',
    'followup_scheduling': 'followup'
};

function syncPipelineNode(nodeId) {
    const frontendId = NODE_MAP[nodeId] || nodeId;
    const nodeIndex = PIPELINE_NODES.indexOf(frontendId);

    if (nodeIndex === -1) return;

    PIPELINE_NODES.forEach((id, i) => {
        const node = document.getElementById(`node-${id}`);
        if (!node) return;

        if (i < nodeIndex) {
            node.className = 'pipeline-node completed';
        } else if (i === nodeIndex) {
            node.className = 'pipeline-node active';
        } else {
            node.className = 'pipeline-node';
        }
    });

    // Handle arrows
    document.querySelectorAll('.pipeline-arrow').forEach((arrow, i) => {
        if (i < nodeIndex) {
            arrow.className = 'pipeline-arrow completed';
        } else if (i === nodeIndex) {
            arrow.className = 'pipeline-arrow active';
        } else {
            arrow.className = 'pipeline-arrow';
        }
    });
}

function resetPipeline() {
    PIPELINE_NODES.forEach(id => {
        const node = document.getElementById(`node-${id}`);
        if (node) node.className = 'pipeline-node';
    });
    document.querySelectorAll('.pipeline-arrow').forEach(arrow => {
        arrow.className = 'pipeline-arrow';
    });
}

function animatePipeline() {
    // No longer used, replaced by real-time syncPipelineNode
}

function completePipeline(data) {
    const activeNodes = ['retrieve', 'guardrails', 'classify', 'context', 'review_check', 'generate'];
    if (data.needs_human_review) {
        activeNodes.push('review_route', 'human_review');
    }
    activeNodes.push('send');
    if (data.followup_scheduled) activeNodes.push('followup');

    PIPELINE_NODES.forEach(id => {
        const node = document.getElementById(`node-${id}`);
        if (node) {
            node.className = 'pipeline-node';
            if (activeNodes.includes(id)) {
                node.classList.add('completed');
            }
        }
    });

    document.querySelectorAll('.pipeline-arrow').forEach(a => a.classList.add('completed'));
}

// ─── History & Stats ───
async function loadHistoryAndStats() {
    try {
        const res = await fetch(`${API_BASE}/api/emails/history`);
        if (!res.ok) throw new Error();

        const data = await res.json();

        // Update stats
        stats = data.stats;
        document.getElementById('statTotal').textContent = stats.total;
        document.getElementById('statAuto').textContent = stats.auto;
        document.getElementById('statReview').textContent = stats.reviewed;
        document.getElementById('statFollowup').textContent = stats.followups;

        // Update history
        emailHistory = data.history.map(e => ({
            id: e.id,
            sender: e.sender,
            subject: e.subject,
            category: e.category,
            priority: e.priority,
            status: e.status,
            is_human_reviewed: e.is_human_reviewed
        }));

        // Dynamically populate history filters
        populateFilter('filterHistoryCategory', emailHistory, 'category', 'All Categories');
        populateFilter('filterHistoryPriority', emailHistory, 'priority', 'All Priorities');
        populateFilter('filterHistoryStatus', emailHistory, 'status', 'All Statuses');

        renderHistory();
    } catch (e) {
        console.error("Failed to load history and stats:", e);
    }
}

function addToHistory(data, payload) {
    emailHistory.unshift({
        id: data.email_id,
        sender: payload.sender,
        subject: payload.subject,
        category: data.category,
        priority: data.priority,
        status: data.status,
        is_human_reviewed: data.needs_human_review, // For test/live updates, we know if it needed review
        time: new Date().toLocaleTimeString(),
    });
    if (emailHistory.length > 50) emailHistory.pop();
    renderHistory();
}

function renderHistory() {
    const tbody = document.getElementById('historyBody');
    const searchTerm = document.getElementById('searchHistory')?.value.toLowerCase() || '';
    const filterCat = document.getElementById('filterHistoryCategory')?.value.toLowerCase() || '';
    const filterPri = document.getElementById('filterHistoryPriority')?.value.toLowerCase() || '';
    const filterSta = document.getElementById('filterHistoryStatus')?.value.toLowerCase() || '';
    const filterType = document.getElementById('filterHistoryType')?.value.toLowerCase() || '';

    const filtered = emailHistory.filter(e => {
        const matchesSearch = e.sender.toLowerCase().includes(searchTerm) ||
            e.subject.toLowerCase().includes(searchTerm) ||
            e.id.toString().includes(searchTerm);

        const matchesCat = !filterCat || (e.category && e.category.toLowerCase() === filterCat);
        const matchesPri = !filterPri || (e.priority && e.priority.toLowerCase() === filterPri);
        const matchesSta = !filterSta || (e.status && e.status.toLowerCase().includes(filterSta.replace('_', ' ')));

        let matchesType = true;
        if (filterType === 'human') matchesType = e.is_human_reviewed;
        else if (filterType === 'auto') matchesType = !e.is_human_reviewed;

        return matchesSearch && matchesCat && matchesPri && matchesSta && matchesType;
    });

    if (!filtered.length) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color: var(--text-muted); padding: 40px;">${(searchTerm || filterCat || filterPri || filterSta || filterType) ? 'No matching results' : 'No emails processed yet'}</td></tr>`;
        return;
    }
    tbody.innerHTML = filtered.map(e => `
        <tr onclick="viewEmailDetails(${e.id})" style="cursor: pointer;">
            <td>#${e.id}</td>
            <td>${e.sender}</td>
            <td>${e.subject}</td>
            <td><span class="badge badge-category">${e.category || '-'}</span></td>
            <td><span class="badge badge-priority ${e.priority || ''}">${e.priority || '-'}</span></td>
            <td><span class="badge badge-status ${getStatusClass(e.status)}">${e.status || '-'}</span></td>
            <td>${e.is_human_reviewed ? '🧑 Human' : '🤖 Auto'}</td>
        </tr>
    `).join('');
}

function updateStats(data) {
    stats.total++;
    if (!data.needs_human_review) stats.auto++;
    else stats.reviewed++;
    if (data.followup_scheduled) stats.followups++;

    document.getElementById('statTotal').textContent = stats.total;
    document.getElementById('statAuto').textContent = stats.auto;
    document.getElementById('statReview').textContent = stats.reviewed;
    document.getElementById('statFollowup').textContent = stats.followups;
}

// ─── Reviews ───
async function loadPendingReviews() {
    const container = document.getElementById('reviewsList');
    try {
        const res = await fetch(`${API_BASE}/api/reviews/pending`);
        if (!res.ok) throw new Error();
        allReviews = await res.json();

        // Dynamically populate review filters
        populateFilter('filterReviewReason', allReviews, 'reason', 'All Reasons');

        renderReviews();
    } catch {
        container.innerHTML = '<div class="reviews-empty"><p>Failed to load reviews</p></div>';
    }
}

function renderReviews() {
    const container = document.getElementById('reviewsList');
    const searchTerm = document.getElementById('searchReviews')?.value.toLowerCase() || '';
    const filterReason = document.getElementById('filterReviewReason')?.value.toLowerCase() || '';

    const filtered = allReviews.filter(r => {
        const matchesSearch = (r.customer_email && r.customer_email.toLowerCase().includes(searchTerm)) ||
            (r.customer_subject && r.customer_subject.toLowerCase().includes(searchTerm)) ||
            (r.customer_body && r.customer_body.toLowerCase().includes(searchTerm));

        const matchesReason = !filterReason || (r.reason && r.reason.toLowerCase().includes(filterReason));

        return matchesSearch && matchesReason;
    });

    if (!filtered.length) {
        container.innerHTML = `
            <div class="reviews-empty">
                <div class="empty-icon">${(searchTerm || filterReason) ? '🔍' : '✅'}</div>
                <p>${(searchTerm || filterReason) ? 'No matching reviews found' : 'No pending reviews'}</p>
            </div>
        `;
        return;
    }

    container.innerHTML = filtered.map(r => `
        <div class="review-card" id="review-${r.review_id}">
            <div class="review-card-header">
                <h4>📧 Review #${r.review_id}</h4>
                <span class="badge badge-review">${r.reason || 'Needs Review'}</span>
            </div>
            
            <div class="review-customer-context" style="background: rgba(0,0,0,0.2); border-radius: 8px; padding: 16px; margin-bottom: 16px; border: 1px solid var(--border-glass);">
                <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">📥 Original Customer Email</div>
                <div style="margin-bottom: 6px; font-size: 14px;"><strong>From:</strong> ${r.customer_email || 'Unknown'}</div>
                <div style="margin-bottom: 16px; font-size: 14px;"><strong>Subject:</strong> ${r.customer_subject || 'No Subject'}</div>
                <div style="white-space: pre-wrap; color: var(--text-secondary); font-size: 14px; line-height: 1.6; background: rgba(255,255,255,0.02); padding: 12px; border-radius: 6px; border-left: 3px solid var(--border-glass);">${r.customer_body || ''}</div>
            </div>

            <div class="review-card-body">
                <div style="margin-bottom: 10px; color: var(--text-primary); font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">🤖 AI Draft Response (Editable)</div>
                <textarea id="review-text-${r.review_id}" style="width: 100%; min-height: 180px; background: rgba(255,255,255,0.04); border: 1px solid var(--border-glass); border-radius: 8px; padding: 16px; color: var(--text-primary); font-family: 'Inter', sans-serif; font-size: 14px; line-height: 1.6; resize: vertical; margin-bottom: 16px; outline: none; transition: border-color 0.2s;" onfocus="this.style.borderColor='var(--accent-indigo)'" onblur="this.style.borderColor='var(--border-glass)'">${r.original_response || ''}</textarea>
            </div>

            <div class="review-actions">
                <button class="btn-approve" onclick="approveReview(${r.review_id})">✅ Approve & Send Response</button>
            </div>
        </div>
    `).join('');
}

async function approveReview(reviewId) {
    try {
        // Read the optionally edited response from the textarea
        const textarea = document.getElementById(`review-text-${reviewId}`);
        const approvedResponse = textarea ? textarea.value : undefined;

        const res = await fetch(`${API_BASE}/api/reviews/${reviewId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ approved_response: approvedResponse }),
        });

        if (!res.ok) throw new Error();

        const data = await res.json();

        // Update the item in the history table
        const historyItem = emailHistory.find(e => e.id === data.email_id);
        if (historyItem) {
            historyItem.status = 'completed';
            renderHistory();
        }

        showToast(`Review #${reviewId} approved!`, 'success');
        loadPendingReviews();
    } catch {
        showToast('Failed to approve review', 'error');
    }
}

// ─── Toast Notifications ───
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} visible`;
    setTimeout(() => toast.classList.remove('visible'), 4000);
}

// ─── Helpers ───
function getPriorityIcon(p) {
    const icons = { urgent: '🔴', high: '🟠', medium: '🟡', low: '🟢' };
    return icons[p] || '⚪';
}

function getStatusClass(s) {
    if (!s) return '';
    if (s.includes('review') || s.includes('pending')) return 'review';
    if (s === 'failed') return 'failed';
    return '';
}

function getStatusIcon(s) {
    if (!s) return '❓';
    if (s === 'completed' || s === 'responded') return '✅';
    if (s.includes('review')) return '👁';
    if (s === 'failed') return '❌';
    return '⏳';
}

/* ─── Modal & Details ─── */
async function viewEmailDetails(emailId) {
    const modal = document.getElementById('emailDetailsModal');
    const title = document.getElementById('modalTitle');
    const body = document.getElementById('modalBody');

    modal.classList.add('active');
    title.innerHTML = `📧 Loading Email #${emailId}...`;
    body.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 40px;"><div class="spinner" style="display:inline-block; border-color: var(--accent-indigo); border-top-color: transparent;"></div></div>`;

    try {
        const res = await fetch(`${API_BASE}/api/emails/${emailId}`);
        if (!res.ok) throw new Error();
        const data = await res.json();

        title.innerHTML = `📧 Email #${data.id} Details`;

        const processedDate = data.processed_at ? new Date(data.processed_at).toLocaleString() : 'Processing...';
        const receivedDate = new Date(data.received_at).toLocaleString();

        let html = `
            <div class="detail-section">
                <div class="detail-section-title">📥 Original Email</div>
                <div class="detail-row"><strong>From:</strong> ${data.sender}</div>
                <div class="detail-row"><strong>Date:</strong> ${receivedDate}</div>
                <div class="detail-row" style="margin-bottom: 12px;"><strong>Subject:</strong> ${data.subject}</div>
                <div class="detail-text-box" style="border-left-color: var(--text-muted);">${data.body}</div>
            </div>

            <div class="detail-section">
                <div class="detail-section-title">🏷️ AI Classification</div>
                <div class="detail-row">
                    <strong>Category:</strong> <span class="badge badge-category">${data.category || 'N/A'}</span>
                    &nbsp;&nbsp;<strong>Priority:</strong> <span class="badge badge-priority ${data.priority || ''}">${data.priority || 'N/A'}</span>
                    &nbsp;&nbsp;<strong>Confidence:</strong> ${data.confidence_score ? (data.confidence_score * 100).toFixed(0) + '%' : 'N/A'}
                </div>
                <div class="detail-row"><strong>Status:</strong> <span class="badge badge-status ${getStatusClass(data.status)}">${data.status}</span></div>
            </div>
        `;

        // Only show AI response if it exists
        if (data.ai_response) {
            html += `
                <div class="detail-section">
                    <div class="detail-section-title">🤖 AI Response Details</div>
                    <div class="detail-row"><strong>Generated by:</strong> ${data.model_used || 'Unknown'}</div>
                    <div class="detail-row"><strong>Processed at:</strong> ${processedDate}</div>
            `;

            if (data.human_reviewed) {
                html += `<div class="detail-row"><span class="badge badge-status review">👁 Human Reviewed & Approved</span></div>`;
                if (data.reviewer_notes) {
                    html += `<div class="detail-row"><strong>Reviewer Notes:</strong> ${data.reviewer_notes}</div>`;
                }
            }

            html += `
                    <div class="detail-text-box">${data.ai_response}</div>
                </div>
            `;
        }

        // Only show followup if one exists
        if (data.followup_scheduled) {
            const followDate = new Date(data.followup_date).toLocaleString();
            html += `
                <div class="detail-section" style="border-color: rgba(16, 185, 129, 0.3);">
                    <div class="detail-section-title" style="color: var(--accent-emerald);">📅 Scheduled Follow-up</div>
                    <div class="detail-row"><strong>Scheduled For:</strong> ${followDate}</div>
                </div>
            `;
        }

        body.innerHTML = html;

    } catch (err) {
        title.innerHTML = `⚠️ Error`;
        body.innerHTML = `<div style="text-align: center; color: var(--accent-rose); padding: 40px;">Failed to fetch email details.</div>`;
    }
}

function closeModal() {
    document.getElementById('emailDetailsModal').classList.remove('active');
}
