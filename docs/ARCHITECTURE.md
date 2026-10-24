# Architecture

The iOS client captures front-camera video only, performs face tracking and head gesture detection locally, and sends normalized video or frames to the backend inference boundary. The backend produces candidate text, Gemini resolves context-dependent ambiguity, and the clarification engine requests a yes/no response when confidence is insufficient. Cartesia is called only after explicit approval and consent checks.

