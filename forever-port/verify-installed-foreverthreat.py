"""Audit the installed addon using its actual source and simulated native inputs.
No changes to ForeverThreat; no claim that mocks measure the game's mechanics.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[2] / 'ForeverThreat'
lua = LuaRuntime(unpack_returned_tuples=True)
compile_lua = lua.eval('function(s,n) local f,e=loadstring(s,n); assert(f,e); return f end')
for path in root.glob('*.lua'):
    compile_lua(path.read_text(encoding='utf-8-sig'), path.name)
lua.execute('''
FT={}; SlashCmdList={}
function GetLocale() return 'enUS' end
function CreateFrame() return {RegisterEvent=function() end, SetScript=function() end} end
function issecretvalue(v) return type(v)=='table' and v.secret==true end
function hidden(v) return {secret=true,value=v} end
members=2; holder='player'; exists={player=true,party1=true,party2=true,partypet1=true,target=true,targettarget=true}
function UnitExists(u) return exists[u] or false end
function IsInRaid() return false end
function IsInGroup() return true end
function GetNumGroupMembers() return members end
function GetNumSubgroupMembers() return members-1 end
function UnitName(u) return u end
function UnitClass() return 'Warrior','WARRIOR' end
function UnitIsConnected() return true end
function UnitIsDeadOrGhost() return false end
function UnitCanAttack() return true end
function UnitAffectingCombat() return true end
function UnitIsUnit(a,b) return a==b or a=='targettarget' and b==holder end
snap={}
function UnitDetailedThreatSituation(u,m)
    assert(m=='target', 'Installed addon should query only the selected target')
    if snap[u] then return unpack(snap[u]) end
end
function UnitThreatSituation(u,m) return snap[u] and snap[u][2] end
''')
for name in ('Core.lua', 'Localization.lua', 'Threat.lua', 'UI.lua'):
    compile_lua((root/name).read_text(encoding='utf-8-sig'), name)('ForeverThreat', lua.globals().FT)
lua.execute('''
FT.db=FT.defaults
assert(FT.version=='1.0.2' and FT.db.showPets==false)
local function entry(data,unit)
    for _,e in ipairs(data) do if e.unit==unit then return e end end
end
print('Simulated inputs through installed ForeverThreat 1.0.2:')
for _,progress in ipairs({60,85,95,99}) do
    local rival=11000*progress/100
    snap={player={true,rival>10000 and 2 or 3,100,100,10000},
        party1={false,rival>10000 and 1 or 0,progress,rival/100, rival}}
    local rows=FT:GetThreatData()
    local tank,challenger=entry(rows,'player'),entry(rows,'party1')
    assert(FT:GetThreatLabel(tank)=='100%')
    assert(challenger.threatDelta==rival-10000)
    assert(FT:GetThreatLabel(challenger)==string.format('%d%%',progress))
    print(string.format('Tank label=%s; challenger=%s; raw delta=%+.0f; remaining pull buffer=%d%%',
        FT:GetThreatLabel(tank),FT:GetThreatLabel(challenger),challenger.threatDelta,100-progress))
end
-- UI prewarning checks the viewing player's scaled percentage, not tank buffer.
local warnings={}
function FT:ShowCombatWarning(text) warnings[#warnings+1]=text end
holder='party1'; snap={player={false,0,95,104.5,10450},party1={true,2,100,100,10000}}
FT:CheckPlayerThreatWarning(FT:GetThreatData())
assert(#warnings==1 and warnings[1]==FT:L('HIGH_THREAT_WARNING'))
-- Protected fields are dropped, rather than decoded/displayed numerically.
holder=nil
snap={player={hidden(true),hidden(3),hidden(100),hidden(100),hidden(10000)}}
local e=FT:GetThreatEntry('player')
assert(e.scaled==nil and e.rawThreat==nil and e.restricted)
assert(FT:GetThreatLabel(e)==FT:L('PROTECTED'))
-- Bar fallback lengths are categorical approximations, not measured percentages.
assert(FT:GetBarValue({status=0})==25 and FT:GetBarValue({status=1})==90)
-- Optional pets change coverage.
assert(#FT:GetGroupUnits()==2)
FT.db.showPets=true; assert(#FT:GetGroupUnits()==3)
-- Raw strongest and nearest-to-pull can be different players (melee/ranged example).
members=3; holder='player'; FT.db.showPets=false
snap={player={true,2,100,100,10000},
    party1={false,0,9500/11000*100,95,9500},
    party2={false,1,10500/13000*100,105,10500}}
local rows=FT:GetThreatData()
assert(entry(rows,'party2').rawThreat>entry(rows,'party1').rawThreat)
assert(entry(rows,'party1').scaled>entry(rows,'party2').scaled)
print('PASS: installed code confirms constant tank100, challenger progression, raw delta semantics, viewer prewarning, protected-field omission, approximate fallback bars, pet opt-in and raw/scaled ranking difference.')
''')
