# Glaze v0.10.1 Chinese upgrade handoff

User explicitly authorized this repository's independent Glaze branch, workflow writes, source checkpoints and APK compilation.

- Upstream stable: v0.10.1, 32def585e23f3d55266484ca8076012549260cf9.
- Previous v0.9.0 Chinese patches are retained unchanged.
- Cumulative new-version patch: checkpoints/Glaze-0.10.1-zh-CN.patch.gz.
- New or revised UI resources: 207 manually translated keys.
- Factory block names and small controls: localization/bundled_manual_zh.json.
- Manually translated common prompt bodies: bundled_core_zh.json, bundled_shino_zh.json, bundled_summary_defaults_zh.json.
- Long bundled texts: bundled_zh.json includes offline machine-assisted reading drafts. They are not fully human-reviewed.
- Localization is an exact-match reading/editing view. Original bundled JSON, database contents and outgoing prompt builder are not rewritten.
- GenericEditor enables the view only in preset editors. Unedited displayed Chinese is mapped back to the original raw field; real user edits are retained. Chinese/original toggle is included.
- Damaged macro translations are rejected. Macro counts and values must match; word order may differ.
- Main build run: https://github.com/c4sfvb4hmz-cyber/RisuNest/actions/runs/43974344089
- Current build: static analysis and focused localization/import/editor regressions passed. Broad Flutter tests are running; no APK success claim yet.
- Fixed prior preflight failures: allow reordered but identical macro multisets; refresh the protected resource contract to official v0.10.1; tolerate a missing EasyLocalization ancestor in standalone preset-editor tests.
- Current code also includes reviewed runtime-adjusted Studio blocks in bundled_studio_zh.json.
- Delivery workflow waits for build 43974344089 to succeed, then preserves the verified APK under releases/ for direct download.
- Real-device installation and live API generation remain untested.
- APK uses a test signature. The previous run did not retain its signing key, so direct replacement of the old APK is not guaranteed.

Continue from the saved branch/checkpoint; do not reconstruct prior translation work or repeat upstream research.
