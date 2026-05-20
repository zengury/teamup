const bakeryTranscript = `[00:00] Customer (Mr. Chen, Owner):
We run a medium bakery with 12 staff. We have three stores and a central kitchen.
Our biggest problem right now is that we get lots of orders through LINE, WhatsApp,
and phone calls, and our staff has to manually enter everything into a spreadsheet.
It's causing mistakes - wrong orders, missed deliveries. I heard AI can help with this.

[00:50] Mr. Chen:
About 80-120 orders per day across all channels. Weekends can hit 200. We sell
bread, cakes, and custom celebration cakes. The custom cakes are the biggest
headache because customers send photos and special instructions.

[01:20] Mr. Chen:
Customer messages come in. My daughter or one of the counter staff checks the
phone every 15 minutes, copies the order details into our Excel sheet, then
sends a confirmation manually.

[02:05] Mr. Chen:
I want the orders to just appear in our system automatically. No manual entry.
And I want the kitchen to know what to bake. Also, for custom cakes, I want the
customer to get an automatic confirmation with price and pickup time.

[02:50] Mr. Chen:
maybe 30,000-50,000 NTD per month?

[03:25] Mr. Chen:
We have a basic POS for in-store sales, but it doesn't connect to anything.
No website, just Facebook and LINE.

[03:55] Mr. Chen:
Please keep it simple. My staff are not technical people.`;
export class BrowserProjectRuntime {
    approvals = {
        scope: false,
        outreach: false
    };
    materialsGranted = false;
    buildCompleted = false;
    testingPassed = false;
    feedbackReceived = false;
    founderQuestionAsked = false;
    projectQuery = "";
    founderMessages = [];
    parsed;
    projects;
    constructor(transcript) {
        this.parsed = parseConversation(transcript);
        this.projects = [
            {
                id: "B07",
                name: `${this.parsed.clientName}${this.parsed.businessType}订单自动化`,
                client: this.parsed.businessName,
                summary: this.baseSummary(),
                status: "active"
            },
            {
                id: "B08",
                name: "厨房批次看板升级",
                client: this.parsed.businessName,
                summary: "把中央厨房制作清单从 Excel 传递改成待制作看板。",
                status: "queued"
            },
            {
                id: "C03",
                name: "投诉归因助手",
                client: "Retail Pilot",
                summary: "聚类投诉来源和根因，给店长周复盘。",
                status: "queued"
            }
        ];
        this.founderMessages = [
            {
                who: "你",
                role: "如来佛祖",
                tone: "founder",
                text: `目标很明确：让 ${this.parsed.clientName} 的订单不要再手抄，先解决漏单、错单和定制蛋糕确认。`
            },
            {
                who: "唐僧",
                role: "leader",
                tone: "agent",
                text: "收到。我会先把首单收在统一接单、自动确认和厨房可读，不把 POS 一起卷进来。"
            }
        ];
    }
    setProjectQuery(query) {
        this.projectQuery = query;
    }
    approveDecision(id) {
        if (id === "d1") {
            this.approvals.scope = true;
            this.founderMessages.push({
                who: "你",
                role: "如来佛祖",
                tone: "founder",
                text: "批准，首单不接 POS，先做最小可交付。"
            });
            this.founderMessages.push({
                who: "唐僧",
                role: "leader",
                tone: "agent",
                text: "明白，我让八戒先把统一订单台和自动确认收成能交给猴哥的规格。"
            });
        }
        if (id === "d2") {
            this.approvals.outreach = true;
            this.founderMessages.push({
                who: "你",
                role: "如来佛祖",
                tone: "founder",
                text: "批准，白龙马可以直接去追样本和权限。"
            });
            this.founderMessages.push({
                who: "白龙马",
                role: "client success",
                tone: "agent",
                text: "收到，我会只追三样关键材料：样本 Excel、真实对话、定制蛋糕确认规则。"
            });
        }
        return this.getSnapshot();
    }
    founderDirective(text) {
        const message = text.trim();
        if (!message)
            return this.getSnapshot();
        this.founderMessages.push({
            who: "你",
            role: "如来佛祖",
            tone: "founder",
            text: message
        });
        if (message.includes("进度")) {
            this.founderMessages.push({
                who: "唐僧",
                role: "leader",
                tone: "agent",
                text: this.materialsGranted
                    ? "现在已经进入工程生产，猴哥在做接入层和字段映射，沙僧等第一版出来就会接手。"
                    : "现在还卡在样本和权限。八戒已经在收口产品规格，但猴哥还没有足够材料开工。"
            });
        }
        else if (message.includes("范围") || message.includes("POS")) {
            this.approvals.scope = true;
            this.founderMessages.push({
                who: "唐僧",
                role: "leader",
                tone: "agent",
                text: "我已经把范围收紧到统一接单、定制蛋糕自动确认和厨房可读，不让首单扩到 POS。"
            });
        }
        else {
            this.founderMessages.push({
                who: "唐僧",
                role: "leader",
                tone: "agent",
                text: "收到，我会把这条指令并进当前批次，更新分工和交付判断。"
            });
        }
        return this.getSnapshot();
    }
    injectCustomerMaterials() {
        this.materialsGranted = true;
        this.approvals.outreach = true;
        this.founderMessages.push({
            who: "白龙马",
            role: "client success",
            tone: "agent",
            text: "客户女儿已经给出 LINE OA 权限、样本 Excel 和几条真实定制蛋糕对话。"
        });
        this.founderMessages.push({
            who: "唐僧",
            role: "leader",
            tone: "agent",
            text: "很好，猴哥现在可以真实开工了。"
        });
        return this.getSnapshot();
    }
    advance() {
        if (this.approvals.scope && this.materialsGranted && !this.buildCompleted) {
            this.buildCompleted = true;
            this.founderMessages.push({
                who: "猴哥",
                role: "builder",
                tone: "agent",
                text: "第一版 intake pipeline 已经搭起来，统一订单台的字段映射也锁了。"
            });
            return this.getSnapshot();
        }
        if (this.buildCompleted && !this.testingPassed) {
            this.testingPassed = true;
            this.founderMessages.push({
                who: "沙僧",
                role: "qa",
                tone: "agent",
                text: "首轮质量门禁通过，主要风险已经缩到定制蛋糕特殊说明的边界样本。"
            });
            return this.getSnapshot();
        }
        if (this.testingPassed && !this.feedbackReceived) {
            this.feedbackReceived = true;
            this.founderMessages.push({
                who: "白龙马",
                role: "client success",
                tone: "agent",
                text: "客户反馈是正向的，最看重的是不再漏掉 LINE 订单和定制蛋糕自动确认。"
            });
            return this.getSnapshot();
        }
        this.founderMessages.push({
            who: "唐僧",
            role: "leader",
            tone: "agent",
            text: "当前批次没有新的状态跃迁，我在继续稳住节奏。"
        });
        return this.getSnapshot();
    }
    pushFeedbackBrief() {
        this.feedbackReceived = true;
        this.founderQuestionAsked = true;
        this.founderMessages.push({
            who: "白龙马",
            role: "client success",
            tone: "agent",
            text: "我已经把客户反馈汇成简报回给唐僧，重点是保持简单和把定制蛋糕场景做好。"
        });
        this.founderMessages.push({
            who: "唐僧",
            role: "leader",
            tone: "agent",
            text: "收到，下一轮我会优先压定制蛋糕确认流程和员工学习成本。"
        });
        return this.getSnapshot();
    }
    getSnapshot() {
        const stage = deriveStage({
            scopeApproved: this.approvals.scope,
            materialsGranted: this.materialsGranted,
            buildCompleted: this.buildCompleted,
            testingPassed: this.testingPassed,
            feedbackReceived: this.feedbackReceived
        });
        return {
            projects: this.projects,
            projectQuery: this.projectQuery,
            summary: buildSummary(this.parsed, stage),
            thread: this.founderMessages,
            decisions: buildDecisions(this.approvals, this.materialsGranted),
            agents: buildAgents(this.parsed, stage, this.approvals, this.materialsGranted, this.buildCompleted, this.testingPassed),
            journey: buildJourney(this.parsed, stage),
            outcome: buildOutcome(this.parsed, this.testingPassed, this.feedbackReceived),
            deliveries: buildDeliveries(this.parsed, stage),
            feedbackScenarios: {
                prototype: buildFeedbackScenario(this.parsed, this.materialsGranted, this.feedbackReceived)
            },
            ops: buildOps(stage, this.materialsGranted, this.testingPassed, this.feedbackReceived),
            marketLoop: buildMarketLoop(this.parsed)
        };
    }
    baseSummary() {
        return `${this.parsed.channels.join("、")}订单自动进入统一系统，减少漏单和定制蛋糕确认错误。`;
    }
}
export function createBakeryDemoRuntime() {
    return new BrowserProjectRuntime(bakeryTranscript);
}
function parseConversation(transcript) {
    const lower = transcript.toLowerCase();
    const teamSize = matchNumber(transcript, /(\d+)\s+staff/);
    const storeCount = matchNumber(transcript, /(\d+)\s+stores?/);
    const businessType = lower.includes("bakery") ? "面包店" : "门店";
    const clientName = transcript.includes("Mr. Chen") ? "陈先生" : "客户";
    const dailyVolume = lower.includes("80-120") ? "80-120 单 / 天，周末 200" : undefined;
    const budget = transcript.includes("30,000-50,000") ? "30,000-50,000 NTD / 月" : undefined;
    const channels = ["LINE", "WhatsApp", "电话"].filter((channel) => transcript.includes(channel));
    return {
        clientName,
        businessName: "Mr. Chen Bakery",
        businessType,
        teamSize,
        storeCount,
        centralKitchen: lower.includes("central kitchen"),
        channels,
        dailyVolume,
        budget,
        problemSummary: "人工每 15 分钟查看消息并抄入 Excel，导致漏单、错单和定制蛋糕确认出错。",
        successSummary: "订单自动进入系统，厨房知道该做什么，定制蛋糕自动确认价格和取货时间。",
        simplicityConstraint: "员工不是技术人员，交付必须简单。"
    };
}
function matchNumber(text, regex) {
    const match = text.match(regex);
    return match ? Number(match[1]) : undefined;
}
function deriveStage(flags) {
    if (!flags.scopeApproved)
        return "planning";
    if (!flags.materialsGranted)
        return "product";
    if (!flags.buildCompleted)
        return "building";
    if (!flags.testingPassed)
        return "testing";
    if (!flags.feedbackReceived)
        return "feedback";
    return "iteration";
}
function buildSummary(parsed, stage) {
    const positionMap = {
        planning: ["当前阶段", "方案定界", "唐僧正在锁定首单范围", "☉", "green", 24],
        product: ["当前阶段", "产品定型", "八戒已接棒，猴哥仍在等真实材料", "◈", "gold", 42],
        building: ["当前阶段", "工程生产", "猴哥已拿到样本和权限，开始真实接入", "⚙", "green", 62],
        testing: ["当前阶段", "质量门禁", "沙僧正在验证接单与自动确认准确率", "◌", "blue", 78],
        feedback: ["当前阶段", "客户回流", "白龙马在把实际反馈回传给唐僧", "✉", "blue", 88],
        iteration: ["当前阶段", "下一轮规划", "唐僧在根据反馈决定下一批次", "✦", "gold", 96]
    };
    const current = positionMap[stage];
    return [
        { label: "当前批次", value: "B07", note: `${parsed.clientName}${parsed.businessType}首单`, icon: "◈", tone: "gold", meter: 32 },
        { label: current[0], value: current[1], note: current[2], icon: current[3], tone: current[4], meter: current[5] },
        {
            label: "任务位置",
            value: positionValue(stage),
            note: "这是一单短周期小场景交付，不是长期运营项目",
            icon: "⇄",
            tone: "blue",
            meter: stageMeter(stage)
        },
        {
            label: "最关键判断",
            value: "首单不接 POS",
            note: "先把统一接单和自动确认跑通，再谈整合",
            icon: "✦",
            tone: "red",
            meter: 74
        }
    ];
}
function positionValue(stage) {
    return {
        planning: "第 2 / 7 阶段",
        product: "第 3 / 7 阶段",
        building: "第 4 / 7 阶段",
        testing: "第 5 / 7 阶段",
        feedback: "第 6 / 7 阶段",
        iteration: "第 7 / 7 阶段"
    }[stage];
}
function stageMeter(stage) {
    return {
        planning: 29,
        product: 43,
        building: 58,
        testing: 74,
        feedback: 87,
        iteration: 100
    }[stage];
}
function buildDecisions(approvals, materialsGranted) {
    const decisions = [];
    if (!approvals.scope) {
        decisions.push({
            id: "d1",
            from: "唐僧",
            title: "是否接受首单不接 POS",
            detail: "先把多渠道订单自动入台和定制蛋糕自动确认交出来，再谈后续系统整合。",
            impact: "这会直接决定首单能不能保持短周期交付。",
            status: "pending"
        });
    }
    if (!materialsGranted) {
        decisions.push({
            id: "d2",
            from: "白龙马",
            title: "是否允许我直接追样本和权限",
            detail: "我只追三样关键材料：样本 Excel、真实消息样本和定制蛋糕确认规则。",
            impact: "这会显著减少猴哥空等时间。",
            status: approvals.outreach ? "approved" : "pending"
        });
    }
    return decisions;
}
function buildAgents(parsed, stage, approvals, materialsGranted, buildCompleted, testingPassed) {
    const tangsengStatus = stage === "iteration" ? "orchestrating" : "active";
    return [
        {
            id: "tangseng",
            name: "唐僧",
            role: "Leader / Coordinator",
            model: "4.5",
            temperament: "温和坚定，目标清晰",
            status: tangsengStatus,
            progress: approvals.scope ? 66 : 38,
            load: 76,
            current: `把 ${parsed.clientName}${parsed.businessType} 的需求压成最小可交付范围。`,
            blocker: approvals.scope ? "当前主要盯住质量与客户反馈，不让范围回弹。" : "等你确认：首单不接 POS，只做统一接单与自动确认。",
            output: "Bakery Automation Brief v1",
            color: "green"
        },
        {
            id: "bajie",
            name: "八戒",
            role: "Product / Ideas / Comms",
            model: "Claude Sonnet",
            temperament: "有品位，点子多，会沟通",
            status: stage === "planning" ? "thinking" : buildCompleted ? "done" : "active",
            progress: stage === "planning" ? 30 : buildCompleted ? 92 : 68,
            load: 64,
            current: "把统一订单台、定制蛋糕自动确认和厨房视图收成好用方案。",
            blocker: approvals.scope ? "没有真正阻塞，正在把细节压成猴哥可执行输入。" : "需要唐僧先冻结范围。",
            output: "Unified Order Desk Proposal",
            color: "gold"
        },
        {
            id: "houge",
            name: "猴哥",
            role: "Core Builder",
            model: "4.7",
            temperament: "最能打，最直接",
            status: !materialsGranted ? "waiting" : buildCompleted ? "done" : "active",
            progress: !materialsGranted ? 14 : buildCompleted ? 88 : 57,
            load: materialsGranted ? 82 : 39,
            current: materialsGranted
                ? `已开始把 ${parsed.channels.join(" / ")} 订单接入统一工作台。`
                : "等待真实样本和渠道权限，再决定接入层和字段映射。",
            blocker: materialsGranted ? "当前没有阻塞，重点在真实消息结构和定制蛋糕字段。" : "没有真实样本前，先写接入层很容易返工。",
            output: "Technical Intake Plan",
            color: "red"
        },
        {
            id: "shaseng",
            name: "沙僧",
            role: "QA & Eval",
            model: "Codex",
            temperament: "认真，耐劳，持续复核",
            status: !buildCompleted ? "queued" : testingPassed ? "done" : "active",
            progress: !buildCompleted ? 24 : testingPassed ? 90 : 58,
            load: 46,
            current: "盯错单、漏单、定制蛋糕图片和特殊说明的边界样本。",
            blocker: buildCompleted ? "第一版已经到位，正在收口风险清单。" : "等猴哥出第一版后再开评测。",
            output: "Order Accuracy Eval Plan",
            color: "blue"
        },
        {
            id: "bailongma",
            name: "白龙马",
            role: "Customer Value",
            model: "Claude Sonnet",
            temperament: "细心可靠，服务感强",
            status: !approvals.outreach ? "listening" : materialsGranted && !testingPassed ? "active" : feedbackReceivedForStage(stage) ? "active" : "listening",
            progress: !approvals.outreach ? 22 : materialsGranted ? 74 : 44,
            load: 57,
            current: approvals.outreach
                ? "持续追踪客户材料、员工可用性和交付后的真实反馈。"
                : "等待你允许我直接去追样本、账号权限和确认规则。",
            blocker: approvals.outreach ? "没有硬阻塞，当前重点是反馈回传速度。" : "是否可以直接找客户要材料还没有被批准。",
            output: "Client Discovery Brief",
            color: "silver"
        }
    ];
}
function feedbackReceivedForStage(stage) {
    return stage === "feedback" || stage === "iteration";
}
function buildJourney(parsed, stage) {
    const currentKey = stage === "planning"
        ? "tangseng_planning"
        : stage === "product"
            ? "bajie_ideating"
            : stage === "building"
                ? "houge_building"
                : stage === "testing"
                    ? "shaseng_testing"
                    : stage === "feedback"
                        ? "bailongma_collecting_feedback"
                        : "tangseng_planning";
    const order = [
        {
            key: "conversation_received",
            title: "需求进线",
            owner: "唐僧",
            signal: "已整理",
            icon: "◎",
            description: `把 ${parsed.clientName} 的访谈和痛点转成可执行任务。`
        },
        {
            key: "tangseng_planning",
            title: "方案定界",
            owner: "唐僧",
            signal: "正在收口",
            icon: "✦",
            description: "先只做统一接单、自动确认和厨房可读，不碰 POS。"
        },
        {
            key: "bajie_ideating",
            title: "产品定型",
            owner: "八戒",
            signal: "下一棒",
            icon: "◈",
            description: "把方案压成客户能懂、猴哥能做的产品规格。"
        },
        {
            key: "houge_building",
            title: "工程生产",
            owner: "猴哥",
            signal: "工作中",
            icon: "⚙",
            description: `把 ${parsed.channels.join(" / ")} 订单自动接到统一工作台。`
        },
        {
            key: "shaseng_testing",
            title: "质量门禁",
            owner: "沙僧",
            signal: "待验证",
            icon: "◌",
            description: "验证漏单、错单和定制蛋糕确认准确率。"
        },
        {
            key: "bailongma_collecting_feedback",
            title: "客户回流",
            owner: "白龙马",
            signal: "回传中",
            icon: "✉",
            description: "把客户使用和采用反馈回传给唐僧。"
        }
    ];
    const currentIndex = order.findIndex((item) => item.key === currentKey);
    return {
        mode: "快速交付模式",
        demandType: "Founder Demand",
        demand: `${parsed.clientName}${parsed.businessType}需要把 ${parsed.channels.join("、")} 订单自动录入系统`,
        narrative: `团队规模 ${parsed.teamSize ?? "未知"} 人，${parsed.storeCount ?? "多"} 家门店${parsed.centralKitchen ? "，带中央厨房" : ""}。这是典型的短周期 agent 交付任务。`,
        position: positionValue(stage),
        positionNote: stage === "planning"
            ? "还在 founder 对齐和范围收口阶段。"
            : stage === "product"
                ? "产品规格基本成形，但工程仍在等真实材料。"
                : stage === "building"
                    ? "已经进入真实生产，不再只是讨论方案。"
                    : stage === "testing"
                        ? "交付前最后一关是准确率和边界样本。"
                        : stage === "feedback"
                            ? "工具已经可用，重点转到客户采用与价值反馈。"
                            : "第一轮闭环已形成，唐僧正在准备下一批次。",
        states: order.map((item, index) => ({
            ...item,
            status: index < currentIndex ? "done" : index === currentIndex ? "current" : index === currentIndex + 1 ? "next" : "future"
        }))
    };
}
function buildOutcome(parsed, testingPassed, feedbackReceived) {
    return {
        health: feedbackReceived ? "已形成闭环" : testingPassed ? "待客户回流" : "方案中",
        type: "SME Agent Pilot",
        title: "多渠道订单自动录入 MVP",
        summary: `目标是在 ${parsed.budget ?? "可接受预算"} 内，把 ${parsed.channels.join("、")} 订单自动进入统一系统，让厨房知道该做什么，并把定制蛋糕确认自动化。`,
        points: [
            `${parsed.storeCount ?? "多"} 家门店${parsed.centralKitchen ? " + 中央厨房" : ""}，${parsed.teamSize ?? "未知"} 名员工`,
            parsed.problemSummary,
            parsed.successSummary
        ]
    };
}
function buildDeliveries(parsed, stage) {
    const built = stage === "testing" || stage === "feedback" || stage === "iteration";
    const released = stage === "feedback" || stage === "iteration";
    return [
        {
            title: "统一订单收件台",
            status: built ? (released ? "ready" : "draft") : "draft",
            owner: "猴哥",
            summary: `${parsed.channels.join("、")} 订单汇到同一个工作台。`,
            result: built ? "第一版已能承接真实订单样本。" : "当前仍在等待真实样本和权限。"
        },
        {
            title: "定制蛋糕自动确认",
            status: built ? "draft" : "queued",
            owner: "八戒 / 猴哥",
            summary: "自动整理图片、特殊说明、价格和取货时间。",
            result: built ? "已完成首轮确认流设计。" : "仍在把确认规则压成可执行字段。"
        },
        {
            title: "厨房可读清单",
            status: released ? "ready" : "queued",
            owner: "猴哥 / 沙僧",
            summary: "让厨房不再只看早晚两次 Excel。",
            result: released ? "已纳入交付包。" : "排在统一订单台稳定之后。"
        }
    ];
}
function buildFeedbackScenario(parsed, materialsGranted, feedbackReceived) {
    return {
        sentiment: feedbackReceived ? "positive" : "neutral-positive",
        summaryText: feedbackReceived
            ? "客户已经看到价值，最关心的是别再漏掉消息和把定制蛋糕确认自动化。"
            : materialsGranted
                ? "客户已经愿意配合推进，团队现在拥有开工所需的样本和权限。"
                : "客户愿意推进，但实现前还缺真实订单样本、账号权限和定制蛋糕规则。",
        recommendation: feedbackReceived
            ? "下一轮继续优化定制蛋糕确认流和员工上手体验。"
            : materialsGranted
                ? "让猴哥继续做真实接入，让沙僧提前准备评测样本。"
                : "先让白龙马追齐样本和权限，再让猴哥开工。",
        evidence: "证据来源：访谈原话、预算约束、订单渠道和门店现场流程",
        followupStatus: feedbackReceived ? "已回传给唐僧" : materialsGranted ? "已拿到关键材料" : "待审批发送",
        followupDraft: feedbackReceived
            ? "我们会把这轮反馈压进下一版，重点继续保持简单和减少定制蛋糕确认时间。"
            : "为了继续往前推，我们只需要订单 Excel、真实对话样本和定制蛋糕确认规则。",
        sources: [
            {
                kind: "meeting_note",
                channel: "访谈转写",
                title: `${parsed.clientName} 访谈记录`,
                detail: parsed.problemSummary
            },
            {
                kind: "customer_message",
                channel: "预算与目标",
                title: "预算与成功定义",
                detail: `${parsed.budget ?? "预算待确认"}；目标是 ${parsed.successSummary}`
            }
        ],
        signals: [
            {
                type: "value_signal",
                sentiment: "positive",
                urgency: "low",
                summary: "客户对自动接单和减少投诉有明确付费意愿。"
            },
            {
                type: "feature_request",
                sentiment: "neutral-positive",
                urgency: "medium",
                summary: "定制蛋糕自动确认是首轮最关键场景。"
            },
            {
                type: materialsGranted ? "adoption_friction" : "bug_risk",
                sentiment: "negative",
                urgency: "medium",
                summary: materialsGranted ? parsed.simplicityConstraint : "没有真实样本前贸然实现会高概率返工。"
            }
        ]
    };
}
function buildOps(stage, materialsGranted, testingPassed, feedbackReceived) {
    return [
        {
            label: "推进稳定度",
            value: stage === "planning" ? "中" : stage === "building" ? "高" : "中高",
            note: stage === "planning" ? "当前主要受 founder 决策影响" : "节拍主要由样本、质量门禁和反馈回流决定",
            icon: "⟠",
            tone: "gold",
            meter: stageMeter(stage)
        },
        {
            label: "当前瓶颈",
            value: !materialsGranted ? "渠道权限" : !testingPassed ? "质量门禁" : !feedbackReceived ? "客户采用反馈" : "下一轮范围选择",
            note: !materialsGranted ? "没有真实样本会卡住工程生产" : "当前主约束已经从方案转到验证与回流",
            icon: "✦",
            tone: "red",
            meter: !materialsGranted ? 82 : 61
        },
        {
            label: "目标良品率",
            value: "95%+",
            note: "接单抽取和自动确认需要接近人工准确率",
            icon: "◌",
            tone: "green",
            meter: testingPassed ? 95 : 72
        }
    ];
}
function buildMarketLoop(parsed) {
    return [
        {
            source: "销售前线",
            title: "价格只要低于再雇一人，就有成交空间",
            effect: `唐僧把首单压在 ${parsed.budget ?? "可接受预算"} 的心智里。`
        },
        {
            source: "客户服务",
            title: "非技术员工不能被复杂系统拖住",
            effect: "八戒和白龙马会持续把交付往极简操作上压。"
        },
        {
            source: "使用场景",
            title: "定制蛋糕是高痛点场景",
            effect: "猴哥和沙僧会优先围绕图片、特殊说明和确认流程做实现与验证。"
        }
    ];
}
