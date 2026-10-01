"""Offline checkbox geometry checks for the Forever window skins; requires lupa (Lua 5.1).

September 29, 2026: the owner's screenshots showed doubled checkbox boxes in the
Forever Group Finder and profession window. Two causes are covered here:
  1. WSkin.Checkbox put its border on the whole CheckButton frame and its fill
     4 inside, which reads as two nested boxes, and 30-wide frames on 22-high
     Group Finder rows overlapped their neighbors.
  2. The shared professions pack and the Forever professions pack both boxed
     Track Recipe (see verify-professions.py for the Forever side).
Mocks verify anchors and ownership marks only, never rendering.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ADDONS = Path(__file__).resolve().parents[2]
SKIN = ADDONS / "EllesmereUIBlizzardSkin"
engine = (SKIN / "EllesmereUIBlizzardSkin_WindowEngine.lua").read_text(encoding="utf-8-sig")
packs = (SKIN / "EllesmereUIBlizzardSkin_WindowPacks.lua").read_text(encoding="utf-8-sig")


def between(text, start, end):
    first = text.index(start)
    return text[first:text.index(end, first)]


checkbox = between(engine, "function WSkin.Checkbox(cb, opts)", "-- Modern dropdown / legacy selector")
guild_check = between(packs, "local function SkinGuildCheck(cb)", "-- Side tab (Chat/Roster/Benefits/Info)")

MOCKS = r'''
WSkin={}; Theme={accR=.1,accG=.8,accB=.6}; FFD={}; secret={}
EllesmereUI={ELLESMERE_GREEN={r=.1,g=.8,b=.6}}
function GetFFD(f) FFD[f]=FFD[f] or {}; return FFD[f] end
WSkin.GetFFD=GetFFD
function issecretvalue(v) return v==secret end
local function region(kind, parent)
 local r={kind=kind,parent=parent,alpha=1,points={},shown=true}
 function r:SetPoint(point,a,b,c,d)
  -- (point, x, y) or (point, relativeTo, relativePoint, x, y)
  if type(a)=="table" then self.points[point]={c or 0,d or 0,a} else self.points[point]={a or 0,b or 0} end
 end
 function r:SetAllPoints(to) self.all=to end
 function r:SetSize(w,h) self.w,self.h=w,h end
 function r:SetAlpha(a) self.alpha=a end
 function r:SetColorTexture(...) self.color={...} end
 function r:SetVertexColor(...) self.vertex={...} end
 function r:SetTexture(v) self.texture=v end
 function r:SetShown(v) self.shown=v and true or false end
 function r:Show() self.shown=true end
 function r:Hide() self.shown=false end
 function r:IsObjectType(k) return k==self.kind end
 return r
end
function Frame(w,h,level)
 local f=region("Frame"); f.w,f.h,f.level=w,h,level or 5; f.regions={}; f.textures={}; f.hooks={}
 function f:IsForbidden() return false end
 function f:GetSize() return self.w,self.h end
 function f:GetFrameLevel() return self.level end
 function f:SetFrameLevel(l) self.level=l end
 function f:CreateTexture(_,layer) local t=region("Texture",self); t.layer=layer; self.textures[#self.textures+1]=t; return t end
 function f:GetRegions() return unpack(self.regions) end
 function f:HookScript(e,fn) self.hooks[e]=fn end
 return f
end
function CheckButton(w,h)
 local f=Frame(w,h); f.normal,f.checkedTex,f.disabledChecked=region("Texture",f),region("Texture",f),region("Texture",f)
 f.regions={f.normal,f.checkedTex,f.disabledChecked}
 function f:SetNormalTexture(v) self.normalArt=v end
 function f:SetPushedTexture(v) self.pushedArt=v end
 function f:SetHighlightTexture(v) self.highlightArt=v end
 function f:GetNormalTexture() return self.normal end
 function f:GetCheckedTexture() return self.checkedTex end
 function f:GetDisabledCheckedTexture() return self.disabledChecked end
 function f:GetChecked() return self.checked end
 function f:SetChecked(v) self.checked=v end
 return f
end
function CreateFrame(_,_,parent) local f=Frame(0,0,(parent.level or 0)+1); f.parent=parent; parent.child=f; return f end
function hooksecurefunc(t,k,hook) local old=t[k]; t[k]=function(...) local r=old(...); hook(...); return r end end
function SolidTex(parent,layer,r,g,b,a) local t=parent:CreateTexture(nil,layer); t:SetColorTexture(r,g,b,a); return t end
function AddBorder(f) f.bordered=(f.bordered or 0)+1 end
WSkin.AddBorder=AddBorder
function WSkin.White(f) f.white=true end
-- Visible box of a skinned checkbox: {left inset, top inset, width, height}.
function Box(cb)
 local fill=GetFFD(cb).bg
 local l,t=fill.points.TOPLEFT[1],-fill.points.TOPLEFT[2]
 local r,b=-fill.points.BOTTOMRIGHT[1],fill.points.BOTTOMRIGHT[2]
 return l,t,cb.w-l-r,cb.h-t-b
end
-- Inset of whatever carries the border, from the checkbox frame edge.
function BorderInset(cb)
 local host=GetFFD(cb).borderHost
 if not host then assert(cb.bordered==1,"no border drawn"); return 0 end
 assert(host.bordered==1 and not cb.bordered,"border drawn twice")
 return host.points.TOPLEFT[1]
end
'''

CASES = r'''
-- Every native size used by the Forever packs draws ONE box: the border hugs
-- the fill, the box is centered and never smaller than 12.
for _,size in ipairs({ {30,30,18}, {24,24,14}, {26,26,16}, {32,32,20}, {30,29,18}, {22,22,14}, {24,23,14}, {15,15,13} }) do
 local cb=CheckButton(size[1],size[2])
 WSkin.Checkbox(cb,{stockCheck=true,boxInset=true})
 local l,t,w,h=Box(cb)
 assert(BorderInset(cb)==l and l==t,"border does not hug the fill at "..size[1])
 assert(w==size[3] and w>=12,"box width "..w.." at "..size[1])
 assert(cb.alpha==1 and cb.normal.alpha==0 and cb.checkedTex.alpha==1 and cb.disabledChecked.alpha==1,"native check state art changed")
 assert(not cb.checkedTex.vertex,"stockCheck tinted the native check")
 assert(cb.child.level==cb.level,"border host must share the checkbox level so the check draws over it")
end
-- Group Finder: 30x30 boxes on 22-high rows must not reach into neighbors.
local row=22
local cb=CheckButton(30,30); WSkin.Checkbox(cb,{stockCheck=true,boxInset=true})
local _,_,_,h=Box(cb)
assert(h<=row-2,"activity row boxes touch or overlap: "..h)
-- An explicit inset is honored; unreadable sizes fall back to the engine default.
cb=CheckButton(30,30); WSkin.Checkbox(cb,{boxInset=7})
assert(select(3,Box(cb))==16 and BorderInset(cb)==7,"explicit box inset ignored")
assert(cb.checkedTex.vertex and cb.checkedTex.vertex[2]==.8,"accent check lost without stockCheck")
cb=CheckButton(secret,secret); cb.w,cb.h=secret,secret
function cb:GetSize() return secret,secret end
WSkin.Checkbox(cb,{boxInset=true}); assert(GetFFD(cb).bg.points.TOPLEFT[1]==4,"secret size was used in arithmetic")
-- Callers that do not opt in keep the upstream geometry exactly.
cb=CheckButton(26,26); WSkin.Checkbox(cb)
assert(GetFFD(cb).bg.points.TOPLEFT[1]==4 and cb.bordered==1 and not cb.child,"default checkbox geometry changed")
cb=CheckButton(26,26); WSkin.Checkbox(cb,{borderInset=4})
assert(GetFFD(cb).bg.points.TOPLEFT[1]==4 and BorderInset(cb)==4 and cb.child.level==cb.level+1,"upstream borderInset path changed")
-- Idempotent on pooled rows.
cb=CheckButton(30,30); WSkin.Checkbox(cb,{boxInset=true}); WSkin.Checkbox(cb,{boxInset=true})
assert(#cb.textures==1 and cb.child.bordered==1,"repeat skin stacked a second box")
'''

lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(MOCKS)
lua.execute(checkbox)
lua.execute(CASES)

# The professions double box: the shared pack's replacement must leave the mark
# the Forever professions pack reads before it adds a box of its own.
lua.execute(guild_check + r'''
local cb=CheckButton(30,29)
SkinGuildCheck(cb)
assert(GetFFD(cb).custom==true,"shared checkbox replacement no longer marks the frame")
assert(cb.child and cb.child.w==14 and cb.child.bordered==1,"shared replacement box changed")
''')
forever = (SKIN / "EllesmereUIBlizzardSkin_ForeverProfessions.lua").read_text(encoding="utf-8-sig")
assert "W.GetFFD(checkbox).custom" in forever, "Forever professions no longer checks for the shared replacement"

# Every Forever pack opts in; none may return to a frame-sized border.
sites = list(SKIN.glob("EllesmereUIBlizzardSkin_Forever*.lua")) + [ADDONS / "EllesmereUIBags/EllesmereUIBags_ForeverBank.lua"]
count = 0
for path in sites:
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if "W.Checkbox(" in line and not line.lstrip().startswith("--"):
            count += 1
            assert "boxInset" in line.replace(" ", ""), f"{path.name}:{number} draws a frame-sized checkbox border"
assert count >= 7, f"expected the known Forever checkbox sites, found {count}"

# Negative control: the geometry before the fix fails the same overlap rule.
before = Path.home() / ".codex/backups/eui-checkbox-double-box-20260929/before/EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_WindowEngine.lua"
if before.exists():
    old = LuaRuntime(unpack_returned_tuples=True)
    old.execute(MOCKS)
    old.execute(between(before.read_text(encoding="utf-8-sig"), "function WSkin.Checkbox(cb, opts)", "-- Modern dropdown / legacy selector"))
    old.execute(r'''
    local cb=CheckButton(30,30); WSkin.Checkbox(cb,{stockCheck=true,boxInset=true})
    local l=Box(cb)
    assert(BorderInset(cb)==0 and l==4,"backup engine is not the reported geometry")
    assert(cb.h>22,"reported border did not overlap the 22-high rows")
    ''')
    control = "reproduced on the pre-fix engine"
else:
    control = "pre-fix backup not present, negative control skipped"

print(f"PASS checkbox boxes: one hugging box at 8 native sizes, 22-high Group Finder rows clear, "
      f"upstream default/borderInset unchanged, secret sizes, idempotence, shared professions mark, "
      f"{count} Forever sites opted in; {control}")
