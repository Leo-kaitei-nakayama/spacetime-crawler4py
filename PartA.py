from pathlib import Path
import sys


# RUNTIME: function tokenize runs in O(n) / Linear time for each n characters in the file by visting e
def tokenize(input_data):
    token_lst = []
    try:
        path = Path(input_data)
        if path.exists() and path.is_file():
            with open(path, "r", encoding="utf-8") as txt_file:
                lines = txt_file.readlines()
        else:
            raise ValueError  # treat as raw text
    except (OSError, ValueError, TypeError):
        lines = input_data.splitlines() if isinstance(input_data, str) else []

    for line in lines:
        for word in line.split():
            if word.isalnum() and word.isascii():
                token_lst.append(word)
            else:
                char_lst = []
                for char in word:
                    if char.isalnum() and char.isascii():
                        char_lst.append(char)
                    else:
                        if char_lst:
                            token_lst.append("".join(char_lst))
                            char_lst.clear()
                if char_lst:
                    token_lst.append("".join(char_lst))

    return token_lst

# RUNTIME: function ComputeWordFrequencies runs in O(n) / Linear time  where n is the number of tokens,
# all tokens are processed within a single loop and lookups are at O(1)
def computeWordFrequencies(list_of_token):
    freq = {}
    for token in list_of_token:
        if token.lower() not in freq:
            freq[token.lower()] = 1
        else:
            new_val = freq[token.lower()] +1
            freq[token.lower()] = new_val
    return freq

# RUNTIME: function print_freq runs in O(N log N) / log-linear time since sorted() function in python is running in O(n log N)
# for worst case
def print_freq(word_frequency):
    sort_dict = (sorted(word_frequency.items(),key = lambda x: (-x[1],x[0])))
    for key,value in sort_dict:
        print(f'{key}->{value}')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    base_path  = Path(sys.argv[1])
    total = tokenize(base_path)
    new_dict = computeWordFrequencies(total)
    print_freq(new_dict)
