"""Lua 5.1 checks for Forever Friends ownership/lifecycle and Guild indicators.

Exercises extracted production functions and Blizzard's unread updater. No game
connection, friend data, messages or UI actions; rendering/secure execution still
require live verification.
"""
from pathlib import Path
import os
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
ADDONS = ROOT.parent
friends = (ADDONS / 'EllesmereUIFriends/EllesmereUIFriends.lua').read_text(encoding='utf-8')
packs = (ADDONS / 'EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_WindowPacks.lua').read_text(encoding='utf-8')
engine = (ADDONS / 'EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_WindowEngine.lua').read_text(encoding='utf-8')
native = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['TEMP']) / 'eui-forever-research/wow-ui-source-forever/Interface/AddOns'))

# The reused TGA files are uncompressed 32-bit, 128px assets. Confirm the
# transparent padding shared by the mask/outline before relying on their UVs.
for name in ('csquare_mask.tga', 'csquare_border.tga'):
    asset = (ROOT / 'media/portraits' / name).read_bytes()
    assert asset[0] == 0 and asset[2] == 2 and asset[16] == 32
    assert int.from_bytes(asset[12:14], 'little') == 128
    assert int.from_bytes(asset[14:16], 'little') == 128
    opaque = [i for i, alpha in enumerate(asset[21::4]) if alpha]
    assert (min(i % 128 for i in opaque), min(i // 128 for i in opaque),
            max(i % 128 for i in opaque) + 1, max(i // 128 for i in opaque) + 1) == (10, 10, 118, 118)

def between(source, start, end):
    begin = source.index(start)
    return source[begin:source.index(end, begin)]

gate = between(friends, 'local function LegacyFriendsRetired()', '\n-------------------------------------------------------------------------------')
apply = between(friends, 'local function ApplyFriends()', '\n-- Visibility')
enable = friends[friends.index('function EBS:OnEnable()'):]
lua = LuaRuntime()
lua.execute(r'''
EUI_FOREVER=true
frames={}; timers={}; applies=0; skins=0; queued=0
EBS={db={profile={friends={enabled=true}}}}
EllesmereUI={_accentElements={},_ModuleNS={}}; ADDON_NAME="EllesmereUIFriends"
C_SocialUI={IsSystemEnabled=function() return featureEnabled end}
function InCombatLockdown() return combat end
function IsInInstance() return false, 'none' end
function QueueApplyAll() queued=queued+1 end
function SkinFriendsFrame() skins=skins+1 end
function PaintChrome() end -- visual helper tested separately; lifecycle assertions retained
function GetBorderColor() return 0,0,0,1 end
PP={UpdateBorder=function() end,SetBorderColor=function() end}
function GetFFD() return {} end
function UpdateBottomButtonAccent() end
function UpdateRaidTabButtonAccent() end
function CreateFrame()
 local f={events={},scripts={},shown=false}
 function f:RegisterEvent(e) self.events[e]=true end
 function f:UnregisterAllEvents() self.events={} end
 function f:SetScript(e,fn) self.scripts[e]=fn end
 function f:Show() self.shown=true end
 function f:Hide() self.shown=false end
 frames[#frames+1]=f; return f
end
C_Timer={After=function(_,fn) timers[#timers+1]=fn end}
function flush() local q=timers; timers={}; for _,fn in ipairs(q) do fn() end end
function event(e,...)
 for _,f in ipairs(frames) do if f.events[e] then f.scripts.OnEvent(f,e,...) end end
end
function hooksecurefunc(f,key,fn)
 local old=f[key]; f[key]=function(...) old(...); fn(...) end
end
''')
lua.execute(gate + '\nLegacyGate=LegacyFriendsRetired\n' + apply + '\nApplyOwner=ApplyFriends\nApplyAll=function() applies=applies+1; ApplyFriends() end\n' + enable)
lua.execute(r'''
-- Match native SocialUIControl.IsEnabled: feature enabled without replacement
-- frame still leaves Camelot's actual legacy window in charge.
featureEnabled=true; assert(not LegacyGate())
SocialUIFrame={}; assert(LegacyGate())
featureEnabled=false; assert(not LegacyGate())
C_SocialUI.IsSystemEnabled=function() error('API temporarily unavailable') end
assert(not LegacyGate())
C_SocialUI.IsSystemEnabled=function() return featureEnabled end
SocialUIFrame=nil; featureEnabled=true

-- Existing owner applies exactly when Blizzard_FriendsFrame arrives later.
EBS:OnEnable(); assert(applies==1 and skins==0)
event('ADDON_LOADED','Unrelated'); flush(); assert(skins==0)
FriendsFrame=CreateFrame(); FriendsFrame.scripts.OnMouseDown=function() end
local mouse=FriendsFrame.scripts.OnMouseDown
event('ADDON_LOADED','Blizzard_FriendsFrame'); flush(); assert(skins==1)
assert(FriendsFrame.scripts.OnMouseDown==mouse and not FriendsFrame.shown)
friendsSkinned=true; FriendsFrame:Show(); flush(); assert(skins==1 and FriendsFrame.shown)
FriendsFrame:Hide(); assert(not FriendsFrame.shown)

-- Delayed work rechecks preferences and the replacement gate.
event('ADDON_LOADED','Blizzard_FriendsFrame'); EBS.db.profile.friends.enabled=false
flush(); assert(skins==1 and EBS.db.profile.friends.enabled==false)
ApplyOwner(); assert(skins==1 and EBS.db.profile.friends.enabled==false)
EBS.db.profile.friends.enabled=true
event('ADDON_LOADED','Blizzard_FriendsFrame'); SocialUIFrame={}; flush(); assert(skins==1)
SocialUIFrame=nil; combat=true; ApplyOwner(); assert(queued==1 and skins==1)
combat=false; ApplyOwner(); assert(skins==2)

-- Already-loaded owner path and initially disabled addon remain distinct.
frames={}; timers={}; EBS:OnEnable(); assert(skins==3)
EBS.db.profile.friends.enabled=false; frames={}; timers={}; FriendsFrame=nil
EBS:OnEnable(); assert(skins==3 and EBS.db.profile.friends.enabled==false)
for _,f in ipairs(frames) do assert(not f.events.ADDON_LOADED) end

-- Existing Retail enable policy and SocialUI LOD path are unchanged.
EUI_FOREVER=false; featureEnabled=false; frames={}; timers={}
EBS:OnEnable(); assert(EBS.db.profile.friends.enabled==true)
FriendsFrame=CreateFrame(); event('ADDON_LOADED','Blizzard_FriendsFrame'); flush(); assert(skins==3)
event('ADDON_LOADED','Blizzard_SocialUI'); flush(); assert(skins==4)
featureEnabled=true; assert(LegacyGate())
''')

bars = between(packs, 'ns.GuildScrollBar = function(bar)', '\nlocal function SkinGuildControlHost')
stock_bar = between(engine, 'function WSkin.ScrollBar(sb, keepSteppers)', '\n-- Recursively flatten')
stock_bars = between(engine, 'function WSkin.ScrollBarsIn(frame, depth)', '\n-- Close (X)')
lua.execute(r'''
EUI_FOREVER=true; ns={}; WSkin={}; data=setmetatable({}, {__mode='k'})
function GetFFD(f) if not data[f] then data[f]={} end; return data[f] end
function tex(alpha)
 local t={alpha=alpha,atlas='native-disabled',shown=false,color={.2,.4,.6}}
 function t:GetAlpha() return self.alpha end
 function t:SetAlpha(a) self.alpha=a end
 return t
end
function host(...)
 local f={children={...},regions={},shown=false,value=31,enabled=false,scripts={OnClick=function() end}}
 function f:GetChildren() return unpack(self.children) end
 function f:IsForbidden() return self.forbidden end
 return f
end
function bar()
 local f=host(); f.Back=host(); f.Back.Texture=tex(.65); f.Back.regions={f.Back.Texture}
 f.Forward=host(); f.Forward.Texture=tex(0); f.Forward.regions={f.Forward.Texture}
 f.Track=host(); return f
end
function FadeRegions(f) for _,t in ipairs(f.regions) do t:SetAlpha(0) end end
function WSkin.IsForeignFrame(f) return f.foreign end
''')
lua.execute(stock_bar + stock_bars + bars)
lua.execute(r'''
local b=bar(); local nativeClick=b.Back.scripts.OnClick
ns.GuildScrollBar(b); ns.GuildScrollBar(b)
assert(b.Back.Texture.alpha==.65 and b.Forward.Texture.alpha==0)
assert(b.Back.Texture.atlas=='native-disabled' and not b.Back.Texture.shown)
assert(b.Back.scripts.OnClick==nativeClick and not b.enabled and not b.shown and b.value==31)
local nested=bar(); local foreign=bar(); foreign.foreign=true
local blocked=host(bar()); blocked.forbidden=true
local root=host(host(nested),foreign,blocked)
ns.GuildScrollBarsIn(root)
assert(GetFFD(nested).skinned and nested.Back.Texture.alpha==.65)
assert(not GetFFD(foreign).skinned and not GetFFD(blocked.children[1]).skinned)
ns.GuildScrollBar(nil)
EUI_FOREVER=false; local retail=bar(); ns.GuildScrollBarsIn(host(retail))
assert(retail.Back.Texture.alpha==0 and retail.Forward.Texture.alpha==0)
''')

unread_source = (native / 'Blizzard_Communities/CommunitiesStreams.lua').read_text(encoding='utf-8')
native_unread = between(unread_source, 'function CommunitiesStreamDropdownMixin:UpdateUnreadNotification()', '\nfunction CommunitiesStreamDropdownMixin:GetCommunitiesFrame')
skin_unread = between(packs, '        if f.StreamDropdown.NotificationOverlay and not EUI_FOREVER then', '\n        WSkin.Dropdown(f.StreamDropdown)')
lua.execute(r'''
CommunitiesStreamDropdownMixin={}
CommunitiesUtil={DoesCommunityHaveOtherUnreadMessages=function(club,ignore)
 assert(club==71 and ignore==92); return unread
end}
overlay={alpha=.85,shown=false,icon=tex(.7)}
function overlay:SetShown(v) self.shown=v end
function overlay:SetAlpha(v) self.alpha=v end
function WSkin.FadeRegions(f) f.icon:SetAlpha(0) end
f={StreamDropdown={NotificationOverlay=overlay}}
community={GetSelectedClubId=function() return selected end,GetSelectedStreamId=function() return 92 end}
function f.StreamDropdown:GetCommunitiesFrame() return community end
''')
lua.execute(native_unread + '\nfunction applyNotificationSkin()\n' + skin_unread + '\nend')
lua.execute(r'''
EUI_FOREVER=true; selected=71; unread=true
local updater=CommunitiesStreamDropdownMixin.UpdateUnreadNotification
updater(f.StreamDropdown); applyNotificationSkin(); assert(overlay.shown and overlay.alpha==.85 and overlay.icon.alpha==.7)
unread=false; updater(f.StreamDropdown); applyNotificationSkin(); assert(not overlay.shown and overlay.alpha==.85)
unread=true; updater(f.StreamDropdown); applyNotificationSkin(); assert(overlay.shown)
selected=nil; updater(f.StreamDropdown); applyNotificationSkin(); assert(not overlay.shown)
assert(updater==CommunitiesStreamDropdownMixin.UpdateUnreadNotification)
EUI_FOREVER=false; applyNotificationSkin(); assert(overlay.alpha==0 and overlay.icon.alpha==0)
''')

# Exercise the exact Guild tab branch with native Communities click methods.
# These CheckButtons are distinct from Camelot's LargeSideTabButtonTemplate.
tab_keys = between(packs, 'local GUILD_TAB_KEYS =', '\n')
tab_skin = between(packs, '    -- Forever retains RightSideTabTemplate', '\n    -- Club finder')
tab_refresh = between(packs, '        for _, key in ipairs(GUILD_TAB_KEYS) do', '\n        WSkin.Restrip("guild")')
native_tabs = (native / 'Blizzard_Communities/CommunitiesTabs.lua').read_text(encoding='utf-8')
native_right = (native / 'Blizzard_SharedXML/Shared/Tabs/RightSideTab.lua').read_text(encoding='utf-8')
lua.execute(r'''
function CreateFromMixins(original)
 local copy={}; for k,v in pairs(original) do copy[k]=v end; return copy
end
SOUNDKIT={IG_MAINMENU_OPTION_CHECKBOX_ON=1}
function PlaySound() end
function IsShiftKeyDown() return shifted end
Settings={SOCIAL_CATEGORY_ID=17,OpenToCategory=function(id) assert(id==17); settingsOpens=(settingsOpens or 0)+1 end}
Theme={accR=.1,accG=.8,accB=.6,bgR=.05,bgG=.05,bgB=.05,bgA=.95}
function GetFileIDFromPath(path) assert(path=='Interface\\SpellBook\\SpellBook-SkillLineTab'); return 98765 end
function cosmetic()
 local t=tex(.8); t.shown=true; t.uv={.03125,.96875,.03125,.96875}; t.mask={native=true}
 function t:SetVertexColor(...) self.tint={...} end
 function t:SetTexCoord(...) assert(not (EUI_FOREVER and self.nativeIcon),'Forever icon cropped'); self.uv={...} end
 function t:SetPoint() end
 function t:ClearAllPoints() self.allPoints=nil end
 function t:SetAllPoints(target) self.allPoints=target end
 function t:SetTexture(path) self.texture=path; self.atlas=nil end
 function t:AddMaskTexture(mask) self.appliedMask=mask; self.maskAdds=(self.maskAdds or 0)+1 end
 function t:GetTexture() return self.texture end
 function t:GetDrawLayer() return self.layer end
 return t
end
function newTab(parent,id)
 local t=host(); t.parent=parent; t.displayMode=id; t.Icon=cosmetic(); t.checkedArt=cosmetic(); t.hover=cosmetic()
 t.Icon.nativeIcon=true
 t.IconOverlay=cosmetic(); t.NotificationOverlay={shown=true,pulse={playing=true},Icon=cosmetic()}
 t.anchor={'TOPLEFT',parent,'TOPRIGHT',0,-36}; t.width=32; t.height=32; t.alpha=.73
 t.checkedArt.shown=false; t.checkedArt.atlas='native-CheckButtonHilight'; t.hover.atlas='native-ButtonHilight-Square'
 t.checkedArt.blend='ADD'; t.hover.blend='ADD'
 t.backing=cosmetic(); t.backing.layer='BORDER'
 t.backing.texture=id%2==0 and 98765 or 'Interface/SpellBook/SpellBook-SkillLineTab'
 t.unknown=cosmetic(); t.unknown.layer='BORDER'; t.unknown.texture='new-semantic-art'
 t.hover.layer='HIGHLIGHT'; t.hover.texture='Interface\\Buttons\\ButtonHilight-Square'
 t.regions={t.Icon,t.IconOverlay,t.checkedArt,t.hover,t.backing,t.unknown}
 function t:GetRegions() return unpack(self.regions) end
 function t:GetCheckedTexture() return self.checkedArt end
 function t:GetHighlightTexture() return self.hover end
 function t:CreateMaskTexture() self.maskCreates=(self.maskCreates or 0)+1; return cosmetic() end
 function t:GetParent() return self.parent end
 function t:SetChecked(v) self.checked=v; self.checkedArt.shown=v end
 function t:IsEnabled() return self.enabled end
 function t:SetAlphaFromBoolean(v,a,b) assert(not EUI_FOREVER,'Forever native alpha overwritten'); self.alpha=v and a or b end
 function t:GetPoint() return unpack(self.anchor) end
 function t:ClearAllPoints() assert(not EUI_FOREVER,'Forever tab layout overwritten') end
 function t:SetPoint(...) assert(not EUI_FOREVER,'Forever tab reanchored'); self.anchor={...} end
 function t:GetFrameLevel() return 510 end
 return t
end
function SquareTabIcon(tab) assert(not EUI_FOREVER,'Forever icon/mask flattened'); tab.squared=true end
function CreateFrame()
 assert(not EUI_FOREVER,'Forever added square plate')
 local f={}; function f:SetPoint() end; function f:SetFrameLevel() end; return f
end
function SolidTex() return cosmetic() end
function WSkin.AddBorder(f) f.border=true end
''')
lua.execute(native_right + native_tabs)
lua.execute(r'''
EUI_FOREVER=true
f={}; function f:SetDisplayMode(v) self.displayMode=v end
function f:IsChatAccessible() return chatAccessible end
for i,key in ipairs({'ChatTab','RosterTab','GuildBenefitsTab','GuildInfoTab','GuildPreferredPlaySettingsTab'}) do
 f[key]=newTab(f,i); f[key].OnClick=CommunitiesFrameTabMixin.OnClick
end
f.ChatTab.OnClick=CommunitiesChatTabMixin.OnClick
f.GuildBenefitsTab.enabled=false; f.GuildBenefitsTab.shown=false
f.RosterTab.enabled=true; f.RosterTab.shown=true
''')
lua.execute(tab_keys + '\nfunction applyGuildTabs()\n' + tab_skin + '\nend\nfunction refreshGuildTabAlpha()\n' + tab_refresh + '\nend')
lua.execute(r'''
local click=f.ChatTab.OnClick
applyGuildTabs(); applyGuildTabs(); refreshGuildTabAlpha()
for _,key in ipairs({'ChatTab','RosterTab','GuildBenefitsTab','GuildInfoTab','GuildPreferredPlaySettingsTab'}) do
 local t=f[key]
 assert(not t.squared and not GetFFD(t).box and not GetFFD(t).bg)
 assert(t.backing.alpha==0 and t.unknown.alpha==.8,'decorative backing was kept or unrelated art was hidden')
 assert(t.Icon.mask.native and t.Icon.uv[1]==.03125 and t.Icon.uv[2]==.96875 and t.Icon.alpha==.8)
 assert(t.checkedArt.texture=='Interface\\AddOns\\EllesmereUI\\media\\portraits\\csquare_border.tga' and t.checkedArt.tint[2]==.8 and not t.checkedArt.shown)
 assert(t.hover.texture==t.checkedArt.texture and t.hover.alpha==.8 and t.IconOverlay.shown)
 assert(t.checkedArt.blend=='ADD' and t.hover.blend=='ADD')
 assert(t.checkedArt.allPoints==t.Icon and t.hover.allPoints==t.Icon and t.checkedArt.uv[1]==10/128 and t.checkedArt.uv[2]==118/128)
 local mask=GetFFD(t).foreverCornerMask
 assert(mask.texture=='Interface\\AddOns\\EllesmereUI\\media\\portraits\\csquare_mask.tga' and mask.allPoints==t.Icon)
 assert(mask.uv[1]==t.checkedArt.uv[1] and mask.uv[2]==t.checkedArt.uv[2])
 assert(t.maskCreates==1 and t.Icon.maskAdds==1 and t.IconOverlay.maskAdds==1)
 assert(t.Icon.appliedMask==mask and t.IconOverlay.appliedMask==mask)
 assert(t.NotificationOverlay.shown and t.NotificationOverlay.pulse.playing)
 assert(t.width==32 and t.height==32 and t.anchor[4]==0 and t.anchor[5]==-36 and t.alpha==.73)
end
assert(not f.GuildBenefitsTab.enabled and not f.GuildBenefitsTab.shown and f.RosterTab.enabled and f.RosterTab.shown)
assert(f.ChatTab.OnClick==click)
chatAccessible=true; f.ChatTab:OnClick('LeftButton'); applyGuildTabs(); assert(f.displayMode==1 and f.ChatTab.checkedArt.shown)
chatAccessible=false; f.ChatTab:OnClick('LeftButton'); applyGuildTabs(); assert(not f.ChatTab.checkedArt.shown)
shifted=true; f.ChatTab:OnClick('LeftButton'); assert(settingsOpens==1); shifted=false
f.RosterTab:OnClick(); applyGuildTabs(); assert(f.displayMode==2 and f.RosterTab.checkedArt.shown)
f.RosterTab:SetChecked(false); applyGuildTabs(); assert(not f.RosterTab.checkedArt.shown)
assert(f.RosterTab.maskCreates==1 and f.RosterTab.Icon.maskAdds==1,'repaint duplicated mask')
local checkedIdentity=f.RosterTab.checkedArt; local hoverIdentity=f.RosterTab.hover
f.RosterTab.checkedArt.alpha=.41; f.RosterTab.hover.shown=false
applyGuildTabs()
assert(f.RosterTab.checkedArt==checkedIdentity and f.RosterTab.hover==hoverIdentity)
assert(f.RosterTab.checkedArt.alpha==.41 and not f.RosterTab.hover.shown,'native indicator visibility changed')

-- Same branch retains the existing square/crop/layout on Retail.
EUI_FOREVER=false; applyGuildTabs(); refreshGuildTabAlpha()
assert(f.ChatTab.squared and GetFFD(f.ChatTab).box.border and f.ChatTab.Icon.uv[1]==.12)
assert(f.ChatTab.anchor[4]==1 and f.RosterTab.anchor[5]==-26 and f.GuildBenefitsTab.alpha==.5)
''')

compile_lua = lua.eval('function(s) local f, e=loadstring(s); assert(f,e) end')
compile_lua(friends)
compile_lua(packs)
assert not (ADDONS / 'EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_ForeverFriends.lua').exists(), 'Competing Friends adapter present'
guild = between(packs, 'ns.GuildScrollBar = function(bar)', '--  Calendar (CalendarFrame)')
assert guild.count('WSkin.ScrollBar(bar)') == 2
assert 'WSkin.ScrollBar(' not in guild[guild.index('local function SkinGuildControlHost'):]
assert 'WSkin.ScrollBarsIn(' not in guild[guild.index('local function SkinGuildControlHost'):]
print('PASS: Friends routing/LOD/preferences/combat/ownership; Guild arrows/unread states, clipped icon masks and matching native checked/hover outlines, preserved overlays/availability/actions; asset alignment, Retail branch and Lua 5.1 syntax.')
