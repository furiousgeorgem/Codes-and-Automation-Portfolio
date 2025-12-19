import csv
import webbrowser

# Path to your CSV file
csv_file = 'SXM_2025_Q4_Dec_15_not_found.csv'

# Open the CSV file and read each row
with open(csv_file, newline='', encoding='utf-8') as file:
    reader = csv.reader(file)
    
    # Skip header row if present
    next(reader)
    
    for row in reader:
        # Assuming the first column is song title and second is artist name
        song_title = row[0]
        artist_name = row[1]
        
        # Create a search URL (you can adjust this URL format)
        search_url = f'https://www.amazon.com/s?k={song_title}+{artist_name}'
        
        # Open the search URL in a new tab
        print(f'Opening: {song_title} - {artist_name}')
        webbrowser.open(search_url)

print("All search tabs opened in Chrome!")