from collections import Counter

def detect_ecb(ciphertexts):
    for i, ciphertext in enumerate(ciphertexts):
        blocks = [ciphertext[j:j+16] for j in range(0, len(ciphertext), 16)]
        block_counts = Counter(blocks)
        most_common_block, count = block_counts.most_common(1)[0]
        if count > 1:
            return i, ciphertext

def main():
    with open('aes.data', 'r') as file:
        ciphertexts = [line.strip() for line in file]

    index, ecb_ciphertext = detect_ecb(ciphertexts)
    print("Ciphertext encrypted using ECB mode found at index:", index)
    print("ECB Ciphertext:", ecb_ciphertext)

if __name__ == "__main__":
    main()
