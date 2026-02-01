"""Room types at Miyamaso Takamiya with private onsen."""

from enum import Enum


class MiyamasoRoom(Enum):
    """Room types at Miyamaso Takamiya with private natural hot spring bath.

    Only rooms with genuine natural hot spring (onsen) water in their private baths
    are included. The hotel has 9 room types total, but only these 3 have real onsen.
    """

    # Detached villa with private open-air onsen (110 m2, up to 4 guests)
    # The only room in all of Zao Onsen with real in-room private onsen.
    HINAKURA = "25112"

    # Ken Okuyama designed suite with open-air onsen (51-61 m2, up to 4 guests)
    # Two variants: Maisonette (2-floor) and Japanese-style with adjoining room
    RIAN_SANSUI_MAISONETTE = "25114"
    RIAN_SANSUI_JAPANESE = "25113"

    @classmethod
    def from_string(cls, s: str) -> "MiyamasoRoom | None":
        """Parse room type from user-friendly string."""
        s_lower = s.lower().strip()
        mapping = {
            # Hinakura aliases
            "hinakura": cls.HINAKURA,
            "hina": cls.HINAKURA,
            "villa": cls.HINAKURA,
            # Rian Sansui aliases - "rian" returns maisonette as default
            "rian": cls.RIAN_SANSUI_MAISONETTE,
            "rian-sansui": cls.RIAN_SANSUI_MAISONETTE,
            "rian_sansui": cls.RIAN_SANSUI_MAISONETTE,
            "sansui": cls.RIAN_SANSUI_MAISONETTE,
            # Specific variants
            "rian-maisonette": cls.RIAN_SANSUI_MAISONETTE,
            "rian_maisonette": cls.RIAN_SANSUI_MAISONETTE,
            "maisonette": cls.RIAN_SANSUI_MAISONETTE,
            "rian-japanese": cls.RIAN_SANSUI_JAPANESE,
            "rian_japanese": cls.RIAN_SANSUI_JAPANESE,
            "rian-jp": cls.RIAN_SANSUI_JAPANESE,
        }
        return mapping.get(s_lower)

    @classmethod
    def parse_multiple(cls, s: str) -> list["MiyamasoRoom"]:
        """Parse room filter that may include 'rian' (both variants).

        When user specifies 'rian', return both Rian Sansui variants.
        """
        s_lower = s.lower().strip()
        if s_lower in ("rian", "rian-sansui", "rian_sansui", "sansui"):
            return [cls.RIAN_SANSUI_MAISONETTE, cls.RIAN_SANSUI_JAPANESE]
        room = cls.from_string(s_lower)
        return [room] if room else []

    @property
    def room_id(self) -> str:
        """Unique ID used by 489ban.net booking system."""
        return self.value

    @property
    def display_name(self) -> str:
        """Human-readable room name."""
        names = {
            self.HINAKURA: "HINAKURA Villa (Private Onsen Suite, 110m2)",
            self.RIAN_SANSUI_MAISONETTE: "Rian Sansui Maisonette (Private Onsen, 51m2)",
            self.RIAN_SANSUI_JAPANESE: "Rian Sansui Japanese (Private Onsen, 51m2)",
        }
        return names[self]

    @property
    def max_guests(self) -> int:
        """Maximum number of guests for this room."""
        # All premium rooms at Miyamaso allow up to 4 guests
        return 4

    @property
    def has_private_onsen(self) -> bool:
        """All Miyamaso rooms we monitor have private natural hot spring bath."""
        return True

    @property
    def japanese_name(self) -> str:
        """Japanese name for the room."""
        names = {
            self.HINAKURA: "離れ・雛蔵",
            self.RIAN_SANSUI_MAISONETTE: "離庵 山水 (メゾネット)",
            self.RIAN_SANSUI_JAPANESE: "離庵 山水 (和室)",
        }
        return names[self]
