"""Exercise native spell-collection grid and visibility edges before timer flush.

Offline regression only: actual rendering/secure execution still needs the client.
"""
from pathlib import Path
import runpy
import re

context = runpy.run_path(str(Path(__file__).with_name('verify-action-edits.py')))
lua = context['lua']
native = context['native']
multi = (native / 'MultiActionBars.lua').read_text(encoding='utf-8-sig')
for method in ('MultiActionBar_ShowAllGrids', 'MultiActionBar_HideAllGrids'):
    lua.execute(re.search(r'function ' + method + r'\s*\([^\n]*\).*?\nend', multi, re.S).group())
lua.execute(r'''
combat=false; nativeEditing=false; nativeReset=false
ACTION_BUTTON_SHOW_GRID_REASON_EVENT=2; ACTION_BUTTON_SHOW_GRID_REASON_SPELLCOLLECTION=4
local function band(a,b)
 local value,power=0,1
 while a>0 and b>0 do
  if a%2==1 and b%2==1 then value=value+power end
  a=math.floor(a/2); b=math.floor(b/2); power=power*2
 end
 return value
end
bit={band=band,bor=function(a,b) return a+b-band(a,b) end,bnot=function(a) return 255-a end}
local function nativeBar(name)
 local bar=system(name); _G[name]=bar
 bar.actionButtons={}; bar.shownButtonContainers={}; bar.numButtonsShowable=4
 bar.visibility='Hidden'; bar.isShownExternal=true
 bar.UpdateShownButtons=ActionBarMixin.UpdateShownButtons
 bar.SetShowGrid=ActionBarMixin.SetShowGrid
 bar.GetShowAllButtons=ActionBarMixin.GetShowAllButtons
 bar.UpdateVisibility=EditModeActionBarMixin.UpdateVisibility
 bar.IsShown=EditModeActionBarMixin.IsShownOverride
 function bar:UpdateFrameStrata() end
 function bar:SetScale(value)
  assert(inNativeChain,'addon called native scale wrapper'); self.scale=value
 end
 function bar:IsInDefaultPosition() return false end
 local showBase=bar.ShowBase
 function bar:ShowBase()
  local changed=not self.shown
  if nativeEditing and inNativeChain then self.shown=true else showBase(self) end
  if changed and self.scripts.OnShow then self.scripts.OnShow(self) end
 end
 function bar:SetShownBase(value) if value then self:ShowBase() else self:HideBase() end end
 for i=1,4 do
  local container=frame(name..'Container'..i,bar)
  function container:SetShown(value) self.shown=value end
  local b=frame(name..'Button'..i,container); b.container=container; b.index=i
  b.statehidden=i==2; b.hasAction=i==1
  function b:GetAttribute(key) if key=='statehidden' then return self.statehidden end end
  function b:SetShowGrid(show,reason)
   self.grid=show and bit.bor(self.grid or 0,reason) or bit.band(self.grid or 0,bit.bnot(reason))
  end
  function b:GetShowGrid() return (self.grid or 0)>0 end
  function b:HasAction() return self.hasAction end
  function b:SetShown(value) self.shown=value end
  bar.actionButtons[i]=b
 end
 return bar
end
local disabled=nativeBar('MultiBarLeft')
local enabled=nativeBar('MultiBarBottomRight')
profile.bars.Bar5={enabled=false,buttonWidth=40,numIcons=3}
profile.bars.Bar3={enabled=true,buttonWidth=40,numIcons=3}
profile.barPositions.Bar5={x=-937,y=259}
profile.barPositions.Bar3={x=0,y=-490}
function GetMultiActionBars() return {{bar=disabled},{bar=enabled}} end
-- The persisted custom layout prevents native default-stack moves. Exercise
-- the actual manager hooks as well, without a synthetic visibility function.
function EditModeUtil:IsRightAnchoredActionBar(bar) return bar==disabled or bar==enabled end
function EditModeManagerFrame:GetRightActionBars() return {disabled,enabled} end
_EAB_Apply(); flush()
local hudBefore=hudCalls
local function grid(show,reason)
 inNativeChain=true
 if show then MultiActionBar_ShowAllGrids(reason) else MultiActionBar_HideAllGrids(reason) end
 inNativeChain=false
end
local function stable()
 assert(not disabled.shown,'disabled left bar became visible')
 assert(enabled.shown,'enabled bar stayed hidden until a queued repaint')
 assert(enabled.w==124 and enabled.actionButtons[3].container.points[1][4]==84,'enabled grid moved')
 assert(not enabled.actionButtons[4].container.shown,'excess slot flashed')
 assert(not enabled.actionButtons[2].shown,'statehidden action was revealed')
 assert(enabled.points[1][4]==0 and disabled.points[1][4]==-937,'saved anchors changed')
 assert(enabled.visibility=='Hidden' and disabled.isShownExternal,'native visibility bookkeeping changed')
 assert(#timers==0 and hudCalls==hudBefore,'spell-collection edge queued a full repaint')
end
for i=1,5 do
 grid(true,ACTION_BUTTON_SHOW_GRID_REASON_SPELLCOLLECTION); stable()
 -- Starting/dropping a drag while Talents is open must preserve both reasons.
 grid(true,ACTION_BUTTON_SHOW_GRID_REASON_EVENT); stable()
 grid(false,ACTION_BUTTON_SHOW_GRID_REASON_EVENT); stable()
 assert(enabled.showAllButtons==4)
 grid(false,ACTION_BUTTON_SHOW_GRID_REASON_SPELLCOLLECTION); stable()
 assert(enabled.showAllButtons==0 and not enabled.actionButtons[3].shown)
end
-- Native Edit Mode owns temporary visibility until its exit/reset finishes.
nativeEditing=true; EventRegistry:TriggerEvent('EditMode.Enter')
grid(true,ACTION_BUTTON_SHOW_GRID_REASON_SPELLCOLLECTION)
assert(disabled.shown,'adapter suppressed native Edit Mode preview')
nativeEditing=false; nativeReset=true
EventRegistry:TriggerEvent('EditMode.Exit'); nativeReset=false; flush()
assert(not disabled.shown and enabled.shown,'Edit Mode exit lost EUI visibility')
''')
print('PASS Talents: actual native show/hide-all grids, UpdateVisibility and manager hooks; repeated open/close, overlapping drag reasons, disabled bar suppression, synchronous enabled visibility/count/anchors, no queued HUD repaint, Edit Mode preview retained')
