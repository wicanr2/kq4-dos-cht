#!/usr/bin/env python3
"""SCI0 EGA view (kViewEga) decoder / encoder.

Reverse-engineered strictly from ScummVM source (read-only reference, not modified):
  scummvm-src/engines/sci/graphics/view.cpp
    - GfxView::initData()   kViewEga branch (isEGA=true; falls into the shared
                             kViewEga/kViewAmiga/kViewAmiga64/kViewVga case block) --
                             header / loop-offset-table / cel-offset-table / cel-header
                             layout (all offsets are absolute, view-resource-relative,
                             16-bit).
    - unpackCelData()        kViewEga branch -- the actual pixel decode:
                                curByte = *rlePtr++;
                                runLength = curByte >> 4;
                                memset(out+pixelNr, curByte & 0x0F, min(runLength, remaining));
                                pixelNr += runLength;
                              i.e. each byte is a (runLength:4, colorIndex:4) RLE pair, no
                              separate literal/skip streams (EGA cels are always fully
                              opaque -- there is no "skip/transparent" opcode in this format,
                              unlike VGA's dual-stream RLE). clearKey is only used to
                              pre-fill the canvas (memset) before decode; for a well-formed
                              cel the RLE run lengths sum to exactly width*height so the
                              pre-fill is never actually visible.
    - GfxView::unpackCel()   confirms offsetEGA (== celOffset+7) is passed as `rlePos` with
                              `literalPos=0` -- single-stream format, no literal indirection.
    - GfxView::getBitmap()   post-decode mirroring (mirrorBits bit per loop) is applied
                              AFTER unpackCel; GfxView::unditherBitmap() is applied after
                              that but only when a *currently displayed picture's* dithered
                              background color table is available (runtime-only heuristic,
                              not part of the stored resource) -- deliberately NOT
                              reproduced here; this tool decodes the raw stored cel content,
                              matching unpackCel()'s output before undithering.
  scummvm-src/engines/sci/graphics/palette16.cpp
    - GfxPalette::setEGA()   the 16 fixed EGA color RGB triples (indices 1-15; index 0 is
                              the universal (0,0,0) black default, same convention as the
                              SCI1.1 sysPalette constructor default noted in sci_view.py).
  scummvm-src/engines/sci/resource/resource.cpp
    - ResourceManager::processPatch()  loose-patch header layout for _volVersion <
      kResVersionSci11 (true for QFG1 EGA, a SCI0 game): patchDataOffset =
      kResourceHeaderSize(2) + byte-at-absolute-offset-1. With that second header byte
      (the "extra header byte count") set to 0, patchDataOffset == 2 -- i.e. the SCI0
      loose-patch wrapper is just the same 2-byte [patchTypeByte, 0x00] wrapper already
      used by this project's SCI_DUMP_RES dump files (out/ega_dump/view.NNN). Patch type
      byte: convertResType() does `type & 0x7F` then s_resTypeMapSci0[] maps 0 ->
      kResourceTypeView, so 0x80 (matching this project's existing dump-tool convention)
      or 0x00 both work.
    - readResourcePatches()  SCI0 naming convention: "<type-name>.<nnn>" (e.g. "view.100"),
      tried unconditionally alongside the SCI1.1+ "<nnn>.<ext>" naming; for a SCI0 game
      only the former is meaningful. This project's dump tooling already uses this name.

Empirically verified (2026-07) against a real ground-truth oracle: ran the actual
instrumented qfg1-build ScummVM binary headless (Xvfb, --language=tw) against the EGA
game data in extract/ega_cht/, which invokes GfxView::dumpCelsToDir()/getBitmap() for
every loop/cel of view 100 -- see out/oracle_view100/view_100_0_{0,1,2}.ppm (98x17,
43x11, 130x16, matching the already-confirmed geometry of the "Wanted / Hero / for the
Village of Spielburg" poster cels). decode_cel() below reproduces those three PPMs
byte-for-byte (see `verify` command).

=====================================================================================
Byte layout notes (see cited functions for the authoritative C++; this is a transcript)
=====================================================================================

View resource data (what GfxView::initData() parses; this is what's inside the 2-byte
SCI_DUMP_RES/patch wrapper -- see "Patch file format" below):

Header:
  0x00 u8    loopCount
  0x01 u8    (isCompressed flag bit 0x40 -- unused by the EGA branch, VGA-only)
  0x02 u16LE mirrorBits         (bit i set => loop i is a mirror of some other loop's
                                  cel data, pixel rows reversed after decode)
  0x06 u16LE paletteOffset      (0 for QFG1 EGA -- no per-view EGA color-mapping table)
  0x08 ..    loopOffset[loopCount]  u16LE each, absolute offsets of each loop's data

Loop data (at loopOffset[n], absolute view-relative offset):
  0x00 u16LE celCount
  0x02 u16LE (unknown/unused)
  0x04 ..    celOffset[celCount]  u16LE each, absolute offsets of each cel's header

Cel data (at celOffset[c], absolute view-relative offset):
  0x00 u16LE width
  0x02 u16LE height
  0x04 i8    displaceX            (signed)
  0x05 u8    displaceY
  0x06 u8    clearKey
  0x07 ..    EGA pixel RLE stream starts here, immediately following the header
             (no separate offset field -- unlike VGA, the pixel stream is NOT
             independently relocatable via a stored pointer; it just directly follows
             the 7-byte cel header at this fixed relative position. To relocate cel
             content when re-encoding, the celOffset table entry itself must be
             rewritten to point to a new [7-byte header][pixel stream] block placed
             wherever convenient -- see rebuild_view() below).

EGA pixel RLE stream: read one byte at a time until width*height pixels have been
produced (self-terminating on pixel count, not on stream length):
  byte = (runLength:4 high bits, colorIndex:4 low bits)
  write `colorIndex` for `runLength` pixels (runLength in 0-15; 0 is a legal, if
  wasteful, no-op that only advances the read pointer)

=====================================================================================
Patch file format (what we must write for ScummVM's loose-patch loader to accept it)
=====================================================================================
SCI0 (_volVersion < kResVersionSci11, true for QFG1 EGA): patchDataOffset =
kResourceHeaderSize(2) + (byte at absolute file offset 1). With that byte == 0:
  offset 0: patch type byte -- (byte & 0x7F) indexed into s_resTypeMapSci0[]; 0 (or 0x80,
            this project's existing dump-tool convention) -> kResourceTypeView
  offset 1: 0x00 (extra header byte count -- must be 0 so patchDataOffset == 2)
  offset 2..: raw view resource data (the "View resource data" section above) begins here
This is byte-for-byte the same 2-byte wrapper this project's SCI_DUMP_RES hook already
emits for out/ega_dump/view.100 -- load_view_data() below auto-detects and strips it.

Filename: SCI0 loose-patch naming is "<resource-type-name>.<nnn>" (see
ResourceManager::readResourcePatches()'s SCI0 mask), i.e. view 100's patch is
"view.100" -- matching this project's existing out/ega_dump/view.100 naming.
"""

import argparse
import struct
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None


# --------------------------------------------------------------------------------
# EGA palette (GfxPalette::setEGA(), palette16.cpp) -- indices 0-15
# --------------------------------------------------------------------------------

EGA_PALETTE = [
    (0x00, 0x00, 0x00),  # 0  black (universal default, not set explicitly by setEGA())
    (0x00, 0x00, 0xAA),  # 1  blue
    (0x00, 0xAA, 0x00),  # 2  green
    (0x00, 0xAA, 0xAA),  # 3  cyan
    (0xAA, 0x00, 0x00),  # 4  red
    (0xAA, 0x00, 0xAA),  # 5  magenta
    (0xAA, 0x55, 0x00),  # 6  brown
    (0xAA, 0xAA, 0xAA),  # 7  light gray
    (0x55, 0x55, 0x55),  # 8  dark gray
    (0x55, 0x55, 0xFF),  # 9  light blue
    (0x55, 0xFF, 0x55),  # 10 light green
    (0x55, 0xFF, 0xFF),  # 11 light cyan
    (0xFF, 0x55, 0x55),  # 12 light red
    (0xFF, 0x55, 0xFF),  # 13 light magenta
    (0xFF, 0xFF, 0x55),  # 14 yellow
    (0xFF, 0xFF, 0xFF),  # 15 white
]


# --------------------------------------------------------------------------------
# Parsing (GfxView::initData(), kViewEga branch)
# --------------------------------------------------------------------------------

class Cel:
    def __init__(self, width, height, displaceX, displaceY, clearKey,
                 cel_offset, table_entry_offset):
        self.width = width
        self.height = height
        self.displaceX = displaceX
        self.displaceY = displaceY
        self.clearKey = clearKey
        self.cel_offset = cel_offset              # absolute offset of the 7-byte cel header
        self.table_entry_offset = table_entry_offset  # absolute offset of the 2-byte
                                                       # celOffset table slot that points here
                                                       # (rewrite this to relocate the cel)

    @property
    def pixel_offset(self):
        return self.cel_offset + 7


class Loop:
    def __init__(self, cels, loop_offset):
        self.cels = cels
        self.loop_offset = loop_offset
        self.mirrorFlag = False  # set by caller from header mirrorBits


class SCI0View:
    def __init__(self, data: bytes):
        self.data = data
        self._parse()

    def _parse(self):
        d = self.data
        self.loopCount = d[0]
        self.flagsByte = d[1]
        self.mirrorBits = struct.unpack_from('<H', d, 2)[0]
        self.paletteOffset = struct.unpack_from('<H', d, 6)[0]

        self.loops = []
        mirror_bits = self.mirrorBits
        for loopNo in range(self.loopCount):
            loop_offset = struct.unpack_from('<H', d, 8 + loopNo * 2)[0]
            celCount = struct.unpack_from('<H', d, loop_offset)[0]
            cels = []
            for celNo in range(celCount):
                table_entry_offset = loop_offset + 4 + celNo * 2
                cel_offset = struct.unpack_from('<H', d, table_entry_offset)[0]
                width = struct.unpack_from('<H', d, cel_offset)[0]
                height = struct.unpack_from('<H', d, cel_offset + 2)[0]
                displaceX = struct.unpack_from('<b', d, cel_offset + 4)[0]
                displaceY = d[cel_offset + 5]
                clearKey = d[cel_offset + 6]
                cels.append(Cel(width, height, displaceX, displaceY, clearKey,
                                 cel_offset, table_entry_offset))
            loop = Loop(cels, loop_offset)
            loop.mirrorFlag = bool(mirror_bits & 1)
            mirror_bits >>= 1
            self.loops.append(loop)


# --------------------------------------------------------------------------------
# Cel bitmap decode (unpackCelData, kViewEga branch) + mirroring (getBitmap())
# --------------------------------------------------------------------------------

def decode_ega_stream(data: bytes, offset: int, pixel_count: int, clear_key: int = 0):
    """Port of unpackCelData()'s kViewEga case. Returns (bitmap bytes of length
    pixel_count, number of stream bytes consumed)."""
    out = bytearray([clear_key]) * pixel_count  # memset(clearColor) pre-fill, per the C++
    ptr = offset
    pixel_nr = 0
    n = len(data)
    while pixel_nr < pixel_count:
        cur = data[ptr]
        ptr += 1
        run_length = cur >> 4
        color = cur & 0x0F
        n_write = min(run_length, pixel_count - pixel_nr)
        if n_write > 0:
            out[pixel_nr:pixel_nr + n_write] = bytes([color]) * n_write
        pixel_nr += run_length
        if ptr > n:
            raise ValueError("EGA cel stream ran past end of resource data")
    return bytes(out), ptr - offset


def decode_cel_raw(view: SCI0View, loopNo: int, celNo: int) -> bytes:
    """Raw decoded bitmap (palette-index bytes, 0-15), no mirroring applied --
    equivalent to unpackCel()'s output before GfxView::getBitmap() mirrors it."""
    cel = view.loops[loopNo].cels[celNo]
    bitmap, _ = decode_ega_stream(view.data, cel.pixel_offset, cel.width * cel.height,
                                   cel.clearKey)
    return bitmap


def decode_cel(view: SCI0View, loopNo: int, celNo: int) -> bytearray:
    """Equivalent of GfxView::getBitmap(): unpack + apply row-mirroring if the loop's
    mirror bit is set (undithering deliberately NOT applied -- see module docstring)."""
    cel = view.loops[loopNo].cels[celNo]
    bitmap = bytearray(decode_cel_raw(view, loopNo, celNo))
    if view.loops[loopNo].mirrorFlag:
        w, h = cel.width, cel.height
        for row in range(h):
            base = row * w
            line = bitmap[base:base + w]
            line.reverse()
            bitmap[base:base + w] = line
    return bitmap


def indices_to_rgb(indices: bytes) -> bytes:
    out = bytearray(len(indices) * 3)
    for i, idx in enumerate(indices):
        r, g, b = EGA_PALETTE[idx & 0x0F]
        out[i * 3] = r
        out[i * 3 + 1] = g
        out[i * 3 + 2] = b
    return bytes(out)


def read_ppm_rgb(path: Path):
    raw = path.read_bytes()
    newlines = 0
    hdr_end = 0
    for idx, b in enumerate(raw):
        if b == 0x0A:
            newlines += 1
            if newlines == 3:
                hdr_end = idx + 1
                break
    header = raw[:hdr_end].split()
    width, height = int(header[1]), int(header[2])
    return width, height, raw[hdr_end:]


def write_ppm(path: Path, width: int, height: int, rgb: bytes):
    with open(path, 'wb') as f:
        f.write(f"P6\n{width} {height}\n255\n".encode('ascii'))
        f.write(rgb)


def write_png(path: Path, width: int, height: int, rgb: bytes):
    if Image is None:
        return
    img = Image.frombytes('RGB', (width, height), rgb)
    img.save(path)


# --------------------------------------------------------------------------------
# File-level helpers (2-byte dump/patch wrapper handling)
# --------------------------------------------------------------------------------

def _looks_like_ega_view_header(d: bytes) -> bool:
    """Plausibility check that `d` starts at a raw SCI0 EGA view resource (loopCount in
    a sane range, and every loop-offset-table entry is a resolvable, in-range offset)."""
    if len(d) < 8:
        return False
    loop_count = d[0]
    if not (1 <= loop_count <= 32):
        return False
    if len(d) < 8 + loop_count * 2:
        return False
    for i in range(loop_count):
        off = struct.unpack_from('<H', d, 8 + i * 2)[0]
        if off < 8 or off + 4 > len(d):
            return False
    return True


def load_view_data(path: Path) -> bytes:
    """Strip the 2-byte SCI_DUMP_RES/patch wrapper ([type|0x80, 0x00]) if present,
    falling back to treating the file as already-unwrapped raw view data."""
    raw = path.read_bytes()
    if len(raw) >= 2 and (raw[0] & 0x80) and raw[1] == 0x00 and _looks_like_ega_view_header(raw[2:]):
        return raw[2:]
    return raw


def make_patch(view_data: bytes) -> bytes:
    """Wrap raw view resource data into a loose SCI0 ScummVM patch file body: 2-byte
    header [0x80, 0x00] + raw view resource data (see module docstring)."""
    return bytes([0x80, 0x00]) + view_data


# --------------------------------------------------------------------------------
# Encoding
# --------------------------------------------------------------------------------

def encode_ega_stream(bitmap: bytes) -> bytes:
    """Re-encode a raw 4-bit index bitmap as EGA (runLength:4, colorIndex:4) RLE pairs,
    greedily chunked to runs of at most 15 identical pixels (the format's max run length
    per byte). ScummVM's unpackCelData() decodes this identically regardless of how the
    original Sierra encoder chunked its runs (it just sums runLength until pixel_count is
    reached), so this is a faithful re-encoding, not necessarily byte-identical to the
    original stream."""
    out = bytearray()
    n = len(bitmap)
    i = 0
    while i < n:
        color = bitmap[i] & 0x0F
        j = i + 1
        limit = min(n, i + 15)
        while j < limit and bitmap[j] == color:
            j += 1
        run = j - i
        out.append((run << 4) | color)
        i = j
    return bytes(out)


def rebuild_view(view: SCI0View, replacements: dict) -> bytes:
    """Rebuild the full view resource, keeping the header/loop-offset-table/loop-data
    (celCount+celOffsetTable) regions at their original absolute offsets and content
    UNCHANGED, except for the 2-byte celOffset table entries of cels being touched (every
    cel is re-encoded, whether replaced or not, to fully exercise the encoder -- matching
    sci_view.py's VGA rebuild_view() round-trip philosophy). Fresh [7-byte cel header +
    EGA RLE stream] blocks are appended after the end of the original buffer; old cel
    content bytes are left in place (dead/unreferenced once no table entry points to them
    -- harmless padding, not read by anything).

    `replacements`: dict of (loopNo, celNo) -> new raw index bitmap (bytes, length must
    equal cel.width*cel.height) overriding the decoded original for that cel; cels not
    present keep their originally-decoded (raw, unmirrored) bitmap.
    """
    d = view.data
    out = bytearray(d)  # keep every original byte; new content is appended after this

    for loopNo, loop in enumerate(view.loops):
        for celNo, cel in enumerate(loop.cels):
            key = (loopNo, celNo)
            if key in replacements:
                bitmap = replacements[key]
                assert len(bitmap) == cel.width * cel.height, (
                    f"replacement bitmap for loop {loopNo} cel {celNo} has "
                    f"{len(bitmap)} bytes, expected {cel.width * cel.height} "
                    f"({cel.width}x{cel.height})")
            else:
                bitmap = decode_cel_raw(view, loopNo, celNo)

            stream = encode_ega_stream(bitmap)

            new_cel_offset = len(out)
            if new_cel_offset > 0xFFFF:
                raise ValueError("rebuilt view exceeds 16-bit offset range (0xFFFF)")

            header = bytearray(7)
            struct.pack_into('<H', header, 0, cel.width)
            struct.pack_into('<H', header, 2, cel.height)
            struct.pack_into('<b', header, 4, cel.displaceX)
            header[5] = cel.displaceY
            header[6] = cel.clearKey
            out += header
            out += stream

            struct.pack_into('<H', out, cel.table_entry_offset, new_cel_offset)

    return bytes(out)


# --------------------------------------------------------------------------------
# Image <-> palette-index mapping
# --------------------------------------------------------------------------------

def image_to_indices(img) -> bytes:
    """Map an RGB(A) Pillow image to EGA palette indices (0-15), exact match against
    EGA_PALETTE only, falling back to nearest-neighbour (e.g. anti-aliased edges) --
    callers should draw with colors sampled directly from EGA_PALETTE to avoid this."""
    img = img.convert('RGB')
    w, h = img.size
    px = img.load()

    exact = {}
    for idx, rgb in enumerate(EGA_PALETTE):
        exact.setdefault(rgb, idx)

    def nearest(rgb):
        best_idx, best_d = 0, None
        for idx, prgb in enumerate(EGA_PALETTE):
            dist = sum((a - b) ** 2 for a, b in zip(rgb, prgb))
            if best_d is None or dist < best_d:
                best_d, best_idx = dist, idx
        return best_idx

    out = bytearray(w * h)
    for y in range(h):
        for x in range(w):
            rgb = px[x, y]
            idx = exact.get(rgb)
            if idx is None:
                idx = nearest(rgb)
            out[y * w + x] = idx
    return bytes(out)


# --------------------------------------------------------------------------------
# CLI commands
# --------------------------------------------------------------------------------

def cmd_decode(args):
    data = load_view_data(Path(args.input))
    view = SCI0View(data)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    count = 0
    for loopNo, loop in enumerate(view.loops):
        for celNo, cel in enumerate(loop.cels):
            bitmap = decode_cel(view, loopNo, celNo)
            rgb = indices_to_rgb(bitmap)
            base = outdir / f"view_{args.view_id}_{loopNo}_{celNo}"
            write_ppm(base.with_suffix('.ppm'), cel.width, cel.height, rgb)
            if Image is not None:
                write_png(base.with_suffix('.png'), cel.width, cel.height, rgb)
            count += 1
    print(f"decoded {count} cel(s) to {outdir}")


def cmd_verify(args):
    """Compare our decode against reference PPMs (real ScummVM GfxView::getBitmap()
    oracle dumps, e.g. out/oracle_view100), pixel-exact."""
    data = load_view_data(Path(args.input))
    view = SCI0View(data)
    ref_dir = Path(args.ref_dir)

    ok = True
    checked = 0
    for loopNo, loop in enumerate(view.loops):
        for celNo, cel in enumerate(loop.cels):
            ref_path = ref_dir / f"view_{args.view_id}_{loopNo}_{celNo}.ppm"
            if not ref_path.exists():
                print(f"  [skip] {ref_path} not found")
                continue
            bitmap = decode_cel(view, loopNo, celNo)
            rgb = indices_to_rgb(bitmap)

            ref_w, ref_h, ref_rgb = read_ppm_rgb(ref_path)
            checked += 1
            if (ref_w, ref_h) != (cel.width, cel.height):
                ok = False
                print(f"  [MISMATCH] loop {loopNo} cel {celNo}: size ours="
                      f"{cel.width}x{cel.height} ref={ref_w}x{ref_h}")
                continue
            if ref_rgb != rgb:
                ok = False
                for i in range(min(len(ref_rgb), len(rgb))):
                    if ref_rgb[i] != rgb[i]:
                        print(f"  [MISMATCH] loop {loopNo} cel {celNo}: "
                              f"first differing byte at {i} "
                              f"(ours={rgb[i]} ref={ref_rgb[i]})")
                        break
            else:
                print(f"  [ok] loop {loopNo} cel {celNo} ({cel.width}x{cel.height})")

    print(f"verify: {checked} cel(s) checked, {'ALL OK' if ok else 'MISMATCHES FOUND'}")
    sys.exit(0 if ok else 1)


def cmd_roundtrip(args):
    """decode -> re-encode (unchanged) -> decode again; compare pixel-for-pixel (raw,
    unmirrored bitmaps -- mirroring is a getBitmap()-level post-process, not stored
    content, so it's irrelevant to encoder correctness)."""
    data = load_view_data(Path(args.input))
    view = SCI0View(data)

    originals = {}
    for loopNo, loop in enumerate(view.loops):
        for celNo, cel in enumerate(loop.cels):
            originals[(loopNo, celNo)] = decode_cel_raw(view, loopNo, celNo)

    new_data = rebuild_view(view, {})
    view2 = SCI0View(new_data)

    ok = True
    for (loopNo, celNo), orig_bitmap in originals.items():
        new_bitmap = decode_cel_raw(view2, loopNo, celNo)
        if new_bitmap != orig_bitmap:
            ok = False
            for i in range(min(len(orig_bitmap), len(new_bitmap))):
                if orig_bitmap[i] != new_bitmap[i]:
                    print(f"  [MISMATCH] loop {loopNo} cel {celNo} byte {i}: "
                          f"orig={orig_bitmap[i]} new={new_bitmap[i]}")
                    break
        else:
            cel = view.loops[loopNo].cels[celNo]
            print(f"  [ok] loop {loopNo} cel {celNo} ({cel.width}x{cel.height}) "
                  f"round-trip identical")

    print(f"round-trip: {'ALL IDENTICAL' if ok else 'MISMATCHES FOUND'}")

    if args.output:
        Path(args.output).write_bytes(new_data)
        print(f"wrote re-encoded raw view resource: {args.output}")
    if args.patch:
        Path(args.patch).write_bytes(make_patch(new_data))
        print(f"wrote re-encoded patch file: {args.patch}")

    sys.exit(0 if ok else 1)


def cmd_encode(args):
    data = load_view_data(Path(args.input))
    view = SCI0View(data)

    replacements = {}
    if args.replace:
        for spec in args.replace:
            loop_s, cel_s, png_path = spec.split(',', 2)
            loopNo, celNo = int(loop_s), int(cel_s)
            cel = view.loops[loopNo].cels[celNo]
            if Image is None:
                raise SystemExit("Pillow required for --replace (PNG input)")
            img = Image.open(png_path)
            if img.size != (cel.width, cel.height):
                raise SystemExit(f"replacement image {png_path} is {img.size}, "
                                  f"expected {(cel.width, cel.height)}")
            bitmap = image_to_indices(img)
            replacements[(loopNo, celNo)] = bitmap

    new_data = rebuild_view(view, replacements)

    out_path = Path(args.output)
    if args.patch:
        out_path.write_bytes(make_patch(new_data))
        print(f"wrote patch file: {out_path} ({out_path.stat().st_size} bytes)")
    else:
        out_path.write_bytes(new_data)
        print(f"wrote raw view resource: {out_path} ({out_path.stat().st_size} bytes)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('decode', help='decode a view to per-cel PNG/PPM')
    p.add_argument('input', help='view file (dump/patch-wrapped or raw)')
    p.add_argument('outdir')
    p.add_argument('--view-id', type=int, default=0, dest='view_id')
    p.set_defaults(func=cmd_decode)

    p = sub.add_parser('verify', help='compare decode output against reference PPMs')
    p.add_argument('input', help='view file (dump/patch-wrapped or raw)')
    p.add_argument('ref_dir', help='directory of reference view_<id>_<loop>_<cel>.ppm')
    p.add_argument('--view-id', type=int, required=True, dest='view_id')
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser('roundtrip', help='decode -> re-encode (unchanged) -> decode, compare')
    p.add_argument('input', help='view file (dump/patch-wrapped or raw)')
    p.add_argument('--output', help='write re-encoded raw view resource here')
    p.add_argument('--patch', help='write re-encoded patch file here')
    p.set_defaults(func=cmd_roundtrip)

    p = sub.add_parser('encode', help='re-encode a view, optionally replacing cels')
    p.add_argument('input', help='view file (dump/patch-wrapped or raw)')
    p.add_argument('output')
    p.add_argument('--replace', action='append',
                    help='loop,cel,pngfile -- replace one cel with a PNG (same '
                         'width/height as the cel; RGB colors must map to the 16-color '
                         'EGA palette)')
    p.add_argument('--patch', action='store_true',
                    help='wrap output as a loose SCI0 ScummVM patch file '
                         '(default: write raw view resource data)')
    p.set_defaults(func=cmd_encode)

    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
