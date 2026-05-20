import { roleHarnessSpecs } from "./roleHarnessSpecs.js";

console.log(JSON.stringify({
  tangseng: {
    inputGate: roleHarnessSpecs.tangseng.inputGate,
    outputGate: roleHarnessSpecs.tangseng.outputGate,
    trustGate: roleHarnessSpecs.tangseng.trustGate,
    failureRouting: roleHarnessSpecs.tangseng.failureRouting
  },
  bajie: {
    inputGate: roleHarnessSpecs.bajie.inputGate,
    outputGate: roleHarnessSpecs.bajie.outputGate,
    trustGate: roleHarnessSpecs.bajie.trustGate,
    crossChecks: roleHarnessSpecs.bajie.crossChecks,
    failureRouting: roleHarnessSpecs.bajie.failureRouting
  },
  houge: {
    inputGate: roleHarnessSpecs.houge.inputGate,
    outputGate: roleHarnessSpecs.houge.outputGate,
    trustGate: roleHarnessSpecs.houge.trustGate,
    crossChecks: roleHarnessSpecs.houge.crossChecks,
    failureRouting: roleHarnessSpecs.houge.failureRouting
  },
  shaseng: {
    inputGate: roleHarnessSpecs.shaseng.inputGate,
    outputGate: roleHarnessSpecs.shaseng.outputGate,
    trustGate: roleHarnessSpecs.shaseng.trustGate,
    crossChecks: roleHarnessSpecs.shaseng.crossChecks,
    failureRouting: roleHarnessSpecs.shaseng.failureRouting
  },
  bailongma: {
    inputGate: roleHarnessSpecs.bailongma.inputGate,
    outputGate: roleHarnessSpecs.bailongma.outputGate,
    trustGate: roleHarnessSpecs.bailongma.trustGate,
    crossChecks: roleHarnessSpecs.bailongma.crossChecks,
    failureRouting: roleHarnessSpecs.bailongma.failureRouting
  }
}, null, 2));
