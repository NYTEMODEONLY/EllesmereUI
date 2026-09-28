"""Execute the installed chat kits with the companion; no WoW input or saves."""
from pathlib import Path
from lupa.lua51 import LuaRuntime

root = Path(__file__).resolve().parents[2]
companion = root / "EllesmereUIChatMeters"
mock = (companion / "tests/mock_wow.lua").read_text(encoding="utf-8-sig")
support = r'''
local F = getmetatable(UIParent).__index
function F:SetTexture(v) self.texture=v end
function F:SetAtlas(v) self.atlas=v end
function F:SetTexCoord(...) self.texcoord={...} end
function F:SetDesaturated(v) self.desaturated=v end
function F:SetDrawLayer(layer,sub) self.layer=layer; self.sub=sub end
function F:GetDrawLayer() return self.layer or "BACKGROUND", self.sub or 0 end
function F:SetColorTexture(...) self.color={...} end
function F:SetVertexColor(...) self.color={...} end
function F:SetHorizTile() end
function F:SetVertTile() end
function F:SetGradient(...) self.gradient={...} end
function F:SetBlendMode(v) self.blend=v end
function F:SetFont(...) self.font={...} end
function F:LockHighlight() self.highlightLocked=true end
function F:UnlockHighlight() self.highlightLocked=false end
for _, kind in ipairs({"Normal","Pushed","Highlight"}) do
    F["Set"..kind.."Texture"]=function(self,v)
        self[kind]=self[kind] or self:CreateTexture(); self[kind]:SetTexture(v)
    end
    F["Set"..kind.."Atlas"]=function(self,v)
        self[kind]=self[kind] or self:CreateTexture(); self[kind]:SetAtlas(v)
    end
    F["Get"..kind.."Texture"]=function(self) return self[kind] end
end
C_Texture={GetAtlasInfo=function() return {} end}
function CreateColor(...) return {values={...},SetRGBA=function(self,...) self.values={...} end} end
EllesmereUI.IS_FOREVER=true
EllesmereUI.FOREVER_BORDER={outer=1,line=1,corner=4}
EllesmereUI.ForeverBorderOK=function() return true end
EllesmereUI.ForeverBorder=function(host) return CreateFrame("Frame",nil,host) end
EllesmereUI.ForeverBorderSeat=function(rim,...) rim.seat={...} end
EllesmereUI.ForeverBorderPaint=function(rim,...) rim.color={...} end
EllesmereUI.ForeverBorderShown=function(rim,on) rim:SetShown(on) end
EllesmereUI.PrimeFontShadow=function() end
CHAT.ECHAT.GetFont=function() return "TestFont" end
CHAT.ChatStock=function() return STYLE~="eui" end
CHAT.ChatStyle=function() return STYLE=="forever" and "blizzard" or STYLE end
CHAT.ChatForever=function() return STYLE=="forever" end
'''
for style in ("eui", "blizzard", "classic", "forever"):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().STYLE = style
    lua.execute(mock)
    lua.execute(support)
    for name in ("EllesmereUIChat_SidebarStock.lua", "EllesmereUIChat_Forever.lua"):
        lua.execute((root / "EllesmereUIChat" / name).read_text(encoding="utf-8-sig"), "EllesmereUIChat", lua.globals().CHAT)
    lua.execute((companion / "ChatMeters.lua").read_text(encoding="utf-8-sig"))
    lua.execute((companion / "tests/style_scenarios.lua").read_text(encoding="utf-8-sig"))

source = (root / "EllesmereUIDamageMeters/EllesmereUIDamageMeters.lua").read_text(encoding="utf-8-sig")
art = source[source.index("ns.DM_BLIZZ_BAR_BG   ="):source.index("-- Header icon visibility")]
for style in ("eui", "blizzard", "classic", "forever"):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().STYLE = style
    lua.execute(mock)
    lua.execute(support)
    lua.execute(r'''
        EUI=EllesmereUI
        MEDIA="Interface\\AddOns\\EllesmereUIDamageMeters\\Media\\"
        Enum.DamageMeterType={DamageDone=0,HealingDone=1,DamageTaken=2,AvoidableDamageTaken=3,
            EnemyDamageTaken=4,Interrupts=5,Dispels=6,Deaths=7}
        DM_TYPE_ICONS={THREAT=MEDIA.."dm_home_taken.png"}
        _EDM_DB={profile={dm={useClassicStyle=STYLE=="classic",
            useBlizzardStyle=STYLE=="blizzard" or STYLE=="forever",useForeverStyle=STYLE=="forever"}}}
        ns={EDM={DB=function() return _EDM_DB.profile.dm end}}
    ''')
    lua.execute(art)
    lua.execute(r'''
        local frame=CreateFrame("Frame",nil,UIParent)
        local tex=frame:CreateTexture()
        local painted=ns.DMPaintHdrArt(tex,"report")
        assert(painted==(STYLE=="classic" or STYLE=="forever"))
        if painted then
            assert(tex._hdrArt and tex.texture)
            assert(ns.DMHdrHover(tex,true)); assert(ns.DMHdrHover(tex,false))
        end
        ns.DMSetTypeIcon(tex,"THREAT")
        if STYLE=="classic" then assert(tex.texture:find("DefensiveStance")) end
        if STYLE=="forever" then assert(tex._hdrArt.plate and tex._fvPlate) end
        local bg=frame:CreateTexture()
        ns.DMPaintWindowBg(bg,0.06,0.08,0.10,1,true)
        if STYLE=="forever" then assert(frame._fvRim) end
        if STYLE=="classic" then assert(bg._classicBg) end
        if STYLE=="blizzard" then assert(bg._blizzParts) end
        local count=#FRAMES
        ns.DMPaintWindowBg(bg,0.06,0.08,0.10,1,true)
        assert(#FRAMES==count,"report shell reuses artwork")
    ''')
    print("PASS: real meter Report/Threat art and dialog shell:", style)

assert 'end, "report")' in source[source.index('W.reportBtn = MakeHeaderBtn'):source.index('-- Ordered list of header buttons')]
glyph = companion / "Media/meters.tga"
assert glyph.exists() and glyph.stat().st_size == 18 + 32 * 32 * 4
print("PASS: custom style contracts; live rendering remains player acceptance")
