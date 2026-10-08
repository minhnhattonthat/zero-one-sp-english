"""Run mGBA headless-ish with lua/harness.lua and a config; returns output dir."""
import json
import shutil
import subprocess
import time

from scripts.rom import ROOT

FPS = 3000
MGBA = ROOT / 'tools' / 'mgba' / 'mGBA.exe'


def lua_val(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return json.dumps(v)  # JSON string escapes are valid Lua
    if isinstance(v, dict):
        return '{' + ','.join(f'[{lua_val(k)}] = {lua_val(x)}' for k, x in v.items()) + '}'
    return '{' + ','.join(lua_val(x) for x in v) + '}'


def run(rom, name, cfg: dict, extra_lua: str = '', timeout=600, state=None, bios=None):
    """bios: real GBA BIOS path; needed for savestates made with one (HLE BIOS crashes on them)."""
    out = ROOT / 'build' / 'runs' / name
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    cfg = dict(cfg, out=out.as_posix() + '/')
    script = out / 'run.lua'
    harness = (ROOT / 'lua' / 'harness.lua').as_posix()
    script.write_text(f'CFG={lua_val(cfg)}\n{extra_lua}\ndofile({json.dumps(harness)})\n', encoding='utf-8')
    args = [str(MGBA), '-C', f'fpsTarget={FPS}', '-C', 'audioSync=0', '-C', 'videoSync=0',
            '-C', 'volume=0', '--script', str(script)]
    if state:
        args += ['-t', str(state)]
    if bios:
        args += ['-C', f'gba.bios={bios}', '-C', 'useBios=1']
    p = subprocess.Popen(args + [str(rom)])
    t = time.time()
    try:
        while not (out / 'done').exists() and time.time() - t < timeout and p.poll() is None:
            time.sleep(0.5)
    finally:
        p.kill()
        p.wait()
    return out
