import sys

def tokenize(text_file_path: str) -> list:
    tokens = []
    try:
        with open(text_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                current_token = []
                for char in line + " ":
                    if char.isalnum() and char.isascii():
                        current_token.append(char.lower())
                    else:
                        if current_token:
                            tokens.append(''.join(current_token))
                            current_token = []
    except FileNotFoundError:
        print(f"Error: file '{text_file_path}' not found.")
    except IOError:
        print(f"Error: could not read file '{text_file_path}'.")

    return tokens

def computeWordFrequencies(tokens: list) -> dict:
    frequencies = {}
    for token in tokens:
        if token in frequencies:
            frequencies[token] += 1
        else:
            frequencies[token] = 1
    return frequencies

def print_frequencies(frequencies: dict) -> None:
    sorted_items = sorted(frequencies.items(), key=lambda x: (-x[1], x[0]))
    for token, count in sorted_items:
        print(f"{token} > {count}")

if __name__ == '__main__':
    file_path = sys.argv[1]

    tokens = tokenize(file_path)
    frequencies = computeWordFrequencies(tokens)
    print_frequencies(frequencies)