import Foundation

@MainActor
final class CommunicationViewModel: ObservableObject {
    @Published private(set) var status = "Ready for silent speech"

    func startCapture() {
        status = "Capture started — silently mouth a sentence"
    }
}

