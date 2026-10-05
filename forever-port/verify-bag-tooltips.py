"""Execute real slot factories and native hover methods with template layer defaults.

The owner's frame stack showed a level-12 item below its level-103 wrapper and
level-100 bag background. XML supplies level 10; reparenting adds two levels.
The model checks that actual factories remove this negative layer offset.
It is not native rendering or combat/taint certification.
"""
from pathlib import Path
import os,re
from lupa.lua51 import LuaRuntime
root=Path(__file__).resolve().parents[1]
bags=root.parent/'EllesmereUIBags'
native=Path(os.environ['EUI_NATIVE_SOURCE_ROOT'])/'Blizzard_UIPanels_Game/Mainline'
xml=(native/'ContainerFrame.xml').read_text()
template=re.search(r'<ItemButton name="ContainerFrameItemButtonTemplate"[^>]+>',xml).group()
level=int(re.search(r'frameLevel="(\d+)"',template).group(1))
native_lua=(native/'ContainerFrame.lua').read_text()
def chunk(text,head):
    return re.search(re.escape(head)+r'.*?\nend\n',text,re.S).group()
sources={p.name:p.read_text(encoding='utf-8-sig') for p in bags.glob('*.lua')}
lua=LuaRuntime(unpack_returned_tuples=True)
lua.globals().templateLevel=level
lua.execute(r'''
combat=false; frames={}; ns={}; itemSlots={}; reagentSlots={}; _bankSlots={}; _hostRows={}
SLOT_SIZE=34; ICON_SIZE=26; STANDARD_TEXT_FONT='font'; profile={}
function BP() return profile end
function GetFont() return 'font' end
function InCombatLockdown() return combat end
function CreateInsetBorder() end
function SetInsetBorderColor() end
function SlotMiddleClick() end
function SetListFont() end
EllesmereUI={SlugFlag=function(s) return s end,ApplyIconTextFont=function() end}
local methods={}
local function noop() end
for _,k in ipairs({'SetAllPoints','SetSize','SetFont','SetPoint','SetText','SetTextColor',
    'SetJustifyH','SetColorTexture','SetTexture','SetAtlas','SetTexCoord','SetVertexColor',
    'SetAlpha','ClearAllPoints','SetHideCountdownNumbers','RegisterForClicks','RegisterForDrag'}) do
    methods[k]=noop
end
function methods:GetFrameLevel() return self.level end
function methods:GetParent() return self.parent end
function methods:SetFrameLevel(level)
    assert(not (combat and self.secure),'protected layer write in combat')
    local delta=level-self.level;self.level=level
    for _,child in ipairs(self.children) do child:SetFrameLevel(child.level+delta) end
end
function methods:SetParent(parent)
    local old=self.parent
    for i,v in ipairs(old.children) do if v==self then table.remove(old.children,i);break end end
    self.parent=parent;parent.children[#parent.children+1]=self
    self:SetFrameLevel(self.level+parent.level-old.level)
end
function methods:SetScript(k,v) self.scripts[k]=v end
function methods:HookScript(k,v) self.hooks[k]=v end
function methods:SetID(id) self.id=id end
function methods:GetID() return self.id end
function methods:Show() self.shown=true end
function methods:Hide() self.shown=false end
function methods:IsPlaying() return false end
function methods:Stop() end
function methods:GetHighlightTexture() return nil end
function methods:GetPushedTexture() return nil end
function methods:HasItem() return true end
function methods:IsReadable() return false end
function methods:CreateTexture() return CreateFrame('Texture',nil,self) end
function methods:CreateFontString() return CreateFrame('FontString',nil,self) end
function CreateFrame(kind,name,parent,template)
    assert(not (combat and template),'secure frame created in combat')
    local f=setmetatable({parent=parent,children={},level=parent and parent.level+1 or 1,
        scripts={},hooks={},shown=true,id=0,secure=template~=nil},{__index=methods})
    if parent then parent.children[#parent.children+1]=f end
    if template then
        assert(template=='ContainerFrameItemButtonTemplate')
        f.level=templateLevel
        for k,v in pairs(ContainerFrameItemButtonMixin) do f[k]=v end
        f.scripts.OnEnter=f.OnEnter;f.scripts.OnLeave=f.OnLeave
        f.scripts.OnClick=nativeClick;f.scripts.OnReceiveDrag=nativeDrag
        f.NewItemTexture=CreateFrame('Texture',nil,f)
        f.BattlepayItemTexture=CreateFrame('Texture',nil,f)
        f.flashAnim=CreateFrame('Animation',nil,f)
        f.newitemglowAnim=CreateFrame('Animation',nil,f)
    end
    frames[#frames+1]=f;return f
end
function nativeClick() end
function nativeDrag() end
ContainerFrameItemButtonMixin={}
function ContainerFrameItemButtonMixin:OnLeave() GameTooltip:Hide() end
GameTooltip={SetOwner=function(self,owner) self.owner=owner end,
 SetBagItem=function(self,bag,slot) self.bag=bag;self.slot=slot;self.shown=true end,
 Hide=function(self) self.shown=false end}
function ContainerFrameItemButton_CalculateItemTooltipAnchors() end
C_NewItems={RemoveNewItem=noop}
TooltipUtil={ShouldDoItemComparison=function() return false end}
function SpellIsTargeting() return false end
function IsModifiedClick() return false end
function CanSellItems() return false end
function ResetCursor() end
function GetCVarBitfield() return true end
ItemLocation={CreateFromBagAndSlot=function() return {IsValid=function() return true end} end}
function SetCursorHoveredItem() end
EventRegistry={TriggerEvent=noop}
ns.BankRoutePreClick=noop;ns.BankRouteOnClick=noop
_itemDragFrame=CreateFrame('Frame')
''')
for name in ['GetBagID','OnUpdate','OnEnter']:
    lua.execute(chunk(native_lua,'function ContainerFrameItemButtonMixin:'+name+'('))
lua.execute(chunk(sources['EllesmereUIBags.lua'],'function ns.SkinItemButton('))
lua.execute(chunk(sources['EllesmereUIBags_List.lua'],'local function SkinRow(')+'\nSkinRowForTest=SkinRow')
lua.execute('SkinRow=SkinRowForTest')
factories=[('EllesmereUIBags_Grid.lua','local function GetOrCreateSlot(','GetOrCreateSlot',True),
 ('EllesmereUIBags.lua','local function GetOrCreateReagentSlot(','GetOrCreateReagentSlot',True),
 ('EllesmereUIBags_Bank.lua','local function GetOrCreateBankSlot(','GetOrCreateBankSlot',False),
 ('EllesmereUIBags_List.lua','function ns.CreateListRow(','ns.CreateListRow',True)]
for filename,head,fn,combat_guard in factories:
    lua.execute(chunk(sources[filename],head)+'\nfactory='+fn)
    for window_level in [1,100,350]:
        lua.globals().windowLevel=window_level
        lua.globals().listFactory=fn=='ns.CreateListRow'
        lua.execute(r'''
        combat=false;itemSlots={};reagentSlots={};_bankSlots={};_hostRows={}
        EUI_Bags=CreateFrame('Frame');EUI_Bags:SetFrameLevel(windowLevel)
        EUI_BagsReagent=EUI_Bags;EUI_Bank=EUI_Bags
        EUI_Bags:SetScript('OnEnter',function() backgroundHover=true end)
        local btn=factory(listFactory and EUI_Bags or 1)
        local sf=CreateFrame('Frame',nil,EUI_Bags)
        local child=CreateFrame('Frame',nil,sf)
        btn:GetParent():SetParent(child)
        btn:GetParent():SetID(2);btn:SetID(7)
        assert(btn.level>btn:GetParent().level,'item button sits below its parent')
        local dropCatch=CreateFrame('Frame',nil,EUI_Bags)
        assert(btn.level>dropCatch.level,'drop catcher intercepts native item target')
        assert(btn.scripts.OnEnter==ContainerFrameItemButtonMixin.OnEnter,'native hover replaced')
        assert(btn.scripts.OnClick==nativeClick,'native click replaced')
        assert(btn.scripts.OnLeave==ContainerFrameItemButtonMixin.OnLeave,'native leave replaced')
        backgroundHover=false;GameTooltip.shown=false
        local winner=btn.level>EUI_Bags.level and btn or EUI_Bags
        winner.scripts.OnEnter(winner)
        assert(not backgroundHover and GameTooltip.shown and GameTooltip.owner==btn)
        assert(GameTooltip.bag==2 and GameTooltip.slot==7,'native tooltip uses wrong item')
        -- Reuse against another real bag/slot; no cached link or metadata path.
        btn:GetParent():SetID(4);btn:SetID(3);btn.scripts.OnEnter(btn)
        assert(GameTooltip.bag==4 and GameTooltip.slot==3)
        btn.scripts.OnLeave(btn);assert(not GameTooltip.shown)
        EUI_Bags:SetFrameLevel(windowLevel+200)
        assert(btn.level>btn:GetParent().level and btn.level>EUI_Bags.level)
        ''')
    if combat_guard:
        lua.execute('combat=true; assert(factory(listFactory and EUI_Bags or 9)==nil);combat=false')
    print('PASS:',filename,'factory; native tooltip enter/reuse/leave; both bag layers; raised window; native click; combat creation guard' if combat_guard else 'PASS: bank factory layers and native tooltip')
print('PASS: native XML default reproduced; corrected factories keep item targets above background/drop layer. Native acceptance remains required.')
