class OpeningBook:
    BOOK = {
        "garchomp": "swords-dance",
        "dragonite": "dragon-dance",
        "rotom": "thunderbolt",
        "primarina": "surf",
        "incineroar": "tailwind",
        "amoonguss": "protect",
        "gholdengo": "shadow-ball",
        "flutter-mane": "moonblast",
    }

    @staticmethod
    def choose(state):
        lead = state.player.name.lower().replace(" ", "-")
        return OpeningBook.BOOK.get(lead)
