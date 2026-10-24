import AVFoundation

final class CameraCaptureService {
    let session = AVCaptureSession()

    // Intentionally configures video only. No microphone input belongs in this service.
    func configure() throws {
        session.beginConfiguration()
        defer { session.commitConfiguration() }
        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) else {
            throw NSError(domain: "VoiceBack.Camera", code: 1)
        }
        let input = try AVCaptureDeviceInput(device: camera)
        guard session.canAddInput(input) else { throw NSError(domain: "VoiceBack.Camera", code: 2) }
        session.addInput(input)
    }
}

