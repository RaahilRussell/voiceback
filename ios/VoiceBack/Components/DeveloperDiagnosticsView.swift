import SwiftUI

struct DeveloperDiagnosticsView: View {
    let diagnostics: DeveloperDiagnostics

    var body: some View {
        DisclosureGroup("Developer diagnostics") {
            VStack(alignment: .leading, spacing: 10) {
                if let fusion = diagnostics.fusion {
                    Text("Fusion: \(fusion.enabled ? "ON" : "OFF") · λ = \(String(format: "%.3f", fusion.weight))")
                        .font(.caption.bold())
                    Text(fusion.scoreFormula).font(.caption2).foregroundStyle(.secondary)
                    if let modelName = fusion.modelName {
                        Text("LM: \(modelName)").font(.caption2)
                    }
                }
                Text("Visual beam candidates").font(.caption.bold())
                ForEach(diagnostics.visualCandidates ?? []) { candidate in
                    Text("\(candidate.text) · raw \(candidate.rawScore.map { String(format: "%.3f", $0) } ?? "n/a")")
                        .font(.caption2)
                }
                Text("Next-token LM scores").font(.caption.bold())
                if let trace = diagnostics.languageModelTrace, !trace.isEmpty {
                    ForEach(trace.prefix(60)) { item in
                        Text("prefix ‘\(item.prefix)’ → ‘\(item.candidateText)’ · logP \(String(format: "%.3f", item.lmLogProbability)) · P \(String(format: "%.4f", item.lmProbability))")
                            .font(.caption2)
                    }
                } else {
                    Text("LM did not run for this request (λ = 0 or no scorer configured).")
                        .font(.caption2).foregroundStyle(.secondary)
                }
                Text("Gemini interaction").font(.caption.bold())
                if let gemini = diagnostics.gemini {
                    Text("available: \(gemini.available.map(String.init) ?? "unknown") · invoked: \(gemini.invoked.map(String.init) ?? "unknown")")
                        .font(.caption2)
                    if let model = gemini.model { Text("model: \(model)").font(.caption2) }
                    if let reason = gemini.reason { Text("status: \(reason)").font(.caption2) }
                    if let prompt = gemini.request?.prompt {
                        Text("Request prompt").font(.caption2.bold())
                        Text(prompt).font(.caption2).textSelection(.enabled)
                    }
                    if let response = gemini.responseText {
                        Text("Raw response").font(.caption2.bold())
                        Text(response).font(.caption2).textSelection(.enabled)
                    }
                } else {
                    Text("No Gemini diagnostic was returned.").font(.caption2).foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding()
        .background(.thinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    }
}
