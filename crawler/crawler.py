import time
import undetected_chromedriver as uc


# --- Configuration ---
# Let's use a Wikipedia page about cafes as our target.
# Later, you can change this to a real guide or listings website.
TARGET_URL = "https://www.tripadvisor.com.br/Restaurant_Review-g304560-d11852967-Reviews-Bode_do_No_Boa_Viagem-Recife_State_of_Pernambuco.html"
OUTPUT_FILENAME = "output.html"

# --- Main Script ---
# Use a try...finally block to ensure the browser always closes properly,
# even if there's an error.
driver = None  # Initialize driver to None
try:
    print("🚀 Starting the crawler...")

    driver = uc.Chrome(
        use_subprocess=False,
    )
    print("Page loaded successfully!")

    # --- Extract and Write HTML to File ---
    # Get the entire HTML source of the page
    page_html = driver.page_source
    print("Fetched the full page HTML.")

    # Write the HTML content to a file
    # 'w' mode overwrites the file if it exists
    # 'encoding="utf-8"' is important for handling special characters
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        f.write(page_html)

    print(f"✅ Successfully saved HTML to '{OUTPUT_FILENAME}'")


finally:
    # This block will run no matter what, ensuring the browser closes.
    if driver:
        print("\n✅ Crawler finished. Closing browser.")
        driver.quit()