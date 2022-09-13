from Mutators import *
from Level import *

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
        self.description = "The only available spell is Fireworks, which you get for free\nFireworks deals 0 fire damage in a 0 tile burst"

    def on_generate_spells(self, spells):
        spells.clear()

    def on_game_begin(self, game):
        game.p1.add_spell(FireworksSpell())

all_trials.append(Trial("Pyrotechnician", Pyrotechnician()))