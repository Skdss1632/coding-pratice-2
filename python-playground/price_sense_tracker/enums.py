from enum import Enum

class DealType(Enum):
    LIGHTNING = "Lightning_Deal"
    LIMITED_TIME = "Limited_Time_Deal"
    DEAL_OF_THE_DAY = "Deal_of_the_Day"
    UNKNOWN = "Unknown"
    TRENDING = "Trending_deal"
    ELECTRONICS = "Electronics_Deal"


class Delay(Enum):
    QUICK = 2
    NORMAL = 5
    MODERATE = 10
    LONG = 20
    EXTENDED = 30


