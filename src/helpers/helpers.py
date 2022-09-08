import time
import functools


def timer(func=None, on=True):
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            if on:
                diff = end - start
                unit = "seconds"
                if diff > 60:
                    diff /= 60
                    unit = "minutes"
                    print(f"Time for {func.__name__:30}: {diff:.2f} {unit}")
            return result

        return wrapper

    return decorate(func) if func else decorate
