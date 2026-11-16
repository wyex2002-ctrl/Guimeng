-- All probabilities live here. Fractions, never rounded percentages.
-- Context: luck, actor/owner, skill/kind, companion; enhancement also item/source.
local oil={
 {1,0,0},          -- 0 -> 1
 {.70,.10,.20},    -- 1
 {.55,.15,.30},    -- 2
 {.40,.20,.40},    -- 3
 {.20,.32,.48},    -- 4
 {.09,.39,.52},    -- 5
 {.03,.46,.51},    -- 6 -> 7
}
return {
 guild_attack=.11, -- Original inclusive integer 90..100, preserved.
 equipment=function(context)
  local x=tonumber(context.luck)or 0
  if x~=x or x==math.huge or x==-math.huge then x=0 end
  x=math.max(0,math.min(context.companion and 7 or 9,x))
  if x<1 then return 0 end -- User correction: zero equipment luck has no effect.
  -- The requested B3 scope is hero + hero-owned summons. Preserve companion
  -- and companion-summon combat behavior from v248 (including zero luck).
  if context.companion then return x>=1 and 1/(10-x)or 0 end
  local q=x/7
  return math.min(1,math.max(0,1/(10-x)+.10*q+.08*q*q))
 end,
 enhancement=function(context)
  local weights=oil[context.luck+1]
  if not weights then return 0,0,0 end
  return weights[1],weights[2],weights[3]
 end,
}
