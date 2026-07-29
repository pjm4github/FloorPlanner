"""Read a Windows minidump's exception + module streams with no debugger.

Written for defect 26 and kept: it is the only way to read a crash on a box
with no cdb/windbg console (the SDK ships only the redistributable DLLs;
WinDbg is the Store GUI app). Usage:

    python tools/read_minidump.py <dump.dmp>

There is no cdb/windbg console on this box (the SDK installed only the
redistributable DLLs; WinDbg is the Store GUI app). But the two things defect 26
needs -- WHICH exception, and WHICH module the faulting instruction is in -- are
in documented streams, so they can be read directly.

Streams used:
  6  ExceptionStream : the exception record (code, address) + faulting thread
  4  ModuleListStream: base/size/name of every loaded module
  3  ThreadListStream: thread stacks, used to sample return addresses

Seeks rather than reads: the dump is ~780 MB.
"""
import struct
import sys

EXC = {0xC0000409: "STATUS_STACK_BUFFER_OVERRUN (__fastfail)",
       0xC0000005: "ACCESS_VIOLATION",
       0x80000003: "BREAKPOINT",
       0xC000001D: "ILLEGAL_INSTRUCTION",
       0xC0000374: "HEAP_CORRUPTION",
       0xE06D7363: "C++ exception (MSC)"}
# winnt.h FAST_FAIL_* -- indices are exact; an off-by-one here mislabels the
# whole diagnosis, which is what happened on the first read of this dump.
FASTFAIL = {0: "LEGACY_GS_VIOLATION", 1: "VTGUARD_CHECK_FAILURE",
            2: "STACK_COOKIE_CHECK_FAILURE", 3: "CORRUPT_LIST_ENTRY",
            4: "INCORRECT_STACK", 5: "INVALID_ARG", 6: "GS_COOKIE_INIT",
            7: "FATAL_APP_EXIT  <-- abort(): a DELIBERATE fatal, not corruption",
            8: "RANGE_CHECK_FAILURE", 9: "UNSAFE_REGISTRY_ACCESS",
            0x1E: "INVALID_THREAD", 0x23: "UNHANDLED_CPP_EXCEPTION"}


def u32(f, off):
    f.seek(off)
    return struct.unpack("<I", f.read(4))[0]


def main(path):
    f = open(path, "rb")
    sig, ver, nstreams, dirrva = struct.unpack("<IIII", f.read(16))
    if sig != 0x504D444D:
        print("not a minidump")
        return 1
    f.seek(dirrva)
    dirs = {}
    for _ in range(nstreams):
        stype, size, rva = struct.unpack("<III", f.read(12))
        dirs[stype] = (size, rva)
    print(f"streams: {sorted(dirs)}")

    # ---- modules first, so the address can be attributed -------------------
    mods = []
    if 4 in dirs:
        _sz, rva = dirs[4]
        f.seek(rva)
        n = struct.unpack("<I", f.read(4))[0]
        raw = f.read(108 * n)
        for i in range(n):
            base, size, _ck, _ts, nrva = struct.unpack_from("<QIIII", raw, 108 * i)
            f.seek(nrva)
            ln = struct.unpack("<I", f.read(4))[0]
            name = f.read(ln).decode("utf-16-le", "replace")
            mods.append((base, size, name))
        mods.sort()
        print(f"modules: {len(mods)}")

    def who(addr):
        for base, size, name in mods:
            if base <= addr < base + size:
                return f"{name.split(chr(92))[-1]}+0x{addr - base:x}"
        return "<unknown module>"

    # ---- the exception -----------------------------------------------------
    if 6 not in dirs:
        print("NO EXCEPTION STREAM -- this dump is not of a fault "
              "(procdump wrote it for another trigger).")
        return 0
    _sz, rva = dirs[6]
    f.seek(rva)
    tid, _al = struct.unpack("<II", f.read(8))
    code, flags, _rec, addr, nparams, _un = struct.unpack("<IIQQII", f.read(32))
    params = struct.unpack("<15Q", f.read(120))
    print("\n=== EXCEPTION ===")
    print(f"  thread id      : {tid}")
    print(f"  code           : 0x{code:08X}  {EXC.get(code, '?')}")
    print(f"  flags          : 0x{flags:08X}")
    print(f"  address        : 0x{addr:016X}  {who(addr)}")
    if code == 0xC0000409 and nparams:
        print(f"  fastfail code  : {params[0]}  "
              f"{FASTFAIL.get(params[0], '?')}")
    print(f"  parameters     : {[hex(p) for p in params[:nparams]]}")

    # ---- poor-man's stack walk: sample the faulting thread's stack for
    # values that land inside a known module. No unwind info needed; false
    # positives are possible, so the ORDER and repetition are the signal.
    if 3 in dirs:
        _sz, rva = dirs[3]
        f.seek(rva)
        n = struct.unpack("<I", f.read(4))[0]
        raw = f.read(48 * n)
        for i in range(n):
            vals = struct.unpack_from("<IIIIQQII", raw, 48 * i)
            t, sp_size, sp_rva = vals[0], vals[6], vals[7]
            if t != tid:
                continue
            f.seek(sp_rva)
            stack = f.read(min(sp_size, 512 * 1024))
            print("\n=== faulting thread stack (module hits, top first) ===")
            seen, shown = set(), 0
            for off in range(0, len(stack) - 8, 8):
                v = struct.unpack_from("<Q", stack, off)[0]
                w = who(v)
                if w == "<unknown module>":
                    continue
                mod = w.split("+")[0]
                if mod in seen:
                    continue
                seen.add(mod)
                print(f"  {v:016X}  {w}")
                shown += 1
                if shown >= 14:
                    break
            break
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
