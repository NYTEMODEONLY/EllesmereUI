"""Run the real Camelot stat initializers through the installed cosmetics."""
from pathlib import Path
import runpy

base = runpy.run_path(str(Path(__file__).with_name("verify-character.py")))
lua, native, between = base["lua"], base["native"], base["between"]
camelot = native / "Blizzard_UIPanels_Game/Camelot"
character = (camelot / "CharacterFrame.lua").read_text(encoding="utf-8-sig")
paper = (camelot / "PaperDollFrame.lua").read_text(encoding="utf-8-sig")
lua.execute(r'''
stylesOff={}
STAT_CATEGORY_GENERAL='General'; STAT_CATEGORY_PRIMARY_ATTRIBUTES='Primary Attributes'
STAT_CATEGORY_WEAPONS='Weapons'; STAT_CATEGORY_MODIFIERS='Modifiers'
STAT_CATEGORY_DEFENSE='Defense'; STAT_CATEGORY_RESISTANCE='Resistance'
C_PaperDollInfo={OffhandHasShield=function() return true end}
CharacterStatFrameMixin={}
function CreateFromMixins(...)
 local out={}; for i=1,select('#',...) do for k,v in pairs(select(i,...)) do out[k]=v end end
 return out
end
format=string.format; STAT_FORMAT='%s:'; TextureKitConstants={UseAtlasSize=true}
''')
lua.execute((camelot / "PaperDollFrameConstants.lua").read_text(encoding="utf-8-sig"))
lua.execute(between(character, "CharacterStatFrameCategoryScrollBoxElementMixin = {};",
                    "CharacterStatsPanePetScrollBoxMixin ="))
lua.execute(between(paper, "function PaperDollFrame_SetLabelAndText(", "function PaperDollFrame_SetOnEnter("))
lua.execute(r'''
EllesmereUI={PP={perfect=.8}}
local originalMake=make
function make(extra)
 local f=originalMake(extra)
 function f:SetText(v) self.text=v end
 function f:GetText() return self.text end
 function f:GetEffectiveScale() return .8 end
 function f:SetTexture(v) self.texture=v end
 function f:SetTexCoord(...) self.uv={...} end
 function f:CreateTexture()
  local t=originalMake({owned=true,points={}})
  function t:SetPoint(...) self.points[#self.points+1]={...} end
  function t:SetHeight(v) self.height=v end
  function t:SetSnapToPixelGrid(v) self.snap=v end
  function t:SetTexelSnappingBias(v) self.bias=v end
  self.ownedTextures=self.ownedTextures or {}; table.insert(self.ownedTextures,t)
  return t
 end
 return f
end
local function update(frame,unit,id)
 PaperDollFrame_SetLabelAndText(frame,'native stat','|cff20ff20+5|r / 100',false,100)
 frame.tooltip='native tooltip'; frame.tooltip2='native detail'; frame.onEnterFunc='native tooltip callback'
 return 100
end
PAPERDOLL_STATINFO=setmetatable({}, {__index=function() return {updateFunc=update} end})
function init(row,data)
 row.data=data
 nativeVisualUpdate=true; row:Init(data); nativeVisualUpdate=false
end
function stat(name,unit,color)
 local row=make({Label=make({textColor={1,.82,0}}),Value=make({textColor=color or {1,1,1,1}}),Background=make()})
 row.Init=CharacterStatFrameScrollBoxBaseElementMixin.Init
 function row:GetElementData() return self.data end
 init(row,{name=name,unit=unit or 'player',statIndex=1})
 return row
end
function heading(name)
 local row=make({Title=make(),Background=make({atlas='UI-Character-Info-Title'})})
 row.regions={row.Background}; row.Init=CharacterStatFrameCategoryScrollBoxElementMixin.Init
 function row:GetElementData() return self.data end
 init(row,{isHeader=true,name=name})
 return row
end
function pane(rows)
 local p=list(rows[1]); p.ScrollBox.rows=rows
 function p.ScrollBox:ForEachFrame(fn) for _,row in ipairs(self.rows) do fn(row) end end
 function p.ScrollBox:SetDataProvider() error('skin replaced native provider') end
 return p
end
function colorIs(fs,r,g,b)
 local c=fs.textColor; return c and math.abs(c[1]-r)<.00001 and math.abs(c[2]-g)<.00001 and math.abs(c[3]-b)<.00001
end
headers={heading(STAT_CATEGORY_GENERAL),heading(STAT_CATEGORY_PRIMARY_ATTRIBUTES),heading(STAT_CATEGORY_WEAPONS),
 heading(STAT_CATEGORY_MODIFIERS),heading(STAT_CATEGORY_DEFENSE),heading(STAT_CATEGORY_RESISTANCE)}
strength=stat('STRENGTH'); spirit=stat('SPIRIT'); weapon=stat('MAINHAND_DAMAGE'); modifier=stat('HITCHANCE'); armor=stat('ARMOR')
buff=stat('STRENGTH','player',{0,1,0,1}); debuff=stat('STRENGTH','player',{1,0,0,1})
unknown=stat('FUTURE_NATIVE_STAT')
local rows={unpack(headers)}
for _,row in ipairs({strength,spirit,weapon,modifier,armor,buff,debuff,unknown}) do rows[#rows+1]=row end
CharacterStatsPaneScrollBox=pane(rows)
petArmor=stat('ARMOR','pet'); CharacterStatsPanePetScrollBox=pane({petArmor})
ns.ForeverCharacter()
assert(colorIs(headers[1].Title,.15,.85,1) and colorIs(headers[2].Title,.047,.824,.616))
assert(colorIs(headers[3].Title,1,.353,.122) and colorIs(headers[4].Title,.471,.255,.784))
assert(colorIs(headers[5].Title,.247,.655,1) and colorIs(headers[6].Title,.859,.325,.855))
assert(colorIs(strength.Value,.047,.824,.616) and colorIs(spirit.Value,.047,.824,.616))
assert(colorIs(weapon.Value,1,.353,.122) and colorIs(modifier.Value,.471,.255,.784))
assert(colorIs(armor.Value,.247,.655,1) and colorIs(petArmor.Value,.15,.85,1),'pet General must use pet category')
assert(colorIs(buff.Value,0,1,0) and colorIs(debuff.Value,1,0,0),'semantic colors lost')
assert(colorIs(unknown.Value,W.Theme.accR,W.Theme.accG,W.Theme.accB),'unknown native stat dropped')
assert(strength.Value.text=='|cff20ff20+5|r / 100' and strength.Label.text=='native stat:')
assert(strength.tooltip=='native tooltip' and strength.tooltip2=='native detail' and strength.onEnterFunc=='native tooltip callback')
assert(strength.numericValue==100 and #rows==14,'native data changed')
for _,h in ipairs(headers) do
 assert(h.Title.text==h.data.name and h.Background.alpha==0)
 assert(#h.ownedTextures==2,'expected only two dividers, no header fill')
 for i=1,2 do
  local line=h.ownedTextures[i]; assert(line.height==1 and line.snap==false and line.bias==0)
  assert(#line.points==2 and line.color[4]==.8,'native-sized header divider missing')
 end
end
-- Recycled headers and stat rows repaint from real native Init arguments, without
-- changing any native tooltip, hidden-zero flag, stat value or row geometry.
init(headers[1],{isHeader=true,name=STAT_CATEGORY_WEAPONS})
assert(colorIs(headers[1].Title,1,.353,.122) and #headers[1].ownedTextures==2)
init(strength,{name='ARMOR',unit='player',statIndex=2})
assert(colorIs(strength.Value,.247,.655,1) and strength.Background.shown==false)
assert(strength.onEnterFunc=='native tooltip callback' and strength.numericValue==100)
local removed={name='HITCHANCE',unit='player',statIndex=1,hideAt=100}
init(strength,removed); assert(removed.shouldRemove==true and colorIs(strength.Value,.471,.255,.784))
-- Initialized-frame callback handles a newly acquired row, then hooks native Init.
local acquired=stat('SPIRIT'); local box=CharacterStatsPaneScrollBox.ScrollBox
box.callback(box.owner,acquired,acquired.data)
assert(colorIs(acquired.Value,.047,.824,.616))
init(acquired,{name='MAINHAND_DAMAGE',unit='player',statIndex=1})
assert(colorIs(acquired.Value,1,.353,.122))
-- Native resistance initializer controls icon/UVs and every tooltip line.
local resistance=stat('ARMOR'); resistance.Icon=make()
function resistance.Icon:Show() assert(nativeVisualUpdate); self.shown=true end
function resistance.Icon:Hide() assert(nativeVisualUpdate); self.shown=false end
resistance.Init=CharacterStatFrameScrollBoxIconElementMixin.Init
init(resistance,{atlas='native-fire-resistance',labelText='Fire',valueText='12',numericValue=12,
 statIndex=1,tooltip='resistance tooltip',tooltip2='resistance detail',tooltip3='resistance level'})
box.callback(box.owner,resistance,resistance.data)
assert(colorIs(resistance.Value,.859,.325,.855) and resistance.Value.text=='12' and resistance.numericValue==12)
assert(resistance.Icon.atlas=='native-fire-resistance' and resistance.Icon.shown and resistance.Icon.uv[2]==1)
assert(resistance.tooltip3=='resistance level')
-- Profile changes recolor old addon tints, leaving semantic changes untouched.
EllesmereUIDB={statCategoryColors={Attack={r=.2,g=.3,b=.4}},statCategoryUseColor={Attack=true}}
W.looks(); assert(colorIs(weapon.Value,.2,.3,.4) and colorIs(headers[3].Title,.2,.3,.4))
assert(colorIs(buff.Value,0,1,0) and colorIs(debuff.Value,1,0,0))
EllesmereUIDB.statCategoryUseColor.Attack=false
W.looks(); assert(colorIs(weapon.Value,1,.353,.122) and colorIs(headers[3].Title,1,.353,.122))
EllesmereUIDB.statCategoryUseColor.Attack=true; W.looks()
local s=setmetatable({}, {__sub=function() error('secret arithmetic') end,__lt=function() error('secret comparison') end})
function issecretvalue(v) return rawequal(v,s) end
buff.Value.textColor={s,s,s,1}; W.looks(); assert(rawequal(buff.Value.textColor[1],s))
stylesOff.charsheet=true
init(weapon,{name='ARMOR',unit='player',statIndex=1})
assert(colorIs(weapon.Value,.2,.3,.4),'disabled style callback ran')
''')
print("PASS character stats: native pooled Init, all Classic/pet categories, EUI palette/profile changes, dividers, values/icons/tooltips/hidden-zero semantics, buff/debuff/secret colors, repeated refresh and disabled skin")
