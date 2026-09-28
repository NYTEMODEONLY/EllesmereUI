"""Forever spellbook skin regressions using Lua 5.1 frame doubles.

Checks content/state preservation across category changes and pooled paging.
This does not emulate client rendering or secure spell/talent execution.
"""
from pathlib import Path
import os
import re
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
lua = LuaRuntime(unpack_returned_tuples=True)
native = (Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['TEMP']) / 'eui-forever-research/wow-ui-source-forever/Interface/AddOns')) / 'Blizzard_SharedXML/Shared/TabSystem/TabSystemTemplates.lua').read_text()
lua.execute('TabSystemButtonArtMixin={}')
for method in ('SetTabSelected', 'GetTextYOffset', 'GetIconYOffset'):
    match = re.search(r'function TabSystemButtonArtMixin:' + method + r'\([^\n]*\).*?\nend\n', native, re.S)
    assert match, method
    lua.execute(match.group())
lua.execute(r'''
EUI_FOREVER=true
EUI_FOREVER_STATUS={}
local function obj()
 local o={alpha=1,shown=true,scripts={},textures={}}
 function o:SetAlpha(a) self.alpha=a end
 function o:SetShown(v) self.shown=v end
 function o:SetEnabled(v) self.enabled=v end
 function o:SetNormalFontObject(value) self.fontObject=value end
 function o:SetTextColor(...) self.color={...} end
 function o:SetColorTexture(...) self.color={...} end
 function o:SetVertexColor(...) self.tint={...} end
 function o:SetDesaturated(v) self.desaturated=v end
 function o:SetAllPoints() end
 function o:SetPoint() end
 function o:SetHeight() end
 function o:CreateTexture() local t=obj(); table.insert(self.textures,t); return t end
 function o:HookScript(k,fn) self.scripts[k]=fn end
 function o:IsShown() return self.shown end
 return o
end
function hooksecurefunc(o,key,hook)
 local prior=o[key]; assert(type(prior)=='function',key)
 o[key]=function(...) local result=prior(...); hook(...); return result end
end
local W={Theme={bgR=.1,bgG=.1,bgB=.1,bgA=.9,accR=.3,accG=.6,accB=1}}
function W.AddBorder(f) f.bordered=true end
function W.Font(f,r,g,b) if f then f.fontApplied=true; if r then f:SetTextColor(r,g,b) end end end
function W.Shell(_,f) f.shell=true end
function W.RemovePortrait() end
function W.CloseButton() end
function W.Dropdown() end
function W.Button() end
function W.StateButtonLabel() end
function W.WindowCallback(_,fn) return fn end
function W.Debounce(fn) return fn end
function W.OnLooksChanged(fn) W.looks=fn end
function W.RegisterWindow(e) W.entry=e end
ns={WSkin=W}
function GetAppropriateTooltip() return {IsOwned=function() return false end} end
local tab=obj(); tab.Icon=obj(); tab.IconMask=obj(); tab.Text=obj(); tab.SquareBackground=obj()
tab.squareMode=true; tab.SquareBackgroundActive=obj(); tab.SquareBackgroundActiveGlow=obj()
tab.IconMask.atlas='SquareMask'; tab.Icon.mask=tab.IconMask
function tab.Icon:RemoveMaskTexture() error('native category mask removed') end
function tab.Icon:SetTexCoord() error('native category icon UVs cropped') end
tab.SquareBackgroundActive.atlas='spellbook-Tab-Frame-Glow-C60'
tab.SquareBackgroundActiveGlow.atlas='spellbook-Tab-Frame-glow-gradient-C60'
tab.SetTabSelected=TabSystemButtonArtMixin.SetTabSelected
tab.GetTextYOffset=TabSystemButtonArtMixin.GetTextYOffset
tab.GetIconYOffset=TabSystemButtonArtMixin.GetIconYOffset
function tab:IsForceDisabled() return self.forceDisabled or false end
tab:SetTabSelected(false)
local item=obj(); item.Button=obj(); item.Button.Icon=obj(); item.Button.Arrow=obj()
item.Button.LevelLinkLock=obj(); item.Button.TrainableBackplate=obj(); item.Button.BorderShadow=obj()
item.Name=obj(); item.SubName=obj(); item.RequiredLevel=obj(); item.TextContainer=obj(); item.Backplate=obj()
function item:UpdateVisuals() self.Name:SetAlpha(.6); self.Button.Icon:SetAlpha(.6); self.Button.LevelLinkLock:SetShown(true) end
function item:OnIconEnter() self.Backplate:SetAlpha(1) end
function item:OnIconLeave() self.Backplate:SetAlpha(.25) end
local header=obj(); header.Text=obj(); header.Backplate=obj(); header.Border=obj()
local paging=obj(); paging.PageText=obj(); paging.PrevPageButton=obj(); paging.NextPageButton=obj()
local prevArrow=obj(); local nextArrow=obj()
function paging.PrevPageButton:GetNormalTexture() return prevArrow end
function paging.NextPageButton:GetNormalTexture() return nextArrow end
local paged=obj(); paged.frames={item,header}; paged.PagingControls=paging
function paged:EnumerateFrames() return ipairs(self.frames) end
function paged:RegisterCallback(event,fn,owner) self.callback=function() fn(owner) end end
PagedContentFrameBaseMixin={Event={OnUpdate='OnUpdate'}}
local book=obj(); book.PagedSpellsFrame=paged; book.CategoryTabSystem={tabs={tab}}
book.SearchBox=obj(); book.SearchBox.Icon=obj(); book.BookBGHalved=obj(); book.SettingsDropdown=obj()
PlayerSpellsFrame=obj(); PlayerSpellsFrame.SpellBookFrame=book
local amount=obj(); amount.color={.4,1,.2}; amount.value=5
local treeRank=obj(); treeRank.color={1,.8,0}; treeRank.value=4
PlayerSpellsFrame.TalentsFrame=obj()
PlayerSpellsFrame.TalentsFrame.ClassCurrencyDisplay={UnspentLabel=obj(),CurrentAmountContainer={CurrencyAmount=amount},CreateTexture=obj().CreateTexture,textures={}}
PlayerSpellsFrame.TalentsFrame.treeHeaders={{Text=treeRank}}
fixture={item=item,tab=tab,header=header,book=book,paged=paged,make=obj,prev=prevArrow,next=nextArrow}
''')
source = (ROOT.parent / 'EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_ForeverSpells.lua').read_text()
chunk = lua.eval('function(source) return assert(loadstring(source)) end')(source)
chunk('EllesmereUIBlizzardSkin', lua.globals().ns)
lua.execute(r'''
local W=ns.WSkin
assert(W.entry.key=='playerspells')
W.entry.apply()
local x=fixture
assert(x.tab.Icon.alpha==1 and x.tab.IconMask.alpha==1,'category icons/masks preserved')
assert(x.book.SearchBox.Icon.alpha==1,'search icon preserved')
assert(x.item.Button.Icon.alpha==1 and x.item.Button.Arrow.alpha==1,'spell/flyout icons preserved')
assert(x.prev.alpha==1 and x.next.alpha==1,'paging arrows preserved')
assert(x.header.Text.color[1]==1,'header is legible')
assert(x.tab.SquareBackground.alpha==0 and not x.tab.bordered and #x.tab.textures==0,'extra icon-tab rectangle/underline remains')
assert(x.tab.Icon.mask==x.tab.IconMask and x.tab.IconMask.atlas=='SquareMask','native category mask changed')
x.tab:SetTabSelected(true)
assert(x.tab.SquareBackgroundActive.shown and x.tab.SquareBackgroundActiveGlow.shown and not x.tab.enabled,'native selected outline/glow/enabled state changed')
assert(x.tab.SquareBackgroundActive.alpha==1 and x.tab.SquareBackgroundActive.atlas=='spellbook-Tab-Frame-Glow-C60','native selected border lost')
x.tab:SetTabSelected(false)
assert(not x.tab.SquareBackgroundActive.shown and not x.tab.SquareBackgroundActiveGlow.shown and x.tab.enabled,'native deselected category state changed')
x.tab.forceDisabled=true; x.tab:SetTabSelected(false)
assert(not x.tab.enabled and x.tab.Icon.alpha==1 and #x.tab.textures==0,'native category availability/art changed')
x.item:UpdateVisuals()
assert(x.item.Button.Icon.alpha==.6 and x.item.Name.alpha==.6,'unlearned state remains native')
assert(x.item.Button.LevelLinkLock.shown,'lock preserved')
x.item:OnIconEnter()
assert(x.item.Backplate.alpha==0,'hover cannot restore parchment backplate')
local header2=x.make(); header2.Text=x.make(); header2.Backplate=x.make(); header2.Border=x.make()
table.insert(x.paged.frames,header2)
x.paged.callback()
assert(header2.Text.color[1]==1,'pooled header styled after native page update')
local amount=PlayerSpellsFrame.TalentsFrame.ClassCurrencyDisplay.CurrentAmountContainer.CurrencyAmount
local rank=PlayerSpellsFrame.TalentsFrame.treeHeaders[1].Text
assert(amount.fontApplied and amount.value==5 and amount.color[1]==.4,'unspent amount state retained')
assert(rank.fontApplied and rank.value==4 and rank.color[2]==.8,'tree rank state retained')
''')
print('PASS: raw masked icon categories without added rectangles; actual native category selection/glow/availability; spell/flyout/search/paging art, unlearned state, locks, hover styling and pooled headers')
