"""
Generate CDN artwork list from text file.
This reads the cdn_artworks_list.txt and creates Python list for seed_from_cdn.py
"""

# Read the file
with open('cdn_artworks_list.txt', 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

print(f"Total lines: {len(lines)}")
print("\n# Copy this into seed_from_cdn.py CDN_ARTWORKS list:\n")

for line in lines:
    # Parse style/filename
    parts = line.split('/')
    if len(parts) == 2:
        style = parts[0]
        filename = parts[1]
        # Default popularity score
        score = 0.75
        print(f'    ("{style}", "{filename}", {score}),')
