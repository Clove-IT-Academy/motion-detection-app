# Manual webcam acceptance

Run using `venv/bin/python -m motion_app`. Never store webcam frames as evidence.
Record app/version, OS/hardware, camera model, actual dimensions, lighting,
placement/distance, dependencies, settings, and date. Mark pass/fail/unverified.

- [ ] Grant camera permission to the terminal/host app and launch successfully.
- [ ] Initial baseline produces no alert; preview remains usable in a quiet scene.
- [ ] Near and far visible movement alerts with sensible current-region boxes.
- [ ] Stopped movement returns to quiet after hold time without excessive flicker.
- [ ] Small noise is filtered; assess small/slow movement and record missed cases.
- [ ] Bright/dark scenes have readable text; inspect smaller camera dimensions.
- [ ] `--no-boxes` hides boxes while detection continues.
- [ ] Try threshold/area/hold overrides, including zero hold.
- [ ] Record false alerts for gradual/abrupt lighting changes and camera bump.
- [ ] Quit separately using q, Esc, native close, and Ctrl+C; reopen the camera after each.
- [ ] Busy/unavailable camera and permission denial produce clear errors and cleanup.
- [ ] Disconnect camera where practical; failed reads exit without stale processing.
- [ ] Extended run remains bounded in memory and creates no media files.
- [ ] Measure live loop duration and control responsiveness under recorded conditions.
- [ ] Repeat on every OS claimed as supported; don't infer support from unit tests.

Demo: launch, show a quiet scene, move, stop, observe alert expiry, quit, relaunch.
If reads block or native close fails, record backend/version and treat as an
acceptance failure. Do not claim a live FPS from the synthetic detector benchmark.
