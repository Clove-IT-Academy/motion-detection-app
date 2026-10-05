# Agent instructions: Motion Detection App

## Role and source of truth

- Work as a senior Python developer and AI engineer: make deliberate, reviewable design choices, explain tradeoffs when they affect the product, and keep the implementation approachable for the project's student audience.
- Follow [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md) and [`Motion_Detection_System_Architecture.pdf`](Motion_Detection_System_Architecture.pdf) in this directory. Preserve their v1 scope, module boundaries, contracts, step ordering, milestone exit criteria, and acceptance criteria. If new information requires a change, update the plan/decision log rather than silently diverging.
- Treat unresolved items in the plan's open-decisions section and decision log as open. Proposed defaults are starting points for calibration, not verified optimal settings. Do not claim support for an operating system, camera, Python version, or packaging format until it has been chosen and checked.
- The v1 app is local and single-process. Camera frames remain in memory. Do not add recording, screenshots, uploads, network communication, analytics, accounts, databases, face recognition, or identity inference without new explicit requirements and a privacy/security review.

## Security and privacy

- Consider security part of implementation and review. Identify trust boundaries, inputs, sensitive data, and failure cases for each change. Do not claim that software is completely exploit-proof; use established safeguards and report remaining risks accurately.
- Validate configuration and external/library inputs at boundaries. For frames, check successful capture, non-null data, expected array shape, supported dtype/channel layout, and reasonable dimensions before processing. Reject invalid values with clear, controlled errors; never use unchecked input to index memory, construct paths, or trigger shell commands.
- Keep camera access limited to the feature's needs. No frame pixels, webcam-derived text, credentials, or unnecessary personal data in logs, exceptions shown to users, telemetry, test fixtures, or crash artifacts. Use synthetic/non-sensitive frames for tests and examples.
- Do not add dynamic code execution, unsafe deserialization, shell invocation, or new network endpoints. Avoid unnecessary dependencies; pin and review dependencies as specified by the plan.
- Surface concise, actionable user errors while retaining only useful, non-sensitive diagnostics. Catch exceptions at appropriate boundaries; do not broadly suppress failures or continue with corrupted state.
- Every exit path (normal quit, window close, camera/read failure, handled exception) must release the camera and close display resources. Cleanup should be safe if called more than once and should not mask the original failure.

## Runtime efficiency and reliability

- Keep the preview loop responsive and bounded in memory. Process one current frame at a time; do not accumulate frame histories, unbounded queues, or duplicate full-frame copies without a demonstrated need.
- Avoid blocking waits, busy-spins, needless conversions/copies, repeated allocations, and expensive work in the per-frame path. Prefer OpenCV/NumPy operations suited to image arrays. Measure on chosen target hardware before making performance claims or optimizing beyond evidence.
- Consider time and space complexity for every non-trivial algorithm and data structure. Prefer the simplest approach with suitable asymptotic behavior; document why any costly operation is acceptable in a frame loop. Avoid scaling work with elapsed runtime or retaining memory proportional to the number of frames processed.
- Do not freeze the UI while doing unnecessary work. Keep v1 single-threaded unless profiling or a concrete requirement justifies concurrency; if concurrency is introduced later, bound queues, define ownership of frames/resources, and ensure shutdown joins/cancels workers safely.
- Handle unavailable, busy, or disconnected cameras and failed reads as expected runtime conditions. Never pass a failed frame into the processor or leave the camera/window open after an error.

## Python engineering standards

- Follow the package layout and separation of concerns in the plan: lifecycle in `app.py`, camera I/O in `camera.py`, frame preparation in `preprocessing.py`, consecutive-frame analysis and baseline state in `motion_detector.py`, window/input behavior in `display.py`, safe defaults/validation in `config.py`, and a minimal `main.py` entry point.
- Use clear names, small cohesive functions, type annotations at module boundaries, standard-library facilities where suitable, and docstrings for non-obvious public behavior. Keep dependencies and abstractions proportional to this small app.
- Keep preprocessing and detector frame sequences deterministic and testable without opening a camera or window. Keep alert timing in the controller and inject a monotonic clock for testing. Make mutation/copy behavior explicit; preserve source frames when the caller contract requires it.
- Keep configuration defaults safe and documented. Validate user-editable settings at startup and fail with a useful explanation instead of silently accepting invalid state.
- Use structured, minimal logging for lifecycle and operational failures only. Never add logging of frame contents.
- Use GUI-enabled OpenCV for the desktop runtime; do not install competing OpenCV distributions in the same environment. Keep imports and help output free of camera/window side effects. Select and pin versions only after checking the environment and reproducible installation.
- Update the README and development plan when behavior, controls, setup, dependencies, platform support, privacy behavior, or known limitations change.

## Motion detection behavior

- Preserve the v1 algorithm: grayscale conversion, light blur, absolute difference between consecutive prepared frames, pixel thresholding, morphological cleanup, external contours, and minimum-area filtering. Do not replace it with object recognition or a background model without a documented scope/design change.
- The first valid frame establishes the baseline without triggering motion. Reset the detector baseline and clear held-alert state when frame dimensions change. Advance the previous-frame baseline after each valid comparison, including quiet frames.
- Keep the detector result structured as the plan specifies: motion flag, current bounding boxes, and baseline/reset indication. The detector must not open a camera, create a window, or manage displayed alert timing.
- Keep raw detection separate from the displayed alert. Use a monotonic clock for the configured hold duration; refresh it on qualifying motion and expire it at the documented boundary. Zero hold means no persistence. Test timing with a fake clock instead of sleeps.
- Render overlays on a display copy; never compare annotated images. Draw only current-frame boxes, even when the status message remains held after motion stops. Disabling boxes must not change detection.
- Show readable `Motion detected!` and `No motion detected` text with sufficient contrast and documented exit controls. Verify `q`, `Esc`, and native window close on each claimed platform; do not recreate a window after it is closed.
- Validate threshold ranges, positive region areas, odd kernel dimensions, and finite nonnegative timing values. Preserve the plan's threshold and area boundary semantics in tests. Pixel-area sensitivity depends on actual frame resolution; document calibration and do not silently resize frames.
- Explain that stopped objects cease triggering raw detection once adjacent frames stabilize, and that lighting changes and camera shake can trigger alerts. Do not claim detection of every movement or suppress global changes without evidence and an explicit design decision.

## Tests, verification, and changes

- Implement tests at the levels called for by the development plan: synthetic-frame unit tests for preprocessing and detection, fake-clock tests for alert timing, fake-camera/component tests for application flow and cleanup, and manual camera checks on each supported platform. Do not make automated tests depend on a physical webcam or personal footage.
- Verify the specific behavior changed and report what was or was not checked. Follow the user's request about running verification; do not imply that checks passed when they were not run.
- Keep changes small and inspectable. Before finishing, review the resulting diff for accidental scope expansion, leaked data, resource leaks, invalid-frame paths, and performance regressions.
- Update milestone checkboxes only after their exit checks are complete, and record the tested environment, results, limitations, and next step. Distinguish camera-free automated checks from manual hardware/platform validation.
- Do not weaken acceptance criteria or add features just because they are easy to implement. Ask for clarification only when a real product decision blocks safe, correct progress; otherwise follow documented defaults and record assumptions.
