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
            VStack(spacing: 10) {
                Button("Start live silent stream") { viewModel.startLiveStream() }
                    .buttonStyle(.borderedProminent)
                    .accessibilityHint("Streams front-camera video frames without microphone audio")
                Button("Start silent capture") { Task { await viewModel.record() } }
                    .buttonStyle(.bordered)
                    .accessibilityHint("Uses the front camera and does not record microphone audio")
                Button("Enroll my voice (consent)") { Task { await viewModel.enrollVoice() } }
                    .buttonStyle(.bordered)
                    .accessibilityHint("Records an eight-second voice sample only for Cartesia voice enrollment")
            }

        case .recording:
            Button("Stop") { viewModel.stopRecording() }
                .buttonStyle(.bordered)

        case .uploading:
            ProgressView()

        case .streaming:
            VStack(spacing: 8) {
                ProgressView()
                Text("The current checkpoint emits a final transcript after the utterance; live frame transport is active.")
                    .font(.caption)
                    .multilineTextAlignment(.center)
            }
            Button("Finish live utterance") { viewModel.stopLiveStream() }
                .buttonStyle(.borderedProminent)

        case .enrolling:
            ProgressView("Enrolling consented voice…")
                .accessibilityHint("The microphone is used only for this explicit voice enrollment sample")

        case .result(let response):
            VStack(alignment: .leading, spacing: 8) {
                ApprovalCard(response: response) {
                    viewModel.approve(response)
                }
                if let diagnostics = response.developerDiagnostics {
                    DeveloperDiagnosticsView(diagnostics: diagnostics)
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
                Button("Speak approved sentence") {
                    Task { await viewModel.speakApproved(response) }
                }
                .buttonStyle(.borderedProminent)
                Text("Only the explicitly approved text is sent for synthesis.")
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
