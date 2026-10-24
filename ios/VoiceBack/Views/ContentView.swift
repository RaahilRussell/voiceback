import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = CommunicationViewModel()

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                CameraPreviewView(session: viewModel.session)
                    .frame(height: 360)
                    .clipShape(RoundedRectangle(cornerRadius: 20))

                Text(viewModel.statusMessage)
                    .font(.headline)
                    .multilineTextAlignment(.center)

                controls
            }
            .padding()
            .navigationTitle("VoiceBack")
            .task { await viewModel.prepare() }
        }
    }

    @ViewBuilder private var controls: some View {
        switch viewModel.state {
        case .ready:
            Button("Start silent capture") { Task { await viewModel.record() } }
                .buttonStyle(.borderedProminent)
                .accessibilityHint("Uses the front camera and does not record microphone audio")

        case .recording:
            Button("Stop") { viewModel.stopRecording() }
                .buttonStyle(.bordered)

        case .uploading:
            ProgressView()

        case .result(let response):
            VStack(alignment: .leading, spacing: 8) {
                ApprovalCard(response: response) {
                    viewModel.approve(response)
                }
                Text("\(response.frames) frames · \(String(format: "%.1f", response.inferenceSeconds))s · audio used: \(response.audioUsed ? "yes" : "no")")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Button("Record again") { Task { await viewModel.record() } }
                .buttonStyle(.borderedProminent)

        case .approved(let response):
            VStack(spacing: 8) {
                Text("Approved transcript")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(response.interpretation?.correctedText ?? response.text)
                    .font(.title3)
                Text("Voice synthesis is intentionally not connected yet.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Button("Record again") { Task { await viewModel.record() } }
                .buttonStyle(.borderedProminent)

        case .failed(let message):
            Text(message)
                .foregroundStyle(.red)
                .multilineTextAlignment(.center)
            Button("Retry") { Task { await viewModel.record() } }
                .buttonStyle(.borderedProminent)

        case .needsPermission:
            Text("Enable camera access in Settings to continue.")
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
    }
}
