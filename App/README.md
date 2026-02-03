# Soundtrackers: Film Composer Research Application

## Introduction

This application is designed to automate the process of conducting deep-dive research on influential film composers. Its primary goal is to gather comprehensive information for a curated list of composers, generate a detailed markdown file for each, and prepare this data for integration into a robust, searchable database. This systematic approach ensures a rich and well-structured knowledge base for film music enthusiasts and researchers.

## Core Functionality

The heart of the application lies in its ability to meticulously collect and organize information about each composer. This is achieved through several key steps orchestrated by Python scripts:

### 1. Composer Data Extraction
The application extracts a wide array of data points for every composer, including:
*   **Biography & Career Details:** A concise overview of their life and professional journey.
*   **Anecdotes & Trivia:** Interesting facts and stories that provide unique insights into their lives and work.
*   **Musical Style:** A description of their distinctive compositional approach.
*   **Top 10 Film Scores:** A curated list of their most significant film scores.
*   **Detailed Awards & Nominations:** Comprehensive information on awards won and nominations received, including the specific films associated with these accolades.

### 2. Web Scraping & Data Collection
To gather this information, the application leverages web scraping techniques:
*   **`google_web_search`:** Used to perform targeted searches for composer biographies, filmographies, awards, and image links.
*   **`requests` & `BeautifulSoup`:** These Python libraries are employed to fetch the content of web pages (primarily Wikipedia and other authoritative sources) and parse their HTML to extract structured data.
*   **Image & Poster Sourcing:** The system actively searches for:
    *   A high-quality **photo of each composer** to be included in their profile.
    *   **Poster links for all films** listed in their "Top 10 Film Scores" section, prioritizing direct image links from reliable sources like `themoviedb.org` or `wikimedia.org`. Placeholder links are used if a direct image cannot be found immediately.

### 3. Markdown File Generation
For each composer, a dedicated markdown file is generated (`001_composer_name.md`). These files are meticulously structured, incorporating all the gathered information in a human-readable and easily parseable format. This includes the composer's photo and links to film posters, enhancing the visual richness of each profile.

### 4. Data Enrichment & Consistency
The application ensures that all generated entries are consistent in their format and content. Special attention is paid to:
*   **Detailed Award Information:** Awards and nominations are now broken down by specific films and categories, providing granular insight into their recognition.
*   **Comprehensive Visuals:** Efforts are made to include a composer photo and a poster for every top film, improving the overall quality of the data.

## Project Structure

The application maintains a clear and organized folder structure:

*   **`App/`**: The main application directory.
    *   **`scripts/`**: Contains all Python scripts responsible for data collection, processing, and file generation.
    *   **`intermediate_research/`**: Stores any intermediate research files, raw data, or source documents used during the process.
    *   **`outputs/`**: The destination for all generated markdown files (e.g., `001_herbert_stothart.md`), as well as the master list of composers (`composers_master_list.md`).

## Database Integration (Future)

Following the successful generation of all markdown files, the next phase of this project will involve integrating the collected data into a **MongoDB** database. MongoDB was chosen for its flexibility, scalability, and ease of integration with web applications. Its document-oriented nature (storing data in JSON-like BSON documents) makes it ideal for exporting data directly to a frontend application via a RESTful API, supporting a robust, modular, and scalable architecture.

## How to Use (Script)

To generate or update the composer markdown files:
1.  Ensure you have Python installed.
2.  Install the required Python libraries: `pip install requests beautifulsoup4 google`.
3.  Navigate to the project root directory.
4.  Run the main script: `python3 App/scripts/create_composer_files.py`.

The script will read `App/outputs/composers_master_list.md`, process each composer, and create/update their respective markdown files in `App/outputs/`.

## Future Enhancements

*   **Database Population Script:** Develop the script to parse the generated markdown files and populate the MongoDB database.
*   **Frontend Development:** Create a web-based user interface to browse, search, and visualize the composer data.
*   **Improved Web Scraping:** Refine the scraping logic for more robust data extraction and error handling, especially for awards and poster links.
*   **Listen Links:** Implement a more robust method to find listen links for soundtracks.
*   **Anecdote & Musical Style Extraction:** Automate the extraction of anecdotes and musical style descriptions directly from web sources.
