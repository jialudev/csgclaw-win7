"""Read PE metadata/imports without executing the Windows program."""
import hashlib
import json
import struct
import sys
from pathlib import Path


def inspect(path):
    b = Path(path).read_bytes()
    u16 = lambda o: struct.unpack_from('<H', b, o)[0]
    u32 = lambda o: struct.unpack_from('<I', b, o)[0]
    pe = u32(0x3c)
    assert b[pe:pe+4] == b'PE\0\0'
    opt = pe + 24
    bits = 64 if u16(opt) == 0x20b else 32
    dd = opt + (112 if bits == 64 else 96)
    sh = opt + u16(pe + 20)
    sections = []
    for i in range(u16(pe + 6)):
        vs, va, size, raw = struct.unpack_from('<IIII', b, sh+i*40+8)
        sections.append((va, max(vs, size), raw))

    def offset(rva):
        for va, size, raw in sections:
            if va <= rva < va + size:
                return raw + rva - va
        return rva

    def string(rva):
        o = offset(rva)
        return b[o:b.index(b'\0', o)].decode('ascii')

    imports = {}
    pos = offset(u32(dd + 8))
    while u32(pos) or u32(pos+12) or u32(pos+16):
        lookup, _, _, name, iat = struct.unpack_from('<IIIII', b, pos)
        dll = string(name)
        cursor = offset(lookup or iat)
        symbols = []
        while True:
            value = struct.unpack_from('<Q' if bits == 64 else '<I', b, cursor)[0]
            if not value:
                break
            if value & (1 << (bits-1)):
                symbols.append('#' + str(value & 0xffff))
            else:
                symbols.append(string(value+2))
            cursor += bits // 8
        imports[dll] = symbols
        pos += 20
    return {'path': str(path), 'bits': bits, 'sha256': hashlib.sha256(b).hexdigest(), 'imports': imports}


# These imports caused the original runtime's loader failure. Dynamic lookups
# are allowed: the compatibility patch handles absent functions at runtime.
UNSUPPORTED_DLLS = {"combase.dll", "bcryptprimitives.dll", "api-ms-win-core-synch-l1-2-0.dll"}
UNSUPPORTED_FUNCTIONS = {
    "FindPackagesByPackageFamily", "GetPackageFamilyName", "GetSystemTimePreciseAsFileTime",
    "CreatePseudoConsole", "ResizePseudoConsole", "ClosePseudoConsole",
    "WaitOnAddress", "WakeByAddressSingle", "WakeByAddressAll", "ProcessPrng",
}

if __name__ == "__main__":
    for path in sys.argv[1:]:
        result = inspect(path)
        if result["bits"] != 64:
            raise SystemExit("Expected a Windows x64 executable")
        failures = []
        for dll, names in result["imports"].items():
            if dll.lower() in UNSUPPORTED_DLLS:
                failures.append(dll)
            failures.extend(dll + "!" + name for name in names if name in UNSUPPORTED_FUNCTIONS)
        if failures:
            raise SystemExit("Unsupported Win7 static imports: " + ", ".join(failures))
        print("PASS: known Win7 loader incompatibilities absent in " + Path(path).name)
