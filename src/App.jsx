import React, { useState, useEffect, useRef, useCallback } from 'react';

/* ==============================
   CONSTANTS
   ============================== */
const BOOKING_URL = 'mailto:zengury@gmail.com';

const NAV_ITEMS = [
  { label: '产品', href: '#product' },
  { label: '方案', href: '#solutions' },
  { label: '定价', href: '#pricing' },
  { label: 'FAQ', href: '#faq' },
];

const PRODUCT_CARDS = [
  {
    label: 'CLIENT SURFACE',
    title: '客户门户与管家',
    icon: 'room_service',
    description: '品牌化客户门户，包含登录、入驻引导、服务时间线、进度更新、文件共享和专属管家体验。',
  },
  {
    label: 'PUBLIC SURFACE',
    title: '落地页与客服',
    icon: 'language',
    description: '定制落地页，包含服务介绍、线索捕获、预约流程和新客户支持路径。',
  },
  {
    label: 'INTERNAL TOOL',
    title: '客户管理与助手',
    icon: 'dashboard_customize',
    description: '内部 CRM 式管理后台：客户管道、档案、语音笔记、任务、文档、会议和跟进。',
  },
  {
    label: 'AI LAYER',
    title: '智能与 AI 代理',
    icon: 'psychology',
    description: '贯穿全平台的 AI 层。基础版配备内部 AI 助手，进阶版增加客服 AI，高级版为每位客户配置专属管家 AI。',
    accent: true,
  },
];

const SOLUTIONS = [
  {
    id: 'healthcare',
    title: '医疗健康',
    icon: 'medical_services',
    summary: '为患者接待、护理更新、预约排期、文档管理和会员支持定制的客户管家系统。',
    cta: '了解方案 →',
  },
  {
    id: 'real-estate',
    title: '房产经纪',
    icon: 'real_estate_agent',
    summary: '从线索捕获、带看协调、交易更新到长期关系维护的全流程工作系统。',
    cta: '了解方案 →',
  },
  {
    id: 'agencies',
    title: '代理机构',
    icon: 'groups',
    summary: '覆盖客户入驻、项目进度、审批、交付物、会议和账户管理的完整服务体系。',
    cta: '了解方案 →',
  },
];

const TIMELINE_STEPS = [
  {
    title: '梳理业务关系',
    description: '深入了解您的客户画像、服务流程、跟进规则、入驻步骤，以及您希望每位客户感受到的体验。',
  },
  {
    title: '搭建管家系统',
    description: '围绕您的业务配置落地页、专属客户管家、内部管理管道、知识库和 AI 行为规则。',
  },
  {
    title: '上线并持续优化',
    description: '系统上线后，根据真实互动、已确认回复、人工校正和新的业务上下文不断迭代改进。',
  },
];

const COMPARISON = [
  {
    label: '传统方式',
    title: '传统定制软件开发',
    tone: 'problem',
    icon: '×',
    points: [
      { value: '¥35万 – 180万+', text: '前期开发预算' },
      { value: '3 – 6+ 个月', text: '才能上线' },
      { value: '需要技术团队', text: '组建和维护成本高' },
    ],
  },
  {
    label: 'SNAKES',
    title: '定制化管家系统',
    tone: 'solution',
    icon: '✓',
    points: [
      { value: '¥15,000 起', text: '一站式搭建' },
      { value: '2 – 3 周', text: '即可上线首个版本' },
      { value: '无需技术团队', text: '我们负责搭建、托管和迭代' },
    ],
  },
];

const PLANS = [
  {
    name: '基础版',
    subtitle: '核心管家系统',
    price: '¥2,999',
    period: '/mo',
    setup: '搭建费 ¥14,999',
    summary: '覆盖专属客户管家体验、线索捕获和内部客户管理的核心功能。',
    featured: false,
    info: '覆盖客户门户、落地页、内部管理后台和内部 AI 助手的核心功能。',
  },
  {
    name: '进阶版',
    subtitle: '扩展管家系统',
    price: '¥4,999',
    period: '/mo',
    setup: '搭建费 ¥21,999',
    summary: '更多的自动化能力、更丰富的客户服务功能和更强的工作流支持。',
    featured: true,
    info: '在基础版之上增加落地页客服 AI，处理咨询、接待、路由和线索跟进。',
  },
  {
    name: '高级版',
    subtitle: '完整管家系统',
    price: '¥6,999',
    period: '/mo',
    setup: '搭建费 ¥35,999',
    summary: '全面覆盖客户体验、线索管理、内部运营和专属 AI 管家关系维护。',
    featured: false,
    info: '为每位客户配置专属管家 AI，提供私密的、个性化的客户服务。',
  },
];

const FEATURE_CATEGORIES = [
  {
    category: '客户门户与管家',
    usage: ['客户体验', '专属管家', 'AI 代理'],
    rows: [
      { name: '专属客户管家', info: '为每一位客户提供品牌化的专属体验和定制化服务层', tiers: [true, true, true] },
      { name: '会员登录与账户', info: '客户可登录管理个人资料，访问专属空间', tiers: [true, true, true] },
      { name: '服务时间线与更新', info: '客户可查看服务里程碑、项目时间线和下一步计划', tiers: [true, true, true] },
      { name: '引导式客户入驻', info: '引导新客户完成信息填写、表单提交等入驻步骤', tiers: [true, true, true] },
      { name: '安全文件共享', info: '与客户共享文档、图片、表格等专属资源', tiers: [true, true, true] },
      { name: '内置预约排期', info: '客户可通过专属界面预约通话、会议和检查节点', tiers: [false, true, true] },
      { name: '自定义域名', info: '在您自己的域名上托管客户体验', tiers: [false, true, true] },
      { name: '自定义数据集成', info: '将管家数据与您的 CRM、表单、排期、文档等业务系统对接', tiers: [false, false, true] },
      { name: '会员管家 AI 代理', info: '每位会员拥有专属 AI 管家，了解其账户、服务历史和当前需求', tiers: [false, false, true] },
      { name: '个性化客户体验', info: '管家记住客户偏好、历史请求、上传文件和未闭环事项', tiers: [false, false, true] },
    ],
  },
  {
    category: '落地页与客服支持',
    usage: ['线索捕获', 'AI 客服', '高级客服'],
    rows: [
      { name: '品牌落地页', info: '围绕您的服务和客户转化路径定制品牌落地页', tiers: [true, true, true] },
      { name: '服务介绍板块', info: '清晰展示服务内容、流程、案例、FAQ 和行动号召', tiers: [true, true, true] },
      { name: '线索捕获表单', info: '收集客户咨询、联系方式、服务需求和下一步请求', tiers: [true, true, true] },
      { name: '预约会议流程', info: '潜在客户可直接从网站预约通话和咨询', tiers: [true, true, true] },
      { name: '智能线索筛选', info: 'AI 过滤低匹配度请求，识别客户意图，标记优质商机', tiers: [false, true, true] },
      { name: '智能线索跟进', info: 'AI 自动跟进新线索、未回复和待处理咨询', tiers: [false, true, true] },
      { name: '客服 AI 代理', info: 'AI 回答服务问题，处理常规客服请求，复杂问题升级至人工', tiers: [false, true, true] },
      { name: '自动管家邀请', info: '在合适的节点自动邀请合格线索或新客户进入专属管家', tiers: [false, false, true] },
    ],
  },
  {
    category: '客户管理与助手',
    usage: ['200 位客户', '500 位客户', '无限制'],
    rows: [
      { name: '自定义客户管道', info: '按您的阶段、标签和流程定制客户管理管道', tiers: [true, true, true] },
      { name: '语音与互动记录', info: '记录语音笔记、通话、会议、备忘录和客户接触点', tiers: [true, true, true] },
      { name: '任务与截止日期', info: '管理待办事项、截止日期、项目里程碑和客户承诺', tiers: [true, true, true] },
      { name: '自动客户跟进', info: '自动标记需要关注的客户，持续推动客户跟进', tiers: [true, true, true] },
      { name: '客户活动报告', info: '定期生成客户活动摘要、优先事项和逾期项目', tiers: [true, true, true] },
      { name: '日历与会议助手', info: '安排会议，准备上下文，将客户跟进与日历打通', tiers: [true, true, true] },
      { name: '文档与资产管理', info: '自动整理合同、收据、文件、图片和客户资产', tiers: [true, true, true] },
      { name: '客户报告与分析', info: '生成周报、月报、客户分析和业绩快照', tiers: [false, true, true] },
      { name: '高级客户洞察', info: 'AI 分析模式，建议最佳跟进时机、客户风险和商机', tiers: [false, false, true] },
    ],
  },
  {
    category: '智能与 AI 代理',
    rows: [
      { name: '语音消息理解', info: 'AI 可转录和理解团队或客户的语音笔记', tiers: [true, true, true] },
      { name: '品牌知识库', info: 'AI 使用您的服务、FAQ、话术、政策和偏好语言准确回答', tiers: [true, true, true] },
      { name: '文件与图片理解', info: 'AI 可读取上传的文档、图片、表格和客户资产获取上下文', tiers: [true, true, true] },
      { name: '业务上下文感知', info: 'AI 理解您的工作流、服务规则、客户阶段和升级边界', tiers: [true, true, true] },
      { name: '多语言支持', info: 'AI 可用多种语言与客户和团队成员沟通', tiers: [false, true, true] },
      { name: '自主学习与改进', info: 'AI 从已确认回复、人工校正和验证答案中持续学习改进', tiers: [false, true, true] },
      { name: '高级安全控制', info: '为敏感工作流增加更严格的内容、语调和升级管控', tiers: [false, false, true] },
    ],
  },
  {
    category: '服务支持',
    rows: [
      { name: '基础支持', info: '通过邮件联系我们的团队', tiers: [true, true, true] },
      { name: '指导型入驻', info: '手把手设置并与您的工具集成', tiers: [true, true, true] },
      { name: '优先支持', info: '需要帮助时快速响应', tiers: [false, false, true] },
    ],
  },
];

const FAQ_ITEMS = [
  {
    question: '这是一个门户、CRM 还是 AI 代理？',
    answer: '这是一个定制化的管家系统，可以同时包含以上三者：面向客户的体验层、内部客户管理层，以及协助运营两端的 AI 代理。',
  },
  {
    question: '每个套餐都包含客户管家吗？',
    answer: '是的。基础版、进阶版和高级版均包含专属客户管家基础、线索捕获和内部客户管理。更高套餐解锁更深度的自动化和更专属的 AI 管家行为。',
  },
  {
    question: '入驻上线需要多长时间？',
    answer: '大多数首个版本可在 14 到 21 个工作日内上线，具体取决于涉及的工作流、数据源和客户界面的数量。',
  },
  {
    question: '可以和我现有的工具对接吗？',
    answer: '可以。我们可根据套餐和集成深度，对接表单、排期、文档、CRM 数据、客户记录和其他业务系统。',
  },
  {
    question: 'AI 不确定时怎么办？',
    answer: '每个工作流都可配置升级规则、审批边界和安全控制，确保不确定或敏感的情况路由至您的团队。',
  },
  {
    question: '需要技术人员来管理吗？',
    answer: '不需要。Snakes 专为没有内部工程团队的服务型企业打造。我们负责搭建、上线和持续优化。',
  },
];

/* ==============================
   HERO DOT GRID (Geek Edition)
   ============================== */

// Glyph patterns for pixel-style number rendering
const GLYPHS = [
  [[0,1],[0,2],[0,3],[1,1],[1,3],[2,1],[2,3],[3,1],[3,3],[4,1],[4,3],[5,1],[5,3],[6,1],[6,2],[6,3],[7,2]], // 0
  [[0,0],[0,1],[0,2],[0,3],[0,4],[0,5],[1,0],[1,1],[1,4],[1,5],[2,0],[2,2],[2,3],[2,5],[3,0],[3,5],[4,0],[4,1],[4,2],[4,3],[4,4],[4,5]], // 1
  [[0,1],[0,2],[0,3],[1,0],[1,4],[2,0],[2,2],[2,4],[3,0],[3,2],[3,4],[4,0],[4,2],[4,3],[4,4],[5,0],[5,4],[6,1],[6,2],[6,3]], // 2
  [[0,2],[0,3],[1,1],[1,4],[2,1],[2,4],[3,2],[3,3],[4,1],[4,2],[4,3],[4,4],[5,0],[5,5],[6,0],[6,5],[7,0],[7,5]], // 3
];

function HeroDotGrid() {
  const [cols, setCols] = useState(40);
  const [anim, setAnim] = useState({ idx: 1, fade: 0, posR: 2, posC: 15 });
  const ref = useRef(null);
  const idxRef = useRef(1);

  useEffect(() => {
    const h = () => { if (ref.current) setCols(Math.floor(ref.current.offsetWidth / 16)); };
    h();
    window.addEventListener('resize', h);
    return () => window.removeEventListener('resize', h);
  }, []);

  useEffect(() => {
    let live = true;
    const run = async () => {
      while (live) {
        const i = idxRef.current % GLYPHS.length;
        const rOff = 2;
        const cOff = 4 + Math.floor(Math.random() * Math.max(1, cols - 12));
        setAnim({ idx: i, fade: 1, posR: rOff, posC: cOff });
        await new Promise(r => setTimeout(r, 3500));
        if (!live) return;
        setAnim({ idx: i, fade: 0, posR: rOff, posC: cOff });
        await new Promise(r => setTimeout(r, 1000));
        if (!live) return;
        idxRef.current = (idxRef.current + 1) % GLYPHS.length;
      }
    };
    const t = setTimeout(() => { if (live) run(); }, 600);
    return () => { live = false; clearTimeout(t); };
  }, [cols]);

  const dots = GLYPHS[anim.idx];
  const activeMap = {};
  const glowMap = {};

  dots.forEach(([r, c]) => {
    activeMap[`${r + anim.posR},${c + anim.posC}`] = true;
    for (let dr = -1; dr <= 1; dr++)
      for (let dc = -1; dc <= 1; dc++) {
        const k = `${r + anim.posR + dr},${c + anim.posC + dc}`;
        if (!activeMap[k]) glowMap[k] = true;
      }
  });

  const W = cols * 16, H = 18 * 16;
  const R_ACTIVE = 5.5, R_GLOW = 3.2, R_IDLE = 1.6;

  return (
    <div className="hero-grid-canvas" ref={ref} aria-hidden="true">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="xMidYMid meet">
        {/* Grid lines */}
        {Array.from({ length: Math.floor(H / 16) + 1 }, (_, r) => (
          <line key={`h${r}`} x1={0} y1={r * 16} x2={W} y2={r * 16} stroke="#232328" strokeWidth="0.5" opacity="0.35" />
        ))}
        {Array.from({ length: cols + 1 }, (_, c) => (
          <line key={`v${c}`} x1={c * 16} y1={0} x2={c * 16} y2={H} stroke="#232328" strokeWidth="0.5" opacity="0.35" />
        ))}
        {/* Dots */}
        {Array.from({ length: 18 }, (_, r) =>
          Array.from({ length: cols }, (_, c) => {
            const key = `${r},${c}`;
            const active = activeMap[key];
            const glow = glowMap[key];
            const size = active ? R_ACTIVE : glow ? R_GLOW : R_IDLE;
            const opacity = active ? 1 : glow ? 0.55 : 0.18;
            const fill = active ? '#00e599' : glow ? '#00e599' : '#3a3a44';
            const cx = c * 16 + 8, cy = r * 16 + 8;
            return (
              <g key={key}>
                <circle cx={cx} cy={cy} r={size} fill={fill} opacity={opacity} className="hero-dot" />
                {active && (
                  <circle cx={cx} cy={cy} r={size * 2} fill="none" stroke="#00e599" strokeWidth="0.6" opacity="0.25">
                    <animate attributeName="r" values={`${size * 1.5};${size * 3};${size * 1.5}`} dur="2.5s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.3;0.05;0.3" dur="2.5s" repeatCount="indefinite" />
                  </circle>
                )}
              </g>
            );
          })
        )}
      </svg>
    </div>
  );
}

/* ==============================
   INFO TOOLTIP
   ============================== */
function InfoTip({ text }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const [pos, setPos] = useState({ top: 0, left: 0 });
  const show = useCallback(() => {
    if (ref.current) {
      const r = ref.current.getBoundingClientRect();
      setPos({ top: r.top - 8, left: r.left + r.width / 2 });
    }
    setOpen(true);
  }, []);
  return (
    <span className="info-tip" ref={ref} onMouseEnter={show} onMouseLeave={() => setOpen(false)} onClick={() => { show(); setOpen(o => !o); }}>
      <span className="info-icon" aria-hidden="true">?</span>
      {open && <span className="info-tooltip" style={{ top: pos.top, left: pos.left }}>{text}</span>}
    </span>
  );
}

/* ==============================
   NAV
   ============================== */
function Nav() {
  return (
    <header className="site-nav">
      <nav className="container nav-inner">
        <a className="brand" href="/">
          <img src="/logo.svg" alt="Snakes" className="brand-logo" />
          snakes
        </a>
        <div className="nav-links">
          {NAV_ITEMS.map(item => (
            <a key={item.href} href={item.href}>{item.label}</a>
          ))}
        </div>
        <a className="btn btn-primary btn-nav" href={BOOKING_URL}>预约演示</a>
      </nav>
    </header>
  );
}

/* ==============================
   FOOTER
   ============================== */
function Footer() {
  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        <div>
          <a className="footer-brand" href="/">
            <img src="/logo.svg" alt="Snakes" className="brand-logo" />
            snakes
          </a>
          <p className="footer-copy">定制化 AI 客户管家系统 —— 让每一段客户关系都被记住、被回应、被推进。</p>
          <p className="footer-legal">© {new Date().getFullYear()} Snakes</p>
        </div>
        <div>
          <p className="footer-title">导航</p>
          <a href="#product">产品</a>
          <a href="#solutions">方案</a>
          <a href="#pricing">定价</a>
          <a href="#faq">FAQ</a>
        </div>
        <div>
          <p className="footer-title">行业</p>
          <a href="#healthcare">医疗健康</a>
          <a href="#real-estate">房产经纪</a>
          <a href="#agencies">代理机构</a>
        </div>
        <div>
          <p className="footer-title">联系</p>
          <a href={BOOKING_URL}>预约演示</a>
          <a href="mailto:zengury@gmail.com">zengury@gmail.com</a>
        </div>
      </div>
    </footer>
  );
}

/* ==============================
   FAQ ITEM
   ============================== */
function FaqItem({ item }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`faq-item ${open ? 'faq-item-open' : ''}`}>
      <button className="faq-question" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span>{item.question}</span>
        <span className="faq-toggle">{open ? '[-]' : '[+]'}</span>
      </button>
      <div className="faq-answer-wrap" style={{ maxHeight: open ? '300px' : '0' }}>
        <p className="faq-answer">{item.answer}</p>
      </div>
    </div>
  );
}

/* ==============================
   FEATURE TABLE
   ============================== */
function FeatureTable() {
  return (
    <div className="feature-table-wrap">
      <table className="feature-table">
        <thead>
          <tr>
            <th className="feature-table-label"></th>
            {PLANS.map(plan => (
              <th key={plan.name} className={plan.featured ? 'feature-table-featured' : ''}>
                {plan.name}
                <InfoTip text={plan.info} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {FEATURE_CATEGORIES.map(cat => (
            <React.Fragment key={cat.category}>
              <tr className="feature-table-category">
                <td colSpan={4}>{cat.category}</td>
              </tr>
              {cat.rows.map(row => (
                <tr key={row.name}>
                  <td className="feature-table-label">
                    {row.name}
                    {row.info && <InfoTip text={row.info} />}
                  </td>
                  {row.tiers.map((tier, i) => (
                    <td key={i} className={PLANS[i]?.featured ? 'feature-table-featured' : ''}>
                      {typeof tier === 'string'
                        ? <span className="table-value">{tier}</span>
                        : tier
                          ? <span className="table-check" aria-label="包含"></span>
                          : <span className="table-dash" aria-label="不包含">—</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ==============================
   MAIN APP
   ============================== */
export default function App() {
  return (
    <div className="page-shell">
      {/* Ambient glow */}
      <div className="glow-orb glow-orb-1" aria-hidden="true" />
      <div className="glow-orb glow-orb-2" aria-hidden="true" />
      <div className="global-grid" aria-hidden="true" />

      <Nav />

      <main>
        {/* ── HERO ── */}
        <section className="section hero-section">
          <div className="container hero-center">
            <h1>
              AI 客户管家<span className="text-accent">.</span>
              <br />
              为您的企业量身打造<span className="text-accent">_</span>
            </h1>
            <p className="hero-text">
              定制化落地页、客户门户、内部管理后台与 AI 代理，打造卓越的客户关系体验。
            </p>
            <p className="hero-sub">// autonomous client concierge infrastructure</p>
            <HeroDotGrid />
            <div className="hero-actions">
              <a className="btn btn-gradient btn-lg" href={BOOKING_URL}>预约演示</a>
              <a className="btn btn-outline btn-lg" href="#product">了解详情</a>
            </div>
          </div>
        </section>

        {/* ── PRODUCT ── */}
        <section className="section section-alt" id="product">
          <div className="container">
            <div className="section-heading">
              <span className="eyebrow">PRODUCT</span>
              <h2>三大定制界面 + 一个 AI 核心层</h2>
              <p>每个项目从品牌落地页、专属客户管家和内部管理后台起步。AI 根据套餐层级在合适的界面发挥智能价值。</p>
            </div>
            <div className="bento-grid">
              {PRODUCT_CARDS.map(card => (
                <article key={card.title} className={`bento-card ${card.accent ? 'bento-accent' : ''}`}>
                  <div className="bento-icon-wrap">
                    <span className="material-symbols-rounded bento-icon" aria-hidden="true">{card.icon}</span>
                  </div>
                  <p className="bento-label">{card.label}</p>
                  <h3>{card.title}</h3>
                  <p>{card.description}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ── SOLUTIONS ── */}
        <section className="section" id="solutions">
          <div className="container">
            <div className="section-heading">
              <span className="eyebrow">SOLUTIONS</span>
              <h2>按行业定制的解决方案</h2>
              <p>每个行业都有专属的演示配置，覆盖客户旅程、内部工作流和 AI 管家行为。</p>
            </div>
            <div className="solution-grid">
              {SOLUTIONS.map(sol => (
                <article key={sol.id} className="solution-card" id={sol.id}>
                  <div className="solution-icon" aria-hidden="true">
                    <span className="material-symbols-rounded">{sol.icon}</span>
                  </div>
                  <p className="solution-demo-label">行业方案</p>
                  <h3>{sol.title}</h3>
                  <p className="solution-summary">{sol.summary}</p>
                  <a className="solution-link" href={BOOKING_URL}>{sol.cta}</a>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ── HOW IT WORKS ── */}
        <section className="section section-alt" id="how-it-works">
          <div className="container timeline-container">
            <div className="section-heading section-heading-center">
              <span className="eyebrow">WORKFLOW</span>
              <h2>从想法到管家系统</h2>
              <p>无需工程师。我们梳理工作流、搭建系统，并在上线后持续迭代优化。</p>
            </div>
            <div className="timeline">
              <div className="timeline-line" aria-hidden="true" />
              {TIMELINE_STEPS.map((step, i) => (
                <div key={step.title} className="timeline-step">
                  <div className={`timeline-marker ${i === 0 ? 'timeline-marker-filled' : ''}`}>
                    {String(i + 1).padStart(2, '0')}
                  </div>
                  <div className="timeline-content">
                    <h3>{step.title}</h3>
                    <p>{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── WHY SNAKES ── */}
        <section className="section" id="why-snakes">
          <div className="container">
            <div className="section-heading section-heading-center">
              <span className="eyebrow">WHY SNAKES</span>
              <h2>定制软件，无需高昂成本和漫长等待</h2>
            </div>
            <div className="comparison-grid">
              {COMPARISON.map(item => (
                <article key={item.title} className={`comparison-card comparison-${item.tone}`}>
                  <div className="comparison-header">
                    <span className={`comparison-icon comparison-icon-${item.tone}`} aria-hidden="true">{item.icon}</span>
                    <div>
                      <p className="comparison-kicker">{item.label}</p>
                      <h3>{item.title}</h3>
                    </div>
                  </div>
                  <ul className="comparison-list">
                    {item.points.map(p => (
                      <li key={p.value}>
                        <span className="comparison-metric">{p.value}</span>
                        <span>{p.text}</span>
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* ── PRICING ── */}
        <section className="section" id="pricing">
          <div className="container">
            <div className="section-heading section-heading-center">
              <span className="eyebrow">PRICING</span>
              <h2>三个套餐，一个专属客户管家</h2>
              <p>每个套餐均包含专属客户体验、线索捕获和内部客户管理。更高层级解锁更深度的自动化和更专属的 AI 管家。</p>
            </div>
            <div className="pricing-grid">
              {PLANS.map(plan => (
                <article key={plan.name} className={`pricing-card ${plan.featured ? 'pricing-card-featured' : ''}`}>
                  {plan.featured && <span className="pricing-badge">MOST POPULAR</span>}
                  <p className="pricing-name">{plan.name}</p>
                  <p className="pricing-subtitle">{plan.subtitle}</p>
                  <div className="pricing-price">
                    <span className="pricing-amount">{plan.price}</span>
                    <span className="pricing-period">{plan.period}</span>
                  </div>
                  <p className="pricing-setup">{plan.setup}</p>
                  <p className="pricing-summary">{plan.summary}</p>
                  <a className={`btn ${plan.featured ? 'btn-gradient' : 'btn-outline'} btn-full`} href={BOOKING_URL}>
                    预约演示
                  </a>
                </article>
              ))}
            </div>
            <FeatureTable />
          </div>
        </section>

        {/* ── FAQ ── */}
        <section className="section section-alt" id="faq">
          <div className="container faq-container">
            <div className="section-heading section-heading-center">
              <span className="eyebrow">FAQ</span>
              <h2>常见问题</h2>
              <p>在为您设计首个管家系统之前，回答几个常见问题。</p>
            </div>
            <div className="faq-list">
              {FAQ_ITEMS.map(item => (
                <FaqItem key={item.question} item={item} />
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA ── */}
        <section className="section section-final-cta" id="cta">
          <div className="cta-grid-bg" aria-hidden="true" />
          <div className="container final-cta-content">
            <h2>
              准备好搭建您的 AI 管家<span className="text-accent">?</span>
            </h2>
            <p>相比传统定制软件节省 90% 成本。无需工程师，无需管理开销 —— 只属于您自己的 AI 系统。</p>
            <div className="cta-actions">
              <a className="btn btn-cta btn-lg" href={BOOKING_URL}>预约演示</a>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
