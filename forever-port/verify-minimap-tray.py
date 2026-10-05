"""Lua 5.1 tray click layering regression; frame order, not native rendering."""
from pathlib import Path
from lupa.lua51 import LuaRuntime

source = (Path(__file__).resolve().parents[2] / "EllesmereUIMinimap/EllesmereUIMinimap.lua").read_text(encoding="utf-8-sig")
start = source.index("function EBS._RaiseLateFlyoutChildren(btn)")
end = source.index("-- Keep the grid open", start)
lua = LuaRuntime()
lua.execute('''
EBS={}; flyoutPanel=nil; combat=false
function InCombatLockdown() return combat end
function GetFFD(f) f.data=f.data or {}; return f.data end
function Frame(parent,level,protected)
 local f={parent=parent,level=level,protected=protected,children={},strata="MEDIUM",shown=true,writes=0}
 if parent then parent.children[#parent.children+1]=f end
 function f:GetParent() return self.parent end
 function f:GetChildren() return unpack(self.children) end
 function f:GetFrameLevel() return self.level end
 function f:IsProtected() return self.protected end
 function f:SetFrameLevel(v) assert(not(combat and self.protected)); self.level=v; self.writes=self.writes+1 end
 function f:SetFrameStrata(v) assert(not(combat and self.protected)); self.strata=v; self.writes=self.writes+1 end
 return f
end
''')
lua.execute(source[start:end])
lua.execute('''
flyoutPanel=Frame(nil,100)
local btn=Frame(flyoutPanel,105)
local bg=Frame(btn,104); bg.strata="DIALOG"; GetFFD(btn).ungroupBg=bg
local popup=Frame(btn,2); local nested=Frame(popup,3)
for i=1,3 do
 EBS._RaiseLateFlyoutChildren(btn)
 assert(bg.level<btn.level and bg.writes==0,"tray click covers the addon icon with its own background")
 assert(popup.level==106 and nested.level==107 and popup.strata=="DIALOG","addon popup no longer raised")
end
bg.shown=false; EBS._RaiseLateFlyoutChildren(btn)
assert(not bg.shown and bg.writes==0,"ring mode background changed")
local protected=Frame(btn,4,true); local child=Frame(protected,5)
combat=true; EBS._RaiseLateFlyoutChildren(btn)
assert(protected.writes==0 and child.writes==0,"protected subtree changed during combat")
assert(bg.level==104 and popup.level==106,"combat changed tray layer ownership")
combat=false; EBS._RaiseLateFlyoutChildren(btn)
assert(protected.level==106 and child.level==107,"popup not raised after combat")
local outside=Frame(nil,9); local outsider=Frame(outside,10)
EBS._RaiseLateFlyoutChildren(outside); assert(outsider.writes==0,"non-tray child changed")
flyoutPanel=nil; EBS._RaiseLateFlyoutChildren(btn)
''')
assert 'btn:HookScript("OnClick", EBS._RaiseLateFlyoutChildren)' in source
print("PASS minimap tray click: background below icon, popup recursion, hidden boxes, protected children and outside buttons")
