import SwiftUI

struct CameraPreviewView: View {
    var body: some View {
        ZStack {
            Color.black
            Text("Front camera preview")
                .foregroundStyle(.white)
        }
        .accessibilityLabel("Front camera preview; microphone audio is not used")
    }
}

