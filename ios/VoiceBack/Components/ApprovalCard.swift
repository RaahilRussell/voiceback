import SwiftUI

struct ApprovalCard: View {
    let transcription: Transcription
    let onApprove: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Original interpretation")
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(transcription.original)
            if let corrected = transcription.corrected {
                Text("Suggested correction")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(corrected).font(.headline)
            }
            Button("Approve and speak", action: onApprove)
                .buttonStyle(.borderedProminent)
        }
        .padding()
        .background(.thinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }
}

