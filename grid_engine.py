def check_grid_signal(price, balance):
    if balance <= 0:
        return None

    # super simplified:
    if price % 3 == 0:
        return "BUY"
    elif price % 5 == 0:
        return "SELL"
    else:
        return None

