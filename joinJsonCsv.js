// This script requires Node.js to be installed on your system.
// It uses built-in modules, so no external packages are needed.
const fs = require("fs/promises");
const path = require("path");

/**
 * @description Sanitizes a string for CSV format. It wraps the string in double quotes
 * and escapes any existing double quotes within the string by doubling them.
 * @param {string} value - The string to sanitize.
 * @returns {string} The CSV-safe string.
 */
function sanitizeForCSV(value) {
  // If the value is null or undefined, return an empty string.
  if (value === null || value === undefined) {
    return '""';
  }

  // Convert value to string.
  let strValue = String(value);

  // Escape any double quotes by replacing them with two double quotes.
  strValue = strValue.replace(/"/g, '""');

  // Wrap the entire string in double quotes.
  return `"${strValue}"`;
}

/**
 * @description Main function to read JSON files and convert them to a single CSV file.
 */
async function createDatabase() {
  const inputDir = "restaurants";
  const outputFile = "restaurants.csv";

  console.log(`🚀 Reading JSON files from the '${inputDir}' directory...`);

  try {
    // 1. Get a list of all files in the input directory.
    const files = await fs.readdir(inputDir);

    // 2. Filter the list to include only .json files.
    const jsonFiles = files.filter(
      (file) => path.extname(file).toLowerCase() === ".json"
    );

    if (jsonFiles.length === 0) {
      console.error(`❌ No .json files found in the '${inputDir}' directory.`);
      return;
    }

    console.log(`✅ Found ${jsonFiles.length} JSON files to process.`);

    // 3. Define the CSV headers. These should match the keys in your JSON files.
    const headers = [
      "name",
      "description",
      "cuisinePrimary",
      "cuisineSecond",
      "address_full",
      "phone",
      "website",
      "latitude",
      "longitude",
      "rating",
      "reviewCount",
      "priceRange",
      "features",
    ];
    let csvContent = headers.join(",") + "\n"; // Start with the header row

    // 4. Loop through each JSON file.
    for (const fileName of jsonFiles) {
      const filePath = path.join(inputDir, fileName);
      try {
        // Read and parse the JSON file.
        const fileContent = await fs.readFile(filePath, "utf-8");
        const data = JSON.parse(fileContent);

        // 5. Create a CSV row by safely accessing JSON data.
        // This prevents errors if a key or nested object is missing.
        const rowData = {
          name: data.name || "",
          description: data.description || "",
          cuisinePrimary: data.cuisineSecond || "",
          cuisineSecondary: data.cuisinePrimary || "",
          address_full: data.address ? data.address.full : "",
          phone: data.phone || "",
          website: data.website || "",
          latitude: data.coordinates ? data.coordinates.latitude : "",
          longitude: data.coordinates ? data.coordinates.longitude : "",
          rating: data.rating ? Number.parseFloat(data.rating) : -1, // Let NULL handle empty values
          reviewCount: data.reviewCount
            ? Number.parseInt(data.reviewCount)
            : -1, // Let NULL handle empty values
          priceRange: data.priceRange || "",
          features: data.features ? data.features.join("; ") : "",
        };

        const row = headers
          .map((header) => {
            if (header === "rating" || header === "reviewCount") return rowData[header];
              return sanitizeForCSV(rowData[header]);
          })
          .join(",");

        // Add the new row to our CSV content string.
        csvContent += row + "\n";
      } catch (error) {
        console.error(
          `⚠️ Could not process file '${fileName}'. Error: ${error.message}`
        );
      }
    }

    // 6. Write the complete CSV content to the output file.
    await fs.writeFile(outputFile, csvContent);
    console.log(
      `\n🎉 Success! All data has been compiled into '${outputFile}'.`
    );
  } catch (error) {
    console.error("An unexpected error occurred:", error);
  }
}

// Run the main function.
createDatabase();
