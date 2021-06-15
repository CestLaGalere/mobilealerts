def extract_start_stop(reading):
    """ 
    Parameters
        reading - of form '19.6 C', '99%', 'South East"
    returns
        distance from the end of the reading 
        the distance from the end of the units
    """
    if type(reading) != str:
        reading = str(reading)
    is_space = False

    for non_digit, c in enumerate(reading):
        if not (c.isdigit() or c == '.' or c == '-'):
            break
        if c == ' ':
            is_space = True
            break

    if non_digit == len(reading) - 1 or non_digit == 0:
        return 0,0

    reading_from_end = len(reading) - non_digit
    unit_from_end = reading_from_end
    if is_space:
        unit_from_end -= 1

    return reading_from_end, unit_from_end


def extract_value_units(reading):
    """ for a reading of 19.5 C
    extract into value & units
    returns
        value (converted to float if numeric)
        units
        e.g. 19.5, C
    """
    if type(reading) != str:
        reading = str(reading)
    reading_from_end, unit_from_end = extract_start_stop(reading)
    if reading_from_end == 0:
        value = reading
        units = ""
    else:
        units = reading[-unit_from_end:]  # get units (ignore the space)
        value = reading[:-reading_from_end]

    # try:
    #     v = float(value)
    #     if v - int(v) == 0:
    #         v = int(v)
    # except:
    #     v = value
    return value, units