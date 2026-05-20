import { createBakeryDemoRuntime } from "./browserRuntime.js";

function main() {
  const runtime = createBakeryDemoRuntime();

  const initial = runtime.getSnapshot();
  runtime.approveDecision("d1");
  runtime.approveDecision("d2");
  runtime.injectCustomerMaterials();
  runtime.advance();
  runtime.advance();
  runtime.pushFeedbackBrief();
  const final = runtime.getSnapshot();

  console.log(JSON.stringify({
    initial: {
      stage: initial.summary[1]?.value,
      decisions: initial.decisions.map((item) => item.title)
    },
    final: {
      stage: final.summary[1]?.value,
      threadTail: final.thread.slice(-4),
      deliveries: final.deliveries.map((item) => ({
        title: item.title,
        status: item.status
      }))
    }
  }, null, 2));
}

main();
