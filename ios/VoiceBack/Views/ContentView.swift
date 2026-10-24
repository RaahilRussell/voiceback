import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = CommunicationViewModel()

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                CameraPreviewView()
                    .frame(height: 360)
                    .clipShape(RoundedRectangle(cornerRadius: 20))

                Text(viewModel.status)
                    .font(.headline)
                    .multilineTextAlignment(.center)

                Text("Your interpretation will be shown here before any voice is played.")
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)

                Button("Start silent capture") { viewModel.startCapture() }
                    .buttonStyle(.borderedProminent)
                    .accessibilityHint("Uses the front camera and does not record microphone audio")
            }
            .padding()
            .navigationTitle("VoiceBack")
        }
    }
}

