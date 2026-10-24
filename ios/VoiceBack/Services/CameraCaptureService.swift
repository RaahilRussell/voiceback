import AVFoundation

enum CameraCaptureError: LocalizedError {
    case unavailableCamera
    case cannotAddInput
    case cannotAddOutput
    case recordingFailed(String)

    var errorDescription: String? {
        switch self {
        case .unavailableCamera: return "No front camera is available."
        case .cannotAddInput: return "The camera input could not be added."
        case .cannotAddOutput: return "The video output could not be added."
        case .recordingFailed(let reason): return "Recording failed: \(reason)"
        }
    }
}

/// Configures a front-camera, video-only capture session and records a short
/// silent clip. There is intentionally no microphone input anywhere here, and
/// no `AVAudioSession` is ever touched.
final class CameraCaptureService: NSObject, AVCaptureFileOutputRecordingDelegate, @unchecked Sendable {
    let session = AVCaptureSession()
    private let movieOutput = AVCaptureMovieFileOutput()
    private let sessionQueue = DispatchQueue(label: "VoiceBack.CameraSession")
    private var recordingContinuation: CheckedContinuation<URL, Error>?

    /// Requests camera permission only — never microphone.
    func requestAccess() async -> Bool {
        await withCheckedContinuation { continuation in
            AVCaptureDevice.requestAccess(for: .video) { granted in
                continuation.resume(returning: granted)
            }
        }
    }

    func configure() throws {
        session.beginConfiguration()
        defer { session.commitConfiguration() }
        session.sessionPreset = .high
        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) else {
            throw CameraCaptureError.unavailableCamera
        }
        let input = try AVCaptureDeviceInput(device: camera)
        guard session.canAddInput(input) else { throw CameraCaptureError.cannotAddInput }
        session.addInput(input)
        guard session.canAddOutput(movieOutput) else { throw CameraCaptureError.cannotAddOutput }
        session.addOutput(movieOutput)
    }

    func startRunning() {
        sessionQueue.async { [weak self] in
            guard let self, !self.session.isRunning else { return }
            self.session.startRunning()
        }
    }

    func stopRunning() {
        sessionQueue.async { [weak self] in
            guard let self, self.session.isRunning else { return }
            self.session.stopRunning()
        }
    }

    /// Records a bounded silent clip and returns the written file URL.
    func recordClip(maxDuration: TimeInterval = 5) async throws -> URL {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("mov")
        movieOutput.maxRecordedDuration = CMTime(seconds: maxDuration, preferredTimescale: 600)
        return try await withCheckedThrowingContinuation { continuation in
            recordingContinuation = continuation
            movieOutput.startRecording(to: url, recordingDelegate: self)
        }
    }

    func stopRecording() {
        if movieOutput.isRecording { movieOutput.stopRecording() }
    }

    // MARK: AVCaptureFileOutputRecordingDelegate

    func fileOutput(
        _ output: AVCaptureFileOutput,
        didFinishRecordingTo outputFileURL: URL,
        from connections: [AVCaptureConnection],
        error: Error?
    ) {
        let continuation = recordingContinuation
        recordingContinuation = nil
        // Hitting maxRecordedDuration reports an error whose success flag is true.
        if let error = error as NSError?,
           (error.userInfo[AVErrorRecordingSuccessfullyFinishedKey] as? Bool) != true {
            continuation?.resume(throwing: CameraCaptureError.recordingFailed(error.localizedDescription))
            return
        }
        continuation?.resume(returning: outputFileURL)
    }
}
