"""Semantic-preservation checks for the Camelot character cosmetics (Lua 5.1)."""
from pathlib import Path
import os
from lupa.lua51 import LuaRuntime

lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
EUI_FOREVER=true
NORMAL_FONT_COLOR={r=1,g=.82,b=0}
function make(extra)
 local f=extra or {}; f.children=f.children or {}; f.regions=f.regions or {}; f.hooks={}
 function f:GetRegions() return unpack(self.regions) end
 function f:GetChildren() return unpack(self.children) end
 function f:GetAtlas() return self.atlas end
 function f:SetAtlas(v) self.atlas=v end
 function f:IsForbidden() return false end
 function f:GetFrameLevel() return self.level or 0 end
 function f:SetFrameLevel(v) self.level=v; self.levelWrites=(self.levelWrites or 0)+1 end
 function f:SetAlpha(v) self.alpha=v end
 function f:SetVertexColor(...) self.color={...} end
 function f:SetColorTexture(...) self.color={...}; self.atlas=nil end
 function f:GetDrawLayer() return self.layer or 'BACKGROUND' end
 function f:SetAllPoints() end
 function f:SetPoint() error('Native anchor changed') end
 function f:SetSize() error('Native size changed') end
 function f:Show() error('Native visibility changed') end
 function f:Hide() error('Native visibility changed') end
 function f:SetShown(v) assert(nativeVisualUpdate,'Native visibility changed'); self.shown=v end
 function f:SetParent() error('Native parent changed') end
 function f:CreateTexture() return make() end
 function f:HookScript(name, fn) self.hooks[name]=fn end
 function f:RegisterEvent() end
 function f:SetScript(name,fn) self.hooks[name]=fn end
 function f:GetTextColor() return unpack(self.textColor or {1,1,1}) end
 function f:SetTextColor(...) self.textColor={...} end
 return f
end
function CreateFrame() return make() end
function hooksecurefunc(frame,key,fn)
 frame.hooks[key]=fn
 local original=frame[key]
 frame[key]=function(...) local result={original(...)}; fn(...); return unpack(result) end
end
W={Theme={accR=.1,accG=.8,accB=.6,insetR=.04,insetG=.04,insetB=.04},FFD={}}
function W.Font(f,r,g,b) if f then f.fontApplied=true; if r then f:SetTextColor(r,g,b) end end end
function W.AddBorder(f) if f then f.border=true end end
function W.Button(f) if f then f.buttonPainted=true end end
function W.StateButtonLabel() end
function W.Checkbox(f) f.checkboxPainted=true end
function W.Dropdown() end
function W.ScrollBar(f) if f and f.Back then f.Back.Texture:SetAlpha(0) end end
function W.SquareIcon(icon,button) button.iconPainted=true end
function W.OnLooksChanged(fn) W.looks=fn end
stylesOff={}
function W.WindowCallback(key,fn) return function(...) if not stylesOff[key] then return fn(...) end end end
ScrollUtil={}
function ScrollUtil.AddInitializedFrameCallback(box,fn,owner) box.callback=fn; box.owner=owner end
function list(row)
 local box=make({row=row}); function box:ForEachFrame(fn) fn(self.row) end
 return make({ScrollBox=box,ScrollBar=make({Back=make({Texture=make()})})})
end
StatRow=make({Label=make({textColor={1,.82,0}}),Value=make({textColor={.1,1,.1}}),Icon=make(),Background=make({atlas='UI-Character-Info-Line-Bounce'})})
StatRow.regions={StatRow.Icon,StatRow.Background}
CharacterStatsPaneScrollBox=list(StatRow)
Tab=make({Background=make({atlas='common-sidetab'}),Icon=make({uv={.03125,.96875,.03125,.96875}}),
 Mask=make({atlas='common-sidetab-mask'}),SelectedTexture=make({atlas='common-sidetab-selected'}),TabGlow=make(),HighlightTexture=make()})
local nativeClick=function() end
Tab.OnMouseUp=nativeClick
CharacterFrame=make({ModeTabs={Tabs={Tab}},RightPaneHost=make(),RightPaneToggleButton=make(),SidePanes={}})
function CharacterFrame:RefreshDisplay() end
ItemIcon=make(); ItemCount=make(); CharacterAmmoSlot=make({Icon=ItemIcon,Count=ItemCount})
CharacterAmmoSlot.OnClick=nativeClick
ReputationRow=make({Content=make({Name=make(),CurrencyIcon=make(),Value=make()})})
ReputationFrame=list(ReputationRow)
InspectFrame=make({ModeTabs={Tabs={Tab}}})
function InspectFrame:SetupModeTabs() end
function InspectFrame:UpdateTabs() end
InspectGuildFrame=make({guildName=make(),guildRealmName=make(),guildLevel=make(),guildNumMembers=make()})
InspectGuildFrameBG=make()
InspectGuildFrameBanner=make({alpha=1})
InspectGuildFrameTabardLeftIcon=make({alpha=1})
InspectGuildFrameTabardRightIcon=make({alpha=1})
InspectPaperDollFrame=make({InspectTalents=make({enabled=false,OnClick=nativeClick})})
InspectRangedSlot=make({Icon=make(),OnClick=nativeClick})
ns={WSkin=W}
''')
# Actual native selected-state and portrait layering methods are used below.
native = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ["LOCALAPPDATA"]) / "Temp/eui-forever-research/wow-ui-source-forever/Interface/AddOns"))
def between(text, first, last):
    start=text.index(first)
    return text[start:text.index(last,start)]
tabs = (native / "Blizzard_SharedXML/Mainline/SharedUIPanelTemplates.lua").read_text(encoding="utf-8-sig")
portrait = (native / "Blizzard_SharedXML/PortraitFrame.lua").read_text(encoding="utf-8-sig")
engine = (Path(__file__).resolve().parents[2] / "EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_WindowEngine.lua").read_text(encoding="utf-8-sig")
lua.execute('SidePanelTabButtonMixin={}; PortraitFrameMixin={}; assertsafe=assert')
lua.execute(between(tabs,"function SidePanelTabButtonMixin:UpdateIconInterior()","function SidePanelTabButtonMixin:GetTooltipTextSetupFunction()"))
lua.execute(between(portrait,"do\n\tlocal function SetFrameLevelInternal","PortraitFrameFlatBaseMixin ="))
lua.execute('''
WSkin=W
function GetFFD(frame) W.FFD[frame]=W.FFD[frame] or {}; return W.FFD[frame] end
C_Texture={GetAtlasInfo=function() return {} end}
''')
lua.execute(between(engine,'local BORDER_ATLAS = "AdventureMap_TopBorder"','--  Primitive skinners.'))
lua.execute('''
for _,f in ipairs({CharacterFrame,InspectFrame}) do
 f.level=500
 f.PortraitContainer=make({level=400,portrait=make({asset='native-Paladin-spec',uv={0,1,0,1},alpha=.9,shown=true}),
  CircleMask=make({atlas='native-circle',nativeAnchors={2,0,-2,4}})})
 f.SetFrameLevelsFromBaseLevel=PortraitFrameMixin.SetFrameLevelsFromBaseLevel
 W.AtlasBorder(f)
 assert(W.FFD[f].atlasBorderFrame:GetFrameLevel()==506)
end
Tab.SetChecked=SidePanelTabButtonMixin.SetChecked
Tab.UpdateIconInterior=SidePanelTabButtonMixin.UpdateIconInterior
nativeVisualUpdate=true; Tab:SetChecked(true); nativeVisualUpdate=false
''')
source = Path(__file__).resolve().parents[2] / "EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_ForeverCharacter.lua"
lua.execute('assert(loadstring(...))("test", ns)', source.read_text(encoding="utf-8"))
lua.execute('''
ns.ForeverCharacter()
assert(CharacterAmmoSlot.OnClick==Tab.OnMouseUp)
assert(ItemIcon.alpha==nil and ItemCount.alpha==nil and Tab.Icon.alpha==nil)
assert(StatRow.Icon.alpha==nil and StatRow.Background.alpha==0)
assert(StatRow.Value.textColor[2]==1 and StatRow.Value.textColor[1]==.1)
assert(StatRow.Label.textColor[1]==.88)
assert(CharacterStatsPaneScrollBox.ScrollBar.Back.Texture.alpha==1)
assert(Tab.Background.alpha==0 and Tab.Background.atlas=='common-sidetab' and not Tab.border,'square tab surround added')
assert(Tab.Mask.atlas=='common-sidetab-mask' and Tab.Icon.uv[1]==.03125,'native trimmed-corner icon changed')
assert(Tab.SelectedTexture.shown and Tab.SelectedTexture.atlas=='common-sidetab-selected','native selected outline removed')
assert(CharacterFrame.PortraitContainer.level==507,'header emblem remains under the shell border')
nativeVisualUpdate=true; Tab:SetChecked(false); nativeVisualUpdate=false
ns.ForeverCharacter()
assert(not Tab.SelectedTexture.shown,'skin forced selected outline on an unselected tab')
nativeVisualUpdate=true; Tab:SetChecked(true); nativeVisualUpdate=false
local newRow=make({Name=make(),StateIcon=make()})
local box=ReputationFrame.ScrollBox
box.callback(box.owner,newRow,{})
assert(newRow.Name.fontApplied and newRow.StateIcon.alpha==nil)
ns.ForeverCharacter()
W.looks()
for _,f in ipairs({CharacterFrame,InspectFrame}) do
 local pc=f.PortraitContainer
 assert(pc.level>W.FFD[f].atlasBorderFrame.level,'portrait occluded by atlas border')
 assert(pc.portrait.asset=='native-Paladin-spec' and pc.portrait.uv[1]==0 and pc.portrait.uv[2]==1)
 assert(pc.portrait.alpha==.9 and pc.portrait.shown and pc.CircleMask.atlas=='native-circle')
 assert(pc.CircleMask.nativeAnchors[1]==2 and pc.CircleMask.nativeAnchors[4]==4)
 local count=pc.levelWrites
 W.looks(); assert(pc.levelWrites==count,'repeated skin needlessly rewrites portrait layering')
 -- Blizzard can reset its portrait layer later; completed native reset restores
 -- just layering, with original higher levels and native visibility preserved.
 f:SetFrameLevelsFromBaseLevel(0)
 assert(pc.level==507)
 f:SetFrameLevelsFromBaseLevel(1000)
 assert(pc.level==1400,'skin lowered an already higher native portrait')
 pc.portrait.shown=false; W.looks(); assert(not pc.portrait.shown)
end
assert(InspectGuildFrame.guildName.fontApplied and InspectGuildFrame.guildNumMembers.fontApplied)
assert(InspectGuildFrame.guildLevel.textColor[1]==.88 and InspectGuildFrame.guildNumMembers.textColor[1]==.88)
assert(InspectGuildFrameBG.color[4]==.85)
assert(InspectGuildFrameBanner.alpha==1 and InspectGuildFrameTabardLeftIcon.alpha==1 and InspectGuildFrameTabardRightIcon.alpha==1)
assert(InspectRangedSlot.iconPainted and InspectRangedSlot.OnClick==Tab.OnMouseUp)
assert(not InspectPaperDollFrame.InspectTalents.enabled and InspectPaperDollFrame.InspectTalents.OnClick==Tab.OnMouseUp)
InspectGuildFrame.guildNumMembers.fontApplied=nil
InspectFrame.hooks.UpdateTabs()
assert(InspectGuildFrame.guildNumMembers.fontApplied)
InspectGuildFrame.hooks.OnShow()
stylesOff.inspect=true
InspectGuildFrame.guildNumMembers.fontApplied=nil
InspectFrame.hooks.UpdateTabs()
assert(not InspectGuildFrame.guildNumMembers.fontApplied)
stylesOff.charsheet=true
StatRow.Label.fontApplied=nil
CharacterFrame.hooks.RefreshDisplay()
assert(not StatRow.Label.fontApplied)
local offRow=make({Name=make(),StateIcon=make()})
box.callback(box.owner,offRow,{})
assert(not offRow.Name.fontApplied)
''')
print("PASS character: raw masked tabs/native selection without square surrounds, portrait above actual EUI border/native layer resets, native geometry/masks/visibility/handlers, icons/counts, semantic colors, scroll arrows, pooled rows and repeated refresh")
