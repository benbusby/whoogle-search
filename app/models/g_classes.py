from enum import Enum


class GClasses(Enum):
    """A class for tracking obfuscated class names used in Google results that
    are directly referenced in Whoogle's filtering code.

    Note: Using these should be a last resort. It is always preferred to filter
    results using structural cues instead of referencing class names, as these
    are liable to change at any moment.
    """
    main_tbm_tab = 'KP7LCb'
    images_tbm_tab = 'n692Zd'

    def __str__(self):
        return self.value
