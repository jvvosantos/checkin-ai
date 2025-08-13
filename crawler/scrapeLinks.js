scrapeTripadvisorRestaurantLinks = async () => {
  let allLinks = new Set();
  let currentPage = 1;

  while (true) {
    console.log(`Scraping page ${currentPage}...`);

    let restaurantUrls = Array.from(document.querySelectorAll('a.BMQDV.ukgoS')).map(link => link.href);

    // Skip first 3 and remove duplicates
    restaurantUrls = restaurantUrls.slice(4);
    restaurantUrls = [...new Set(restaurantUrls)];

    allLinks = new Set([...allLinks, ...restaurantUrls]);

    console.log(
      `Found ${restaurantUrls.length} links on this page. Total unique links so far: ${allLinks.size}`
    );

    const nextButton = document.querySelector(
      'a[data-smoke-attr="pagination-next-arrow"]'
    );

    if (nextButton) {
      console.log("Navigating to the next page...");
      nextButton.click();
      currentPage++;

      // overshoot wait for page to load
      await new Promise((resolve) => setTimeout(resolve, 3000));
    } else {
      console.log("Scraping finished. No more pages found.");
      break;
    }
  }

  const linksArray = Array.from(allLinks);

  console.log(
    `\n✅ --- All ${linksArray.length} Unique Restaurant Links Found ---`
  );
  linksArray.forEach((link, index) => {
    console.log(`${index + 1}. ${link}`);
  });

  window.allRestaurantLinks = linksArray;
}

const exportLinks = (filename, links) => {
  exportFile(
    filename,
    "data:text/plain;charset=utf-8,%EF%BB%BF" + encodeURIComponent(links)
  );
};

const exportFile = (filename, content) => {
  var link = document.createElement("a");
  link.setAttribute("href", content);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};


const FILENAME = "restaurantes_links.txt";
await scrapeTripadvisorRestaurantLinks();
exportLinks(FILENAME, window.allRestaurantLinks);
