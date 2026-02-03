# PENDING CHANGES for `App/scripts/create_composer_files.py`

This document outlines the changes and enhancements required for the `create_composer_files.py` script based on recent user feedback and expanded requirements.

## 1. Goal: Process all composers from `composers_master_list.md` with enhanced data.

The script needs to iterate through *all* composers in the `composers_master_list.md` and generate a detailed markdown file for each.

## 2. Enhanced Data Collection Requirements per Composer:

### a. Composer Photo:
*   **Source:** Primary search on Wikipedia, then broaden if necessary.
*   **Action:** Find a reliable image URL for the composer's photo.
*   **Output:** Download the image and save it locally. The markdown file should link to this local image.

### b. Top 10 Film Scores:
*   **Source:** Web search for "COMPOSER best film scores ranked list".
*   **Action:** Extract up to 10 film titles.
*   **Output:** Store film titles (and year, if found). These will be highlighted in the "Complete Filmography" section.

### c. Complete Filmography:
*   **Source:** Broaden search beyond Wikipedia. Prioritize reliable film databases (e.g., IMDb, AllMovie) or comprehensive filmography lists. This will require more advanced scraping logic.
*   **Action:** Extract as many film titles and release years as possible.
*   **Output:** A list of dictionaries `[{'title': 'Film Title', 'year': 19XX}]`, sorted chronologically.

### d. Film Posters for *All* Films in Complete Filmography:
*   **Source:** Web search for "[Film Title] movie poster". Prioritize `themoviedb.org`, `wikimedia.org`, or other reliable direct image links.
*   **Action:** For *each* film in the complete filmography, find the best possible poster image URL. Download the image.
*   **Local Storage:** Images should be saved in a subfolder named after the markdown file (e.g., `App/outputs/001_herbert_stothart/poster_film_title.jpg`).
*   **Output:** The markdown file should link to the local path of the downloaded image.

### e. Detailed Awards and Nominations:
*   **Source:** Targeted web searches for "COMPOSER awards and nominations". Prioritize official award sites (e.g., Academy Awards, Golden Globes, BAFTA) or reputable film/music news sites.
*   **Action:** Extract award name, year, the specific film/project for which the award was given/nominated, and the status (Win/Nomination).
*   **Output:** A structured list of dictionaries, e.g., `[{'award': 'Academy Award', 'year': 1939, 'film': 'The Wizard of Oz', 'status': 'Win'}]`.

## 3. Script (`create_composer_files.py`) Modifications:

### a. New Helper Functions:
*   `download_image(image_url, destination_path)`: Downloads an image and saves it locally. Handles creating necessary directories.
*   `get_film_poster(film_title, composer_folder_path)`: Finds image URL, calls `download_image`, returns local image path.
*   `get_complete_filmography(composer_name)`: Searches multiple sources, scrapes film titles/years, returns structured list.
*   `get_detailed_awards(composer_name)`: Searches multiple sources, scrapes detailed award info, returns structured list.

### b. Modify `get_composer_info(composer_name)`:
*   Integrate calls to `get_complete_filmography` and `get_detailed_awards`.
*   Pass the composer's folder path to `get_film_poster` for local storage.

### c. Modify `create_markdown_file(composer_info, index)`:
*   Ensure the composer-specific image folder is created (`App/outputs/001_herbert_stothart/`).
*   Generate markdown content:
    *   Composer photo linked locally.
    *   "Top 10 Film Scores" section as before.
    *   New "Complete Filmography" section:
        *   List all films chronologically.
        *   **Highlight (bold)** films that are also in the Top 10.
        *   Link to local poster image for each film.
    *   "Awards and Nominations" section with the new structured details.

### d. Modify `main()` function:
*   Remove the temporary `print(composer_info)` call.
*   Ensure proper looping through all composers and calling `create_markdown_file`.

## 4. Iteration Strategy:

*   Focus on implementing these changes for a single composer first (e.g., "Herbert Stothart").
*   Validate the output (markdown file, downloaded images, data accuracy).
*   Once confident, run the script for all composers.
