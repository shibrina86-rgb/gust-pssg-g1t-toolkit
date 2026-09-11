# Codex instructions for PSSG/G1T work

These instructions apply to the entire repository.

Before changing or packing any PSSG/G1T file:

1. Read `README.md` and `docs/a14-help-case-study.md` completely.
2. Inventory the target Switch PSSG and record its resource names, order, count, size, and SHA-256.
3. Never append a G1T that was not already present in that exact PSSG unless the game reference and a known-good container prove that it belongs there.
4. If the Switch game stores the target G1T as a loose sibling resource, preserve that relative path and patch it as a loose file.
5. For an embedded transplant, require matching resource name, total size, header size, and texture count. Preserve the Switch PSSG byte layout and replace only compatible G1T blocks.
6. Restore the Switch G1T platform field to `0x10` and verify the output inventory after writing.
7. Treat parser round-trip success as structural validation only, not proof of game-loader compatibility.
8. Keep a known-good booting version, produce staged outputs, and report hashes and changed resources for every build.

Do not commit copyrighted game assets, translated texture images, fonts, executables, keys, or user logs to this repository.

