# Persona Engine v10 Sensory and Semi-Embodiment Notes

v10 adds mockable sensory and embodiment plumbing while preserving the doctrine from v8 and v9.

## Invariants

The interface displays organism state. It does not author organism state.

Sensors report bounded observations. They do not infer feelings, motives, trust, hostility, or character belief.

The world authority owns objective world facts. Audio, vision, simulator, UI, and host events enter the organism through `WorldAuthority` or the existing server-truth path.

The organism interprets facts. `InterpretationEngine` receives visible facts and forms grounded subjective beliefs.

Voice and avatar perform state. `VoicePlanner` receives finished text plus an expression envelope. `AvatarProjector` receives public status only.

Renderer output is not canonical truth.

## PC and mobile readiness

The core ships no microphone, camera, TTS, avatar, network, or GPU dependency. Hosts attach adapters.

PC hosts can subclass `MicrophoneAdapter`, `CameraAdapter`, `TTSAdapter`, and `AvatarEngineAdapter` using whatever desktop libraries they prefer.

Mobile hosts can feed the same dataclasses from native iOS or Android code through an HTTP, local socket, FFI, or bridge layer.

The deterministic core remains testable with `MockAudioSensor`, `MockVisionSensor`, `MockTTSAdapter`, and `MockAvatarEngine`.

## C99 port guidance

Do not port microphone, camera, TTS, avatar, network, or GPU code into the C99 core.

Port only typed event structs and reducers:

- `audio_observation_t`
- `vision_observation_t`
- `world_fact_t`
- `world_authority_apply_sensor_event`
- `voice_plan_t`
- `avatar_state_t`

Platform hosts should provide sensor observations and consume voice/avatar plans.

Keep all character-specific sensory, voice, and avatar parameters in the cartridge. Engine modules must remain character-agnostic.
