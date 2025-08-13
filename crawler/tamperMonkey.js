// ==UserScript==
// @name         Export TripAdvisor
// @namespace    http://tampermonkey.net/
// @version      2025-08-12
// @description  try to take over the world!
// @author       You
// @match        https://www.tripadvisor.com.br/Restaurant_Review*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=tripadvisor.com.br
// @grant        none
// ==/UserScript==

(function () {
  "use strict";
  const restaurant = {};

  // --- Step 1: Prioritize the structured JSON-LD data ---
  const jsonLdScript = Array.from(
    document.querySelectorAll('script[type="application/ld+json"]')
  ).find((script) =>
    script.textContent.includes('"@type":"FoodEstablishment"')
  );

  if (jsonLdScript) {
    console.log(
      "Found structured JSON-LD data. Using it as the primary source."
    );
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

  // The "VANTAGENS" (Features) are not in the JSON-LD, so we grab them from the page.
  restaurant.features = [];
  const featureElements = document.querySelectorAll(
    ".iPiKu.f.e.Q1.RpLvz .rREKL .biGQs._P.pZUbB.avBIb.AWdfh"
  );
  featureElements.forEach((el) => {
    restaurant.features.push(el.textContent.trim());
  });

  restaurant.description = document
    .querySelector("div.pZUbB.avBIb.AWdfh")
    ?.textContent.trim();

  const tagTexts = Array.from(
    document.querySelectorAll("span.bTeln span.AWdfh")
  ).map((el) => el.textContent.trim());
  const cuisineTypes = originalArray.filter((item) => {
    return !item.includes(" ") && !/^\$+$/.test(item);
  });

  restaurant.cuisinePrimary = cuisineTypes.length > 0 ? cuisineTypes[0] : undefined;
  restaurant.cuisineSecond = cuisineTypes.length > 1 ? cuisineTypes[1] : undefined;

  var link = document.createElement("a");
  link.setAttribute(
    "href",
    "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(restaurant))
  );
  link.setAttribute("download", `${restaurant.name}.json`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.close();
})();
