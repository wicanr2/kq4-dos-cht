#!/usr/bin/env python3
"""
遞迴收集 ELF binary 的共享庫依賴(供 AppImage/AppDir 打包用)。
排除標準 glibc 核心(假設任何目標 Linux 都有,不必也不應打包)。

用法:pkg_collect_libs.py <binary> <out_libdir>
必須在「與 binary 同一 runtime」的容器/環境裡跑(ldd 才解得出正確路徑與版本)。
"""
import os
import re
import shutil
import subprocess
import sys

# AppImage 慣例排除清單:核心 glibc / 動態連結器,目標系統一定有,
# 打包反而可能因版本不符鎖死相容性(見 AppImage 官方 excludelist 精神)。
EXCLUDE = re.compile(
    r"^(linux-vdso\.so|ld-linux|libc\.so|libm\.so|libpthread\.so|"
    r"libdl\.so|librt\.so|libresolv\.so|libnsl\.so|libutil\.so)"
)


def collect(path, seen):
    if path in seen:
        return
    seen.add(path)
    out = subprocess.run(["ldd", path], capture_output=True, text=True).stdout
    for line in out.splitlines():
        m = re.search(r"=>\s+(/\S+)\s+\(0x", line)
        if not m:
            continue
        lib = m.group(1)
        if EXCLUDE.match(os.path.basename(lib)):
            continue
        collect(lib, seen)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    bin_path, libdir = sys.argv[1], sys.argv[2]
    os.makedirs(libdir, exist_ok=True)
    seen = set()
    collect(bin_path, seen)
    seen.discard(bin_path)
    for lib in sorted(seen):
        shutil.copy(lib, os.path.join(libdir, os.path.basename(lib)))
    print(f">> collected {len(seen)} shared libs into {libdir}")


if __name__ == "__main__":
    main()
