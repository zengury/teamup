import { createBakeryDemoRuntime } from "./dist/runtime/browserRuntime.js";

const state = {
  projects: [
    {
      id: "B07",
      name: "陈先生面包店订单自动化",
      client: "Mr. Chen Bakery",
      summary: "多渠道订单自动入台，降低漏单和定制蛋糕确认错误。",
      status: "active"
    },
    {
      id: "B08",
      name: "厨房批次看板升级",
      client: "Mr. Chen Bakery",
      summary: "把中央厨房制作清单从 Excel 传递改成可视看板。",
      status: "queued"
    },
    {
      id: "C03",
      name: "门店投诉归因助手",
      client: "Retail Pilot",
      summary: "把客户投诉按渠道、门店和原因聚类，给店长复盘。",
      status: "queued"
    }
  ],
  projectQuery: "",
  nav: [
    { label: "作业面", desc: "你与唐僧对话、补充需求、裁决关键事项", tag: "核心", icon: "◉", active: true },
    { label: "生产面", desc: "看当前阶段、流水线、谁在做谁在等", tag: "主屏", icon: "⟠" },
    { label: "反馈面", desc: "客户反馈、追问材料、下一步建议", tag: "重点", icon: "✦" },
    { label: "交付面", desc: "客户最终会拿到什么、现在做到了哪", tag: "结果", icon: "⬢" },
    { label: "分析面", desc: "瓶颈、品质、库存、市场回流", tag: "辅助", icon: "◌" }
  ],
  tick: 0,
  thread: [
    {
      who: "你",
      role: "如来佛祖",
      tone: "founder",
      text: "这单目标很明确：减少漏单、错单和客户投诉，但一定要简单，员工不能被复杂系统拖住。"
    },
    {
      who: "唐僧",
      role: "leader",
      tone: "agent",
      text: "收到。我建议先做统一订单收件台和定制蛋糕自动确认，不在首单里碰 POS。当前最卡的是样本 Excel 和 LINE OA 权限。"
    }
  ],
  decisions: [
    {
      id: "d1",
      from: "唐僧",
      title: "是否接受首单不接 POS",
      detail: "这样可以把交付周期控制在 5.8 天内，否则范围会立刻膨胀。",
      impact: "会直接决定猴哥是否现在就能开工。",
      status: "pending"
    },
    {
      id: "d2",
      from: "白龙马",
      title: "是否允许我直接向客户要样本与账号权限",
      detail: "如果允许，白龙马可以直接追 LINE OA 权限、样本 Excel 和 3 条真实对话。",
      impact: "会显著减少猴哥空等的时间。",
      status: "pending"
    }
  ],
  agents: [
    {
      id: "tangseng",
      name: "唐僧",
      role: "Leader / Coordinator",
      model: "4.5",
      temperament: "温和坚定，念念不忘目标",
      status: "orchestrating",
      progress: 46,
      load: 74,
      current: "把陈先生的访谈压成可交付 MVP：先接 LINE / WhatsApp / 电话订单，不碰 POS。",
      blocker: "等待你确认：是否接受先不接 POS、先做人机协作版而非全自动版。",
      output: "Bakery Automation Brief v1",
      color: "green"
    },
    {
      id: "bajie",
      name: "八戒",
      role: "Product / Ideas / Comms",
      model: "Claude Sonnet",
      temperament: "会来事，有品位，点子多",
      status: "thinking",
      progress: 34,
      load: 66,
      current: "设计统一订单收件台和定制蛋糕自动确认体验，重点是“简单到非技术员工也能用”。",
      blocker: "需要唐僧冻结 MVP 边界，避免同时做接单台、厨房屏和定价引擎。",
      output: "Unified Order Desk Proposal",
      color: "gold"
    },
    {
      id: "houge",
      name: "猴哥",
      role: "Core Builder",
      model: "4.7",
      temperament: "直来直去，能打硬仗",
      status: "waiting",
      progress: 12,
      load: 41,
      current: "等待 LINE Official Account 权限、样本 Excel 和各渠道消息样本，再确定 ingestion 方案。",
      blocker: "当前等待原因：没有真实消息样本和账号权限，先写接入层会很容易返工。",
      output: "Technical Intake Plan",
      color: "red"
    },
    {
      id: "shaseng",
      name: "沙僧",
      role: "QA & Eval",
      model: "Codex",
      temperament: "少说多做，稳稳复核",
      status: "queued",
      progress: 18,
      load: 44,
      current: "先准备错单、漏单、定制蛋糕图片和特殊说明的评测样本。",
      blocker: "正式评测要等猴哥出第一版 intake pipeline。",
      output: "Order Accuracy Eval Plan",
      color: "blue"
    },
    {
      id: "bailongma",
      name: "白龙马",
      role: "Customer Value",
      model: "Claude Sonnet",
      temperament: "安静可靠，贴心承载",
      status: "listening",
      progress: 29,
      load: 55,
      current: "整理访谈痛点，准备追问权限、样本表格、定制蛋糕确认规则。",
      blocker: "是否自动 follow-up 取决于你是否允许白龙马直接向客户要样本和账号信息。",
      output: "Client Discovery Brief",
      color: "silver"
    }
  ],
  flows: [
    {
      id: "f1",
      from: "客户访谈",
      to: "唐僧",
      label: "转写稿 + 痛点 + 3 个月目标",
      status: "done",
      artifact: "Bakery Discovery Transcript"
    },
    {
      id: "f2",
      from: "唐僧",
      to: "如来佛祖",
      label: "MVP 边界与报价逻辑",
      status: "waiting",
      artifact: "Solution Framing Brief"
    },
    {
      id: "f3",
      from: "唐僧",
      to: "八戒",
      label: "统一订单台与确认体验",
      status: "active",
      artifact: "Product Proposal"
    },
    {
      id: "f4",
      from: "八戒",
      to: "猴哥",
      label: "可执行字段、渠道和确认规则",
      status: "waiting",
      artifact: "Implementation Input Pending"
    },
    {
      id: "f5",
      from: "猴哥",
      to: "沙僧",
      label: "接单引擎与订单同步测试",
      status: "queued",
      artifact: "Intake Pipeline"
    },
    {
      id: "f6",
      from: "白龙马",
      to: "唐僧",
      label: "权限、样本、非技术员工可用性反馈",
      status: "active",
      artifact: "Client Discovery Brief"
    },
    {
      id: "f7",
      from: "沙僧",
      to: "唐僧",
      label: "错单率与漏单风险门禁",
      status: "queued",
      artifact: "QA Gate Report"
    },
    {
      from: "唐僧",
      to: "客户",
      label: "MVP 方案与所需配合事项",
      status: "queued",
      artifact: "Proposal Deck + Checklist"
    }
  ],
  lanes: [
    {
      title: "需求线",
      owner: "唐僧",
      status: "done",
      items: ["确认数据入口", "冻结 MVP 非目标", "形成 12 天里程碑"]
    },
    {
      title: "产品线",
      owner: "八戒",
      status: "active",
      items: ["三个方案取舍", "客户确认脚本", "原型改版建议"]
    },
    {
      title: "工程线",
      owner: "猴哥",
      status: "waiting",
      items: ["ingestion pipeline", "任务生成 API", "pilot workspace"]
    },
    {
      title: "评测线",
      owner: "沙僧",
      status: "active",
      items: ["40 条样本集", "误判降级", "隐私检查"]
    },
    {
      title: "客户线",
      owner: "白龙马",
      status: "active",
      items: ["追问原型反馈", "识别采用风险", "整理客户价值"]
    }
  ],
  artifacts: [
    {
      title: "Bakery Automation Brief v1",
      owner: "唐僧",
      type: "Decision",
      status: "draft",
      summary: "先解决多渠道订单手工录入与漏单，不接 POS，不做全店 ERP。"
    },
    {
      title: "统一订单台 Proposal",
      owner: "八戒",
      type: "Product",
      status: "draft",
      summary: "让店员只看一个收件台，把 LINE / WhatsApp / 电话订单汇到一个地方。"
    },
    {
      title: "多渠道 Intake Plan",
      owner: "猴哥",
      type: "Engineering",
      status: "waiting",
      summary: "等 LINE OA 权限、样本 Excel 和消息截图后再锁定接入层。"
    },
    {
      title: "Order Accuracy Eval Plan",
      owner: "沙僧",
      type: "QA",
      status: "draft",
      summary: "覆盖漏单、错单、定制蛋糕特殊说明丢失、自动确认错误报价。"
    },
    {
      title: "客户访谈洞察简报",
      owner: "白龙马",
      type: "CS",
      status: "new",
      summary: "客户核心诉求是去掉手工录入，最怕漏单和定制蛋糕确认出错。"
    }
  ],
  outcome: {
    health: "方案中",
    type: "SME Agent Pilot",
    title: "多渠道订单自动录入 MVP",
    summary: "目标是在 30,000-50,000 NTD / 月预算内，把 LINE、WhatsApp、电话订单自动进统一订单台，并为定制蛋糕自动回确认。",
    points: [
      "客户真实环境：3 家门店、中央厨房、12 名员工、80-120 单 / 天，周末 200 单",
      "当前明确痛点：人工抄单、漏看消息、定制蛋糕图片和特殊说明最容易出错",
      "当前目标：先做统一接单与自动确认，不在第一单里碰 POS 集成"
    ]
  },
  summary: [
    { label: "当前批次", value: "B07", note: "面包店订单自动化首单", icon: "◈", tone: "gold", meter: 28 },
    { label: "当前阶段", value: "方案定界", note: "唐僧正在冻结 MVP 边界", icon: "☉", tone: "green", meter: 46 },
    { label: "任务位置", value: "第 2 / 7 阶段", note: "还没进入真实工程生产", icon: "⇄", tone: "blue", meter: 29 },
    { label: "最关键决策", value: "先不接 POS", note: "否则范围与交付复杂度都会上升", icon: "✦", tone: "red", meter: 72 }
  ],
  deliveryStats: [
    { label: "订单规模", value: "80-120 单/日", note: "周末最高约 200 单" },
    { label: "预算窗口", value: "30k-50k NTD/月", note: "低于再雇 1 人即可接受" },
    { label: "预计交付周期", value: "5.8 天", note: "从方案冻结到首个可用 MVP" },
    { label: "当前最大风险", value: "渠道权限未齐", note: "LINE OA 与样本表格不到位会拖慢交付" }
  ],
  pulse: [
    { label: "正在干活", value: "4 / 5", note: "唐僧、八戒、沙僧、白龙马已接单" },
    { label: "等待中", value: "猴哥", note: "等真实渠道权限和样本" },
    { label: "最新产出", value: "访谈洞察简报", note: "已明确先做订单自动入表与定制蛋糕确认" }
  ],
  deliveries: [
    {
      title: "统一订单收件台",
      status: "draft",
      owner: "猴哥",
      summary: "把 LINE、WhatsApp、电话订单汇到一个统一工作台，而不是继续人工抄 Excel。",
      result: "预期减少漏单与抄单错误，但尚未开始开发"
    },
    {
      title: "定制蛋糕自动确认",
      status: "draft",
      owner: "八戒 / 猴哥",
      summary: "针对图片、特殊说明、价格和取货时间，自动生成确认信息给客户。",
      result: "这是陈先生最重视的高痛点场景"
    },
    {
      title: "厨房批次看板",
      status: "queued",
      owner: "沙僧",
      summary: "把早晚两次 Excel 传递改成厨房可直接看的待制作清单。",
      result: "只有在接单台稳定后才进入这一批次"
    },
    {
      title: "员工操作 SOP",
      status: "draft",
      owner: "白龙马",
      summary: "确保非技术员工能在 30 分钟内学会接单、确认和查看厨房任务。",
      result: "直接回应陈先生“请保持简单”的要求"
    }
  ],
  journey: {
    mode: "快速交付模式",
    demandType: "Founder Demand",
    demand: "把面包店多渠道订单自动录入，减少漏单、错单和客户投诉",
    narrative: "这不是长期国家治理，而是一单明确的中小客户需求：在短时间内交出一个能让门店少漏单、少跑腿、少出错的工具。",
    position: "第 2 / 7 阶段",
    positionNote: "当前卡在方案定界与样本准备之间，还没有进入真实工程生产。",
    currentState: "tangseng_planning",
    states: [
      {
        key: "conversation_received",
        title: "需求进线",
        owner: "唐僧",
        status: "done",
        signal: "已整理",
        icon: "◎",
        description: "把陈先生的访谈转成可拆解业务问题。"
      },
      {
        key: "tangseng_planning",
        title: "方案定界",
        owner: "唐僧",
        status: "current",
        signal: "正在收口",
        icon: "✦",
        description: "先只做订单自动入台与定制蛋糕自动确认，不顺手接 POS。"
      },
      {
        key: "bajie_ideating",
        title: "产品定型",
        owner: "八戒",
        status: "next",
        signal: "下一棒",
        icon: "◈",
        description: "把统一订单台、厨房视图和自动确认话术做成可执行产品规格。"
      },
      {
        key: "houge_building",
        title: "工程生产",
        owner: "猴哥",
        status: "future",
        signal: "等样本",
        icon: "⚙",
        description: "接入 LINE、WhatsApp、电话录入流程，把订单自动落到统一工作台。"
      },
      {
        key: "shaseng_testing",
        title: "质量门禁",
        owner: "沙僧",
        status: "future",
        signal: "待验证",
        icon: "◌",
        description: "重点看漏单、错单、定制蛋糕特殊说明丢失和错误自动确认。"
      },
      {
        key: "customer_delivered",
        title: "客户交付",
        owner: "白龙马 / 唐僧",
        status: "future",
        signal: "待交付",
        icon: "✉",
        description: "把工具交到陈先生和女儿手里，并确认 12 名员工真能上手。"
      },
      {
        key: "closed",
        title: "任务结束",
        owner: "唐僧",
        status: "future",
        signal: "待收口",
        icon: "☼",
        description: "确认投诉、漏单和人工录入是否下降，然后关闭或升级到下一单。"
      }
    ],
    checkpoints: [
      { label: "当前状态", value: "方案定界", note: "唐僧正在锁定 MVP 边界与预算逻辑。" },
      { label: "下一状态", value: "产品定型", note: "八戒会把统一订单台和自动确认流程定型。" },
      { label: "当前节拍风险", value: "中", note: "如果权限和样本迟迟不到，猴哥工位会继续等待。" }
    ],
    finishRules: [
      { title: "正常结束", detail: "订单不再需要人工抄进 Excel，定制蛋糕能自动发出确认，厨房知道该做什么。" },
      { title: "提前结束", detail: "若先完成 LINE + WhatsApp 两路自动入台且已显著降错单，可先关闭电话自动化为下一单。" },
      { title: "升级结束", detail: "如果陈先生后续要接 Facebook、POS 或会员体系，这一单交付关闭，另开升级批次。" }
    ]
  },
  lineStatus: "产线运行中",
  productionLine: [
    {
      station: "需求进线",
      owner: "唐僧 / 白龙马",
      activity: "已整理",
      icon: "◎",
      wip: 1,
      queue: 3,
      status: "done",
      note: "把陈先生的访谈、预算和成功标准归成可生产需求。",
      batches: [
        { id: "B07", label: "多渠道订单自动录入", status: "done" },
        { id: "B08", label: "厨房批次看板", status: "queued" }
      ]
    },
    {
      station: "产品定型",
      owner: "八戒",
      activity: "规格收口中",
      icon: "◈",
      wip: 1,
      queue: 2,
      status: "active",
      note: "把统一订单台、自动确认和厨房视图压成员工能用、猴哥能做的规格。",
      batches: [
        { id: "B07", label: "统一订单台规格", status: "active" },
        { id: "B07-C", label: "定制蛋糕确认流", status: "queued" }
      ]
    },
    {
      station: "工程生产",
      owner: "猴哥",
      activity: "等待样本",
      icon: "⚙",
      wip: 0,
      queue: 3,
      status: "warning",
      note: "当前瓶颈工位，渠道权限、样本消息和样本 Excel 不齐时不能贸然开工。",
      batches: [
        { id: "B07", label: "LINE / WhatsApp intake", status: "blocked" },
        { id: "B07-P", label: "Phone order assistant", status: "queued" }
      ]
    },
    {
      station: "质量门禁",
      owner: "沙僧",
      activity: "等待首版",
      icon: "◌",
      wip: 1,
      queue: 2,
      status: "queued",
      note: "会重点检查错单、漏单、图片订单遗漏和错误自动确认。",
      batches: [
        { id: "B07-QA", label: "Order accuracy tests", status: "queued" },
        { id: "B07-CAKE", label: "Custom cake edge cases", status: "queued" }
      ]
    },
    {
      station: "交付回流",
      owner: "白龙马 / 唐僧",
      activity: "追材料中",
      icon: "✉",
      wip: 1,
      queue: 2,
      status: "active",
      note: "先向客户追权限和样本，交付后再收员工采用反馈，决定要不要升级下一批次。",
      batches: [
        { id: "B07-D", label: "权限与样本追问", status: "active" },
        { id: "B08", label: "POS / Facebook 升级判断", status: "queued" }
      ]
    }
  ],
  ops: [
    { label: "推进稳定度", value: "中高", note: "方案冻结前节拍稳定，工程仍受样本影响", icon: "⟠", tone: "gold", meter: 68 },
    { label: "当前瓶颈", value: "渠道权限", note: "LINE OA 和样本消息不到位会卡住猴哥", icon: "✦", tone: "red", meter: 84 },
    { label: "目标良品率", value: "95%+", note: "订单抽取和自动确认必须接近人工准确率", icon: "◌", tone: "green", meter: 95 },
    { label: "样本库存", value: "12 / 40", note: "当前只有 12 条真实订单样本可用于训练与评测", icon: "◈", tone: "blue", meter: 30 },
    { label: "在制批次", value: "6", note: "B07 主批次及其子任务正在不同工位流转", icon: "⇄", tone: "gold", meter: 54 },
    { label: "客户响应性", value: "待追齐", note: "白龙马正在把样本、权限和规则补齐", icon: "✉", tone: "blue", meter: 48 }
  ],
  marketLoop: [
    {
      source: "销售前线",
      title: "预算低于一名员工工资就有成交机会",
      effect: "唐僧把首单控制在 30k-50k NTD / 月可接受边界内"
    },
    {
      source: "客户服务",
      title: "非技术员工最怕复杂操作，陈先生反复强调“请保持简单”",
      effect: "八戒把员工 SOP 和极简接单台放进 MVP，而不是做复杂后台"
    },
    {
      source: "使用数据",
      title: "当前还没有真实使用数据，只有访谈证据和流程痛点",
      effect: "白龙马优先去追真实消息样本和现有 Excel，避免闭门造车"
    }
  ],
  reports: [
    {
      name: "周产线分析",
      cadence: "每周一 09:00",
      summary: "本周瓶颈不是技术难度，而是前期权限和样本采集。建议白龙马优先追齐真实数据。"
    },
    {
      name: "品质报告",
      cadence: "每次 release gate 后",
      summary: "重点关注错单、漏单、定制蛋糕图片和特殊说明的抽取准确率是否达到 95% 以上。"
    },
    {
      name: "库存消耗报告",
      cadence: "每日 18:00",
      summary: "当前真实订单样本偏少，若没有更多 LINE / WhatsApp 对话样本，沙僧的评测将失真。"
    }
  ],
  events: [
    ["03:55", "客户 → 你", "请保持简单，我的员工不是技术人员。"],
    ["03:50", "你 → 唐僧", "客户要的是订单自动进系统、厨房知道做什么、定制蛋糕自动确认。"],
    ["03:25", "客户 → 白龙马", "已有 POS 但不连接任何东西，LINE Official Account 由女儿管理。"],
    ["02:50", "客户 → 唐僧", "预算希望控制在 30,000-50,000 NTD / 月，低于招一人即可。"],
    ["01:20", "客户 → 全队", "现在靠人工每 15 分钟看消息抄 Excel，常常漏单、错单、漏回。"]
  ],
  feedbackScenarios: {
    prototype: {
      title: "访谈后澄清追问",
      summary: "白龙马把访谈里的痛点拆成唐僧真正能下任务的澄清问题，而不是急着去问空泛意见。",
      actionLabel: "起草 follow-up",
      actionReason: "客户已说清楚痛点，但还没给权限、样本 Excel 和定制蛋糕确认规则，必须继续追问。",
      sentiment: "neutral-positive",
      summaryText: "客户愿意推进，但实现前还缺真实订单样本、账号权限和定制蛋糕报价规则。",
      recommendation: "先让白龙马追齐 LINE OA 权限、样本 Excel、3 条真实定制蛋糕对话，再让猴哥开工。",
      evidence: "证据来源：访谈记录、预算表述、渠道现状",
      followupStatus: "待审批发送",
      followupDraft: "谢谢您，下一步为了让团队出具体方案，我们只需要三样资料：现有订单 Excel、一小段 LINE / WhatsApp 真实对话样本，以及定制蛋糕通常怎么确认价格和取货时间。",
      sources: [
        {
          kind: "meeting_note",
          channel: "访谈转写",
          title: "陈先生访谈记录",
          detail: "客户明确说最大问题是人工抄单、漏单、定制蛋糕特殊说明处理麻烦。"
        },
        {
          kind: "customer_message",
          channel: "口头预算",
          title: "预算与约束",
          detail: "30,000-50,000 NTD / 月，可接受前提是低于再招一人。"
        }
      ],
      signals: [
        {
          type: "value_signal",
          sentiment: "positive",
          urgency: "low",
          summary: "客户已经明确愿意为自动接单和少投诉付费，价值主线成立。"
        },
        {
          type: "feature_request",
          sentiment: "neutral-positive",
          urgency: "medium",
          summary: "客户重点要求定制蛋糕自动确认价格与取货时间，这是 MVP 核心场景。"
        },
        {
          type: "adoption_friction",
          sentiment: "negative",
          urgency: "medium",
          summary: "非技术员工是明显风险，因此交付必须极简，不能逼店员学复杂后台。"
        }
      ]
    },
    silence: {
      title: "客户尚未给样本和权限",
      summary: "白龙马不是只等评价，他也负责追交付前必需的客户侧物料，沉默本身就是进度风险。",
      actionLabel: "自动追问",
      actionReason: "如果 24 小时还没收到 Excel 或账号信息，白龙马应该主动轻提醒，否则整条产线都会空转。",
      sentiment: "unknown",
      summaryText: "客户还没把样本 Excel 和 LINE OA 权限给出来，猴哥暂时无法开始真实接入。",
      recommendation: "白龙马发出简短提醒，只追关键材料，不在这一步继续教育客户或扩展范围。",
      evidence: "证据来源：24 小时无回复、尚未收到样本文件",
      followupStatus: "已进入自动发送队列",
      followupDraft: "我们已经开始内部设计了。为了不耽误您下周看到方案，麻烦先发一份现在的订单 Excel 和 2-3 条真实订单截图，我们就能继续往前推。",
      sources: [
        {
          kind: "customer_message",
          channel: "LINE",
          title: "最近一次追问记录",
          detail: "已询问订单 Excel、LINE OA 权限和定制蛋糕确认规则，但尚未收到资料。"
        },
        {
          kind: "support_ticket",
          channel: "内部待办",
          title: "样本资料缺失",
          detail: "当前没有真实多渠道订单样本，无法验证自动抽取准确率。"
        }
      ],
      signals: [
        {
          type: "silence",
          sentiment: "unknown",
          urgency: "medium",
          summary: "客户还没提供关键样本，属于产线阻塞型沉默，需要温和追问。"
        },
        {
          type: "bug_risk",
          sentiment: "unknown",
          urgency: "medium",
          summary: "在没有样本的情况下设计抽取逻辑，后续很可能返工。"
        }
      ]
    },
    expansion: {
      title: "客户后续想接 POS 或 Facebook",
      summary: "白龙马要把“想要更多”压回到下一批次，而不是让当前这单无限膨胀。",
      actionLabel: "回传唐僧决策",
      actionReason: "这不是当前批次必须完成的目标，先作为升级需求收进下一单，不打乱这单交付节拍。",
      sentiment: "neutral-positive",
      summaryText: "客户后续很可能会要 Facebook、POS 或会员数据打通，但这不该挤进首个 MVP。",
      recommendation: "唐僧把 POS / Facebook 记为下一批次 B08，当前单只交付多渠道自动入台与自动确认。",
      evidence: "证据来源：现有系统描述、老板对未来扩展的隐含预期",
      followupStatus: "无需立即追问",
      followupDraft: "当前不需要额外追问，白龙马会等唐僧先把首单方案收敛，再把升级需求单独立项。",
      sources: [
        {
          kind: "meeting_note",
          channel: "访谈转写",
          title: "现有系统描述",
          detail: "客户已有基础 POS，但完全不连接其他东西。"
        },
        {
          kind: "customer_message",
          channel: "访谈语境",
          title: "未来扩展可能",
          detail: "既然客户提到 Facebook、LINE 和 POS 分散，后续很可能继续提出系统整合诉求。"
        }
      ],
      signals: [
        {
          type: "feature_request",
          sentiment: "neutral-positive",
          urgency: "medium",
          summary: "客户未来扩展需求很明确，但应留到下一单而不是塞进首单。"
        },
        {
          type: "value_signal",
          sentiment: "positive",
          urgency: "low",
          summary: "客户愿意继续深化，说明如果首单成功，后续批次空间很大。"
        }
      ]
    }
  }
};

const runtime = createBakeryDemoRuntime();

const $ = (selector) => document.querySelector(selector);

function syncState(snapshot) {
  state.projects = snapshot.projects;
  state.projectQuery = snapshot.projectQuery;
  state.summary = snapshot.summary;
  state.thread = snapshot.thread;
  state.decisions = snapshot.decisions;
  state.agents = snapshot.agents;
  state.journey = snapshot.journey;
  state.outcome = snapshot.outcome;
  state.deliveries = snapshot.deliveries;
  state.feedbackScenarios = snapshot.feedbackScenarios;
  state.ops = snapshot.ops;
  state.marketLoop = snapshot.marketLoop;
}

function statusLabel(status) {
  return {
    orchestrating: "编排中",
    thinking: "构思中",
    waiting: "等输入",
    testing: "测试中",
    listening: "听反馈",
    delivered: "已交付",
    ready: "待发送",
    active: "运行",
    done: "完成",
    queued: "排队",
    approved: "已批准",
    draft: "草稿",
    running: "运行中",
    new: "新信号"
  }[status] ?? status;
}

function toneClass(tone = "gold") {
  return {
    green: "tone-green",
    gold: "tone-gold",
    blue: "tone-blue",
    red: "tone-red",
    silver: "tone-silver"
  }[tone] ?? "tone-gold";
}

function feedbackMix(signals) {
  const mix = [
    { key: "value_signal", label: "价值确认", tone: "green" },
    { key: "feature_request", label: "功能诉求", tone: "gold" },
    { key: "adoption_friction", label: "采用阻力", tone: "red" },
    { key: "bug_risk", label: "错误风险", tone: "red" },
    { key: "silence", label: "沉默风险", tone: "blue" }
  ]
    .map((item) => ({
      ...item,
      count: signals.filter((signal) => signal.type === item.key).length
    }))
    .filter((item) => item.count > 0);

  const total = mix.reduce((sum, item) => sum + item.count, 0) || 1;
  return mix.map((item) => ({ ...item, share: Math.round((item.count / total) * 100) }));
}

function renderProjectRail() {
  const title = $("#projectTitle");
  const summary = $("#projectSummary");
  const list = $("#projectList");
  if (title) title.textContent = state.projects[0]?.name ?? "";
  if (summary) summary.textContent = state.projects[0]?.summary ?? "";
  if (!list) return;

  const query = state.projectQuery.trim().toLowerCase();
  const projects = state.projects.filter((project) => {
    if (!query) return true;
    return [project.id, project.name, project.client, project.summary].join(" ").toLowerCase().includes(query);
  });

  if (!projects.length) {
    list.innerHTML = `<article class="project-chip empty"><div><strong>没有匹配项目</strong><p>换个客户名、批次号或关键词试试</p></div></article>`;
    return;
  }

  list.innerHTML = projects
    .map((project) => `<article class="project-chip ${project.status} ${project.id === state.projects[0].id ? "active" : ""}">
      <div>
        <strong>${project.name}</strong>
        <p>${project.client}</p>
      </div>
      <span>${project.id}</span>
    </article>`)
    .join("");
}

function renderNav() {
  const nav = $("#navList");
  if (!nav) return;
  nav.innerHTML = state.nav
    .map((item) => `<article class="nav-item ${item.active ? "active" : ""}">
      <div class="nav-copy">
        <strong><span class="nav-icon">${item.icon}</span>${item.label}</strong>
        <span>${item.desc}</span>
      </div>
      <span class="nav-tag">${item.tag}</span>
    </article>`)
    .join("");
}

function renderMetrics() {
  const current = state.journey.states.find((item) => item.status === "current")?.title ?? "方案定界";
  state.summary[1] = { label: "当前阶段", value: current, note: "唐僧正在冻结 MVP 边界", icon: "☉", tone: "green", meter: 46 };
  const currentIndex = state.journey.states.findIndex((item) => item.status === "current");
  if (currentIndex >= 0) {
    state.summary[2] = {
      label: "任务位置",
      value: `第 ${currentIndex + 1} / ${state.journey.states.length} 阶段`,
      note: "看位置和状态，不再用不准的工期感",
      icon: "⇄",
      tone: "blue",
      meter: Math.round(((currentIndex + 1) / state.journey.states.length) * 100)
    };
  }
}

function renderRoster() {
  const roster = $("#agentRoster");
  if (!roster) return;
  roster.innerHTML = state.agents
    .map((agent) => `<article class="agent-row ${agent.status}" data-agent="${agent.id}">
      <div class="agent-seal ${agent.color}">${agent.name.slice(0, 1)}</div>
      <div class="agent-main">
        <div class="agent-title">
          <strong>${agent.name}</strong>
          <span>${agent.model}</span>
        </div>
        <p>${agent.role}</p>
        <div class="agent-current">${agent.current}</div>
        <div class="agent-meta">
          <span>完成度 ${agent.progress}%</span>
          <span>产出：${agent.output}</span>
        </div>
        <div class="load-track"><span style="width:${agent.progress}%"></span></div>
        <div class="agent-blocker">${agent.blocker}</div>
      </div>
      <span class="status-pill ${agent.status === "waiting" ? "warning" : "live"}">${statusLabel(agent.status)}</span>
    </article>`)
    .join("");
}

function renderTeamStage() {
  const stage = $("#teamStage");
  if (!stage) return;

  const cast = [
    {
      id: "founder",
      name: "如来佛祖",
      role: "发愿者 / 总控",
      status: "live",
      current: "提出目标，盯住结果与节奏。",
      output: "任务目标",
      artifact: "减少投诉、降低漏单",
      slot: "founder-slot"
    },
    ...state.agents.map((agent) => ({
      ...agent,
      artifact: agent.output,
      slot: `${agent.id}-slot`
    }))
  ];

  stage.innerHTML = `
    <div class="stage-core">
      <span class="artifact-type">${state.journey.demandType}</span>
      <strong>当前协作脉冲</strong>
      <p>${state.journey.states.find((item) => item.status === "current")?.description ?? state.outcome.summary}</p>
      <div class="core-position">
        <span>${state.journey.position}</span>
        <strong>${state.journey.states.find((item) => item.status === "current")?.title ?? "方案定界"}</strong>
      </div>
    </div>
    ${cast
      .map((member) => `<article class="actor-card ${member.slot} ${member.id} ${member.status}">
        <div class="actor-avatar ${member.id}">
          <span class="actor-aura"></span>
          <span class="actor-skull">
            <i class="actor-ear left"></i>
            <i class="actor-ear right"></i>
            <span class="actor-face">
              <i class="eye left"></i>
              <i class="eye right"></i>
              <i class="mouth"></i>
            </span>
          </span>
          <span class="actor-body"></span>
          <span class="actor-prop"></span>
        </div>
        <div class="actor-copy">
          <div class="actor-head">
            <strong>${member.name}</strong>
            <span class="status-pill ${member.status === "waiting" ? "warning" : member.status === "queued" ? "" : "live"}">${member.id === "founder" ? "发愿中" : statusLabel(member.status)}</span>
          </div>
          <p>${member.current}</p>
          <button class="artifact-link" type="button">${member.artifact}</button>
        </div>
      </article>`)
      .join("")}
  `;
}

function renderJourneyMap(filter = "all") {
  return filter;
}

function renderEvents() {
  const stream = $("#eventStream");
  if (!stream) return;
  stream.innerHTML = state.events
    .map(([time, route, text]) => `<article class="event-item">
      <span>${time}</span>
      <strong>${route}</strong>
      <p>${text}</p>
    </article>`)
    .join("");
}

function renderOutcome() {
  const overview = $("#briefOverview");
  const bullets = $("#briefBulletList");
  if (overview) {
    overview.textContent = state.outcome.summary;
  }
  if (bullets) {
    bullets.innerHTML = state.outcome.points
      .map((point) => `<div class="brief-bullet">${point}</div>`)
      .join("");
  }
}

function renderWorkbench() {
  $("#commandThread").innerHTML = state.thread
    .map((item) => `<article class="thread-item ${item.tone}">
      <div class="thread-head">
        <strong>${item.who}</strong>
        <span>${item.role}</span>
      </div>
      <p>${item.text}</p>
    </article>`)
    .join("");

  $("#summaryGrid").innerHTML = state.summary
    .map((item) => `<article class="stat-card ${toneClass(item.tone)}">
      <div class="stat-head">
        <span>${item.label}</span>
        <div class="stat-glyph ${toneClass(item.tone)}">${item.icon ?? "◌"}</div>
      </div>
      <strong>${item.value}</strong>
      <p>${item.note}</p>
      <div class="mini-meter"><span style="width:${item.meter ?? 50}%"></span></div>
    </article>`)
    .join("");

  $("#decisionList").innerHTML = state.decisions
    .map((item) => `<article class="decision-card ${item.status}">
      <div class="thread-head">
        <strong>${item.title}</strong>
        <span>${item.from}</span>
      </div>
      <p>${item.detail}</p>
      <div class="decision-impact">${item.impact}</div>
      <div class="decision-actions">
        <button class="ghost-button compact" data-action="approve-decision" data-id="${item.id}">批准</button>
        <button class="ghost-button compact" data-action="ask-decision" data-id="${item.id}">追问</button>
      </div>
    </article>`)
    .join("");
}

function renderDeliveries() {
  const deliveryList = $("#deliveryList");
  if (!deliveryList) return;
  deliveryList.innerHTML = state.deliveries
    .map((delivery, index) => `<article class="artifact-preview-card ${delivery.status}">
      <div class="preview-screen tone-${["gold", "green", "blue", "red"][index % 4]}">
        <div class="preview-topbar">
          <span></span><span></span><span></span>
        </div>
        <div class="preview-layout">
          <i class="preview-block wide"></i>
          <i class="preview-block"></i>
          <i class="preview-block"></i>
          <i class="preview-line"></i>
          <i class="preview-line short"></i>
        </div>
      </div>
      <div class="artifact-preview-copy">
        <span class="artifact-type">${delivery.owner}</span>
        <strong>${delivery.title}</strong>
        <p>${delivery.result}</p>
      </div>
      <span class="status-pill ${delivery.status === "draft" ? "warning" : delivery.status === "delivered" || delivery.status === "ready" ? "live" : ""}">${statusLabel(delivery.status)}</span>
    </article>`)
    .join("");
}

function renderFactory() {
  const ops = $("#opsGrid");
  if (ops) {
    ops.innerHTML = state.ops
      .map((item) => `<article class="stat-card ${toneClass(item.tone)}">
        <div class="stat-head">
          <span>${item.label}</span>
          <div class="ring-meter ${toneClass(item.tone)}" style="--meter:${item.meter ?? 50}">
            <i>${item.icon ?? "◌"}</i>
          </div>
        </div>
        <strong>${item.value}</strong>
        <p>${item.note}</p>
      </article>`)
      .join("");
  }

  const market = $("#marketList");
  if (market) {
    market.innerHTML = state.marketLoop
      .map((item) => `<article class="market-card">
        <span class="artifact-type">${item.source}</span>
        <strong>${item.title}</strong>
        <p>${item.effect}</p>
      </article>`)
      .join("");
  }
}

function renderJourneyStateMachine() {
  $("#journeyMode").textContent = state.journey.mode;
  $("#journeyDemandType").textContent = state.journey.demandType;
  $("#journeyDemand").textContent = state.journey.demand;
  $("#journeyNarrative").textContent = state.journey.narrative;
  $("#journeyPosition").textContent = state.journey.position;
  $("#journeyPositionNote").textContent = state.journey.positionNote;

  $("#stateTrack").innerHTML = state.journey.states
    .map((item, index) => `<article class="state-node ${item.status}">
      <div class="state-node-top">
        <span class="artifact-type">0${index + 1} · ${item.owner}</span>
        <span class="status-pill ${item.status === "current" || item.status === "done" ? "live" : item.status === "next" ? "warning" : ""}">${item.signal}</span>
      </div>
      <strong><span class="state-icon">${item.icon ?? "◌"}</span>${item.title}</strong>
      <p>${item.description}</p>
    </article>`)
    .join("");
}

function signalTone(signal) {
  if (signal.sentiment === "negative") return "warning";
  if (signal.sentiment === "positive" || signal.sentiment === "neutral-positive") return "live";
  return "";
}

function renderFeedbackDemo() {
  const scenario = state.feedbackScenarios.prototype;
  if (!scenario) return;
  $("#feedbackSentiment").textContent = scenario.sentiment;
  $("#feedbackSummaryText").textContent = scenario.summaryText;
  $("#feedbackRecommendation").textContent = scenario.recommendation;
  $("#feedbackEvidence").textContent = scenario.evidence;
  $("#followupStatus").textContent = scenario.followupStatus;
  $("#followupDraft").textContent = scenario.followupDraft;

  $("#feedbackSources").innerHTML = scenario.sources
    .map((source) => `<article class="source-card">
      <div class="source-head">
        <span class="artifact-type">${source.kind}</span>
        <span class="status-pill">${source.channel}</span>
      </div>
      <strong>${source.title}</strong>
      <p>${source.detail}</p>
    </article>`)
    .join("");

  $("#feedbackSignals").innerHTML = scenario.signals
    .map((signal) => `<article class="signal-card ${signalTone(signal)}">
      <div class="source-head">
        <span class="artifact-type">${signal.type}</span>
        <span class="status-pill ${signalTone(signal)}">${signal.urgency}</span>
      </div>
      <strong>${signal.sentiment}</strong>
      <p>${signal.summary}</p>
    </article>`)
    .join("");

  const mix = feedbackMix(scenario.signals);
  $("#signalMixBar").innerHTML = mix
    .map((item) => `<div class="mix-segment ${toneClass(item.tone)}" style="width:${item.share}%"></div>`)
    .join("");
  $("#signalLegend").innerHTML = mix
    .map((item) => `<div class="legend-item">
      <span class="legend-dot ${toneClass(item.tone)}"></span>
      <strong>${item.label}</strong>
      <span>${item.share}%</span>
    </div>`)
    .join("");
  $("#feedbackCadence").innerHTML = [
    { label: "访谈完成", state: "done" },
    { label: "追样本", state: "current" },
    { label: "方案回传", state: "next" },
    { label: "交付回访", state: "future" }
  ]
    .map((item) => `<div class="cadence-step ${item.state}">
      <span class="cadence-dot"></span>
      <strong>${item.label}</strong>
    </div>`)
    .join("");
}

function pushFeedbackBrief() {
  const scenario = state.feedbackScenarios.prototype;
  state.events.unshift(["刚刚", "白龙马 → 唐僧", `${scenario.title}：${scenario.recommendation}`]);
  state.artifacts.unshift({
    title: `${scenario.title} 简报`,
    owner: "白龙马",
    type: "CS",
    status: "new",
    summary: scenario.summaryText
  });
  state.outcome.points[2] = `当前目标：${scenario.recommendation}`;
  $("#founderFocus").textContent = `唐僧已收到白龙马简报：${scenario.recommendation}`;
  renderAll();
}

function appendThread(who, role, tone, text) {
  state.thread.push({ who, role, tone, text });
}

function respondFromTangseng(message) {
  const lower = message.toLowerCase();
  if (lower.includes("进度")) {
    return "当前进度在方案定界尾声。最卡的是渠道权限与真实样本，一旦白龙马追齐，猴哥就会进入工程生产。";
  }
  if (lower.includes("范围") || lower.includes("收紧")) {
    state.journey.checkpoints[0] = { label: "当前状态", value: "范围已收紧", note: "唐僧已确认首单不接 POS，只做统一订单台与自动确认。" };
    state.summary[3] = { label: "最关键决策", value: "首单不接 POS", note: "交付复杂度因此保持可控", icon: "✦", tone: "red", meter: 74 };
    return "我会把首单范围收紧到统一订单台、定制蛋糕自动确认和厨房视图，POS 集成移到下一批次。";
  }
  return "我收到了。接下来我会据此更新方案边界，并把需要你裁决的地方继续放进决策 inbox。";
}

function sendDirective(text) {
  const content = text.trim();
  if (!content) return;
  appendThread("你", "如来佛祖", "founder", content);
  appendThread("唐僧", "leader", "agent", respondFromTangseng(content));
}

function openCommandMenu() {
  $("#commandMenu").classList.remove("hidden");
  $("#commandInput").focus();
  $("#commandResults").innerHTML = [
    "运行唐僧全局编排",
    "让八戒生成客户确认话术",
    "确认猴哥必需输入",
    "启动沙僧 release gate",
    "让白龙马追问客户反馈",
    "切换白龙马反馈采集场景"
  ]
    .map((item) => `<div class="command-result">${item}</div>`)
    .join("");
}

function closeCommandMenu() {
  $("#commandMenu").classList.add("hidden");
}

function advanceTick() {
  state.tick += 1;
  const time = `15:${40 + state.tick}`;
  state.events.unshift([time, "唐僧 → 八戒", "已下发本轮要求：先收敛统一订单台和定制蛋糕自动确认，再把最小字段集交给猴哥。"]);
  state.artifacts.unshift({
    title: `唐僧调度记录 ${state.tick}`,
    owner: "唐僧",
    type: "Run Log",
    status: "new",
    summary: "本轮继续保持猴哥等待真实渠道权限与样本，避免无样本接入导致返工。"
  });
  state.journey.positionNote = "方案定界已更清楚，但没有真实样本前，任务仍停在工程启动前一格。";
  appendThread("唐僧", "leader", "agent", "我刚推进了一轮内部编排。八戒继续收敛产品规格，白龙马继续追样本，猴哥暂不冒进开工。");
  renderAll();
}

function injectFeedback() {
  state.events.unshift(["刚刚", "客户女儿 → 白龙马", "已同意提供 LINE Official Account 管理权限、现有 Excel 模板和 3 条定制蛋糕对话样本。"]);
  const houge = state.agents.find((agent) => agent.id === "houge");
  if (houge) {
    houge.status = "orchestrating";
    houge.current = "已拿到样本与权限，开始做 LINE / WhatsApp / 电话订单 intake pipeline";
    houge.progress = 41;
    houge.load = 78;
    houge.blocker = "阻塞已解除，当前进入真实渠道接入与字段映射。";
  }
  state.journey.states = state.journey.states.map((item) => {
    if (item.key === "tangseng_planning") return { ...item, status: "done" };
    if (item.key === "bajie_ideating") return { ...item, status: "done" };
    if (item.key === "houge_building") return { ...item, status: "current" };
    if (item.key === "shaseng_testing") return { ...item, status: "next" };
    return item;
  });
  state.journey.checkpoints[0] = { label: "当前状态", value: "工程生产", note: "猴哥已拿到权限和样本，开始真实接入。" };
  state.journey.checkpoints[1] = { label: "下一状态", value: "质量门禁", note: "沙僧将验证订单抽取和定制蛋糕自动确认准确率。" };
  state.journey.position = "第 4 / 7 阶段";
  state.journey.positionNote = "主要阻塞已解除，任务已经从前期定界进入真实工程生产。";
  const buildStation = state.productionLine.find((item) => item.station === "工程生产");
  if (buildStation) {
    buildStation.activity = "工作中";
    buildStation.status = "active";
    buildStation.wip = 1;
    buildStation.note = "已拿到真实渠道样本和权限，正在做接入层与字段映射。";
    buildStation.batches = [
      { id: "B07", label: "LINE / WhatsApp intake", status: "active" },
      { id: "B07-P", label: "Phone order assistant", status: "queued" }
    ];
  }
  const flow = state.flows.find((item) => item.id === "f4");
  if (flow) flow.status = "active";
  appendThread("白龙马", "client success", "agent", "我已经追到 LINE OA 权限和样本 Excel，猴哥可以进入真实接入。");
  appendThread("唐僧", "leader", "agent", "很好，工程工位开始动了。接下来我会盯住猴哥与沙僧之间的交接，不让质量门禁掉线。");
  $("#founderFocus").textContent = "客户女儿已给出 LINE OA 权限与样本，猴哥可以开始做真实接入，沙僧同步准备订单准确率评测。";
  renderAll();
}

function approveLatest() {
  const latest = state.artifacts.find((artifact) => artifact.status === "new" || artifact.status === "draft");
  if (!latest) return;
  latest.status = "approved";
  state.events.unshift(["刚刚", "你 → 唐僧", `已批准：${latest.title}`]);
  renderAll();
}

function bindActions() {
  document.body.addEventListener("click", (event) => {
    const action = event.target.dataset.action;
    if (!action) return;
    if (action === "open-command") openCommandMenu();
    if (action === "advance-tick" || action === "run-tangseng") {
      syncState(runtime.advance());
      renderAll();
    }
    if (action === "inject-feedback") {
      syncState(runtime.injectCustomerMaterials());
      renderAll();
    }
    if (action === "cycle-feedback-scenario" || action === "push-feedback-brief") {
      syncState(runtime.pushFeedbackBrief());
      renderAll();
    }
    if (action === "approve-latest") approveLatest();
    if (action === "ask-progress") {
      syncState(runtime.founderDirective("给我一个不绕的当前进度。"));
      renderAll();
    }
    if (action === "tighten-scope") {
      syncState(runtime.founderDirective("先收紧范围，首单不要碰 POS。"));
      renderAll();
    }
    if (action === "send-directive") {
      syncState(runtime.founderDirective($("#directiveInput").value));
      $("#directiveInput").value = "";
      renderAll();
    }
    if (action === "approve-decision") {
      syncState(runtime.approveDecision(event.target.dataset.id));
      renderAll();
    }
    if (action === "ask-decision") {
      const item = state.decisions.find((decision) => decision.id === event.target.dataset.id);
      if (item) {
        appendThread("你", "如来佛祖", "founder", `再解释一下：${item.title}`);
        appendThread("唐僧", "leader", "agent", `${item.detail} 这件事的真实影响是：${item.impact}`);
        renderAll();
      }
    }
    if (action === "inspect-flow") {
      const flow = state.flows.find((item) => item.id === event.target.dataset.flowId);
      if (flow) {
        state.events.unshift(["刚刚", "你查看了流转", `${flow.from} 到 ${flow.to}：${flow.label}`]);
        renderEvents();
      }
    }
  });

  $("#commandMenu").addEventListener("click", (event) => {
    if (event.target.id === "commandMenu") closeCommandMenu();
  });

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      openCommandMenu();
    }
    if (event.key === "Escape") closeCommandMenu();
  });

  const projectSearch = $("#projectSearchInput");
  if (projectSearch) {
    projectSearch.addEventListener("input", (event) => {
      runtime.setProjectQuery(event.target.value);
      syncState(runtime.getSnapshot());
      renderProjectRail();
    });
  }
}

function renderAll() {
  renderProjectRail();
  renderMetrics();
  renderWorkbench();
  renderJourneyStateMachine();
  renderTeamStage();
  renderFactory();
  renderOutcome();
  renderDeliveries();
  renderEvents();
  renderFeedbackDemo();
}

function init() {
  syncState(runtime.getSnapshot());
  renderNav();
  renderAll();
  bindActions();
}

init();
