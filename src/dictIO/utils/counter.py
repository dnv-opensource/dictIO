from typing import Dict, List

__all__ = ["BorgCounter", "DejaVue"]


class BorgCounter:
    """
    A class that implements a static global counter.
    Instances of this class all share the same global counter.
    This is used in DictReader class to assure that multiple instances
    of CppDict do not generate conflicting IDs for placeholder strings
    (as would be the case otherwise when merging included dicts).
    """

    Borg: Dict[str, int] = {"theCount": -1}

    def __init__(self):
        self.__dict__ = BorgCounter.Borg

    def __call__(self) -> int:
        """Increments BorgCounter and returns next value.

        Returns
        -------
        int
            the next value (after incrementation)
        """
        self.theCount += 1
        #   Small tweak for our use case: As we have only six digits available in our placeholder strings,
        #   we don't want the counter to exceed this. Fair to start again at 0 then :-)
        if self.theCount > 999999:
            self.theCount = 0  # pyright: ignore
        return self.theCount

    @staticmethod
    def reset():
        """Reset the BorgCounter."""
        BorgCounter.Borg["theCount"] = -1


class DejaVue:
    """A class that implements a static global registry of strings."""

    djv: Dict[str, List[str]] = {"strings": []}

    def __init__(self):
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
    def strings(self) -> List[str]:
        """Return a list with all strings currently registered with DejaVue.

        Returns
        -------
        List[str]
            list with all strings currently registered with DejaVue.
        """
        return self.djv["strings"]

    def reset(self):
        """Reset DejaVue.

        Clears the list of registered strings.
        """
        self.djv["strings"] = []
        self.ret_val = False
