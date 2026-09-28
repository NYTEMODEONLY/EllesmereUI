"""Run the real bag-sort engine against an asynchronous Lua 5.1 inventory model.

This verifies planning and transaction handling, not WoW secure execution.
"""
from pathlib import Path
from lupa.lua51 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
BAGS = ROOT.parent / 'EllesmereUIBags'
ENGINE = (BAGS / 'EllesmereUIBags_Sort.lua').read_text(encoding='utf-8-sig')
MODEL = r'''
EllesmereUI = {}
Enum = {BagIndex={ReagentBag=5}, BagSlotFlags={DisableAutoSort=1}}
NUM_TOTAL_EQUIPPED_BAG_SLOTS = 5
now, timers, frames, inventory, sizes, families, ignored = 0, {}, {}, {}, {}, {}, {}
maxStack, moves, scans, calls, starts, finishes = {}, 0, 0, 0, 0, 0
itemFamilies, itemEquipLoc, craftingReagents = {}, {}, {}
bit = {band=function(a,b)
    local result, power = 0,1
    while a>0 and b>0 do
        if a%2==1 and b%2==1 then result=result+power end
        a=math.floor(a/2); b=math.floor(b/2); power=power*2
    end
    return result
end}
latency = 0.35
function GetTime() return now end
function InCombatLockdown() return combat end
function GetCursorInfo() return cursor and 'item' or externalCursor end
function CursorHasItem() return cursor ~= nil end
function ClearCursor() cursor = nil end
function geterrorhandler() return function(e) luaError=e end end
function CreateFrame()
    local f = {events={}}
    function f:RegisterEvent(e) self.events[e]=true end
    function f:UnregisterAllEvents() self.events={} end
    function f:SetScript(kind, cb) self[kind]=cb end
    frames[#frames+1]=f
    return f
end
function Fire(event, ...)
    for _, f in ipairs(frames) do
        if f.events[event] then f:OnEvent(event, ...) end
    end
end
C_Timer = {}
function C_Timer.NewTimer(delay, callback)
    local timer = {at=now+delay, callback=callback}
    function timer:Cancel() self.cancelled=true end
    timers[#timers+1]=timer
    return timer
end
C_Timer.After = C_Timer.NewTimer
function Advance(duration)
    local deadline=now+duration
    local steps=0
    while true do
        local index, at
        for i, t in ipairs(timers) do
            if not t.cancelled and t.at <= deadline and (not at or t.at < at) then index, at=i,t.at end
        end
        if not index then break end
        local t=table.remove(timers,index)
        now=t.at; t.callback()
        steps=steps+1; assert(steps<20000, 'timer loop')
    end
    now=deadline
end
function Bag(bag, size, family)
    sizes[bag]=size; families[bag]=family or 0; inventory[bag]={}
end
function Item(bag, slot, id, count, link)
    link=link or ('item:'..id)
    inventory[bag][slot]={itemID=id, stackCount=count or 1, hyperlink=link}
    if itemFamilies[link]==nil then itemFamilies[link]=families[bag] or 0 end
end
function Clone(item, count)
    if not item or count==0 then return nil end
    return {itemID=item.itemID, hyperlink=item.hyperlink, stackCount=count or item.stackCount, isBound=item.isBound}
end
function Totals()
    local counts={}
    for _, bag in pairs(inventory) do
        for _, item in pairs(bag) do counts[item.hyperlink]=(counts[item.hyperlink] or 0)+item.stackCount end
    end
    return counts
end
C_Item = {GetItemInfo=function(link)
    if missingInfo then return end
    return link, nil, 1, 1, 1, 'type', nil, maxStack[link] or 1, itemEquipLoc[link] or '',
        nil, nil, nil, nil, nil, nil, nil, craftingReagents[link] or false
end, GetItemFamily=function(link)
    if missingFamily then return end
    return itemFamilies[link]
end}
function Accepts(bag, item)
    if not item then return true end
    local family=families[bag]
    if family==nil then return false end
    if family==0 and bag~=Enum.BagIndex.ReagentBag then return true end
    if itemEquipLoc[item.hyperlink]=='INVTYPE_BAG' then return false end
    if family==0 then return craftingReagents[item.hyperlink] end
    return bit.band(family,itemFamilies[item.hyperlink] or 0)~=0
end
C_Container = {
    GetContainerNumSlots=function(b) return sizes[b] or 0 end,
    GetContainerNumFreeSlots=function(b) return 0,families[b] end,
    GetBackpackAutosortDisabled=function() return ignored[0] end,
    GetBagSlotFlag=function(b) return ignored[b] end,
    GetContainerItemInfo=function(b,s) scans=scans+1; return inventory[b] and inventory[b][s] end,
    GetContainerItemLink=function(b,s) return inventory[b] and inventory[b][s] and inventory[b][s].hyperlink end,
}
function C_Container.PickupContainerItem(b,s)
    calls=calls+1
    assert(not combat, 'moved during combat')
    if not cursor then
        assert(not pending, 'overlapping server transactions')
        local item=inventory[b][s]
        assert(item and not item.isLocked, 'picked empty/locked source')
        if rejectPickup then return end
        cursor={item=item, bag=b, slot=s}
        return
    end
    local source=cursor
    if throwOnDrop then error('test pickup API error') end
    local dest=inventory[b][s]
    assert(not dest or not dest.isLocked, 'locked destination')
    assert(Accepts(b,source.item), 'incompatible specialty destination')
    assert(not dest or Accepts(source.bag,dest), 'incompatible displaced item')
    assert(not ignored[b] and not ignored[source.bag], 'ignored bag touched')
    local afterSource, afterTarget=Clone(dest),Clone(source.item)
    if dest and dest.hyperlink==source.item.hyperlink then
        local max=maxStack[dest.hyperlink] or 1
        local amount=math.min(source.item.stackCount,max-dest.stackCount)
        assert(amount>0,'unnecessary same-item swap')
        afterSource=Clone(source.item,source.item.stackCount-amount)
        afterTarget=Clone(dest,dest.stackCount+amount)
    end
    cursor=afterSource and {item=afterSource} or nil
    moves=moves+1
    if rejectMove then return end
    pending=true
    source.item.isLocked=true
    if dest then dest.isLocked=true end
    C_Timer.NewTimer(latency,function()
        inventory[source.bag][source.slot]=afterSource
        inventory[b][s]=afterTarget
        pending=false
        if not missingEvents then
            Fire('ITEM_LOCK_CHANGED',source.bag,source.slot)
            Fire('ITEM_LOCK_CHANGED',b,s)
            Fire('BAG_UPDATE_DELAYED')
        end
    end)
end
function Order(items)
    orderCalls=(orderCalls or 0)+1
    table.sort(items,function(a,b)
        if a.info.itemID~=b.info.itemID then return a.info.itemID<b.info.itemID end
        if a.itemLink~=b.itemLink then return a.itemLink<b.itemLink end
        if a.bag~=b.bag then return a.bag<b.bag end
        return a.slot<b.slot
    end)
end
function Options(bottom, random)
    return {order=Order,bottom=bottom,random=random,
        onStart=function() starts=starts+1; refresh=false; locked=true end,
        onDone=function(reason,skipped) finishes=finishes+1; message=reason; skippedLocked=skipped; refresh=true; locked=false end}
end
function Start(bottom, random)
    before=Totals()
    return EllesmereUI._BagSort:Start(Options(bottom, random))
end
function CheckFinished(expectedError)
    assert(not EllesmereUI._BagSort:IsRunning(),'run stranded')
    assert(refresh and not locked,'UI stranded')
    assert(not luaError,luaError)
    if expectedError then assert(message,'missing interruption reason') else assert(not message,message) end
    local after=Totals()
    for k,v in pairs(before) do assert(after[k]==v,'item count changed: '..k) end
    for k,v in pairs(after) do assert(before[k]==v,'unexpected item: '..k) end
    for _,f in ipairs(frames) do assert(next(f.events)==nil,'leaked event listener') end
end
'''


def case(name, script):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MODEL)
    lua.execute(ENGINE)
    try:
        lua.execute(script)
    except Exception as exc:
        raise AssertionError(name) from exc
    print('PASS:', name)


case('server latency; chained swaps; no overlap; one classification per group', '''
Bag(0,6); Item(0,1,4); Item(0,2,3); Item(0,4,2); Item(0,6,1)
Start(); Advance(15); CheckFinished()
for i=1,4 do assert(inventory[0][i].itemID==i) end
assert(not inventory[0][5] and not inventory[0][6]); assert(orderCalls==1)
assert(moves==4 and calls==8)
''')
case('partial stack overflow; stack conservation; full bags', '''
Bag(0,5); maxStack['item:1']=20
Item(0,1,1,13); Item(0,2,2); Item(0,3,1,8); Item(0,4,1,7); Item(0,5,1,4)
Start(); Advance(15); CheckFinished()
assert(inventory[0][1].itemID==1 and inventory[0][2].itemID==1 and inventory[0][3].itemID==2)
assert(inventory[0][1].stackCount+inventory[0][2].stackCount==32)
assert(not inventory[0][4] and not inventory[0][5])
''')
case('ordinary/specialty/reagent bag groups; ignored bags; top-to-bottom option', '''
Bag(0,3); Bag(1,2); Bag(2,3,32); Bag(3,2,32); Bag(4,2); Bag(5,2,32)
Item(0,1,5); Item(1,1,1); Item(2,1,9); Item(3,2,7); Item(4,1,88); Item(5,1,6)
ignored[4]=true
Start(true); Advance(20); CheckFinished()
assert(not inventory[0][1] and not inventory[0][2] and not inventory[0][3])
assert(inventory[1][1].itemID==1 and inventory[1][2].itemID==5)
assert(inventory[3][1].itemID==7 and inventory[3][2].itemID==9)
assert(inventory[4][1].itemID==88 and inventory[5][2].itemID==6)
''')
case('20-slot enchanting bag in reagent slot receives only compatible supplies', '''
Bag(0,12); Bag(1,4); Bag(5,20,64)
itemFamilies['item:10940']=64; itemFamilies['item:10938']=64
itemFamilies['item:2447']=32; itemFamilies['item:11130']=64
Item(0,1,10940,8); Item(1,3,10938,3); Item(0,2,2447,5); Item(0,4,25)
Item(0,7,11130); itemEquipLoc['item:11130']='INVTYPE_BAG'
maxStack['item:10940']=20; maxStack['item:10938']=20
Start(); Advance(20); CheckFinished()
assert(inventory[5][1].itemID==10938 and inventory[5][2].itemID==10940)
assert(inventory[0][1].itemID==25 and inventory[0][2].itemID==2447)
assert(inventory[0][3].itemID==11130)
local previous=moves
Start(); Advance(10); CheckFinished(); assert(moves==previous,'second sort moved items')
''')
case('multiple profession families and masks; top and bottom placement', '''
for mode=1,2 do
    inventory,sizes,families,ignored = {},{},{},{}
    Bag(0,6); Bag(1,3,64); Bag(2,3,32); Bag(3,2,1024)
    itemFamilies['item:101']=64; itemFamilies['item:102']=32; itemFamilies['item:103']=1024
    itemFamilies['item:104']=64+128
    Item(0,1,101); Item(0,2,102); Item(0,3,103); Item(0,4,104); Item(0,5,1)
    Start(mode==2); Advance(15); CheckFinished()
    assert(inventory[1][mode==2 and 2 or 1].itemID==101)
    assert(inventory[1][mode==2 and 3 or 2].itemID==104)
    assert(inventory[2][mode==2 and 3 or 1].itemID==102)
    assert(inventory[3][mode==2 and 2 or 1].itemID==103)
end
''')
case('full specialty bag tops up stacks and leaves consolidated overflow', '''
Bag(0,4); Bag(5,1,64); itemFamilies['item:1']=64; maxStack['item:1']=20
Item(0,1,1,20); Item(0,2,1,3); Item(0,3,2); Item(5,1,1,12)
Start(); Advance(15); CheckFinished()
assert(inventory[5][1].stackCount==20)
assert(inventory[0][1].itemID==1 and inventory[0][1].stackCount==15)
assert(inventory[0][2].itemID==2 and not inventory[0][3])
''')
case('consolidation frees specialty capacity before transferring new supplies', '''
Bag(0,3); Bag(5,2,64)
itemFamilies['item:1']=64; itemFamilies['item:2']=64; maxStack['item:1']=20
Item(5,1,1,4); Item(5,2,1,8); Item(0,2,2)
Start(); Advance(15); CheckFinished()
assert(inventory[5][1].itemID==1 and inventory[5][1].stackCount==12)
assert(inventory[5][2].itemID==2 and not next(inventory[0]))
''')
case('profession routing respects locked sources, destinations and ignored bags', '''
Bag(0,6); Bag(1,3,64); Bag(2,3); Bag(5,2,64)
itemFamilies['item:1']=64; maxStack['item:1']=20
Item(0,1,1,4); Item(0,2,1,5); Item(2,1,1,6); Item(5,1,1,7)
inventory[0][1].isLocked=true; inventory[5][1].isLocked=true
ignored[1]=true; ignored[2]=true
Start(); Advance(15); CheckFinished()
assert(skippedLocked==2 and inventory[0][1].stackCount==4 and inventory[5][1].stackCount==7)
assert(inventory[2][1].stackCount==6 and not next(inventory[1]))
assert(inventory[5][2].stackCount==5)
''')
case('ignored backpack and unknown bag families never become routing sources', '''
Bag(0,3); Bag(1,3); Bag(5,2,64); families[1]=nil; ignored[0]=true
itemFamilies['item:1']=64; Item(0,1,1); Item(1,1,1)
Start(); Advance(10); CheckFinished(); assert(moves==0 and not next(inventory[5]))
''')
case('generic reagent slot accepts crafting reagents only', '''
Bag(0,4); Bag(5,3); craftingReagents['item:1']=true
Item(0,1,1); Item(0,2,2)
Start(); Advance(10); CheckFinished()
assert(inventory[5][1].itemID==1 and inventory[0][1].itemID==2)
''')
case('missing family metadata stops before any planned transaction', '''
Bag(0,4); Bag(5,3,64); Item(0,1,1,2); Item(0,2,1,3)
maxStack['item:1']=20; missingFamily=true
Start(); Advance(2); CheckFinished(true); assert(calls==0)
''')
case('cross-bag merges preserve variant links and binding states', '''
Bag(0,4); Bag(5,3,64)
for _,link in ipairs({'item:1','item:1:variant'}) do
    itemFamilies[link]=64; maxStack[link]=20
end
Item(0,1,1,3); Item(5,1,1,4); inventory[5][1].isBound=true
Item(0,2,1,5,'item:1:variant')
Start(); Advance(15); CheckFinished()
local counts={}
for _,item in pairs(inventory[5]) do
    counts[item.hyperlink..(item.isBound and ':bound' or ':unbound')]=item.stackCount
end
assert(counts['item:1:bound']==4 and counts['item:1:unbound']==3)
assert(counts['item:1:variant:unbound']==5 and not next(inventory[0]))
''')
case('missing bag events still settle; no permanently disabled UI', '''
Bag(0,3); Item(0,2,2); Item(0,3,1); missingEvents=true
Start(); Advance(15); CheckFinished(); assert(inventory[0][1].itemID==1)
''')
case('rejected transaction times out without resending it', '''
Bag(0,3); Item(0,3,1); rejectMove=true
Start(); Advance(10); CheckFinished(true); assert(moves==1)
''')
case('combat during server response; stale timers cannot affect a new run', '''
Bag(0,4); Item(0,3,2); Item(0,4,1)
Start(); Advance(.2); combat=true; Fire('PLAYER_REGEN_DISABLED'); Advance(1)
CheckFinished(true); assert(moves==1 and finishes==1)
combat=false; Start(); Advance(10); CheckFinished(); assert(finishes==2)
''')
case('cursor/combat start guards; no pickup or cursor clearing', '''
Bag(0,2); Item(0,2,1); externalCursor='spell'
assert(not Start()); CheckFinished(true); assert(externalCursor=='spell' and calls==0)
externalCursor=nil; combat=true; assert(not Start()); CheckFinished(true); assert(calls==0)
''')
case('new cursor between transactions is preserved', '''
Bag(0,4); Item(0,3,2); Item(0,4,1)
Start(); Advance(.2); externalCursor='item'; Advance(5)
CheckFinished(true); assert(moves==1 and externalCursor=='item')
''')
case('locked starting item stays put; failed pickup stops safely', '''
Bag(0,2); Item(0,2,1); inventory[0][2].isLocked=true
Start(); Advance(1); CheckFinished(); assert(calls==0 and skippedLocked==1)
inventory[0][2].isLocked=false; rejectPickup=true
Start(); Advance(1); CheckFinished(true); assert(calls==1 and moves==0)
''')
case('Forever persistent locks reserve their slots while remaining inventory sorts', '''
for mode=1,3 do
    inventory, sizes, families, ignored = {}, {}, {}, {}
    Bag(0,8); maxStack['item:5527']=20; maxStack['item:1']=20
    Item(0,1,4); Item(0,2,5527,20); Item(0,3,1,6); Item(0,4,3)
    Item(0,5,5527,20); Item(0,7,1,9); Item(0,8,2)
    local lockedA,lockedB=inventory[0][2],inventory[0][5]
    lockedA.isLocked=true; lockedB.isLocked=true
    Start(mode==2,mode==3); Advance(15); CheckFinished()
    assert(skippedLocked==2 and inventory[0][2]==lockedA and inventory[0][5]==lockedB)
    if mode==1 then
        assert(inventory[0][1].itemID==1 and inventory[0][1].stackCount==15)
        assert(inventory[0][3].itemID==2 and inventory[0][4].itemID==3 and inventory[0][6].itemID==4)
        assert(not inventory[0][7] and not inventory[0][8])
    elseif mode==2 then
        assert(not inventory[0][1] and not inventory[0][3])
        assert(inventory[0][4].itemID==1 and inventory[0][6].itemID==2)
        assert(inventory[0][7].itemID==3 and inventory[0][8].itemID==4)
    end
end
''')
case('missing item links / metadata never become invalid moves', '''
Bag(0,2); Item(0,2,1); inventory[0][2].hyperlink=nil
assert(EllesmereUI._BagSort:Start(Options())); Advance(1)
assert(message and not EllesmereUI._BagSort:IsRunning() and calls==0)
inventory[0][2].hyperlink='item:1'; missingInfo=true
Start(); Advance(1); CheckFinished(true); assert(calls==0)
''')
case('identical IDs with different links never consolidate together', '''
Bag(0,3); Item(0,1,1,4,'item:1:b'); Item(0,3,1,5,'item:1:a')
maxStack['item:1:a']=20; maxStack['item:1:b']=20
Start(); Advance(10); CheckFinished()
assert(inventory[0][1].hyperlink=='item:1:a' and inventory[0][1].stackCount==5)
assert(inventory[0][2].hyperlink=='item:1:b' and inventory[0][2].stackCount==4)
''')
case('randomize uses confirmed moves and retains partial stacks', '''
Bag(0,7); Bag(1,2,32); Item(0,1,1,3); Item(0,2,1,4); Item(0,3,2); Item(0,4,3); Item(1,1,9)
maxStack['item:1']=20; math.randomseed(31)
Start(false,true); Advance(15); CheckFinished()
local stacks=0; for _,item in pairs(inventory[0]) do if item.itemID==1 then stacks=stacks+1 end end
assert(stacks==2 and moves>0)
''')
case('duplicate start; empty inventory; repeated invocation reuses one frame', '''
Bag(0,3); Start(); assert(not EllesmereUI._BagSort:Start(Options()))
Advance(1); CheckFinished(); Start(); Advance(1); CheckFinished()
assert(#frames==1 and starts==2 and finishes==2 and moves==0)
''')
case('bag replacement invalidates remaining plan', '''
Bag(0,4); Item(0,3,2); Item(0,4,1)
Start(); Advance(.2); sizes[0]=5; Advance(5); CheckFinished(true); assert(moves==1)
''')
case('new lock between moves is waited out without duplicate pickup', '''
Bag(0,4); Item(0,3,2); Item(0,4,1)
Start(); Advance(.2); inventory[0][3].isLocked=true
C_Timer.NewTimer(1,function() inventory[0][3].isLocked=false; Fire('ITEM_LOCK_CHANGED',0,3) end)
Advance(10); CheckFinished(); assert(inventory[0][1].itemID==1 and inventory[0][2].itemID==2)
''')
case('Lua errors clean up the run and remain visible to diagnostics', '''
Bag(0,2); Item(0,2,1)
local options=Options(); options.order=function() error('test planner error') end
before=Totals(); EllesmereUI._BagSort:Start(options); Advance(1)
assert(luaError and message and refresh and not locked and not EllesmereUI._BagSort:IsRunning())
''')

case('bound and unbound partial stacks stay separate', '''
Bag(0,3); Item(0,1,1,3); Item(0,2,1,4); inventory[0][1].isBound=true
maxStack['item:1']=20
Start(); Advance(10); CheckFinished(); assert(moves==0 and inventory[0][1].stackCount==3)
''')
case('an API exception returns only the sorter-owned cursor', '''
Bag(0,2); Item(0,2,1); throwOnDrop=true
Start(); Advance(1)
assert(luaError and message and refresh and not locked and not cursor)
assert(not EllesmereUI._BagSort:IsRunning())
''')
case('100 varied layouts: counts, category order, gaps and stack consolidation', '''
for seed=1,100 do
    inventory, sizes, families, ignored = {}, {}, {}, {}
    Bag(0,20); Bag(1,12); math.randomseed(seed); latency=.02
    for id=1,8 do maxStack['item:'..id]=20 end
    for bag=0,1 do
        for slot=1,sizes[bag] do
            if math.random(4)>1 then Item(bag,slot,math.random(8),math.random(20)) end
        end
    end
    local bottom=seed%2==0
    Start(bottom); Advance(30); CheckFinished()
    local last,empty,seen=0,false,false
    local partials={}
    for bag=0,1 do
        for slot=1,sizes[bag] do
            local item=inventory[bag][slot]
            if item then
                assert(item.itemID>=last,'category order')
                if not bottom then assert(not empty,'gap before item') end
                last=item.itemID; seen=true
                if item.stackCount<20 then partials[last]=(partials[last] or 0)+1 end
            else
                if bottom then assert(not seen,'gap after item') end
                empty=true
            end
        end
    end
    for _,count in pairs(partials) do assert(count==1,'unconsolidated stacks') end
end
''')

lua = LuaRuntime()
lua.execute(MODEL)
lua.execute(ENGINE)
source = (BAGS / 'EllesmereUIBags.lua').read_text(encoding='utf-8-sig')
lua.execute('''
EUI=EllesmereUI
profile={}
function BP() return profile end
function Button()
    return {EnableMouse=function(self,enabled) self.enabled=enabled end,
        icon={SetAlpha=function(self,alpha) self.alpha=alpha end}}
end
sort=Button()
EUI_Bags={_diceBtn=Button(), RefreshInventory=function(self) self.refreshed=true end}
EUI_BagsReagent={IsVisible=function() return false end}
UIErrorsFrame={AddMessage=function(self,text) self.message=text end}
EUI_CategoryManager={
    ClassifyAll=function(self,items) for _,item in ipairs(items) do item.categoryIndex=1 end end,
    GetCategories=function() return {{}} end,
}
function PreCacheSortFields() end
function VisualSortCompare(a,b) return a.info.itemID<b.info.itemID end
sounds=0
SOUNDKIT={UI_BAG_SORTING_01=123}
function PlaySound(id) assert(id==123); sounds=sounds+1 end
nativeSorts=0
C_Container.SortBags=function() nativeSorts=nativeSorts+1 end
''')
start = source.index('    local sortLocked = false')
end = source.index('    DoVisualSort = function()', start)
native_start = source.index('    local function DoBlizzardSort()')
native_end = source.index('    sort:SetScript("OnClick"', native_start)
lua.execute(source[start:end] + source[native_start:native_end] + '''
PhysicalForTest=DoPhysicalSort
NativeForTest=DoBlizzardSort
''')
lua.execute('''
Bag(0,3); Item(0,3,1)
PhysicalForTest(); assert(not sort.enabled and EUI_Bags.refreshEnabled==false)
EUI_Bags._unlockSort(); assert(not sort.enabled,'drag callback unlocked running sort')
PhysicalForTest(); NativeForTest(); assert(nativeSorts==0,'overlapping sort modes')
Advance(5)
assert(sort.enabled and EUI_Bags._diceBtn.enabled and EUI_Bags.refreshEnabled and EUI_Bags.refreshed)
assert(sounds==1, 'one physical-sort sound after acceptance')
NativeForTest(); EUI_Bags._unlockSort(); assert(not sort.enabled and nativeSorts==1)
Advance(4); assert(sort.enabled)
combat=true; NativeForTest(); assert(nativeSorts==1 and UIErrorsFrame.message)
combat=false; externalCursor='item'; NativeForTest(); assert(nativeSorts==1 and externalCursor=='item')
assert(sounds==2, 'blocked or duplicate sorts must not play sounds')
''')
print('PASS: actual header integration; button lock ownership; native sort guards; refresh cleanup')

compile_lua = lua.eval('function(s) local f,e=loadstring(s); assert(f,e) end')
for path in BAGS.glob('*.lua'):
    compile_lua(path.read_text(encoding='utf-8-sig'))
toc = (BAGS / 'EllesmereUIBags.toc').read_text()
assert toc.index('EllesmereUIBags_Sort.lua') < toc.index('\nEllesmereUIBags.lua')
print('PASS: all Bags Lua syntax; sort engine manifest order')
