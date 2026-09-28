"""Native group adapter: combat, identity/state, roster discovery and anchors."""
from pathlib import Path
import sys
from lupa.lua51 import LuaRuntime

lua = LuaRuntime(unpack_returned_tuples=True)
lua.globals().test_build = sys.argv[1] if len(sys.argv) > 1 else "69977"
lua.execute(r'''
EUI_FOREVER=true; EUI_FOREVER_STATUS={}; combat=false; mutations=0; settingsWrites=0
CompactRaidGroupTypeEnum={Party=1,Raid=2,Arena=3}
Enum={EditModeUnitFrameSetting={UseRaidStylePartyFrames=1,FrameWidth=2,FrameHeight=3,UseHorizontalGroups=4}}
STANDARD_TEXT_FONT='font.ttf'
function GetBuildInfo() return '1.60.1',test_build end
function InCombatLockdown() return combat end
local function geom() assert(not combat,'protected geometry mutated in combat'); mutations=mutations+1 end
function make(extra)
 local f=extra or {}; f.points={}; f.scripts=f.scripts or {}; f.attributes={unit='untouched'}
 function f:SetSize(w,h) geom(); self.w=w; self.h=h end
 function f:SetWidth(w) geom(); self.w=w end
 function f:SetHeight(h) geom(); self.h=h end
 function f:GetWidth() return self.w or 72 end
 function f:GetHeight() return self.h or 36 end
 function f:GetEffectiveScale() return 1 end
 function f:ClearAllPoints() geom(); self.points={} end
 function f:SetPoint(...) geom(); table.insert(self.points,{...}) end
 function f:SetAttribute() error('native unit/secure attribute changed') end
 function f:SetParent() error('native parent changed') end
 function f:Show() error('native visibility changed') end
 function f:Hide() error('native visibility changed') end
 function f:IsShown() return self.shown~=false end
 function f:SetScript(k,v) assert(self.eventOwner,'native scripts replaced'); self.scripts[k]=v end
 function f:RegisterEvent() end
 function f:CreateTexture() geom(); local t=make(); self.created=self.created or {}; table.insert(self.created,t); return t end
 function f:SetColorTexture(...) self.color={...} end
 function f:SetVertexColor(...) self.vertex={...} end
 function f:SetAlpha(a) self.alpha=a end
 function f:SetStatusBarTexture(t) self.texture=t end
 function f:SetStatusBarColor() error('native class/power state overwritten') end
 function f:SetMinMaxValues() error('native unit data overwritten') end
 function f:SetValue() error('native unit data overwritten') end
 function f:GetValue() error('secret health read') end
 function f:GetMinMaxValues() error('secret health range read') end
 function f:GetStatusBarColor() error('secret native color read') end
 function f:AddMaskTexture() error('native mask changed') end
 function f:RemoveMaskTexture() error('native mask changed') end
 function f:SetFont(path,size,flags) self.font={path,size,flags} end
 function f:SetTextColor(...) self.textColor={...} end
 function f:SetJustifyH(v) self.justify=v end
 function f:SetShouldAdjustHealthBarAnchor() error('native max-health Lua fields tainted') end
 function f:SetPowerBarUsedHeight() error('native private-aura Lua fields tainted') end
 return f
end
UIParent=make({w=1920,h=1080})
function unit(kind,name)
 return make({groupType=kind,unit=name,displayedUnit=name,healthBar=make(),powerBar=make({background=make()}),
  background=make(),name=make(),statusText=make(),TempMaxHealthLoss=make(),
  selectionHighlight=make(),aggroHighlight=make(),totalAbsorb=make(),readyCheckIcon=make(),roleIcon=make(),
  scripts={OnClick='nativeClick',OnEvent='nativeEvents'},optionTable={useClassColors=true}})
end
PartyUnits={unit(1,'player'),unit(1,'party1')}
RaidUnits={unit(2,'raid1'),unit(2,'raid2')}
Nameplate=unit(nil,'nameplate1'); Arena=unit(3,'arena1')
function system(extra)
 local f=make(extra); f.settings={[1]=0,[2]=72,[3]=36,[4]=0}
 function f:IsInitialized() return true end
 function f:HasSetting() return true end
 function f:GetSettingValue(k,raw) return self.settings[k] end
 function f:ConvertSettingDisplayValueToRawValue(k,v)
  if quantize and (k==2 or k==3) then return math.floor(v+.5) end
  return v
 end
 function f:ApplySystemAnchor()
  self:ClearAllPoints(); self:SetPoint('TOPLEFT',UIParent,'TOPLEFT',self.savedX or 240,self.savedY or -180)
 end
 function f:Layout() end
 return f
end
PartyFrame=system()
PartyFrame:ApplySystemAnchor()
function standardPart(extra)
 local f=make(extra)
 local function forbidden() error('standard party native geometry changed; health resize enters secret prediction update') end
 f.SetSize=forbidden; f.SetWidth=forbidden; f.SetHeight=forbidden
 f.SetPoint=forbidden; f.ClearAllPoints=forbidden
 return f
end
function standardUnit(name)
 local f=standardPart({unit=name,unitToken=name,displayedUnit=name,
  scripts={OnClick='nativePartyClick',OnEvent='nativePartyEvents'},Name=standardPart(),
  HealthBarContainer=standardPart({HealthBar=standardPart({masks={'nativeHealthMask'},texture='native-health'}),
   CenterText=standardPart(),LeftText=standardPart(),RightText=standardPart(),
   HealthBarMask=standardPart(),TempMaxHealthLoss=standardPart()}),
  ManaBar=standardPart({masks={'nativeManaMask'},texture='native-power',CenterText=standardPart(),LeftText=standardPart(),RightText=standardPart()}),
  Portrait=standardPart(),PortraitMask=standardPart(),Texture=standardPart(),VehicleTexture=standardPart({shown=false}),
  Flash=standardPart(),PowerBarAlt=standardPart({shown=false}),
  PartyMemberOverlay=standardPart({RoleIcon=standardPart(),Disconnect=standardPart({shown=false})}),
  ReadyCheck=standardPart(),NotPresentIcon=standardPart(),PetFrame=standardPart(),AuraFrameContainer=standardPart()})
 function f:UpdateArt()
  assert(nativeEvent,'addon invoked standard party art/unit refresh')
  self.HealthBarContainer.HealthBar.texture='native-health'; self.ManaBar.texture='native-power'
 end
 function f:UpdateMember() error('addon invoked standard party unit refresh') end
 function f:Setup() error('addon invoked standard party secure setup') end
 return f
end
StandardUnits={standardUnit('party1'),standardUnit('party2')}
PartyFrame.PartyMemberFramePool={}
function PartyFrame.PartyMemberFramePool:EnumerateActive()
 local i=0; return function() i=i+1; return StandardUnits[i] end
end
function PartyFrame:InitializePartyMemberFrames() assert(nativeEvent,'addon invoked native party initialization') end
CompactPartyFrame=make({groupType=1,memberUnitFrames=PartyUnits})
RaidGroup=make({groupType=2,memberUnitFrames=RaidUnits})
CompactRaidFrameContainer=system()
CompactRaidFrameContainer:ApplySystemAnchor()
function CompactRaidFrameContainer:ApplyToFrames(kind,fn)
 if kind=='normal' then for _,f in ipairs(RaidUnits) do fn(f) end; for _,f in ipairs(PartyUnits) do fn(f) end
 elseif kind=='group' then fn(RaidGroup); fn(CompactPartyFrame) end
end
function CompactRaidGroup_UpdateLayout(f)
 assert(nativeEvent,'addon invoked native group layout')
 f:SetSize(f.memberUnitFrames[1]:GetWidth(),#f.memberUnitFrames*f.memberUnitFrames[1]:GetHeight()+14)
end
function CompactPartyFrame:UpdateLayout() assert(nativeEvent,'addon invoked native party layout'); CompactRaidGroup_UpdateLayout(self) end
function DefaultCompactUnitFrameSetup() end
function CompactUnitFrame_UpdateName() end
function CompactUnitFrame_UpdateHealthColor() end
function FlowContainer_SetHorizontalSpacing(f,v) geom(); f.hSpacing=v end
function FlowContainer_SetVerticalSpacing(f,v) geom(); f.vSpacing=v end
EditModeManagerFrame={}
function EditModeManagerFrame:IsEditModeActive() return editing end
function EditModeManagerFrame:OnSystemSettingChange() error('addon entered taint-sensitive native unit refresh') end
function EditModeManagerFrame:ShouldRaidFrameUseHorizontalRaidGroups(kind) return kind==1 and PartyFrame.settings[4]==1 end
timers={}; C_Timer={After=function(_,fn) table.insert(timers,fn) end}
function flush()
 local count=0
 while #timers>0 do count=count+1; assert(count<10,'layout refresh loop'); table.remove(timers,1)() end
end
events={}
function CreateFrame() local f=make({eventOwner=true}); events[#events+1]=f; return f end
function hooksecurefunc(a,b,c)
 local target,key,callback
 if type(a)=='string' then target,key,callback=_G,a,b else target,key,callback=a,b,c end
 local original=target[key]
 target[key]=function(...) local result={original(...)}; callback(...); return unpack(result) end
end
function fire() for _,e in ipairs(events) do e.scripts.OnEvent(e,'GROUP_ROSTER_UPDATE') end end
EventRegistry={callbacks={}}
function EventRegistry:RegisterCallback(event,fn) self.callbacks[event]=fn end
function EventRegistry:TriggerEvent(event) self.callbacks[event]() end
addon={}; EllesmereUI={Lite={},Widgets={}}
function EllesmereUI.Lite.NewAddon() return addon end
function EllesmereUI.Lite.NewDB(_,d)
 local p={frameWidth=107,frameHeight=40,unlockPos={point='CENTER',relPoint='CENTER',x=-717,y=9},
 partyUnlockPos={point='CENTER',relPoint='CENTER',x=-868,y=9}}
 setmetatable(p,{__index=d.profile}); return {profile=p}
end
function EllesmereUI.BuildBarTextureTables() return {atrocity='eui-health.tga'} end
function EllesmereUI.GetFontPath() return 'eui-font.ttf' end
function EllesmereUI.GetFontOutlineFlag() return 'OUTLINE' end
function EllesmereUI:RegisterModule() end
''')
path = Path(__file__).resolve().parents[2] / "EllesmereUIRaidFrames/EllesmereUIRaidFrames_Forever.lua"
source = path.read_text(encoding="utf-8-sig")
# Other client families must still use their original group module.
other_client = LuaRuntime(unpack_returned_tuples=True)
other_client.execute('assert(loadstring(...))("test")', source)
assert other_client.globals().EUI_FOREVER_NATIVE_GROUPS is None
for forbidden in ("OnSystemSettingChange(", "UpdateSystemSettingValue(", "CompactUnitFrame_UpdateAll(", "CompactUnitFrame_UpdateAllFromEditMode(", ":RefreshMembers(", "UnitFrame_Update(", ":UpdateArt(", ":UpdateMember(", ":InitializePartyMemberFrames(", ":SetPowerBarUsedHeight(", ":SetShouldAdjustHealthBarAnchor("):
    assert forbidden not in source, f"Addon-driven native refresh reintroduced: {forbidden}"
lua.execute('assert(loadstring(...))("test")', source)
lua.execute(r'''
addon:OnInitialize(); addon:OnEnable(); flush()
assert(EUI_FOREVER_NATIVE_GROUPS)
assert(RaidUnits[1].w==107 and RaidUnits[1].h==40)
assert(PartyUnits[1].w==125 and PartyUnits[1].h==60)
assert(RaidUnits[1].healthBar.texture=='eui-health.tga' and RaidUnits[1].powerBar.texture=='eui-health.tga')
assert(RaidUnits[1].name.font[2]==10 and RaidUnits[1].name.justify=='LEFT')
assert(RaidUnits[1].powerBar.h==4 and RaidUnits[1].powerUsed==nil)
assert(RaidUnits[1].TempMaxHealthLoss.lossAnchor==nil)
assert(RaidUnits[1].scripts.OnClick=='nativeClick' and RaidUnits[1].attributes.unit=='untouched')
assert(RaidUnits[1].selectionHighlight.alpha==nil and RaidUnits[1].aggroHighlight.alpha==nil)
assert(RaidUnits[1].totalAbsorb.alpha==nil and RaidUnits[1].readyCheckIcon.alpha==nil)
assert(RaidUnits[1].optionTable.useClassColors==true)
assert(CompactRaidFrameContainer.points[1][4]==240 and CompactRaidFrameContainer.points[1][5]==-180,'startup overwrote native raid position')
assert(PartyFrame.points[1][4]==240 and PartyFrame.points[1][5]==-180,'startup overwrote native party position')
assert(CompactRaidFrameContainer.settings[2]==72 and CompactRaidFrameContainer.settings[3]==36)
assert(PartyFrame.settings[1]==0 and PartyFrame.settings[2]==72)
assert(settingsWrites==0,'native Edit Mode settings changed')
local writes=settingsWrites
local oldWidth=UIParent.w
UIParent.w=1800; fire(); flush()
assert(PartyFrame.points[1][4]==240,'screen change overwrote native party position')
assert(CompactRaidFrameContainer.points[1][4]==240,'screen change overwrote native raid position')
UIParent.w=oldWidth; fire(); flush()
fire(); flush(); assert(settingsWrites==writes,'native settings needlessly rewritten')
DefaultCompactUnitFrameSetup(Nameplate); CompactUnitFrame_UpdateHealthColor(Nameplate)
DefaultCompactUnitFrameSetup(Arena); CompactUnitFrame_UpdateName(Arena); flush()
assert(Nameplate.healthBar.texture==nil and Nameplate.name.font==nil and Arena.healthBar.texture==nil)
local before=mutations; combat=true
DefaultCompactUnitFrameSetup(RaidUnits[1]); CompactUnitFrame_UpdateName(RaidUnits[1]); fire(); flush()
assert(mutations==before and #timers==0,'protected combat operation')
RaidUnits[#RaidUnits+1]=unit(2,'raid3')
DefaultCompactUnitFrameSetup(RaidUnits[3]); assert(RaidUnits[3].healthBar.texture=='eui-health.tga')
assert(RaidUnits[3].w==nil,'new frame resized in combat')
combat=false; fire(); flush()
assert(RaidUnits[3].w==107 and RaidUnits[3].scripts.OnClick=='nativeClick')
-- Combined/flush discovery supplies a new frame not present in a discrete group.
local extra=unit(2,'raid4'); local original=CompactRaidFrameContainer.ApplyToFrames
function CompactRaidFrameContainer:ApplyToFrames(kind,fn)
 original(self,kind,fn); if kind=='normal' then fn(extra) end
end
fire(); flush(); assert(extra.w==107 and extra.unit=='raid4')
assert(CompactRaidFrameContainer.points[1][4]==240,'roster changed native origin')
-- Native power visibility stays native, including hidden bars and role NONE.
extra.powerBar.shown=false; fire(); flush(); assert(extra.powerUsed==nil and extra.powerBar.shown==false)
assert(extra.healthBar.points[2][5]==1)
addon.db.profile.partySyncSections={textDisplay=false}; addon.db.profile.party_nameSize=14
fire(); flush(); assert(PartyUnits[1].name.font[2]==14 and RaidUnits[1].name.font[2]==10)
-- Noninteger UI scale and native rounding must settle without repeated dirty
-- setting writes even when the requested physical size is fractional.
EllesmereUI.PP={perfect=1}; function UIParent:GetEffectiveScale() return .711111 end
quantize=true; fire(); flush(); local scaledWrites=settingsWrites
fire(); flush(); fire(); flush()
assert(settingsWrites==scaledWrites,'fractional scale repeatedly dirtied native settings')
-- Standard party members use actual pool identity, retain native geometry and
-- masks, and receive cosmetics without invoking native unit/health refresh.
local s=StandardUnits[1]
assert(s.HealthBarContainer.HealthBar.texture=='native-health' and s.ManaBar.texture=='native-power')
assert(s.Name.font[2]==14 and s.Name.textColor[1]==1)
assert(s.HealthBarContainer.CenterText.font[2]==9 and s.ManaBar.RightText.font[2]==9)
assert(#s.created==4 and s.created[1].color[1]==0)
assert(s.unit=='party1' and s.attributes.unit=='untouched' and s.scripts.OnClick=='nativePartyClick')
assert(s.HealthBarContainer.HealthBar.masks[1]=='nativeHealthMask' and s.ManaBar.masks[1]=='nativeManaMask')
assert(s.Portrait.alpha==nil and s.Texture.alpha==nil and s.VehicleTexture.shown==false)
assert(s.PartyMemberOverlay.RoleIcon.alpha==nil and s.PartyMemberOverlay.Disconnect.shown==false)
assert(s.ReadyCheck.alpha==nil and s.AuraFrameContainer.alpha==nil and s.PetFrame.alpha==nil)
assert(s.PowerBarAlt.shown==false and s.HealthBarContainer.HealthBar.alpha==nil)
nativeEvent=true; s:UpdateArt(); nativeEvent=false
assert(s.HealthBarContainer.HealthBar.texture=='native-health','posthook should queue, not reenter native art')
flush(); assert(s.HealthBarContainer.HealthBar.texture=='native-health')
-- A newly acquired/reused pool member is discovered after native initialization.
local reused=StandardUnits[2]; StandardUnits={s,standardUnit('party3'),reused}
nativeEvent=true; PartyFrame:InitializePartyMemberFrames(); nativeEvent=false
flush(); assert(StandardUnits[2].Name.font[2]==14 and #reused.created==4)
-- Combat changes queue cosmetics until regen; no border creation/geometry.
local count=mutations; combat=true; nativeEvent=true; s:UpdateArt(); nativeEvent=false
StandardUnits[#StandardUnits+1]=standardUnit('party4'); fire(); flush()
assert(mutations==count and StandardUnits[4].Name.font==nil and s.HealthBarContainer.HealthBar.texture=='native-health')
combat=false; fire(); flush()
assert(StandardUnits[4].Name.font[2]==14 and s.HealthBarContainer.HealthBar.texture=='native-health')
-- Native Edit Mode sets its flag false BEFORE resetting party frames. Hold the
-- enter-event latch until Exit, then queue work after the native call stack ends.
fire(); local beforeEdit=mutations
editing=true; EventRegistry:TriggerEvent('EditMode.Enter')
RaidUnits[1].healthBar.texture='native-preview'
s.HealthBarContainer.HealthBar.texture='native-standard-preview'
DefaultCompactUnitFrameSetup(RaidUnits[1]); CompactUnitFrame_UpdateName(RaidUnits[1])
CompactUnitFrame_UpdateHealthColor(RaidUnits[1]); fire(); flush()
assert(mutations==beforeEdit and RaidUnits[1].healthBar.texture=='native-preview')
assert(s.HealthBarContainer.HealthBar.texture=='native-standard-preview')
nativeEvent=true; CompactRaidGroup_UpdateLayout(RaidGroup); nativeEvent=false
assert(RaidGroup.h==#RaidUnits*RaidUnits[1]:GetHeight()+14,'group spacing changed in Edit Mode')
beforeEdit=mutations
editing=false
DefaultCompactUnitFrameSetup(RaidUnits[1]); CompactUnitFrame_UpdateHealthColor(RaidUnits[1]); fire(); flush()
assert(mutations==beforeEdit and RaidUnits[1].healthBar.texture=='native-preview','styling resumed during native exit reset')
EventRegistry:TriggerEvent('EditMode.Exit')
assert(mutations==beforeEdit and RaidUnits[1].healthBar.texture=='native-preview','exit callback must only schedule')
flush()
assert(RaidUnits[1].healthBar.texture=='eui-health.tga' and s.HealthBarContainer.HealthBar.texture=='native-standard-preview')
-- Saving a drag must survive the exit styling pass, later native layouts,
-- roster changes, combat exit, and a new addon instance after reload.
editing=true; EventRegistry:TriggerEvent('EditMode.Enter')
PartyFrame.savedX=420; PartyFrame.savedY=-260
CompactRaidFrameContainer.savedX=680; CompactRaidFrameContainer.savedY=-320
PartyFrame:ApplySystemAnchor(); CompactRaidFrameContainer:ApplySystemAnchor()
editing=false; EventRegistry:TriggerEvent('EditMode.Exit'); flush()
function assertSavedPositions()
 assert(PartyFrame.points[1][3]=='TOPLEFT' and PartyFrame.points[1][4]==420 and PartyFrame.points[1][5]==-260,'saved party drag was lost')
 assert(CompactRaidFrameContainer.points[1][4]==680 and CompactRaidFrameContainer.points[1][5]==-320,'saved raid drag was lost')
end
assertSavedPositions()
PartyFrame:ApplySystemAnchor(); PartyFrame:Layout()
CompactRaidFrameContainer:ApplySystemAnchor(); CompactRaidFrameContainer:Layout()
fire(); flush(); assertSavedPositions()
combat=true; fire(); combat=false; fire(); flush(); assertSavedPositions()
-- Cancel restores the native saved anchor, not the abandoned drag.
editing=true; EventRegistry:TriggerEvent('EditMode.Enter')
PartyFrame:ClearAllPoints(); PartyFrame:SetPoint('TOPLEFT',UIParent,'TOPLEFT',999,-555)
PartyFrame:ApplySystemAnchor()
editing=false; EventRegistry:TriggerEvent('EditMode.Exit'); flush(); assertSavedPositions()
''')
lua.execute('assert(loadstring(...))("test-reload")', source)
lua.execute('addon:OnInitialize(); addon:OnEnable(); flush(); assertSavedPositions()')
print("PASS groups: native refresh/field-write prohibition, Edit Mode entry+exit deferral, compact dimensions, native saved party/raid positions across save/cancel/layout/roster/combat/reload, standard party geometry+mask preservation, textures/fonts/borders, native state/handlers, nameplate+arena exclusion, combat deferral, late/flush/pool roster, power visibility, sparse defaults/party overrides")
