"""Singleton classes for global counter, indentation and string registry."""

# pyright: reportUnnecessaryTypeIgnoreComment=false
from typing import Any, ClassVar

__all__ = ["BorgCounter", "Indenter", "DejaVue"]


class BorgCounter:
    """A class that implements a static global counter.

    Instances of this class all share the same global counter.
    This is used in DictReader class to ensure that multiple instances
    of SDict do not generate conflicting IDs for placeholder strings
    (as would be the case otherwise when merging included dicts).
    """

    Borg: ClassVar[dict[str, int]] = {"theCount": -1}

    def __init__(self) -> None:
        self.__dict__ = BorgCounter.Borg

    def __call__(self) -> int:
        """Increments BorgCounter and returns next value.

        Returns
        -------
        int
            the next value (after incrementation)
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
        self.__dict__ = Indenter.Ind
        Indenter.Ind["TabSize"] = tab_size
        Indenter.Ind["TabChar"] = tab_char

    def __call__(self) -> str:
        """Call does not increment and returns next value.

        Returns
        -------
        str
            indent string
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
    """A class that implements a static global registry of strings."""

    djv: ClassVar[dict[str, list[str]]] = {"strings": []}

    def __init__(self) -> None:
        self.__dict__ = DejaVue.djv
        self.ret_val: bool = False

    def __call__(self, string: str) -> bool:
        """Call DejaVue with passed string.

        Checks whether the passed in string is already registered in DejaVue.
        If so, returns True. Otherwise False.

        Parameters
        ----------
        string : str
            the string to be checked

        Returns
        -------
        bool
            True if string is already registered. False otherwise.
        """
        if string in self.djv["strings"]:
            self.ret_val = True

        self.djv["strings"].append(string)

        return self.ret_val

    @property
    def strings(self) -> list[str]:
        """Return a list with all strings currently registered with DejaVue.

        Returns
        -------
        List[str]
            list with all strings currently registered with DejaVue.
        """
        return self.djv["strings"]

    def reset(self) -> None:
        """Reset DejaVue.

        Clears the list of registered strings.
        """
        self.djv["strings"] = []
        self.ret_val = False
