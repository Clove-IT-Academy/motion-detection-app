# Release checklist

Candidate: 0.1.0. Source distribution; no executable packaging or release tag yet.

- [x] Source modules, entry point, configuration, and meaningful comments supplied.
- [x] Exact tested dependencies and venv installation instructions supplied.
- [x] Synthetic detection, timing, frame validation, lifecycle, and display tests pass.
- [x] Native synthetic preview opens and cleans up on Cocoa.
- [ ] Complete real-camera manual checks and calibration.
- [ ] Verify camera reuse after normal/failed runs and each native quit control.
- [ ] Record live responsiveness and supported camera/platform combinations.
- [ ] Another student follows the setup and demo instructions successfully.
- [ ] Assign maintenance owner.
- [ ] Review final accepted revision and create a versioned release when requested.

Keep camera content out of reports and source control. Dependency updates require
regression tests and native camera/window checks. No broader platform support or
packaged-executable support is claimed by this candidate.
