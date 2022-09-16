class Iso8601:
    """Implements date/time formatting according to ISO8601."""

    def __init__(self):
        pass

    @staticmethod
    def formatTimeGmtimeToIso(dateTimeTuple) -> str:
        """Format tuple returned by time.gmtime() tor ISO8601 string."""
        s = '{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}+00:00'.format(
            dateTimeTuple[0], dateTimeTuple[1], dateTimeTuple[2],
            dateTimeTuple[3], dateTimeTuple[4], dateTimeTuple[5]
        )
        return s

    @staticmethod
    def formatRtcDatetimeToIso(dateTimeTuple) -> str:
        """Format tuple returned by rtc.datetime() tor ISO8601 string."""
        s = '{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}+00:00'.format(
            dateTimeTuple[0], dateTimeTuple[1], dateTimeTuple[2],
            dateTimeTuple[4], dateTimeTuple[5], dateTimeTuple[6]
        )
        return s
