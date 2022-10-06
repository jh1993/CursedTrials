from Mutators import *
from Level import *
from Consumables import *

class FireworksSpell(Spell):

    def on_init(self):
        self.name = "Fireworks"
        self.level = 1
        self.tags = [Tags.Fire, Tags.Sorcery]
        self.max_charges = 18
        self.range = 8
        self.damage = 0
        self.radius = 0
    
    def get_description(self):
        return "Deals [{damage}_fire:fire] damage to units in a [{radius}_tile:radius] burst.".format(**self.fmt_dict())
    
    def cast(self, x, y):
        for point in Bolt(self.caster.level, self.caster, Point(x, y)):
            self.caster.level.show_effect(point.x, point.y, Tags.Fire, minor=True)
            yield
        damage = self.get_stat("damage")
        for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')):
            for point in stage:
                self.caster.level.deal_damage(point.x, point.y, damage, Tags.Fire, self)
            yield

    def get_impacted_tiles(self, x, y):
        return [p for stage in Burst(self.caster.level, Point(x, y), self.get_stat('radius')) for p in stage]

class Pyrotechnician(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "The only available spell is Fireworks, which deals 0 fire damage in a 0 tile burst.\nStart with Fireworks for free and all SP on realm 1 already collected."

    def on_generate_spells(self, spells):
        spells.clear()

    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty == 1:
            levelgen.num_xp = 0

    def on_game_begin(self, game):
        game.p1.xp = 4
        game.p1.add_spell(FireworksSpell())

class CurseOfArachneBuff(Buff):

    def on_init(self):
        self.name = "Curse of Arachne"
        self.color = Tags.Spider.color
        self.buff_type = BUFF_TYPE_NONE
        self.description = "Take 1 poison damage per turn. Cannot be removed."
    
    def on_advance(self):
        self.owner.deal_damage(1, Tags.Poison, self)

class WorldWideWeb(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Start with Silkshifter and Teleport. Arcane Accounting is not allowed.\nAll enemies are spiders. You always take 1 poison damage per turn."
        self.global_triggers[EventOnUnitPreAdded] = self.on_unit_pre_added

    def on_unit_pre_added(self, evt):
        if not evt.unit.ever_spawned:
            self.modify_unit(evt.unit)

    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        if unit.team == TEAM_PLAYER:
            return
        unit.tags.append(Tags.Spider)
        buff = SpiderBuff()
        buff.buff_type = BUFF_TYPE_PASSIVE
        unit.apply_buff(buff)

    def on_generate_skills(self, skills):
        for skill in skills:
            if isinstance(skill, ArcaneAccountant):
                skills.remove(skill)
                return

    def on_game_begin(self, game):
        game.p1.apply_buff(CurseOfArachneBuff())
        for spell in game.all_player_spells:
            if type(spell) == Teleport:
                game.p1.add_spell(spell)
                break
        for skill in game.all_player_skills:
            if isinstance(skill, SilkShifter):
                game.p1.apply_buff(skill)

class ToxicHumor(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "All living, nature, and demon enemies have -100 poison resistance and +200 resistance to all other elements.\nAll other enemies have +100 poison resistance."
        self.global_triggers[EventOnUnitPreAdded] = self.on_unit_pre_added

    def on_unit_pre_added(self, evt):
        if not evt.unit.ever_spawned:
            self.modify_unit(evt.unit)

    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        if unit.team == TEAM_PLAYER:
            return
        if [tag for tag in [Tags.Living, Tags.Demon, Tags.Nature] if tag in unit.tags]:
            unit.resists[Tags.Poison] -= 100
            for tag in [Tags.Fire, Tags.Ice, Tags.Lightning, Tags.Arcane, Tags.Physical, Tags.Holy, Tags.Dark]:
                unit.resists[tag] += 200
        else:
            unit.resists[Tags.Poison] += 100

all_trials.extend([Trial("Pyrotechnician", Pyrotechnician()), Trial("World Wide Web", WorldWideWeb()), Trial("Toxic Humor", ToxicHumor())])