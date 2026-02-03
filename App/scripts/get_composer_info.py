
import json
import sys
from tavily import TavilyClient

def get_composer_info(composer_name, tavily_client):
    """
    Gathers detailed information about a composer using the Tavily API.
    """
    print(f"Gathering information for {composer_name}...")

    # Define the categories of information to search for
    categories = {
        "biography": "biography",
        "professional_career": "professional career",
        "anecdotes": "anecdotes",
        "top_10_soundtracks": "top 10 most successful soundtracks",
        "total_soundtracks": "number of soundtracks composed",
        "musical_style": "musical style characteristics",
        "birth_death_dates": "birth and death dates",
        "milestones_awards_nominations": "milestones, awards, and nominations",
        "education": "education"
    }

    composer_data = {"name": composer_name}

    # Perform a search for each category
    for key, query_suffix in categories.items():
        query = f"{composer_name} {query_suffix}"
        print(f"  - Searching for: {query}")
        try:
            response = tavily_client.search(query=query, search_depth="advanced")
            composer_data[key] = response["results"]
        except Exception as e:
            print(f"  - Error searching for {key}: {e}")
            composer_data[key] = []

    # Get details for the top 10 soundtracks
    if composer_data.get("top_10_soundtracks"):
        soundtracks = []
        # A simple way to extract soundtrack titles from search results
        # This is a placeholder and needs to be more robust
        for result in composer_data["top_10_soundtracks"][:10]:
            soundtracks.append(result['title'])
        
        detailed_soundtracks = []
        for soundtrack_title in soundtracks:
            print(f"  - Getting details for soundtrack: {soundtrack_title}")
            soundtrack_details = {"title": soundtrack_title}
            
            # Search for soundtrack info
            query_info = f'"{soundtrack_title}" soundtrack information'
            try:
                info_response = tavily_client.search(query=query_info, search_depth="basic")
                soundtrack_details["information"] = info_response["results"]
            except Exception as e:
                print(f"    - Error getting info: {e}")
                soundtrack_details["information"] = []

            # Search for emblematic theme
            query_theme = f'"{soundtrack_title}" emblematic theme'
            try:
                theme_response = tavily_client.search(query=query_theme, search_depth="basic")
                soundtrack_details["emblematic_theme"] = theme_response["results"]
            except Exception as e:
                print(f"    - Error getting theme: {e}")
                soundtrack_details["emblematic_theme"] = []

            # Search for movie poster
            query_poster = f'"{soundtrack_title}" movie poster'
            try:
                poster_response = tavily_client.search(query=query_poster, search_depth="basic", include_images=True)
                # Find the first image result
                image_url = next((res.get("image") for res in poster_response.get("images", [])), None)
                soundtrack_details["poster_url"] = image_url
            except Exception as e:
                print(f"    - Error getting poster: {e}")
                soundtrack_details["poster_url"] = None
                
            detailed_soundtracks.append(soundtrack_details)
        
        composer_data["top_10_soundtracks_detailed"] = detailed_soundtracks


    return composer_data

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python get_composer_info.py <composer_name> <tavily_api_key>")
        sys.exit(1)

    composer_name_arg = sys.argv[1]
    api_key = sys.argv[2]
    
    client = TavilyClient(api_key=api_key)

    composer_information = get_composer_info(composer_name_arg, client)

    # Save the data to a JSON file
    output_filename = f"{composer_name_arg.replace(' ', '_').lower()}_info.json"
    with open(output_filename, 'w') as f:
        json.dump(composer_information, f, indent=4)

    print(f"\nInformation saved to {output_filename}")
