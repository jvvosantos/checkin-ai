const extractRestaurantData = () => {
  const restaurant = {};

  // --- Step 1: Prioritize the structured JSON-LD data ---
  const jsonLdScript = Array.from(
    document.querySelectorAll('script[type="application/ld+json"]')
  ).find((script) =>
    script.textContent.includes('"@type":"FoodEstablishment"')
  );

  if (jsonLdScript) {
    const data = JSON.parse(jsonLdScript.textContent);

    restaurant.name = data.name || null;
    restaurant.address = {
      street: data.address?.streetAddress || null,
      city: data.address?.addressLocality || null,
      state: data.address?.addressRegion || null,
      postalCode: data.address?.postalCode || null,
      full: `${data.address?.streetAddress || ""}, ${
        data.address?.addressLocality || ""
      }, ${data.address?.addressRegion || ""} ${
        data.address?.postalCode || ""
      }`.trim(),
    };
    restaurant.phone = data.telephone || null;
    restaurant.website =
      document.querySelector('[data-automation="restaurantsWebsiteButton"]')
        ?.href || null;
    restaurant.coordinates = {
      latitude: data.geo?.latitude || null,
      longitude: data.geo?.longitude || null,
    };
    restaurant.rating = data.aggregateRating?.ratingValue || null;
    restaurant.reviewCount = data.aggregateRating?.reviewCount || null;
    restaurant.priceRange = data.priceRange || null;
    restaurant.cuisines = data.servesCuisine || [];

    // Process opening hours into a cleaner format
    if (data.openingHoursSpecification) {
      restaurant.openingHours = {};
      data.openingHoursSpecification.forEach((spec) => {
        // Taking the English day name for consistency
        const day = spec.dayOfWeek;
        restaurant.openingHours[day] = `${spec.opens} – ${spec.closes}`;
      });
    }
  } else {
    console.warn(
      "⚠️ Could not find structured JSON-LD data. Falling back to manual scraping."
    );
    restaurant.name = document
      .querySelector("h1.biGQs._P.fiohW.hzzSG.CIuBz")
      ?.textContent.trim();
    restaurant.address = {
      full: document
        .querySelector('[data-automation="restaurantsMapLinkOnName"] span')
        ?.textContent.trim(),
    };
    restaurant.phone = document
      .querySelector('a[href^="tel:"]')
      ?.textContent.trim();
  }


  restaurant.features = [];
  const featureElements = document.querySelectorAll(
    ".iPiKu.f.e.Q1.RpLvz .rREKL .biGQs._P.pZUbB.avBIb.AWdfh"
  );
  featureElements.forEach((el) => {
    restaurant.features.push(el.textContent.trim());
  });

  return restaurant;
};

const exportJson = (filename, json) => {
  var link = document.createElement("a");
  link.setAttribute(
    "href",
    "data:application/json;charset=utf-8,%EF%BB%BF" + encodeURIComponent(json)
  );
  link.setAttribute("download", `${filename}.json`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const visitPage = async (url) => {
  window.location = url;
  await new Promise((resolve) => setTimeout(resolve, 3000));
};

// const URLS_FILE = "restaurantes_links.txt";
const URLS_STR =
  "https://www.tripadvisor.com.br/Restaurant_Review-g304560-d11852967-Reviews-Bode_do_No_Boa_Viagem-Recife_State_of_Pernambuco.html";
const urls = URLS_STR.split(",")
  .map((url) => url.trim())
  .filter((url) => url);

console.log(`Found ${urls.length} URLs to process.`);

for (let i = 0; i < urls.length; i++) {
  await visitPage(urls[i]);
  const restaurantInfo = extractRestaurantData();
  exportJson(restaurantInfo.name, restaurantInfo);
}
