# Windows 7 runtime compatibility

The Win7 desktop build is based on CSGClaw v0.8.0 and targets Windows 7 SP1 x64.
It uses Electron 22.3.27, Chromium 108 assets, and XTLS/go-win7 patched-1.26.7.
Desktop automatic updates remain disabled.

## HTTPS handshake timeouts

On the UTM test VM, DNS resolution and TCP port 443 worked. Requests with Go's
native Windows certificate verifier timed out, including with TLS 1.2 and with
ML-KEM disabled. The same endpoints immediately returned HTTP 200 with a fresh
PEM-backed root pool. The delay is in Win7 Crypt32 chain/root retrieval rather
than protocol negotiation or a missing network connection.

`internal/netcompat` enables a fresh certificate pool only on Windows 6.1
(Win7 / Server 2008 R2). It combines the bundled Mozilla roots with certificates
from the Windows ROOT store. It deliberately avoids `SystemCertPool`, whose
Windows flag delegates verification back to Crypt32. Server certificates and
hostnames are still checked; no `InsecureSkipVerify` or OS trust-store changes
are used. Both HTTP clients and the model Responses WebSocket transport use it.

The root bundle's source, date, checksum and MPL-2.0 license are recorded in
`internal/netcompat/README.md`. Refresh the bundle as part of future releases.

## Codex loader failure

The previous bundled Codex exited with decimal `3221225785` / `0xC0000139`
(`STATUS_ENTRYPOINT_NOT_FOUND`) before app-server initialization. Its PE imports
included Win8/10-only package APIs, `ResizePseudoConsole`, `WaitOnAddress`,
`combase.dll` and `bcryptprimitives.dll`.

The compatibility runtime is built from OpenAI Codex commit
`2685e3a4cec1cf6ec8df5231bf2311ff7ae9551f` with the audited, rebased patch from
HaiKuoTianKong179/codex-win7-port. The exact inputs and licenses are documented
in [the build scripts](../../scripts/win7-codex/README.md). The upstream source
commit reports `codex-cli 0.0.0`; this is a development build, not a published
OpenAI release with that version number. Packaged metadata records the actual
reported version, source commit and binary SHA-256.

The patch uses dynamic lookups for unsupported APIs, a delay-load compatibility
hook, static CRT, Rust's Win7 target, and winpty 0.4.3. On Windows 6.1 CSGClaw
also disables Codex `code_mode` and `code_mode_host`, whose modern Node/V8 hosts
cannot run on Win7. Existing sandbox permissions and approval settings are kept.
Native shell execution, sandbox isolation, browser automation and unrelated
plugins require separate validation; a successful chat is not proof of those
capabilities.

## Build and verification

The fork's `fix/win7-tls-codex` branch and `main` build in GitHub Actions. Pushing
any semantic-version tag builds a portable ZIP and publishes it, its checksum,
and build metadata to that repository's Releases. Tags with prerelease versions
create GitHub prereleases. Feature branch tags need not be merged into `main`.

CI builds and caches the pinned Codex runtime. Tag builds may reuse a successful
runtime artifact from this repository only when its complete `scripts/win7-codex`
Git tree matches. The artifact must pass checksum, source/toolchain, patch-hash,
import and protocol checks again; expired artifacts or changed inputs trigger a
fresh source build. CI rejects the known incompatible
static imports, and checks CSGClaw's stdio app-server `initialize` request. The
portable job bundles Codex, winpty, their licenses, the actual Web UI and the
backend. Windows Server CI does not replace a real Win7 test.

The Win7 VM retains its existing model/login configuration under
`%USERPROFILE%\.csgclaw`. Updating application files does not require copying
credentials into the release ZIP. Keep the previous application folder as a rollback copy.

## VM regression procedure

Build the existing Go integration test with the pinned Win7 Go toolchain:

```bash
GOWORK=off GOOS=windows GOARCH=amd64 CGO_ENABLED=0 \
  go test -c -o win7-codex-e2e.exe ./internal/runtime/codex
```

In the Win7 guest, point `CSGCLAW_TEST_CODEX_BINARY` to the bundled executable
and run `win7-codex-e2e.exe -test.run=^TestAgentMCPBundledCodexE2E/full_tools$ -test.v`.
On slow emulation, set `CSGCLAW_TEST_CODEX_TIMEOUT=3m` and pass
`-test.timeout=4m`. The isolated fixtures disable system-proxy discovery for their
local-only traffic; production Agent proxy settings remain unchanged.

This exercises real Codex turns, local Responses/MCP fixtures, tool-catalog
refresh and cold session recovery. It uses no external credentials or models.
The initial community runtime passed `initialize` but reproduced `0xC06D007E`
at `turn/start` in this test. The revised delay-load hook returns a real module
handle for the three missing API-set DLLs so exact procedure fallbacks can run;
unknown libraries and procedures still fail normally.

The hook also corrects `DeriveCapabilitySidsFromName`: its return type is
[`BOOL`](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-derivecapabilitysidsfromname),
so an `HRESULT` failure value is nonzero and incorrectly signals success.
The typed fallback now returns `FALSE`, clears the output pointers/counts and
sets `ERROR_CALL_NOT_IMPLEMENTED`. Its regression test checks that contract.

## Observed VM results (2026-10-19)

The original installed application was `0.8.0-alpha.win7.2`. With the patched
backend and DLL-compatible runtime in that same UTM Win7 SP1 x64 guest:

- Chat Completions returned HTTP 200 and `WIN7_TLS_OK`.
- Streaming Responses returned HTTP 200, completed normally and emitted
  `WIN7_RESPONSES_OK`.
- The actual Manager conversation displayed `WIN7_AGENT_FIXED_OK` with
  `succeeded` status. This verifies the full UI/backend/Codex/model reply path.
- Native command-argument tests passed on Win7.
- The isolated full MCP regression passed in 63 seconds: three tool calls,
  live catalog refresh, same-thread continuity and cold recovery succeeded.

The 40-second local MCP fixture initially exceeded its timeout while native
HTTP clients reported proxy-route timeouts. WinHTTP inspection confirmed
automatic proxy detection was enabled, with no explicit proxy or PAC URL.
Fixture isolation and a configurable regression timeout keep this environment
behavior separate from protocol failures. Native shell/browser capabilities
have not been certified by these question-answering checks.
