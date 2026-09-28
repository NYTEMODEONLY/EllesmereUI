"""Native auction money/sort behavior survives the auction-only skin helpers."""
import os
from pathlib import Path
from lupa.lua51 import LuaRuntime

folder = Path(__file__).resolve().parent
addons = folder.parents[1]
skin = (addons / "EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_WindowPacks.lua").read_text(encoding="utf-8-sig")
engine = (addons / "EllesmereUIBlizzardSkin/EllesmereUIBlizzardSkin_WindowEngine.lua").read_text(encoding="utf-8-sig")
native = Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ["LOCALAPPDATA"]) / "Temp/eui-forever-research/wow-ui-source-forever/Interface/AddOns"))

def between(text, start, end):
    first = text.index(start)
    return text[first:text.index(end, first)]

auction = skin[skin.index("local function Skin_AuctionHouse()"):]
helpers = between(auction, "    local function MoneyBox(eb)", "    -- Refresh corner:")
sell = between(auction, "    local function ItemDisplay(host)", "    -- Search bar:")
rebid = between(auction, "    local function ReFadeMoney()", "    ReFadeMoney()")
table_native = (native / "Blizzard_AuctionHouseUI/Shared/Blizzard_AuctionHouseTableBuilder.lua").read_text(encoding="utf-8-sig")
header_native = between(table_native, "function AuctionHouseTableHeaderStringMixin:OnClick()", "AuctionHouseTableBuilderMixin =")
money_native = (native / "Blizzard_MoneyFrame/Shared/MoneyInputFrame.lua").read_text(encoding="utf-8-sig")
bid_money = (native / "Blizzard_MoneyFrame/Mainline/MoneyInputFrame.lua").read_text(encoding="utf-8-sig")
bid_native = (native / "Blizzard_AuctionHouseUI/Shared/Blizzard_AuctionHouseSharedTemplates.lua").read_text(encoding="utf-8-sig")

lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute(r'''
WSkin={}; FFD={}; registrations={}
function GetFFD(f) FFD[f]=FFD[f] or {}; return FFD[f] end
function texture(parent)
 local t={alpha=1,shown=true,atlas='native',parent=parent}
 function t:SetAlpha(a) self.alpha=a end
 function t:GetAlpha() return self.alpha end
 function t:SetShown(v) self.shown=v end
 function t:Show() self.shown=true end
 function t:Hide() self.shown=false end
 function t:SetAtlas(v) self.atlas=v end
 function t:SetTexture(v) self.art=v end
 function t:SetTexCoord(...) self.uv={...} end
 function t:IsObjectType(kind) return kind=='Texture' end
 for _,m in ipairs({'SetPoint','SetAllPoints','SetColorTexture','SetHeight','SetWidth','ClearAllPoints'}) do t[m]=function() end end
 function t:GetTop() return nil end
 function t:GetBottom() return nil end
 return t
end
function SolidTex(frame)
 local t=texture(frame); table.insert(frame.regions,t); return t
end
function AddBorder(frame) frame.skinned=true end
function WSkin.White(fs) fs.white=true end
function WSkin.Button() end
function WSkin.WhiteButtonLabel() end
function WSkin.IsForeignFrame() return false end
function WhiteBtn() end
function box(name,large)
 local eb={name=name,regions={},number=0,enabled=true,shown=true,height=25,
  scripts={OnTabPressed='nativeTab',OnTextChanged='nativeAmountChanged'}}
 local coin=texture(eb); coin.atlas=name..'-coin'; coin.alpha=0.75
 if large then eb.Icon=coin else eb.texture=coin end
 for _,part in ipairs({'Left','Middle','Right'}) do
  local art=texture(eb); table.insert(eb.regions,art); _G[name..part]=art
 end
 table.insert(eb.regions,coin)
 function eb:IsForbidden() return false end
 function eb:GetRegions() return unpack(self.regions) end
 function eb:GetName() return self.name end
 function eb:SetNumber(v) self.number=v end
 function eb:GetNumber() return self.number end
 function eb:SetText(v) self.number=tonumber(v) or 0 end
 function eb:GetText() return tostring(self.number) end
 function eb:SetEnabled(v) self.enabled=v end
 function eb:SetShown(v) self.shown=v end
 function eb:Hide() self.shown=false end
 function eb:ClearAllPoints() self.nativeReanchored=true end
 function eb:SetPoint(...) self.nativePoint={...} end
 function eb:GetHeight() return self.height end
 function eb:SetHeight(v) self.height=v end
 for k,v in pairs(eb.scripts) do assert(v) end
 if large then setmetatable(eb,{__index=LargeMoneyInputBoxMixin}) end
 return eb
end
function largeMoney(name)
 local m={useAuctionHouseCopperValue=true,GoldBox=box(name..'Gold',true),
  SilverBox=box(name..'Silver',true),CopperBox=box(name..'Copper',true)}
 return setmetatable(m,{__index=LargeMoneyInputFrameMixin})
end
function bidMoney(name)
 local m={gold=box(name..'Gold'),silver=box(name..'Silver'),copper=box(name..'Copper')}
 function m:SetWidth(v) self.width=v end
 return m
end
function frame()
 local t={regions={}}
 function t:IsForbidden() return false end
 function t:GetRegions() return unpack(self.regions) end
 function t:GetChildren() return unpack(self.children or {}) end
 function t:CreateTexture() return SolidTex(self) end
 function t:GetTop() return nil end
 function t:GetLeft() return nil end
 function t:GetRight() return nil end
 return t
end
f=frame()
C_AuctionHouse={SupportsCopperValues=function() return supportsCopper end}
supportsCopper=true; COPPER_PER_SILVER=100; COPPER_PER_GOLD=10000
floor=math.floor; mod=math.fmod
function GetMoney() return 1000000 end
AUCTION_HOUSE_TOOLTIP_TITLE_NOT_ENOUGH_MONEY='no money'
AUCTION_HOUSE_TOOLTIP_TITLE_OWN_AUCTION='owned'
AuctionHouseTableHeaderStringMixin={}; AuctionHouseBidFrameMixin={}
AuctionHouseSortOrderState={PrimarySorted=1,PrimaryReversed=2,Unsorted=3}
''')
# Use the real engine fading/edit-box implementation, so these regressions
# would catch loss of semantic texture alpha instead of mocking it away.
lua.execute(between(engine, "local function FadeRegions(frame, keep)", "--  Style-aware window shell.")
            + between(engine, "function WSkin.EditBox(eb)", "-- Checkbox ->")
            + between(engine, "function WSkin.ScrollBar(sb, keepSteppers)", "-- Close (X) button"))
lua.execute(money_native)
lua.execute(between(bid_money, "function MoneyInputFrame_SetEnabled", "function MoneyInputFrame_OnTextChanged"))
lua.execute(between(bid_native, "function AuctionHouseBidFrameMixin:OnLoad()", "function AuctionHouseBidFrameMixin:PlaceBid()"))
lua.execute(header_native)
stepper_native = (native / "Blizzard_SharedXML/Shared/Scroll/MinimalScrollBar.lua").read_text(encoding="utf-8-sig")
lua.execute("MinimalScrollBarStepperScriptsMixin={}; TextureKitConstants={UseAtlasSize=true}\n" +
            between(stepper_native, "function MinimalScrollBarStepperScriptsMixin:GetAtlas()", "MinimalScrollBarThumbScriptsMixin ="))
lua.execute(helpers + sell + rebid + "\nTestMoney=MoneyInputs; TestHeaders=Headers; TestSell=SellFrame; TestBid=ReFadeMoney; TestScroll=ScrollBars")
lua.execute(r'''
-- Native sell initialization owns copper availability, amount and keyboard chain.
for _,supported in ipairs({true,false}) do
 supportsCopper=supported
 local mi=largeMoney(supported and 'CopperSell' or 'RetailSell')
 mi:OnLoad(); mi:SetAmount(123456); mi:SetNextEditBox(mi.GoldBox)
 local silverNext,copperNext=mi.SilverBox.nextEditBox,mi.CopperBox.nextEditBox
 local sf=frame(); sf.PriceInput={MoneyInputFrame=mi}
 TestSell(sf)
 for _,eb in ipairs({mi.GoldBox,mi.SilverBox,mi.CopperBox}) do
  assert(eb.skinned and eb.height==20,'denomination omitted from sell styling')
  assert(eb.Icon.alpha==0.75 and eb.Icon.atlas==eb.name..'-coin','coin texture erased')
  assert(eb.scripts.OnTabPressed=='nativeTab' and eb.scripts.OnTextChanged=='nativeAmountChanged')
 end
 assert(mi.CopperBox.shown==supported and mi:GetAmount()==123456)
 assert(mi.SilverBox.nextEditBox==silverNext and mi.CopperBox.nextEditBox==copperNext)
 mi:SetEnabled(false); TestSell(sf); WSkin.Restrip()
 assert(not mi.GoldBox.enabled and not mi.SilverBox.enabled and not mi.CopperBox.enabled)
 assert(mi.CopperBox.height==20 and mi.CopperBox.Icon.alpha==0.75,'repeated skin altered input')
 -- Colorblind-mode visibility is native: no alpha repair may Show its coin.
 mi.CopperBox.Icon:Hide(); TestMoney(mi); WSkin.Restrip()
 assert(not mi.CopperBox.Icon.shown and mi.CopperBox.Icon.alpha==0.75)
 mi:SetEnabled(true); mi:SetAmount(10001)
 assert(mi:GetAmount()==10001 and mi.CopperBox.enabled)
end

-- Native bid controls are lowercase fields. Both views must receive all three
-- styles without relying on the colliding global BidAmount name in their XML.
supportsCopper=true
function bidFrame(name)
 local b={BidAmount=bidMoney(name),BidButton={SetDisableTooltip=function(self,v) self.tip=v end}}
 setmetatable(b,{__index=AuctionHouseBidFrameMixin})
 b:OnLoad(); return b
end
ibf={BidFrame=bidFrame('OneItem')}; f.AuctionsFrame={BidFrame=bidFrame('MyBids')}
for _,host in ipairs({ibf,f.AuctionsFrame}) do host.BidFrame:SetPrice(98765,false,false) end
TestBid(); WSkin.Restrip()
for _,host in ipairs({ibf,f.AuctionsFrame}) do
 local b=host.BidFrame
 assert(b:GetPrice()==98765 and b.BidAmount.copper.shown and b.BidAmount.width==176)
 for _,eb in ipairs({b.BidAmount.gold,b.BidAmount.silver,b.BidAmount.copper}) do
  assert(eb.skinned and eb.texture.alpha==0.75 and eb.enabled)
  assert(_G[eb.name..'Left'].alpha==0 and _G[eb.name..'Middle'].alpha==0)
 end
 b:SetPrice(98765,true,false); TestBid(); WSkin.Restrip()
 assert(not b.BidAmount.copper.enabled and b.BidButton.tip=='owned')
 supportsCopper=false; b:OnLoad(); TestBid()
 assert(not b.BidAmount.copper.shown and b.BidAmount.width==126)
 supportsCopper=true
end
ibf=nil; f.AuctionsFrame={BidFrame=bidFrame('OnlyMyBids')}
TestBid()
assert(f.AuctionsFrame.BidFrame.BidAmount.copper.skinned,'missing first view skipped second bid view')

-- Actual native Init/OnClick/SetArrowState remain responsible for sorting.
local col=frame(); col.Arrow=texture(col); col.regions={col.Arrow}
for _,part in ipairs({'Left','Middle','Right'}) do
 col[part]=texture(col); table.insert(col.regions,col[part])
end
function col:GetObjectType() return 'Button' end
function col:GetFontString() return self.text end
function col:SetText(v) self.text={value=v} end
function col:SetEnabled(v) self.enabled=v end
function col:GetBottom() return nil end
setmetatable(col,{__index=AuctionHouseTableHeaderStringMixin})
local owner={state=AuctionHouseSortOrderState.PrimarySorted,clicks=0}
function owner:RegisterHeader(header) self.header=header end
function owner:GetSortOrderState(order) assert(order==42); return self.state end
function owner:SetSortOrder(order)
 assert(order==42); self.clicks=self.clicks+1; self.state=AuctionHouseSortOrderState.PrimaryReversed
end
col:Init(owner,'Native price',42)
local list=frame(); list.HeaderContainer=frame()
function list.HeaderContainer:GetChildren() return col end
TestHeaders(list); WSkin.Restrip()
assert(col.Arrow.shown and col.Arrow.alpha==1 and col.Arrow.uv[3]==1,'ascending sort indicator erased')
assert(col.Left.alpha==0 and col.Middle.alpha==0 and col.Right.alpha==0)
col:OnClick(); TestHeaders(list); WSkin.Restrip()
assert(owner.clicks==1 and col.Arrow.shown and col.Arrow.alpha==1 and col.Arrow.uv[3]==0)
owner.state=AuctionHouseSortOrderState.Unsorted; col:UpdateArrow(); WSkin.Restrip()
assert(not col.Arrow.shown,'skin forced an unsorted arrow visible')
col:Init({},'Unsortable',nil); TestHeaders(list); WSkin.Restrip()
assert(not col.enabled and not col.Arrow.shown,'skin changed noninteractive header')

-- Native stepper hover/pressed/disabled atlas selection remains visible.
local host=frame(); local bar=frame(); host.ScrollBar=bar; host.children={bar}
bar.Track=frame(); bar.Track.Thumb=frame()
bar.Back=frame(); bar.Forward=frame()
for _,button in ipairs({bar.Back,bar.Forward}) do
 button.Texture=texture(button); button.regions={button.Texture}
 button.normalTexture='native-normal'; button.downTexture='native-pressed'; button.overTexture='native-hover'
 button.enabled=true; button.clickHandler='native-step-scroll'
 function button:IsEnabled() return self.enabled end
 setmetatable(button,{__index=MinimalScrollBarStepperScriptsMixin})
end
bar.children={bar.Track,bar.Back,bar.Forward}
TestScroll(host)
assert(GetFFD(bar.Track.Thumb).bg,'EUI scrollbar thumb missing')
for _,button in ipairs({bar.Back,bar.Forward}) do
 button.over=true; button:OnButtonStateChanged(); TestScroll(host)
 assert(button.Texture.alpha==1 and button.Texture.atlas=='native-hover')
 button.down=true; button:OnButtonStateChanged()
 assert(button.Texture.alpha==1 and button.Texture.atlas=='native-pressed')
 button.enabled=false; button:OnButtonStateChanged(); WSkin.Restrip()
 assert(button.Texture.alpha==1 and button.Texture.atlas=='native-normal' and not button.enabled)
 assert(button.clickHandler=='native-step-scroll')
end
''')
print("PASS auction: native copper availability, three-denomination skin/icons, amounts, enabled state, keyboard links, two bid views, colorblind visibility, pooled/reversed/unsorted header arrows, native scrollbar stepper states and engine restrips")
