def benchmark(func):
    import time

    def seconds_to_minutes(seconds):
        if seconds < 60:
            return f"{seconds} сек"
        else:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes} мин {remaining_seconds:.2f} сек"

    def wrapper(*args, **kwargs):
        start = time.time()
        return_value = func(*args, **kwargs)
        end = time.time()
        print(f'[*] Время выполнения: {seconds_to_minutes(end-start)} {func.__name__}')
        return return_value

    return wrapper

@benchmark
def main():
    for _ in range(100000):
        pass

if __name__ == '__main__':
    main()