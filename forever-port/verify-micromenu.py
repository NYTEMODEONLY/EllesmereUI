"""Verify the requested official 9.3 native bar ownership; no live actions.

Former custom-tile regressions are retained in the external full-suite backup.
Their rendering requirements were explicitly retired by the owner's request.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime
ROOT=Path(__file__).resolve().parents[2]
pack=(ROOT/'EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_WindowPacks.lua').read_text(encoding='utf-8')
section=pack[pack.index('local MICRO_BUTTONS = {'):pack.index('--  Dressing Room (DressUpFrame)')]
options=(ROOT/'EllesmereUIOptions/EUI_BlizzardSkin_Options.lua').read_text(encoding='utf-8')
a=options.index("    -- WoW Forever keeps Blizzard's micro menu art:")
card_filter=options[a:options.index('    local function ',a)]
for combat in (False,True):
 for preference in ('true','false','nil'):
  lua=LuaRuntime()
  lua.execute('''
local function forbidden() error('Forever native ownership changed') end
EUI_FOREVER=true; EllesmereUI={IS_FOREVER=true}
EllesmereUIDB={reskinMicroMenu=PREFERENCE,blizzWindowStyles={micromenu='eui'}}
WSkin={RegisterWindow=forbidden}; CreateFrame=forbidden; hooksecurefunc=forbidden
local native=setmetatable({}, {__index=forbidden,__newindex=forbidden})
MicroMenu=native; BagsBar=native; MainMenuBarBagManager=native
CharacterMicroButton=native; KeyRingButton=native
function InCombatLockdown() return COMBAT end
function UpdateMicroButtons() nativeUpdates=(nativeUpdates or 0)+1 end
originalUpdate=UpdateMicroButtons
'''.replace('PREFERENCE',preference).replace('COMBAT',str(combat).lower()))
  lua.execute(section)
  lua.execute('''
assert(UpdateMicroButtons==originalUpdate)
UpdateMicroButtons(); assert(nativeUpdates==1)
assert(WSkin.MenuTile==nil and WSkin.MenuBarShell==nil and WSkin.SkinForeverBags==nil)
assert(EllesmereUIDB.blizzWindowStyles.micromenu=='eui')
assert(EllesmereUIDB.reskinMicroMenu==PREFERENCE)
'''.replace('PREFERENCE',preference))
print('PASS: Forever combat/noncombat and saved true/false/unset install no painters, hooks, events or visual writes')
for forever in (True,False):
 lua=LuaRuntime()
 lua.execute('EllesmereUI={IS_FOREVER='+str(forever).lower()+'}')
 lua.execute("WINDOWS={{key='bags'},{key='micromenu'},{key='charsheet'},{key='housing'}}; EllesmereUIDB={reskinMicroMenu=true}")
 lua.execute(card_filter)
 lua.execute('''
local found=false
for _,win in ipairs(WINDOWS) do if win.key=='micromenu' then found=true end end
assert(found==not EllesmereUI.IS_FOREVER)
assert(WINDOWS[1].key=='bags' and WINDOWS[#WINDOWS].key=='housing')
assert(EllesmereUIDB.reskinMicroMenu==true)
''')
print('PASS: official options filter removes only Forever micro skin card; dormant choice survives')
# Non-Forever registration and deferred initialization must still work.
lua=LuaRuntime()
lua.execute('''
EllesmereUI={IS_FOREVER=false}; Theme={bgR=.08,bgG=.08,bgB=.08}
combat=true; hooks=0; passes=0; timers={}
function InCombatLockdown() return combat end
WSkin={RegisterWindow=function(e) entry=e end}
function CreateFrame()
 local f={}; function f:RegisterEvent(e) assert(e=='PLAYER_REGEN_ENABLED') end
 function f:SetScript(e,fn) assert(e=='OnEvent'); callback=function() fn(f) end end
 function f:UnregisterAllEvents() unregistered=true end
 return f
end
function UpdateMicroButtons() nativeUpdates=(nativeUpdates or 0)+1 end
function hooksecurefunc(name,fn)
 hooks=hooks+1; local original=_G[name]
 _G[name]=function(...) original(...); fn(...) end
end
function WSkin.Debounce(fn)
 local pending=false
 return function() if pending then return end; pending=true
 timers[#timers+1]=function() pending=false; fn() end end
end
function flush() local batch=timers; timers={}; for _,fn in ipairs(batch) do fn() end end
-- A forbidden native button must be skipped before any visual access.
CharacterMicroButton={IsForbidden=function() passes=passes+1; return true end}
''')
lua.execute(section)
lua.execute('''
assert(entry.key=='micromenu'); entry.apply(); assert(hooks==0 and passes==0)
combat=false; callback(); assert(unregistered and hooks==1 and passes==1)
UpdateMicroButtons(); UpdateMicroButtons(); assert(#timers==1 and passes==1)
flush(); assert(passes==2 and nativeUpdates==2)
combat=true; UpdateMicroButtons(); flush(); assert(passes==2)
''')
print('PASS: upstream non-Forever registration, forbidden-frame skip, combat deferral and debounce')
action_options=(ROOT/'EllesmereUIOptions/EUI_ActionBars_Options.lua').read_text(encoding='utf-8')
assert 'VisOpts("MicroBar", "Micro Menu Visibility")' in action_options
assert 'VisOpts("BagBar", "Bag Bar Visibility")' in action_options
for build in ('70009','70010'):
 lua=LuaRuntime()
 lua.execute('EUI_FOREVER=true; function GetBuildInfo() return "1.60.1", "'+build+'" end')
 for name in ('ForeverCombatLayout','Forever','ForeverHUD'):
  lua.execute((ROOT/f'EllesmereUIActionBars/EllesmereUIActionBars_{name}.lua').read_text(encoding='utf-8'))
 assert lua.eval('EUI_FOREVER_NATIVE_ACTIONS==nil and EUI_FOREVER_StyleHUD==nil')
print('PASS: official visibility controls retained; old-build action/HUD adapters stay inert')
