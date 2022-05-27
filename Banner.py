from enum import Enum, auto


class Rarity(Enum):
    ThreeStar = auto()
    FourStar = auto()
    FiveStar = auto()


class FallingStar:
    def __init__(self, name, rarity):
        self.name = name
        self.rarity = rarity


class BannerGameTreeNode:
    def visit(self, visitor):
        raise NotImplementedError()


class BannerGameWeightedChoice(BannerGameTreeNode):
    def __init__(self, *choices):
        choices = choices[0]
        self.choices = list(map(lambda t: t[0], choices))
        self.probabilities = list(map(lambda t: t[1], choices))

    def visit(self, visitor):
        visitor.visit_choice(self.choices, self.probabilities)


class BannerGameChoice(BannerGameWeightedChoice):
    def __init__(self, *choices):
        super().__init__(map(lambda c: (c, 1.0 / len(choices)), choices))


class BannerGameWin(BannerGameTreeNode):
    def __init__(self, star):
        self.star = star

    def visit(self, visitor):
        visitor.visit_win(self.star)


class BannerGameTreeVisitor:
    def visit_choice(self, choices, probabilities):
        pass

    def visit_win(self, star):
        pass


class BannerGameRoller(BannerGameTreeVisitor):
    def __init__(self, rng):
        self.rng = rng
        self.last_win = None

    def acquire_wish(self, game):
        game.visit(self)
        return self.last_win

    def visit_choice(self, choices, probabilities):
        choice = self.rng.choices(choices, weights=probabilities)
        choice[0].visit(self)

    def visit_win(self, star):
        self.last_win = star


class AbstractBannerFactory:
    def __init__(self):
        raise NotImplementedError()

    def make_character_banner(self):
        raise NotImplementedError()

    def make_weapon_banner(self):
        raise NotImplementedError()

    def make_standard_banner(self):
        raise NotImplementedError()


class TwoSevenBannerFactory:
    def __init__(self):
        pass

    def make_character_banner(self):
        pass

    def make_weapon_banner(self):
        pass


class Banner:
    def __init__(self, seed):
        from random import Random
        self.rng = Random(seed)

    def wish(self):
        game = self.configure_game()
        star = BannerGameRoller(self.rng).acquire_wish(game)
        self.upon_wish(star)
        return star

    def configure_game(self):
        raise NotImplementedError()

    def upon_wish(self, star):
        raise NotImplementedError()


class GenericCharacterBanner(Banner):
    def __init__(self, seed, is_empirical_dist=True):
        super().__init__(seed)
        self.games = dict()
        self.is_empirical_dist = is_empirical_dist
        self.featured_character = FallingStar("Featured 5★ Character", Rarity.FiveStar)
        self.games[GenericCharacterBanner.BannerPhase.STANDARD] = \
            BannerGameWeightedChoice([
                (BannerGameWin(self.featured_character), 3),
                (BannerGameWin(FallingStar("Other 5★ Character", Rarity.FiveStar)), 3),
                (BannerGameWin(FallingStar("4★ Character", Rarity.FourStar)), 51),
                (BannerGameWin(FallingStar("3★ Character", Rarity.ThreeStar)), 943),
            ])
        self.games[GenericCharacterBanner.BannerPhase.GUARANTEE_4STAR] = \
            BannerGameWeightedChoice([
                (BannerGameWin(self.featured_character), 3),
                (BannerGameWin(FallingStar("Other 5★ Character", Rarity.FiveStar)), 3),
                (BannerGameWin(FallingStar("4★ Character", Rarity.FourStar)), 994),
            ])
        self.games[GenericCharacterBanner.BannerPhase.GUARANTEE_5STAR] = \
            BannerGameWeightedChoice([
                (BannerGameWin(self.featured_character), 1),
                (BannerGameWin(FallingStar("Other 5★ Character", Rarity.FiveStar)), 1),
            ])
        self.games[GenericCharacterBanner.BannerPhase.GUARANTEE_FEATURED] = \
            BannerGameWin(self.featured_character)
        self.last_5star_was_featured = True
        self.wishes_since_last_5star = 0
        self.wishes_since_last_4star = 0

    class BannerPhase(Enum):
        STANDARD = auto()
        GUARANTEE_4STAR = auto()
        GUARANTEE_5STAR = auto()
        GUARANTEE_FEATURED = auto()

    def configure_game(self):
        if self.wishes_since_last_5star == 89:
            if self.last_5star_was_featured:
                return self.games[GenericCharacterBanner.BannerPhase.GUARANTEE_5STAR]
            else:
                return self.games[GenericCharacterBanner.BannerPhase.GUARANTEE_FEATURED]

        if self.wishes_since_last_4star == 9:
            return self.games[GenericCharacterBanner.BannerPhase.GUARANTEE_4STAR]

        if self.is_empirical_dist and self.wishes_since_last_5star >= 73:
            # This is partly inspired by the empirical distribution, but doesn't use actual data.
            # It turns out we get very close to the empirical distribution if we linearly interpolate the probabilities
            # from the standard rates to 100% 5★ guarantee at the 90th wish.
            #
            x = self.wishes_since_last_5star + 1
            game = \
                BannerGameWeightedChoice([
                    (BannerGameWin(self.featured_character), 3/(90 - 73) * (90 - x) + 500/(90 - 73) * (x - 73)),
                    (BannerGameWin(FallingStar("Other 5★ Character", Rarity.FiveStar)), 3/(90 - 73) * (90 - x) + 500/(90 - 73) * (x - 73)),
                    (BannerGameWin(FallingStar("4★ Character", Rarity.FourStar)), 51/(90 - 73) * (90 - x)),
                    (BannerGameWin(FallingStar("3★ Character", Rarity.ThreeStar)), 943/(90 - 73) * (90 - x)),
                ])
            return game

        return self.games[GenericCharacterBanner.BannerPhase.STANDARD]

    def upon_wish(self, star):
        if star.rarity == Rarity.FiveStar:
            self.wishes_since_last_5star = 0
            self.wishes_since_last_4star = 0
            self.last_5star_was_featured = (star == self.featured_character)
        elif star.rarity == Rarity.FourStar:
            self.wishes_since_last_5star = self.wishes_since_last_5star + 1
            self.wishes_since_last_4star = 0
        else:
            self.wishes_since_last_5star = self.wishes_since_last_5star + 1
            self.wishes_since_last_4star = self.wishes_since_last_4star + 1


class GenericEpitomizedWeaponBanner(Banner):

    class BannerPhase(Enum):
        STANDARD = auto()
        GUARANTEE_4STAR = auto()
        GUARANTEE_5STAR = auto()
        GUARANTEE_FEATURED = auto()

    def __init__(self, seed):
        super().__init__(seed)
        self.games = dict()
        self.fate_point = 0
        self.featured_fated_weapon = FallingStar("Featured Fated 5★ Weapon", Rarity.FiveStar)
        self.featured_other_weapon = FallingStar("Featured Non-Fated 5★ Weapon", Rarity.FiveStar)
        self.games[GenericCharacterBanner.BannerPhase.STANDARD] = \
            BannerGameWeightedChoice([
                (BannerGameWin(self.featured_character), 3),
                (BannerGameWin(FallingStar("Other 5★ Character", Rarity.FiveStar)), 3),
                (BannerGameWin(FallingStar("4★ Character", Rarity.FourStar)), 51),
                (BannerGameWin(FallingStar("3★ Character", Rarity.ThreeStar)), 943),
            ])
        self.games[GenericCharacterBanner.BannerPhase.GUARANTEE_4STAR] = \
            BannerGameWeightedChoice([
                (BannerGameWin(self.featured_character), 3),
                (BannerGameWin(FallingStar("Other 5★ Character", Rarity.FiveStar)), 3),
                (BannerGameWin(FallingStar("4★ Character", Rarity.FourStar)), 51),
            ])
        self.games[GenericCharacterBanner.BannerPhase.GUARANTEE_5STAR] = \
            BannerGameWeightedChoice([
                (BannerGameWin(self.featured_character), 1),
                (BannerGameWin(FallingStar("Other 5★ Character", Rarity.FiveStar)), 1),
            ])
        self.games[GenericCharacterBanner.BannerPhase.GUARANTEE_FEATURED] = \
            BannerGameWin(self.featured_character)
        self.last_5star_was_featured = True
        self.wishes_since_last_5star = 0
        self.wishes_since_last_4star = 0

    class BannerPhase(Enum):
        STANDARD = auto()
        GUARANTEE_4STAR = auto()
        GUARANTEE_5STAR = auto()
        GUARANTEE_FEATURED = auto()

    def configure_game(self):
        if self.wishes_since_last_5star == 89:
            if self.last_5star_was_featured:
                return self.games[GenericCharacterBanner.BannerPhase.GUARANTEE_5STAR]
            else:
                return self.games[GenericCharacterBanner.BannerPhase.GUARANTEE_FEATURED]

        if self.wishes_since_last_4star == 9:
            return self.games[GenericCharacterBanner.BannerPhase.GUARANTEE_4STAR]

        return self.games[GenericCharacterBanner.BannerPhase.STANDARD]

    def upon_wish(self, star):
        if star.rarity == Rarity.FiveStar:
            self.wishes_since_last_5star = 0
            self.wishes_since_last_4star = 0
            self.last_5star_was_featured = (star == self.featured_character)
        elif star.rarity == Rarity.FourStar:
            self.wishes_since_last_5star = self.wishes_since_last_5star + 1
            self.wishes_since_last_4star = 0
        else:
            self.wishes_since_last_5star = self.wishes_since_last_5star + 1
            self.wishes_since_last_4star = self.wishes_since_last_4star + 1
