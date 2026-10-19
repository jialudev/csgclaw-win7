# Bundled Codex for Windows 7

The upstream Windows Codex executable imports Windows 8/10 APIs and cannot
start on Windows 7. Build the private runtime from these fixed sources:

- OpenAI Codex `2685e3a4cec1cf6ec8df5231bf2311ff7ae9551f`
  (`0.130.0-alpha.5`), Apache-2.0.
- Compatibility patch and delay-load hook from
  [codex-win7-port](https://github.com/HaiKuoTianKong179/codex-win7-port/tree/31899c3041c5934c027da052d41797dac76d7eaf),
  commit `31899c3041c5934c027da052d41797dac76d7eaf`, Apache-2.0 as
  stated in that project's README. The patch is rebased onto the documented
  baseline, including its windows-sys 0.52 integer handle types;
  `prepare.py` replaces the original developer-specific paths during the build.
- Rust `1.95.0`, `x86_64-win7-windows-msvc`, static CRT and rebuilt std.
- [winpty 0.4.3](https://github.com/rprichard/winpty/releases/tag/0.4.3), MIT;
  official `winpty-0.4.3-msvc2015.zip` SHA-256
  `35a48ece2ff4acdcbc8299d4920de53eb86b1fb41e64d2fe5ae7898931bcee89`.

CI caches the built runtime by these build inputs, checks static imports,
and tests the same stdio app-server initialization used by CSGClaw. The
runtime archive includes the upstream licenses and source metadata.
Windows runner checks must still be followed by a real Windows 7 test.
No sandbox or certificate-validation settings are weakened by these scripts.
