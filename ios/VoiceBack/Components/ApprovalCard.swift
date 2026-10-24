import Foundation
import SwiftUI

struct ApprovalCard: View {
    let response: TranscriptionResponse
    let onApprove: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Original Auto-AVSR transcript")
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(response.text)
            if let interpretation = response.interpretation {
                Text("Suggested correction")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(interpretation.correctedText).font(.headline)
                let confidenceText = String(format: "%.0f%%", interpretation.confidence * 100)
                Text("Gemini confidence: \(confidenceText)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                ForEach(interpretation.wordChecks, id: \.observedWord) { check in
                    let wordConfidence = String(format: "%.0f%%", check.confidence * 100)
                    Text("Check ‘\(check.observedWord)’: \(wordConfidence) — \(check.alternatives.joined(separator: ", "))")
                        .font(.caption)
                        .foregroundStyle(.orange)
                }
                if let question = interpretation.clarificationQuestion {
                    Text(question)
                        .font(.subheadline)
                }
                Button("Approve for speech", action: onApprove)
                    .buttonStyle(.borderedProminent)
                    .disabled(interpretation.needsClarification)
                    .accessibilityHint("Approval is required before any voice synthesis can run")
            } else {
                Text("Gemini correction is unavailable. The original transcript remains unchanged.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.thinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }
}

