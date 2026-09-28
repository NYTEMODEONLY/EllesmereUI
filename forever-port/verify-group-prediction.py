"""Native group predictions remain native while Forever applies group cosmetics.

Runs the actual Camelot-family prediction calculations with ordinary fixture
values. The native-only guard verifies the addon never queries health/heal data
or mutates prediction layers; it does not simulate the game's secure execution.
"""
from pathlib import Path
import os
import runpy

here = Path(__file__).resolve().parent
fixture = runpy.run_path(str(here / "verify-groups.py"))
lua = fixture["lua"]
native = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ["TEMP"]) / "eui-forever-research/wow-ui-source-forever/Interface/AddOns")) / 'Blizzard_UnitFrame'
compact = (native / "Shared/CompactUnitFrame.lua").read_text(encoding="utf-8-sig")
standard = (native / "Mainline/UnitFrame.lua").read_text(encoding="utf-8-sig")
party = (native / "Mainline/PartyMemberFrame.lua").read_text(encoding="utf-8-sig")
options = (native / "Mainline/CompactUnitFrameOptions.lua").read_text(encoding="utf-8-sig")

# Check the real native setup still supplies the full prediction surface, and
# retains the exact event registrations responsible for updating it in game.
for option_table in ("DefaultCompactUnitFrameOptions", "DefaultCompactMiniFrameOptions"):
    block = options.split(option_table + " = {", 1)[1].split("}", 1)[0]
    assert "displayHealPrediction = true" in block, option_table
for field in ("MyHealPredictionBar", "OtherHealPredictionBar", "TotalAbsorbBar",
              "OverAbsorbGlow", "OverHealAbsorbGlow", "HealAbsorbBar"):
    assert "myHealthbar." + field in party, field
for event in ("UNIT_HEAL_PREDICTION", "UNIT_ABSORB_AMOUNT_CHANGED", "UNIT_HEAL_ABSORB_AMOUNT_CHANGED"):
    assert event in compact and event in standard, event

lua.execute(r'''
max=math.max
local function nativeOnly() assert(nativePrediction, 'addon entered native prediction data/layer path') end
predictionWrites=0
function predictionRegion()
 local r={shown=false,points={},atlas='native-prediction',color='native-color',mask='native-mask'}
 local function write() nativeOnly(); predictionWrites=predictionWrites+1 end
 function r:Show() write(); self.shown=true end
 function r:Hide() write(); self.shown=false end
 function r:SetShown(v) write(); self.shown=v end
 function r:SetWidth(v) write(); self.width=v end
 function r:SetPoint(...) write(); table.insert(self.points,{...}) end
 function r:ClearAllPoints() write(); self.points={} end
 function r:SetAlpha() error('prediction alpha changed') end
 function r:SetVertexColor() error('prediction color changed') end
 function r:SetTexture() error('prediction texture replaced') end
 function r:UpdateFillPosition(previous,amount,offset)
  write(); self.previous=previous; self.amount=amount; self.offset=offset
  self.shown=amount>0; return self.shown and self or previous
 end
 return r
end
function attachHealth(health,owner)
 health.nativeHealthTexture={nativeStatusTexture=true}
 function health:GetMinMaxValues() nativeOnly(); return 0, maximum end
 function health:GetValue() nativeOnly(); return current end
 function health:GetStatusBarTexture() nativeOnly(); return self.nativeHealthTexture end
 if owner then function health:GetWidth() return owner:GetWidth()-2 end end
end
function UnitGetIncomingHeals(unit,source)
 nativeOnly(); assert(unit==expectedUnit,'native prediction queried wrong unit')
 assert(source==nil or source=='player'); return source and incomingMine or incomingAll
end
function UnitGetTotalAbsorbs(unit) nativeOnly(); assert(unit==expectedUnit); return shields end
function UnitGetTotalHealAbsorbs(unit) nativeOnly(); assert(unit==expectedUnit); return healAbsorbs end
function values(health,mine,all,absorb,healAbsorb)
 maximum=1000; current=health; incomingMine=mine; incomingAll=all; shields=absorb; healAbsorbs=healAbsorb
end
function nativeUpdate(fn,frame)
 expectedUnit=frame.displayedUnit or frame.unit
 nativePrediction=true; fn(frame); nativePrediction=false
end
function near(a,b) assert(math.abs(a-b)<0.000001,tostring(a)..' != '..tostring(b)) end
function preserved()
 local before=predictionWrites
 fire(); flush()
 assert(predictionWrites==before,'adapter changed native predictions')
end
compactPredictions={}
for _,list in ipairs({PartyUnits,RaidUnits}) do
 for _,f in ipairs(list) do
  attachHealth(f.healthBar,f)
  f.optionTable.displayHealPrediction=true
  for _,key in ipairs({'myHealPrediction','otherHealPrediction','totalAbsorb','totalAbsorbOverlay',
    'overAbsorbGlow','myHealAbsorb','myHealAbsorbOverlay','myHealAbsorbLeftShadow',
    'myHealAbsorbRightShadow','overHealAbsorbGlow','TotalAbsorbLeftShadow'}) do
   f[key]=predictionRegion()
  end
  f.totalAbsorb.overlay=f.totalAbsorbOverlay
  table.insert(compactPredictions,f)
 end
end
local s=StandardUnits[1]
s.healthbar=s.HealthBarContainer.HealthBar
attachHealth(s.healthbar)
for field,nativeField in pairs({myHealPredictionBar='MyHealPredictionBar',otherHealPredictionBar='OtherHealPredictionBar',
 totalAbsorbBar='TotalAbsorbBar',overAbsorbGlow='OverAbsorbGlow',overHealAbsorbGlow='OverHealAbsorbGlow',healAbsorbBar='HealAbsorbBar'}) do
 local region=predictionRegion(); s[field]=region; s.healthbar[nativeField]=region
end
s.healAbsorbBar.LeftShadow=predictionRegion(); s.healAbsorbBar.RightShadow=predictionRegion()
''')

# Execute the source functions without invoking any other native unit refresh.
lua.execute(compact[compact.index("function CompactUnitFrame_GetHealthValuesActual(frame)"):
                    compact.index('local roles = {"TANK"')])
lua.execute(standard[standard.index("local MAX_INCOMING_HEAL_OVERFLOW = 1.0;"):
                     standard.index("function UnitFrameManaCostPredictionBars_Update(")])
lua.execute(r'''
-- 70% health: the player's 100 heal + someone else's 50 heal + a real 50 shield.
values(700,100,150,50,0)
for _,f in ipairs(compactPredictions) do
 nativeUpdate(CompactUnitFrame_UpdateHealPrediction,f)
 local width=f.healthBar:GetWidth()
 near(f.myHealPrediction.width,width*.10); near(f.otherHealPrediction.width,width*.05)
 near(f.totalAbsorb.width,width*.05)
 assert(f.myHealPrediction.shown and f.otherHealPrediction.shown and f.totalAbsorbOverlay.shown)
 assert(not f.overAbsorbGlow.shown and not f.myHealAbsorb.shown)
 assert(f.myHealPrediction.points[1][2]==f.healthBar.nativeHealthTexture)
 assert(f.otherHealPrediction.points[1][2]==f.myHealPrediction)
 assert(f.totalAbsorb.points[1][2]==f.otherHealPrediction)
end
preserved()
for _,f in ipairs(compactPredictions) do
 assert(f.optionTable.displayHealPrediction==true and f.totalAbsorbOverlay.shown)
 assert(f.myHealPrediction.atlas=='native-prediction' and f.myHealPrediction.mask=='native-mask')
 assert(f.myHealPrediction.color=='native-color')
end
-- Shield overflow and heal-absorb amounts are native quantitative values.
local f=RaidUnits[1]; local width=f.healthBar:GetWidth()
values(700,0,0,500,0); nativeUpdate(CompactUnitFrame_UpdateHealPrediction,f)
near(f.totalAbsorb.width,width*.30); assert(f.overAbsorbGlow.shown)
assert(not f.myHealPrediction.shown and not f.otherHealPrediction.shown)
preserved()
values(700,100,100,50,400); nativeUpdate(CompactUnitFrame_UpdateHealPrediction,f)
near(f.myHealAbsorb.width,width*.30); near(f.myHealPrediction.width,width*.10)
assert(f.myHealAbsorbOverlay.shown and f.myHealAbsorbLeftShadow.shown)
assert(f.totalAbsorb.points[#f.totalAbsorb.points-1][2]==f.myHealAbsorb)
preserved()
-- Native updates can happen in combat; addon styling does not perform them.
combat=true
values(700,0,0,0,900); nativeUpdate(CompactUnitFrame_UpdateHealPrediction,f)
assert(f.overHealAbsorbGlow.shown); near(f.myHealAbsorb.width,width*.70)
preserved(); combat=false; preserved()
-- Respect an explicitly disabled native display option instead of forcing it.
f.optionTable.displayHealPrediction=false
nativeUpdate(CompactUnitFrame_UpdateHealPrediction,f); preserved()
assert(not f.myHealPrediction.shown and not f.totalAbsorb.shown and not f.myHealAbsorb.shown)
assert(f.optionTable.displayHealPrediction==false)
f.optionTable.displayHealPrediction=true
-- Standard noncompact party uses native StatusBarOverlaySegment objects.
local s=StandardUnits[1]
values(700,100,150,50,0); nativeUpdate(UnitFrameHealPredictionBars_Update,s)
assert(s.myHealPredictionBar.amount==100 and s.otherHealPredictionBar.amount==50)
assert(s.totalAbsorbBar.amount==50 and not s.overAbsorbGlow.shown)
assert(s.myHealPredictionBar.previous==s.healthbar.nativeHealthTexture)
assert(s.otherHealPredictionBar.previous==s.myHealPredictionBar)
preserved()
values(700,100,100,50,400); nativeUpdate(UnitFrameHealPredictionBars_Update,s)
assert(s.healAbsorbBar.amount==300 and s.healAbsorbBar.shown)
assert(s.totalAbsorbBar.previous==s.healAbsorbBar)
assert(not s.healAbsorbBar.LeftShadow.shown and s.healAbsorbBar.RightShadow.shown)
preserved()
values(700,0,0,500,0); nativeUpdate(UnitFrameHealPredictionBars_Update,s)
assert(s.totalAbsorbBar.amount==300 and s.overAbsorbGlow.shown)
assert(s.healthbar.MyHealPredictionBar==s.myHealPredictionBar)
assert(s.healthbar.HealAbsorbBar==s.healAbsorbBar)
assert(s.healthbar.masks[1]=='nativeHealthMask')
preserved()
-- Native lack of current incoming-heal data must remain an empty segment.
values(700,nil,nil,nil,nil); nativeUpdate(UnitFrameHealPredictionBars_Update,s)
assert(not s.myHealPredictionBar.shown and s.totalAbsorbBar.amount==0)
nativeUpdate(CompactUnitFrame_UpdateHealPrediction,f)
assert(not f.myHealPrediction.shown and not f.totalAbsorb.shown)
preserved()
''')
print("PASS group prediction: actual native compact+standard quantitative fills, own/other heals, shield overflow, heal absorbs, nil data, display setting preservation, combat-native updates, addon never reads health/heals or changes prediction layers")
