import itertools
import random
import time

from datetime import datetime

# 00:00:00, Jan 1, 2025
DOOVER_EPOCH = 1735689600000


class SnowflakeType:
    Unknown = 0
    Agent = 1
    Message = 2
    Channel = 3
    WSSSession = 4
    ProcessorSchedule = 5
    Token = 6


nums = list(range(16))
random.shuffle(nums)
RANDOM_NUMBERS = itertools.cycle(nums)


def generate_snowflake_id(
    type_id: int = SnowflakeType.Unknown, region_id: int = 0, instance_id: int = 0
):
    millis = int(time.time() * 1000 - DOOVER_EPOCH)
    rand = next(RANDOM_NUMBERS)

    return millis << 22 | region_id << 18 | instance_id << 8 | type_id << 4 | rand


def generate_snowflake_id_at(
    at: datetime,
    type_id: int = SnowflakeType.Unknown,
    region_id: int = 0,
    instance_id: int = 0,
    use_rand: bool = False,
):
    millis = int(at.timestamp() * 1000 - DOOVER_EPOCH)
    if use_rand:
        rand = next(RANDOM_NUMBERS)
    else:
        rand = 0

    return millis << 22 | region_id << 18 | instance_id << 8 | type_id << 4 | rand
