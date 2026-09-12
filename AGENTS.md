# Codex instructions for PSSG/G1T work

These instructions apply to the entire repository.

For Ayesha Switch NSO/main string localization, first read `docs/ayesha-main-localization.md`, `docs/ayesha-internal-strings.md`, and `docs/ayesha-next-session.md`. Preserve the last user-tested 6563 build. Treat offsets, classification counts, and table strides as build-specific observations. Exclude English shared with the Japanese build from additional translation per the recorded user preference; shared English is not proof of internal-only usage. Patch only evidenced display references and report static checks separately from game tests. Do not force a batch size by translating internal identifiers. These documents are the persistent project handoff for later sessions.

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

For G1N or Switch OTF/TTF font work, also read `docs/g1n-to-switch-font-workflow.md` completely. Treat G1N as a bitmap/mapping source, preserve each Switch font as the structural base, distinguish TrueType `glyf` from CFF outlines, apply the recovered legacy-slot mapping to every font actually used by the game, and validate both Unicode Hangul and glyph-slot rendering.

