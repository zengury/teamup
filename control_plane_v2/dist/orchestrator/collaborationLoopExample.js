import { buildIterationPlan, describeRoleToolkits } from "./collaborationLoop.js";
const plan = buildIterationPlan({
    iteration: 1,
    goal: "Ship a usable SME agent workflow pilot, learn from customer usage, then plan the next increment."
});
console.log(JSON.stringify({
    plan,
    toolkits: describeRoleToolkits()
}, null, 2));
