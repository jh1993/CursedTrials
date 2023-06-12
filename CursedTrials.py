from Mutators import *
from Level import *
from Consumables import *
from Upgrades import *
from Spells import *
from Monsters import *
from Variants import *
from RareMonsters import *

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
        self.description = "Take 1 poison damage per turn if there are enemies in the realm."
    
    def on_advance(self):
        if all([u.team == TEAM_PLAYER for u in self.owner.level.units]):
            return
        self.owner.deal_damage(1, Tags.Poison, self)

class WorldWideWeb(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Start with Silkshifter and Teleport.\nArcane Accounting is not allowed.\nAll enemies are spiders.\nYou always take 1 poison damage per turn if there are enemies in the realm."
        self.global_triggers[EventOnUnitAdded] = self.on_unit_added

    def on_unit_added(self, evt):
        self.modify_unit(evt.unit)

    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        if unit.team == TEAM_PLAYER:
            return
        if Tags.Spider not in unit.tags:
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
                return

class ToxicHumor(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "All living, nature, and demon enemies have -100 poison resistance,\nand +200 resistance to all other elements.\nAll other enemies have +100 poison resistance."
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

class CurseOfTheDarkGodBuff(Buff):

    def on_init(self):
        self.name = "Curse of the Dark God"
        self.color = Color(252, 176, 96)
        self.description = "Whenever you cast a spell, before it resolves, you are teleported to the target tile.\nConvert tiles into floor tiles and swap place with the target unit if necessary."
        self.buff_type = BUFF_TYPE_NONE
        self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
    
    def on_spell_cast(self, evt):
        if not self.owner.flying:
            self.owner.level.make_floor(evt.x, evt.y)
        unit = self.owner.level.get_unit_at(evt.x, evt.y)
        if unit and not unit.flying:
            self.owner.level.make_floor(self.owner.x, self.owner.y)
        self.owner.level.act_move(self.owner, evt.x, evt.y, teleport=True, force_swap=True)

class TomeOfTheDarkGod(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Whenever you cast a spell, before it resolves, you are teleported to the target tile.\nConvert tiles into floor tiles and swap place with the target unit if necessary.\nNon-sorcery spells and self-targeted spells are not available."

    def on_generate_spells(self, spells):
        for spell in list(spells):
            if Tags.Sorcery not in spell.tags or spell.range == 0:
                spells.remove(spell)

    def on_game_begin(self, game):
        game.p1.apply_buff(CurseOfTheDarkGodBuff())

class ExtraReincarnations(Mutator):

    def __init__(self, lives):
        Mutator.__init__(self)
        self.lives = lives
        self.description = "All enemy units have +%i reincarnations" % self.lives
        self.global_triggers[EventOnUnitAdded] = self.on_unit_added

    def on_unit_added(self, evt):
        self.modify_unit(evt.unit)

    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        if unit.team == TEAM_PLAYER:
            return
        existing = unit.get_buff(ReincarnationBuff)
        if existing:
            existing.lives += self.lives
        else:
            buff = ReincarnationBuff(self.lives)
            buff.buff_type = BUFF_TYPE_PASSIVE
            unit.apply_buff(buff)

class ExtraPhoenixFire(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Realm 1 has no enemies\nAll enemies have Phoenix Fire\nPhoenixes explode an additional time on death"
        self.global_triggers[EventOnUnitAdded] = self.on_unit_added

    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty == 1:
            levelgen.num_generators = 0
            levelgen.num_monsters = 0
            levelgen.bosses = []

    def on_unit_added(self, evt):
        self.modify_unit(evt.unit)

    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        if unit.team == TEAM_PLAYER:
            return
        existing = unit.get_buff(PhoenixBuff)
        if existing:
            existing.stack_type = STACK_INTENSITY
        buff = PhoenixBuff()
        buff.buff_type = BUFF_TYPE_PASSIVE
        buff.stack_type = STACK_INTENSITY
        unit.apply_buff(buff)

class FullImmunity(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "All enemies gain 100 resistance of each damage type they are immune to.\nFiery Judgement, Starfire, and Holy Thunder are not allowed."
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
        for tag in unit.resists.keys():
            if unit.resists[tag] >= 100:
                unit.resists[tag] += 100

    def on_generate_skills(self, skills):
        for skill in list(skills):
            if type(skill) in [FieryJudgement, Starfire, HolyThunder]:
                skills.remove(skill)

class SuckerPunchBuff(Buff):

    def on_init(self):
        self.color = Tags.Translocation.color
        self.buff_type = BUFF_TYPE_PASSIVE
        self.description = "Each turn, teleports to a random tile before acting."
    
    def on_pre_advance(self):
        randomly_teleport(self.owner, RANGE_GLOBAL)

class SuckerPunch(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Realm 1 has no enemies.\nEach turn, each enemy teleports to a random tile before acting.\nAll enemies have Death Touch."
        self.global_triggers[EventOnUnitAdded] = self.on_unit_added

    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty == 1:
            levelgen.num_generators = 0
            levelgen.num_monsters = 0
            levelgen.bosses = []

    def on_unit_added(self, evt):
        self.modify_unit(evt.unit)

    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        if unit.team == TEAM_PLAYER:
            return
        unit.apply_buff(SuckerPunchBuff())
        melee = SimpleMeleeAttack(damage=200, damage_type=Tags.Dark)
        melee.name = "Death Touch"
        unit.add_spell(melee, prepend=True)

class AmogusBuff(Buff):

    def on_init(self):
        self.buff_type = BUFF_TYPE_PASSIVE

    def on_pre_advance(self):
        if random.random() >= 0.1:
            return
        if all([u.team == TEAM_PLAYER for u in self.owner.level.units]):
            return
        self.owner.team = TEAM_ENEMY

class AmongThem(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Each minion you summon has a 25% chance to be a traitor.\nEach turn, a traitor has a 10% chance to become permanently hostile before it acts,\nif there are enemies in the realm.\nYou cannot tell whether a minion is a traitor until it becomes hostile."
        self.global_triggers[EventOnUnitAdded] = self.on_unit_added

    def on_unit_added(self, evt):
        self.modify_unit(evt.unit)

    def modify_unit(self, unit):
        if unit.team != TEAM_PLAYER or unit.is_player_controlled or random.random() >= 0.25:
            return
        unit.apply_buff(AmogusBuff())

class ArcaneWeaknessBuff(Buff):
    def on_init(self):
        self.name = "Arcane Weakness"
        self.color = Tags.Arcane.color
        self.buff_type = BUFF_TYPE_PASSIVE
        self.resists[Tags.Arcane] = -100

class SpawnBoneShamblersOnDeath(Buff):

    def on_init(self):
        self.owner_triggers[EventOnDeath] = self.on_death
        self.name = "Spawn Bone Shamblers on Death"
        self.buff_type = BUFF_TYPE_PASSIVE

    def on_attempt_apply(self, owner):
        return "Bone Shambler" not in owner.name

    def on_death(self, evt):
        for _ in range(2):
            unit = BoneShambler(self.owner.max_hp//2)
            if unit.max_hp == 0:
                return
            self.summon(unit)
            
    def get_tooltip(self):
        return "On death, spawn 2 bone shamblers with half of this unit's max HP."

class BombasticBones(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Start with Arcane Combustion\nAll units have Arcane Weakness"
        self.global_triggers[EventOnUnitAdded] = self.on_unit_added

    def on_unit_added(self, evt):
        self.modify_unit(evt.unit)

    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        unit.apply_buff(ArcaneWeaknessBuff())

    def on_game_begin(self, game):
        buff = ArcaneWeaknessBuff()
        buff.buff_type = BUFF_TYPE_NONE
        game.p1.apply_buff(buff)
        for skill in game.all_player_skills:
            if isinstance(skill, ArcaneCombustion):
                game.p1.apply_buff(skill)
                return

class SimulatedViolenceBuff(Buff):

    def on_init(self):
        self.buff_type = BUFF_TYPE_PASSIVE
        self.owner_triggers[EventOnPreDamaged] = self.on_pre_damaged
    
    def on_pre_damaged(self, evt):
        if evt.damage <= 0 or self.owner.shields > 0:
            return
        penetration = evt.penetration if hasattr(evt, "penetration") else 0
        damage = math.ceil(evt.damage*(100 - min(self.owner.resists[evt.damage_type] - penetration, 100))/100)
        if damage <= 0:
            return
        self.owner.add_shields(1)
        self.owner.cur_hp = max(0, self.owner.cur_hp - damage)
        if self.owner.cur_hp == 0:
            self.owner.kill(trigger_death_event=self.owner.has_buff(ReincarnationBuff))

class SimulatedViolence(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Whenever an unshielded unit is about to take damage, it gains 1 SH and loses HP equal to the damage it would take.\nIf a unit without reincarnations is reduced to 0 HP this way, it vanishes without dying.\nUnder these conditions, most effects normally triggered by units taking damage or dying cannot be triggered."
        self.global_triggers[EventOnUnitAdded] = self.on_unit_added

    def on_unit_added(self, evt):
        self.modify_unit(evt.unit)

    def on_levelgen(self, levelgen):
        for u in levelgen.level.units:
            self.modify_unit(u)

    def modify_unit(self, unit):
        unit.apply_buff(SimulatedViolenceBuff())

    def on_game_begin(self, game):
        self.modify_unit(game.p1)

class ShameBuff(Buff):

    def on_init(self):
        self.name = "Shame"
        self.color = COLOR_DAMAGE
        self.buff_type = BUFF_TYPE_NONE
        self.stack_type = STACK_INTENSITY
    
    def on_applied(self, owner):
        if self.owner.get_buff_stacks(ShameBuff) >= 25:
            self.owner.level.queue_spell(self.kill())
        else:
            self.owner.level.show_effect(0, 0, Tags.Sound_Effect, 'death_player')

    def kill(self):
        self.owner.kill()
        yield

class JustDontGetHitBuff(Buff):

    def on_init(self):
        self.buff_type = BUFF_TYPE_PASSIVE
        self.owner_triggers[EventOnDamaged] = self.on_damaged
    
    def on_damaged(self, evt):
        self.owner.apply_buff(ShameBuff())

class JustDontGetHit(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "When you take damage, you permanently gain a stack of Shame, which cannot be removed.\nIf you reach 25 stacks of Shame, you die instantly."

    def on_game_begin(self, game):
        game.p1.apply_buff(JustDontGetHitBuff())

class MoassemansScornBuff(Buff):

    def __init__(self, game):
        self.game = game
        Buff.__init__(self)

    def on_init(self):
        self.name = "Moasseman's Scorn"
        self.color = COLOR_CHARGES
        self.buff_type = BUFF_TYPE_NONE
        self.description = "When you gain a new spell, you lose max HP equal to 50 times your previous number of spells.\nWhen you cast a spell, that spell loses 1 max charge until you use a mana potion."
        self.owner_triggers[EventOnSpellCast] = self.on_spell_cast
    
    def on_spell_cast(self, evt):
        if isinstance(evt.spell, SpellCouponSpell):
            for buff in list(self.owner.buffs):
                if isinstance(buff, MaxChargePenaltyBuff):
                    self.owner.remove_buff(buff)
            evt.spell.cast_instant(evt.x, evt.y)
        elif evt.spell.max_charges > 0:
            self.owner.apply_buff(MaxChargePenaltyBuff(evt.spell))
            evt.spell.cur_charges = min(evt.spell.cur_charges, evt.spell.get_stat("max_charges"))

    def on_add_spell(self, spell):
        self.owner.max_hp = max(0, self.owner.max_hp - 50*len(self.owner.spells))
        self.owner.cur_hp = min(self.owner.cur_hp, self.owner.max_hp)
        if self.owner.max_hp == 0:
            self.owner.kill()
            self.owner.level.is_awaiting_input = False
            self.game.check_triggers()

class MaxChargePenaltyBuff(Buff):
    def __init__(self, spell):
        Buff.__init__(self)
        self.name = "-1 %s" % spell.name
        self.color = COLOR_CHARGES
        self.buff_type = BUFF_TYPE_NONE
        self.stack_type = STACK_INTENSITY
        self.spell_bonuses[type(spell)]["max_charges"] = -1

class MoassemansScorn(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "When you gain a new spell, you lose max HP equal to 50 times your previous number of spells.\nWhen you cast a spell, that spell loses 1 max charge until you use a mana potion."

    def on_game_begin(self, game):
        game.p1.apply_buff(MoassemansScornBuff(game))

class ParanoiaBuff(Buff):

    def on_init(self):
        self.name = "Paranoia"
        self.color = Stun().color
        self.buff_type = BUFF_TYPE_NONE
        self.description = "Each turn, each tile has a 0.02% chance to spawn a Concussive Idol."
    
    def on_advance(self):
        if all([unit.team == TEAM_PLAYER for unit in self.owner.level.units]):
            return
        for tile in self.owner.level.iter_tiles():
            if random.random() >= 0.0002:
                continue
            self.summon(ConcussiveIdol(), target=tile, radius=0, team=TEAM_ENEMY)

class Paranoia(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Each turn, each tile has a 0.02% chance to spawn a Concussive Idol.\nPurity is not allowed."

    def on_game_begin(self, game):
        game.p1.apply_buff(ParanoiaBuff())

    def on_generate_spells(self, spells):
        for spell in spells:
            if isinstance(spell, PuritySpell):
                spells.remove(spell)
                return

random_tags = [Tags.Sorcery, Tags.Enchantment, Tags.Conjuration, Tags.Fire, Tags.Ice, Tags.Lightning, Tags.Nature, Tags.Arcane, Tags.Dark, Tags.Holy, Tags.Chaos, Tags.Metallic, Tags.Translocation, Tags.Dragon, Tags.Orb, Tags.Eye, Tags.Word]

class ImproviserUnhinged(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "All spells and spell upgrades have randomized levels between 1 and 7.\nAll skills have randomized levels between 4 and 7.\nAll spells and skills have 2 to 4 randomized tags."
    
    def on_generate_spells(self, spells):
        for spell in spells:
            spell.level = random.choice(list(range(1, 8)))
            random.shuffle(random_tags)
            spell.tags = list(random_tags[:random.choice(list(range(2, 5)))])
            for upgrade in spell.spell_upgrades:
                upgrade.tags = list(spell.tags)
                upgrade.level = random.choice(list(range(1, 8)))
        spells.sort(key=lambda s: s.level)

    def on_generate_skills(self, skills):
        for skill in skills:
            skill.level = random.choice(list(range(4, 8)))
            random.shuffle(random_tags)
            skill.tags = list(random_tags[:random.choice(list(range(2, 5)))])
        skills.sort(key=lambda s: s.level)

class BruhMoment(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Whenever a unit takes damage, if there are enemies in the realm,\nthe realm has a 0.5% chance to be planeshifted.\nThese planeshifts will never result in unreachable tiles."

    def on_game_begin(self, game):
        game.p1.apply_buff(BruhMomentBuff())

class BruhMomentBuff(Buff):

    def __init__(self):
        Buff.__init__(self)
        self.buff_type = BUFF_TYPE_NONE
        self.name = "Bruh Moment"
        self.description = "Whenever a unit takes damage, if there are enemies in the realm, the realm has a 0.5% chance to be planeshifted.\nThese planeshifts will never result in unreachable tiles."
        self.color = Color(216, 27, 96)
        self.spell = MordredCorruption()
        self.spell.num_exits = 3
        self.global_triggers[EventOnDamaged] = self.on_damaged
    
    def on_applied(self, owner):
        self.spell.caster = self.owner
        self.spell.owner = self.owner

    def on_damaged(self, evt):
        if random.random() >= 0.005:
            return
        if all([u.team == TEAM_PLAYER for u in self.owner.level.units]):
            return
        self.owner.level.queue_spell(self.spell.cast(self.owner.x, self.owner.y))
        self.owner.level.gen_params.ensure_connectivity()
        self.owner.level.gen_params.ensure_connectivity(chasm=True)

class SkillIssue(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Realm 1 and 2 have no enemies\nSpells are unavailable"

    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty <= 2:
            levelgen.num_generators = 0
            levelgen.num_monsters = 0
            levelgen.bosses = []

    def on_generate_spells(self, spells):
        spells.clear()

class NoWalls(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Realms have no walls"
    
    def on_levelgen(self, levelgen):
        for tile in levelgen.level.iter_tiles():
            if tile.is_wall():
                levelgen.level.make_chasm(tile.x, tile.y)

class SpeedrunnerBuff(Buff):

    def on_init(self):
        self.buff_type = BUFF_TYPE_PASSIVE
    
    def on_advance(self):
        if random.random() >= 0.05 or all([u.team == TEAM_PLAYER for u in self.owner.level.units]):
            return
        buff = ShameBuff()
        buff.name = "Anxiety"
        self.owner.apply_buff(buff)

class Speedrunner(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Each turn, if there are enemies in the realm, you have a 5% chance\nto permanently gain a stack of Anxiety, which cannot be removed.\nIf you reach 25 stacks of Anxiety, you die instantly."

    def on_game_begin(self, game):
        game.p1.apply_buff(SpeedrunnerBuff())

class DepressionBuff(Buff):

    def on_init(self):
        self.name = "Depression"
        self.color = COLOR_DAMAGE
        self.buff_type = BUFF_TYPE_NONE
        self.global_bonuses["damage"] = -999999

class AsianParent(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Your minions deal 999999 less damage, to a minimum of 0.\nRealm 1, 2, and 3 have no enemies."
        self.global_triggers[EventOnUnitAdded] = self.on_unit_added

    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty <= 3:
            levelgen.num_generators = 0
            levelgen.num_monsters = 0
            levelgen.bosses = []

    def on_unit_added(self, evt):
        if evt.unit.team != TEAM_PLAYER:
            return
        evt.unit.apply_buff(DepressionBuff())

class AsianChild(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "You deal 999999 less damage, to a minimum of 0.\nRealm 1, 2, and 3 have no enemies."

    def on_levelgen_pre(self, levelgen):
        if levelgen.difficulty <= 3:
            levelgen.num_generators = 0
            levelgen.num_monsters = 0
            levelgen.bosses = []

    def on_game_begin(self, game):
        game.p1.apply_buff(DepressionBuff())

class NoConjuration(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Conjuration spells are unavailable"
    
    def on_generate_spells(self, spells):
        for s in list(spells):
            if Tags.Conjuration in s.tags:
                spells.remove(s)

class PjoxtsScornBuff(Buff):

    def on_init(self):
        self.name = "Pjoxt's Scorn"
        self.color = Tags.Ice.color
        self.buff_type = BUFF_TYPE_NONE
        self.owner_triggers[EventOnUnitAdded] = self.on_unit_added
    
    def min_spells(self, num):
        if not self.owner:
            return 0
        return math.ceil(3*num/4)

    def get_description(self):
        if not self.owner:
            return ""
        return "You must have at least %i spells before entering the next realm." % self.min_spells(self.owner.level.gen_params.difficulty + 1)

    def on_unit_added(self, evt):
        if len(self.owner.spells) < self.min_spells(self.owner.level.gen_params.difficulty):
            self.owner.kill()

class PjoxtsScorn(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "When you enter a new realm, you must have more\nspells than 3/4 of the realm number, rounded up.\nIf you don't have enough spells, you die instantly."

    def on_game_begin(self, game):
        game.p1.apply_buff(PjoxtsScornBuff())

class NoUpgrades(Mutator):

    def __init__(self):
        Mutator.__init__(self)
        self.description = "Spell upgrades are unavailable"
    
    def on_generate_spells(self, spells):
        for s in spells:
            s.spell_upgrades = []

all_trials.append(Trial("Pyrotechnician", Pyrotechnician()))
all_trials.append(Trial("World Wide Web", WorldWideWeb()))
all_trials.append(Trial("Toxic Humor", ToxicHumor()))
all_trials.append(Trial("Worst Possible Weekly Run", [NumPortals(1), StackLimit(1), EnemyBuff(lambda: RespawnAs(Gnome), exclude_named="Gnome"), RandomSpellRestriction(0.95), RandomSkillRestriction(0.95)]))
all_trials.append(Trial("Tome of the Dark God", TomeOfTheDarkGod()))
all_trials.append(Trial("Angry Birds", [ExtraPhoenixFire(), ExtraReincarnations(1)]))
all_trials.append(Trial("Full Immunity", FullImmunity()))
all_trials.append(Trial("Sucker Punch", SuckerPunch()))
all_trials.append(Trial("Among Them", [SpellTagRestriction(Tags.Conjuration), AmongThem()]))
all_trials.append(Trial("Bombastic Bones", [SpellTagRestriction(Tags.Arcane), BombasticBones(), EnemyBuff(SpawnBoneShamblersOnDeath)]))
all_trials.append(Trial("Simulated Violence", SimulatedViolence()))
all_trials.append(Trial("Just Don't Get Hit", JustDontGetHit()))
all_trials.append(Trial("Moasseman's Scorn", MoassemansScorn()))
all_trials.append(Trial("Paranoia", Paranoia()))
all_trials.append(Trial("Improviser Unhinged", ImproviserUnhinged()))
all_trials.append(Trial("Bruh Moment", BruhMoment()))
all_trials.append(Trial("Skill Issue", SkillIssue()))
all_trials.append(Trial("Eye Scream", [NoWalls(), EnemyBuff(lambda: RespawnAs(FloatingEyeIce), exclude_named="Ice Eye")]))
all_trials.append(Trial("Speedrunner", Speedrunner()))
all_trials.append(Trial("Asian Parent", [SpellTagRestriction(Tags.Conjuration), AsianParent()]))
all_trials.append(Trial("Asian Child", [NoConjuration(), AsianChild()]))
all_trials.append(Trial("Pjoxt's Scorn", PjoxtsScorn()))
all_trials.append(Trial("Noob's Toolbox", [NoSkills(), NoUpgrades()]))