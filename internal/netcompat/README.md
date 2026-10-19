# Windows 7 HTTPS trust

The native Crypt32 chain verifier on the test Win7 SP1 installation blocks
while retrieving missing roots. Changing TLS versions or key exchange does
not fix it. With the same compiler and server, a fresh pure-Go root pool
completes verified TLS 1.3 in under a second.

On Windows 7 / Server 2008 R2 only, clients use a pure-Go certificate pool
containing Mozilla's roots plus certificates installed in Windows' ROOT store.
Certificate signatures, validity periods, chains, and hostnames are checked;
protocol and cipher defaults are preserved. Other platforms use their normal
trust behavior. This does not change the guest machine's certificate stores.

`mozilla-roots.pem` is curl's Mozilla CA extraction dated 2026-09-25:

- Source: <https://curl.se/ca/cacert.pem>
- Published SHA-256: <https://curl.se/ca/cacert.pem.sha256>
- SHA-256: `a41b5d356aea97a529fe27e0f7316d2f9d946d75927476cf9cf1b90637d00505`
- Certificate data license: Mozilla Public License 2.0; see `LICENSE-MPL-2.0.txt`.

Refresh the file from the official extraction, verify its published hash, and
update this provenance when maintaining the legacy build.
