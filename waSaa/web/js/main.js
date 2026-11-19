const API_BASE = "http://127.0.0";


document.addEventListener("DOMContentLoaded", () => {
    loadDropdownMetadata();
    loadHomepageRecommendations();

    const searchForm = document.getElementById("search-form");
    if (searchForm) {
        searchForm.addEventListener("submit", handleSearchSubmit);
    }
});

/* ==========================================================================
   1. FAVORITES MANAGEMENT (localStorage)
   ========================================================================== */
function getFavorites() {
    try {
        return JSON.parse(localStorage.getItem("wasaa_favorites")) || [];
    } catch (e) {
        return [];
    }
}

function toggleFavorite(service) {
    let favorites = getFavorites();
    const index = favorites.findIndex(f => f.service_name === service.service_name);

    if (index > -1) {
        favorites.splice(index, 1); // Remove if already in favorites
    } else {
        favorites.push(service); // Add to favorites
    }

    localStorage.setItem("wasaa_favorites", JSON.stringify(favorites));
}

/* ==========================================================================
   2. DYNAMIC CATEGORY IMAGE MAPPER
   ========================================================================== */
function getCategoryImage(categoryString) {
    const cat = (categoryString || "").toLowerCase();
    if (cat.includes("vet") || cat.includes("pet") || cat.includes("animal")) {
        return "https://images.unsplash.com/photo-1548767797-d8c844163c4c?w=500&q=80";
    } else if (cat.includes("doctor") || cat.includes("hospital") || cat.includes("urgent care") || cat.includes("health") || cat.includes("medical")) {
        return "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=500&q=80";
    } else if (cat.includes("auto") || cat.includes("car") || cat.includes("tire") || cat.includes("repair") || cat.includes("automotive")) {
        return "https://images.unsplash.com/photo-1486006920555-c77dce18193b?w=500&q=80";
    } else if (cat.includes("home") || cat.includes("contractor") || cat.includes("floor") || cat.includes("appliance")) {
        return "https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=500&q=80";
    } else if (cat.includes("optometrist") || cat.includes("eyewear") || cat.includes("optician")) {
        return "https://images.unsplash.com/photo-1591076482161-42ce6da69f67?w=500&q=80";
    }
    return "https://images.unsplash.com/photo-1521737711867-e3b97375f902?w=500&q=80";
}

/* ==========================================================================
   3. CARD RENDERER WITH INTERACTIVE HEART
   ========================================================================== */
function createServiceCard(item) {
    const card = document.createElement("div");
    card.className = "service-card";

    const title = item.service_name || item.name || "Lifestyle Service";
    const area = item.area || item.city || "Tampa";
    const category = item.category || item.tags || "General";
    const imageUrl = getCategoryImage(category);

    const favorites = getFavorites();
    const isFav = favorites.some(f => f.service_name === title);

    card.innerHTML = `
        <div class="card-image-wrapper">
            <img src="${imageUrl}" alt="${title}" loading="lazy">
            <button class="btn-fav-toggle ${isFav ? 'is-active' : ''}" title="Save to Favorites">❤️</button>
        </div>
        <div class="card-body">
            <div>
                <h3 class="card-title">${title}</h3>
                <p class="card-tags">🏷️ ${category}</p>
            </div>
            <div class="card-footer">
                <span class="location-badge">📍 ${area}</span>
            </div>
        </div>
    `;

    const favBtn = card.querySelector(".btn-fav-toggle");
    favBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();

        const serviceData = {
            service_name: title,
            category: category,
            area: area,
            image: imageUrl
        };

        toggleFavorite(serviceData);
        favBtn.classList.toggle("is-active");
    });

    return card;
}

/* ==========================================================================
   4. METADATA & API LOADERS
   ========================================================================== */
async function loadDropdownMetadata() {
    try {
        const response = await fetch(`${API_BASE}/meta`);
        const meta = await response.json();

        const categorySelect = document.getElementById("search-category");
        if (categorySelect) {
            categorySelect.innerHTML = '<option value="">All Sectors</option>';
            meta.categories.forEach(cat => {
                const opt = document.createElement("option");
                opt.value = cat;
                opt.textContent = cat;
                categorySelect.appendChild(opt);
            });
        }

        const areaList = document.getElementById("area-list");
        if (areaList) {
            areaList.innerHTML = "";
            meta.areas.forEach(area => {
                const opt = document.createElement("option");
                opt.value = area;
                areaList.appendChild(opt);
            });
        }
    } catch (err) {
        console.error("Failed to load metadata options:", err);
    }
}

async function loadHomepageRecommendations() {
    const listDiv = document.getElementById("recommendations-list");
    if (!listDiv) return;

    try {
        const response = await fetch(`${API_BASE}/recommendations`);
        const data = await response.json();

        listDiv.innerHTML = "";
        data.data.forEach(item => {
            listDiv.appendChild(createServiceCard(item));
        });
    } catch (err) {
        console.error("Error loading recommendations:", err);
        listDiv.innerHTML = "<p>Unable to load recommendations.</p>";
    }
}

async function handleSearchSubmit(event) {
    if (event) event.preventDefault();

    const query = document.getElementById("search-query").value;
    const category = document.getElementById("search-category").value;
    const area = document.getElementById("search-area").value;

    const resultsContainer = document.getElementById("results-container");
    const resultsList = document.getElementById("results-list");
    const resultsCount = document.getElementById("results-count");

    try {
        const url = new URL(`${API_BASE}/search`);
        url.searchParams.append("query", query || "top services");
        if (category) url.searchParams.append("category", category);
        if (area) url.searchParams.append("area", area);

        const response = await fetch(url);
        const data = await response.json();

        resultsList.innerHTML = "";

        if (data.data.length === 0) {
            resultsList.innerHTML = "<p>No matching lifestyle services found.</p>";
            resultsCount.textContent = "0 matches";
        } else {
            resultsCount.textContent = `${data.data.length} matches found`;
            data.data.forEach(item => {
                resultsList.appendChild(createServiceCard(item));
            });
        }

        resultsContainer.style.display = "block";
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
        console.error("Error running search query:", err);
    }
}

