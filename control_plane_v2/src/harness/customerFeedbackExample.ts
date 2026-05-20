import { collectCustomerFeedback, type CustomerFeedbackSource } from "./customerFeedback.js";

const sources: CustomerFeedbackSource[] = [
  {
    id: "msg_001",
    kind: "customer_message",
    title: "Ops manager reply after prototype review",
    capturedAt: new Date().toISOString(),
    channel: "wechat",
    customerContact: "ops_manager",
    text: "The remediation queue is useful, but the first screen is still a little confusing for store managers."
  },
  {
    id: "usage_001",
    kind: "usage_metric",
    title: "Prototype usage snapshot",
    capturedAt: new Date().toISOString(),
    channel: "prototype_analytics",
    metrics: {
      activeUsers: 3,
      completedTasks: 12
    }
  }
];

const result = collectCustomerFeedback({
  engagementId: "eng_001",
  sources,
  openQuestions: ["Which role should own overdue task escalation?"],
  customerRespondedWithinSla: true
});

console.log(JSON.stringify(result, null, 2));
