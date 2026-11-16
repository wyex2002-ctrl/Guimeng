-- Single edit point. Probabilities are fractions, not integer percentages.
-- Context includes luck, actor/owner, skill (combat), and item (enhancement).
return {
 guild_attack=.11, -- Existing 幸运加持: integer 90..100 inclusive.
 equipment=function(context)return context.luck>=1 and 1/(10-context.luck)or 0 end,
 enhancement=function(context)return .40,.30,.30 end, -- success, loss, unchanged
}
