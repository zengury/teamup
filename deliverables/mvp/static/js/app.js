/* ============================================================
   SweetLoaf AI 组织转型系统 — 前端交互逻辑
   ============================================================ */

(function() {
  'use strict';

  // ---- 工具函数 ----
  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.from((ctx || document).querySelectorAll(sel)); }

  function showToast(msg, duration) {
    duration = duration || 2500;
    var t = document.getElementById('toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'toast';
      t.className = 'toast';
      document.body.appendChild(t);
    }
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(t._hideTimer);
    t._hideTimer = setTimeout(function() { t.classList.remove('show'); }, duration);
  }

  function getUserId() {
    var el = document.getElementById('current-user-id');
    return el ? parseInt(el.value, 10) : null;
  }

  // ---- API 调用封装 ----
  var api = {
    get: function(url) {
      return fetch(url).then(function(r) { return r.json(); });
    },
    post: function(url, data) {
      return fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data || {}),
      }).then(function(r) { return r.json(); });
    },
  };

  // ---- 技能搜索（防抖） ----
  function initSkillSearch() {
    var input = document.getElementById('skill-search-input');
    if (!input) return;
    var timer = null;
    input.addEventListener('input', function() {
      clearTimeout(timer);
      timer = setTimeout(function() {
        var keyword = input.value.trim();
        var category = new URLSearchParams(location.search).get('category') || '';
        var params = new URLSearchParams();
        if (keyword) params.set('keyword', keyword);
        if (category) params.set('category', category);
        window.location.href = '/skills?' + params.toString();
      }, 400);
    });
  }

  // ---- 分类筛选 ----
  function initCategoryFilter() {
    $$('.filter-chip').forEach(function(chip) {
      chip.addEventListener('click', function() {
        var cat = this.dataset.category || '';
        var keyword = new URLSearchParams(location.search).get('keyword') || '';
        var params = new URLSearchParams();
        if (keyword) params.set('keyword', keyword);
        if (cat) params.set('category', cat);
        window.location.href = '/skills?' + params.toString();
      });
    });
  }

  // ---- 点赞 ----
  function initLikeButtons() {
    $$('.action-btn[data-action="like"]').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var skillId = this.dataset.skillId;
        var countEl = this.querySelector('.action-count');
        api.post('/api/skill/' + skillId + '/like').then(function(res) {
          if (res.success) {
            if (countEl) countEl.textContent = res.like_count;
            btn.classList.toggle('active');
            showToast('已點讚 ❤️');
          }
        });
      });
    });
  }

  // ---- 收藏 ----
  function initCollectButtons() {
    $$('.action-btn[data-action="collect"]').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var skillId = this.dataset.skillId;
        var countEl = this.querySelector('.action-count');
        api.post('/api/skill/' + skillId + '/collect').then(function(res) {
          if (res.success) {
            if (countEl) countEl.textContent = res.collect_count;
            btn.classList.toggle('active');
            showToast('已收藏 ⭐');
          }
        });
      });
    });
  }

  // ---- 评论提交 ----
  function initCommentForm() {
    var form = document.getElementById('comment-form');
    if (!form) return;
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var input = this.querySelector('input[name="comment"]');
      var skillId = this.dataset.skillId;
      if (!input.value.trim()) return;
      api.post('/api/skill/' + skillId + '/comment', { comment: input.value.trim() }).then(function(res) {
        if (res.success) {
          showToast('評論已送出 💬');
          input.value = '';
          // 简单刷新页面显示新评论
          setTimeout(function() { location.reload(); }, 500);
        }
      });
    });
  }

  // ---- 技能创建 ----
  function initSkillCreate() {
    var form = document.getElementById('skill-create-form');
    if (!form) return;

    var textInput = document.getElementById('skill-text-input');
    var parseBtn = document.getElementById('parse-btn');
    var previewEl = document.getElementById('parse-preview');
    var saveBtn = document.getElementById('save-skill-btn');
    var modeRadios = document.querySelectorAll('input[name="create-mode"]');
    var templateSelect = document.getElementById('template-select');
    var templateQuestions = document.getElementById('template-questions');

    // 模式切换
    modeRadios.forEach(function(r) {
      r.addEventListener('change', function() {
        var mode = this.value;
        document.getElementById('free-input-area').style.display = mode === 'free' ? 'block' : 'none';
        if (templateQuestions) {
          templateQuestions.style.display = mode === 'template' ? 'block' : 'none';
        }
      });
    });

    // AI 解析
    if (parseBtn && textInput) {
      parseBtn.addEventListener('click', function() {
        var text = textInput.value.trim();
        if (!text) { showToast('請輸入經驗描述'); return; }
        parseBtn.disabled = true;
        parseBtn.innerHTML = '<span class="spinner"></span> 解析中...';
        api.post('/skill/parse', { text: text }).then(function(res) {
          parseBtn.disabled = false;
          parseBtn.textContent = '🔍 AI 解析';
          if (res.success && res.parsed) {
            renderPreview(res.parsed);
          } else {
            showToast('解析失敗，請重試');
          }
        }).catch(function() {
          parseBtn.disabled = false;
          parseBtn.textContent = '🔍 AI 解析';
          showToast('網絡錯誤');
        });
      });
    }

    function renderPreview(parsed) {
      if (!previewEl) return;
      var html = '';
      if (parsed.title) html += '<div class="preview-field"><span class="field-label">📌 標題：</span><span class="field-value">' + escHtml(parsed.title) + '</span></div>';
      if (parsed.trigger_condition) html += '<div class="preview-field"><span class="field-label">⚡ 觸發條件：</span><span class="field-value">' + escHtml(parsed.trigger_condition) + '</span></div>';
      if (parsed.steps && parsed.steps.length) {
        html += '<div class="preview-field"><span class="field-label">📋 操作步驟：</span></div><ol>';
        parsed.steps.forEach(function(s) { html += '<li>' + escHtml(s) + '</li>'; });
        html += '</ol>';
      }
      if (parsed.expected_result) html += '<div class="preview-field"><span class="field-label">✅ 預期效果：</span><span class="field-value">' + escHtml(parsed.expected_result) + '</span></div>';
      if (parsed.tips) html += '<div class="preview-field"><span class="field-label">💡 小提示：</span><span class="field-value">' + escHtml(parsed.tips) + '</span></div>';
      previewEl.innerHTML = html;
      previewEl.classList.add('show');
      // 保存解析结果到隐藏域
      var hidden = document.getElementById('parsed-data');
      if (!hidden) {
        hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.id = 'parsed-data';
        hidden.name = 'parsed_data';
        form.appendChild(hidden);
      }
      hidden.value = JSON.stringify(parsed);
    }

    // 保存（自由输入模式）
    if (saveBtn && textInput) {
      saveBtn.addEventListener('click', function() {
        var text = textInput.value.trim();
        if (!text) { showToast('請輸入經驗描述'); return; }
        saveBtn.disabled = true;
        saveBtn.textContent = '儲存中...';
        api.post('/skill/create', { text: text }).then(function(res) {
          saveBtn.disabled = false;
          saveBtn.textContent = '💾 儲存 Skill';
          if (res.success) {
            showToast('✅ Skill 已建立！');
            setTimeout(function() { window.location.href = '/skill/' + res.skill_id; }, 800);
          } else {
            showToast('儲存失敗：' + (res.error || '未知錯誤'));
          }
        }).catch(function() {
          saveBtn.disabled = false;
          saveBtn.textContent = '💾 儲存 Skill';
          showToast('網絡錯誤');
        });
      });
    }
  }

  // ---- 模板引导提交 ----
  function initTemplateSubmit() {
    var tmplForm = document.getElementById('template-form');
    if (!tmplForm) return;
    tmplForm.addEventListener('submit', function(e) {
      e.preventDefault();
      var data = {};
      $$('input, textarea, select', this).forEach(function(el) {
        if (el.name) data[el.name] = el.value;
      });
      var templateType = document.getElementById('template-select').value;
      var btn = this.querySelector('button[type="submit"]');
      btn.disabled = true;
      btn.textContent = '儲存中...';
      api.post('/skill/create', { template_type: templateType, answers: data }).then(function(res) {
        btn.disabled = false;
        btn.textContent = '💾 建立 Skill';
        if (res.success) {
          showToast('✅ Skill 已建立！');
          setTimeout(function() { window.location.href = '/skill/' + res.skill_id; }, 800);
        } else {
          showToast('儲存失敗：' + (res.error || '未知錯誤'));
        }
      }).catch(function() {
        btn.disabled = false;
        btn.textContent = '💾 建立 Skill';
        showToast('網絡錯誤');
      });
    });
  }

  // ---- 拍照诊断 ----
  function initPhotoDiagnose() {
    var input = document.getElementById('photo-input');
    var preview = document.getElementById('photo-preview');
    var resultEl = document.getElementById('diagnosis-result');
    if (!input) return;

    input.addEventListener('change', function() {
      var file = this.files[0];
      if (!file) return;
      // 预览
      var reader = new FileReader();
      reader.onload = function(e) {
        if (preview) {
          preview.src = e.target.result;
          preview.style.display = 'block';
        }
      };
      reader.readAsDataURL(file);

      // 调用诊断 API
      if (resultEl) {
        resultEl.innerHTML = '<div class="spinner"></div> 診斷中...';
      }
      api.post('/api/diagnose', {}).then(function(res) {
        if (res.success && resultEl) {
          var d = res.diagnosis;
          var gradeColor = d.quality_grade === 'A' ? 'var(--success)' : d.quality_grade === 'B' ? 'var(--warning)' : 'var(--danger)';
          resultEl.innerHTML = '<div style="margin-top:12px;padding:12px;background:var(--bg-secondary);border-radius:var(--radius-sm)">' +
            '<div style="font-size:1.2rem;font-weight:700;color:' + gradeColor + '">等級：' + d.quality_grade + '</div>' +
            '<div style="margin:4px 0;font-size:0.9rem">' + escHtml(d.verdict) + '</div>' +
            (d.suggestions && d.suggestions.length ? '<div style="margin-top:8px;font-size:0.8rem;color:var(--text-light)">💡 建議：<br>' + d.suggestions.map(function(s) { return '· ' + escHtml(s); }).join('<br>') + '</div>' : '') +
            '</div>';
        }
      }).catch(function() {
        if (resultEl) resultEl.innerHTML = '<div style="color:var(--danger)">診斷失敗，請重試</div>';
      });
    });
  }

  // ---- 通知轮询 ----
  function initNotificationPoll() {
    var badge = document.getElementById('notification-badge');
    if (!badge) return;
    var userId = getUserId();
    if (!userId) return;

    function poll() {
      api.get('/api/notifications?unread_only=true').then(function(res) {
        if (res.success && res.notifications) {
          var unread = res.notifications.length;
          if (unread > 0) {
            badge.textContent = unread > 9 ? '9+' : unread;
            badge.style.display = 'flex';
          } else {
            badge.style.display = 'none';
          }
        }
      });
    }
    poll();
    setInterval(poll, 30000);
  }

  // ---- 图表渲染 ----
  function initChart() {
    var canvas = document.getElementById('trend-chart');
    if (!canvas || typeof Chart === 'undefined') return;

    var labels = JSON.parse(canvas.dataset.labels || '[]');
    var data = JSON.parse(canvas.dataset.values || '[]');

    new Chart(canvas, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: '技能總數',
          data: data,
          borderColor: '#D4943A',
          backgroundColor: 'rgba(212, 148, 58, 0.1)',
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#D4943A',
          pointRadius: 4,
          borderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1, font: { size: 11 } },
            grid: { color: 'rgba(0,0,0,0.05)' },
          },
          x: {
            ticks: { font: { size: 11 } },
            grid: { display: false },
          },
        },
      },
    });
  }

  // ---- 技能进度更新 ----
  function initProgressUpdate() {
    $$('.progress-update-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var skillId = this.dataset.skillId;
        var status = this.dataset.status;
        api.post('/api/skill/' + skillId + '/progress', { status: status }).then(function(res) {
          if (res.success) {
            showToast('進度已更新 ✅');
            setTimeout(function() { location.reload(); }, 500);
          }
        });
      });
    });
  }

  // ---- HTML 转义 ----
  function escHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ---- 初始化（DOM Ready） ----
  document.addEventListener('DOMContentLoaded', function() {
    initSkillSearch();
    initCategoryFilter();
    initLikeButtons();
    initCollectButtons();
    initCommentForm();
    initSkillCreate();
    initTemplateSubmit();
    initPhotoDiagnose();
    initNotificationPoll();
    initChart();
    initProgressUpdate();
  });

})();
