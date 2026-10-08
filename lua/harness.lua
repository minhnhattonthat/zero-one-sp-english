-- Generic driver. Expects global CFG (set by scripts/emu.py):
--   out        dir for screenshots/logs (trailing slash)
--   frames     stop after this many frames (writes out.."done")
--   mash       press mash_key (default A; B advances dialogue) for 6 frames every `mash` frames
--   inputs     { {frame, keyname, duration}, ... } keynames: A B START SELECT UP DOWN LEFT RIGHT L R
--   shot_every screenshot interval (0 = off); shots = {frame,...} explicit
--   save_at    { [frame] = path } savestates to write
--   on_start   optional function run once after load (for RE watchpoints etc.)
local f0 = nil
local log = io.open(CFG.out .. "log.txt", "w")
function LOG(s) log:write(s .. "\n"); log:flush() end
local held = {}
local shotset = {}
for _, f in ipairs(CFG.shots or {}) do shotset[f] = true end

local started = false
local function start()
  if CFG.on_start then CFG.on_start() end
end

CUR_KEYS = 0
callbacks:add("keysRead", function() emu:setKeys(CUR_KEYS) end)

callbacks:add("frame", function()
  local now = emu:currentFrame()
  if not f0 then f0 = now end
  local f = now - f0
  if not started then started = true; start() end
  local keys = 0
  for _, ev in ipairs(CFG.inputs or {}) do
    if f >= ev[1] and f < ev[1] + (ev[3] or 2) then keys = keys | (1 << C.GBA_KEY[ev[2]]) end
  end
  if (CFG.mash or 0) > 0 and f % CFG.mash < 6 then keys = keys | (1 << C.GBA_KEY[CFG.mash_key or "A"]) end
  CUR_KEYS = keys
  if ((CFG.shot_every or 0) > 0 and f % CFG.shot_every == 0) or shotset[f] then
    emu:screenshot(CFG.out .. string.format("f%06d.png", f))
  end
  if CFG.save_at and CFG.save_at[f] then emu:saveStateFile(CFG.save_at[f], 31) end
  if CFG.on_frame then CFG.on_frame(f) end
  if f == CFG.frames then
    local d = io.open(CFG.out .. "done", "w"); d:write("ok"); d:close()
  end
end)

-- dump memory regions to out dir: DUMP("name") -> name_io.bin, name_vram.bin, ...
function DUMP(name)
  local regions = { io = {"io", 0x400}, pal = {"palette", 0x400}, vram = {"vram", 0x18000},
                    oam = {"oam", 0x400}, ewram = {"wram", 0x40000}, iwram = {"iwram", 0x8000} }
  for k, r in pairs(regions) do
    local ok, data = pcall(function() return emu.memory[r[1]]:readRange(0, r[2]) end)
    if ok then
      local fh = io.open(CFG.out .. name .. "_" .. k .. ".bin", "wb")
      fh:write(data); fh:close()
    else
      LOG("DUMP " .. k .. " failed: " .. tostring(data))
    end
  end
end
