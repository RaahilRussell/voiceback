import SwiftUI
import AVFoundation

/// Live front-camera preview backed by an `AVCaptureVideoPreviewLayer`.
/// Shows a black placeholder until a running session is provided (e.g. in the
/// simulator, where no camera exists).
struct CameraPreviewView: UIViewRepresentable {
    let session: AVCaptureSession?

    func makeUIView(context: Context) -> PreviewUIView {
        let view = PreviewUIView()
        view.backgroundColor = .black
        if let session { view.setSession(session) }
        return view
    }

    func updateUIView(_ uiView: PreviewUIView, context: Context) {
        if let session { uiView.setSession(session) }
    }

    final class PreviewUIView: UIView {
        override class var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }

        private var previewLayer: AVCaptureVideoPreviewLayer {
            // Safe: layerClass guarantees this type.
            layer as! AVCaptureVideoPreviewLayer
        }

        func setSession(_ session: AVCaptureSession) {
            previewLayer.session = session
            previewLayer.videoGravity = .resizeAspectFill
        }
    }
}
