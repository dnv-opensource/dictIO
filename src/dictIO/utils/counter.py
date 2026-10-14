"""Singleton classes for global counter, indentation and string registry."""

# pyright: reportUnnecessaryTypeIgnoreComment=false
from typing import Any, ClassVar

__all__ = ["BorgCounter", "DejaVue", "Indenter"]


class BorgCounter:
    """A class that implements a static global counter.

    Instances of this class all share the same global counter.
    This is used in DictReader class to ensure that multiple instances
    of SDict do not generate conflicting IDs for placeholder strings
    (as would be the case otherwise when merging included dicts).

    Attributes:
        Borg: Shared storage for the counter value.
    """

    Borg: ClassVar[dict[str, int]] = {"theCount": -1}

    def __init__(self) -> None:
        """Initialize an instance that shares the class-level counter."""
        self.__dict__ = BorgCounter.Borg

    def __call__(self) -> int:
        """Increments BorgCounter and returns next value.

        Returns:
            The next counter value.
        """
        self.theCount += 1  # type: ignore[has-type]
        #   Small tweak for our use case: As we have only six digits available in our placeholder strings,
        #   we don't want the counter to exceed this. Fair to start again at 0 then :-)
        if self.theCount > 999999:  # type: ignore[has-type]  # noqa: PLR2004
            self.theCount = 0  # pyright: ignore[reportUninitializedInstanceVariable]
        return self.theCount

    @staticmethod
    def reset() -> None:
        """Reset the BorgCounter."""
        BorgCounter.Borg["theCount"] = -1


class Indenter:
    """A class that implements a static global indentation.

    Instances of this class all share the same global indentation.
    This is used in logger class to ensure a readable message hirarchy.

    Attributes:
        Ind: Shared storage for the indentation level and formatting settings.
    """

    Ind: dict[str, Any] = {  # noqa: RUF012
        "Indent": 0,
        "TabSize": 4,
        "TabChar": " ",
    }

    def __init__(
        self,
        tab_size: int = 4,
        tab_char: str = " ",
    ) -> None:
        """Initialize shared indentation formatting settings.

        Args:
            tab_size: Number of characters per indentation level. Defaults to
                `4`.
            tab_char: Character used to render indentation. Defaults to
                `" "`.
        """
        self.__dict__ = Indenter.Ind
        Indenter.Ind["TabSize"] = tab_size
        Indenter.Ind["TabChar"] = tab_char

    def __call__(self) -> str:
        """Call does not increment and returns next value.

        Returns:
            The current indentation string.
        """
        return "".join([Indenter.Ind["TabChar"] for _ in range(Indenter.Ind["Indent"] * Indenter.Ind["TabSize"])])

    @staticmethod
    def incr(increase: int = 1) -> None:
        """Increase the Indent."""
        Indenter.Ind["Indent"] += increase

    @staticmethod
    def decr(decrease: int = 1) -> None:
        """Decreas the Indent."""
        Indenter.Ind["Indent"] -= decrease

    @staticmethod
    def reset() -> None:
        """Reset the Indent."""
        Indenter.Ind["Indent"] = 0


class DejaVue:
    """A class that implements a static global registry of strings.

    Attributes:
        djv: Shared storage for registered strings.
        ret_val: Whether the most recent call found an existing string.
    """

    djv: ClassVar[dict[str, list[str]]] = {"strings": []}

    def __init__(self) -> None:
        """Initialize an instance using the shared string registry."""
        self.__dict__ = DejaVue.djv
        self.ret_val: bool = False

    def __call__(self, string: str) -> bool:
        """Check whether a string has already been registered, then register it.

        Args:
            string: String to check and add to the registry.

        Returns:
            `True` if the string was already registered, otherwise `False`.
        """
        if string in self.djv["strings"]:
            self.ret_val = True

        self.djv["strings"].append(string)

        return self.ret_val

    @property
    def strings(self) -> list[str]:
        """Return a list with all strings currently registered with DejaVue.

        Returns:
            The shared list of registered strings.
        """
        return self.djv["strings"]

    def reset(self) -> None:
        """Reset DejaVue.

        Clear the list of registered strings and reset the last-call result.
        """
        self.djv["strings"] = []
        self.ret_val = False
