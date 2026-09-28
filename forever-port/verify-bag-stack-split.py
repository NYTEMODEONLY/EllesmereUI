"""Check merged bag click targets against the native Forever split handler."""
from pathlib import Path
import os
import re
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[1]
source = (root.parent / 'EllesmereUIBags/EllesmereUIBags.lua').read_text(encoding='utf-8-sig')
native = (Path(os.environ.get('EUI_NATIVE_SOURCE_ROOT', Path(os.environ['TEMP']) / 'eui-forever-research/wow-ui-source-forever/Interface/AddOns')) / 'Blizzard_UIPanels_Game/Mainline/ContainerFrame.lua').read_text()
lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
profile = {}
function BP() return profile end
EUI_Bags = {}
function AcquireSlotTable() return {} end
function IsGearCategory(category) return category == 99 end
function wipe(t) for k in pairs(t) do t[k] = nil end end
ContainerFrameItemButtonMixin = {}
ItemLocation = { CreateFromBagAndSlot = function() return {} end }
function IsModifiedClick(action) return action == "SPLITSTACK" end
function HandleModifiedItemClick() return false end
function CursorHasItem() return false end
C_Container = {
    GetContainerItemLink = function() return "dust" end,
    GetContainerItemInfo = function(bag, slot) return slots[bag .. ":" .. slot] end,
}
StackSplitFrame = { OpenStackSplitFrame = function(self, count, owner)
    self.maxStack = count; self.owner = owner
end }
''')
compile_lua = lua.eval('function(s) local f,e=loadstring(s); assert(f,e) end')
compile_lua(source)
merge = re.search(r'local function MergeDuplicates\(items\).*?\nend\n', source, re.S).group()
lua.execute(merge + '\nMergeForTest = MergeDuplicates')
handler = re.search(r'function ContainerFrameItemButtonMixin:OnModifiedClick\(button\).*?\nend\n', native, re.S).group()
lua.execute(handler)
lua.execute('''
function item(bag, slot, count, link, category)
    return {bag=bag, slot=slot, itemLink=link or "dust", categoryIndex=category,
        info={stackCount=count, itemID=10940}, marker=bag .. ":" .. slot}
end
local one, twenty = item(0, 1, 1), item(2, 2, 20)
one.oldOnly = true
slots = {["0:1"]=one.info, ["2:2"]=twenty.info}
local function click(data)
    StackSplitFrame.maxStack = nil
    local button = {GetBagID=function() return data.bag end,
        GetID=function() return data.slot end}
    ContainerFrameItemButtonMixin.OnModifiedClick(button, "LeftButton")
    return StackSplitFrame.maxStack
end
assert(click(one) == nil, "reproduce original singleton click failure")
local out = MergeForTest({one, twenty})
assert(#out == 1 and out[1]._mergedCount == 21)
assert(out[1].bag == 2 and out[1].slot == 2 and out[1].info == twenty.info)
assert(out[1].marker == "2:2" and out[1].oldOnly == nil)
assert(click(out[1]) == 20, "native split dialog must open on the real stack")
assert(one.info.stackCount == 1 and twenty.info.stackCount == 20)
assert(one._mergedCount == nil and twenty._mergedCount == nil)
assert(one.bag == 0 and one.slot == 1 and one.oldOnly)
out = MergeForTest({twenty, one})
assert(out[1]._mergedCount == 21 and out[1].slot == 2)
local bigger = item(3, 3, 30)
local other = item(0, 4, 2, "powder")
out = MergeForTest({one, other, twenty, bigger})
assert(#out == 2 and out[1]._mergedCount == 51 and out[1].bag == 3)
assert(out[2] == other, "first occurrence keeps the merged display position")
local equal = item(1, 5, 20)
out = MergeForTest({twenty, equal})
assert(out[1].bag == 2 and out[1]._mergedCount == 40, "ties stay stable")
local singles = MergeForTest({one, item(1, 6, 1)})
assert(singles[1]._mergedCount == 2 and click(singles[1]) == nil,
    "two singletons cannot be split as a physical stack")
local items = {one, twenty}
profile.bagMergeDuplicates = false
assert(MergeForTest(items) == items)
profile.bagMergeDuplicates = true
_anyItemPanelOpen = true
assert(MergeForTest(items) == items)
_anyItemPanelOpen = false
EUI_Bags._unmergedLinks = {dust=true}
out = MergeForTest(items)
assert(#out == 2 and out[1] == one and out[2] == twenty)
EUI_Bags._unmergedLinks = nil
out = MergeForTest({item(0, 1, 1, "gear", 99), item(0, 2, 1, "gear", 99)})
assert(#out == 2)
out = MergeForTest({item(0, 1, 1, "dust:a"), item(0, 2, 20, "dust:b")})
assert(#out == 2, "different item links remain separate")
''')
print('PASS: Lua syntax; singleton reproduction; native split popup count; largest-stack selection; display order; canonical data isolation; merge exclusions')
