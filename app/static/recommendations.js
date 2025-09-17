document.addEventListener('DOMContentLoaded', function() {
    // --- Sidebar ---
    const menuToggle = document.getElementById('menuToggle');
    const closeSidebarBtn = document.getElementById('closeSidebar');
    const sidebar = document.getElementById('sidebar');
    const body = document.body;

    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.add('open');
            body.classList.add('sidebar-open');
        });
    }
    if (closeSidebarBtn) {
        closeSidebarBtn.addEventListener('click', () => {
            sidebar.classList.remove('open');
            body.classList.remove('sidebar-open');
        });
    }

    // --- Rekomendacje i paginacja ---
    const recommendationsList = document.getElementById('recommendationsList');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const pageIndicator = document.getElementById('currentPageIndicator');

    let allRecommendations = Array.from(recommendationsList.querySelectorAll('.movie-item-content')).map(item => ({
        element: item,
        title: item.querySelector('.movie-title')?.textContent?.trim(),
        movie_id: item.dataset.movieId
    }));

    const itemsPerPage = 5;
    let currentPage = 0;
    const totalPages = Math.ceil(allRecommendations.length / itemsPerPage);

    function renderPage(page) {
        if (!recommendationsList) return;
        recommendationsList.innerHTML = "";

        const start = page * itemsPerPage;
        const end = start + itemsPerPage;
        const pageItems = allRecommendations.slice(start, end);

        pageItems.forEach(rec => {
            const li = document.createElement('li');
            li.appendChild(rec.element);
            recommendationsList.appendChild(li);
        });

        prevBtn.disabled = (page === 0);
        nextBtn.disabled = (page >= totalPages - 1);
        pageIndicator.textContent = (page + 1);
    }

    prevBtn?.addEventListener('click', () => {
        if (currentPage > 0) {
            currentPage--;
            renderPage(currentPage);
        }
    });

    nextBtn?.addEventListener('click', () => {
        if (currentPage < totalPages - 1) {
            currentPage++;
            renderPage(currentPage);
        }
    });

    renderPage(currentPage);

    // --- Powiadomienia ---
    function showNotification(message) {
        const notif = document.getElementById("notification");
        if (!notif) return;
        notif.textContent = message;
        notif.classList.add("show");
        setTimeout(() => notif.classList.remove("show"), 2000);
    }

    // --- Obsługa checkboxów (delegacja) ---
    document.addEventListener('change', async (e) => {
        const target = e.target;
        if (!target.classList.contains('watchlist-checkbox') &&
            !target.classList.contains('watched-checkbox') &&
            !target.classList.contains('favorite-checkbox')) return;

        if (target.dataset.sending) return; // jeśli już wysyłamy, ignoruj kolejne eventy
        target.dataset.sending = true;

        const parent = target.closest('.movie-item-content');
        const movie_id = target.dataset.movieId;
        const movieTitle = parent?.querySelector('.movie-title')?.textContent?.trim() || '';

        let endpoint = '';
        let bodyData = { movie_id: movie_id };

    if (target.classList.contains('watchlist-checkbox')) {
        if (target.checked) {
            // Dodaj do watchlisty
            endpoint = '/add_to_watchlist';
            bodyData.watched = 0;

            // jeśli był zaznaczony watched, odznaczamy
            const watchedCheckbox = parent.querySelector('.watched-checkbox');
            if (watchedCheckbox && watchedCheckbox.checked) watchedCheckbox.checked = false;
        } else {
            // Odznaczenie → usuń z watchlisty
            endpoint = '/remove_from_watchlist';
        }

    } else if (target.classList.contains('watched-checkbox')) {
        if (target.checked) {
            // Zaznaczenie jako watched
            endpoint = '/add_to_watchlist';
            bodyData.watched = 1;

            // odznaczamy watchlist, jeśli był zaznaczony
            const watchlistCheckbox = parent.querySelector('.watchlist-checkbox');
            if (watchlistCheckbox && watchlistCheckbox.checked) watchlistCheckbox.checked = false;
        } else {
            // Odznaczenie watched → ustaw watched=0 (ale pozostaw w watchlist?)
            endpoint = '/add_to_watchlist';
            bodyData.watched = 0;
        }

    } else if (target.classList.contains('favorite-checkbox')) {
        endpoint = target.checked ? '/favorites/add' : '/favorites/remove';
    }

    target.disabled = true;


        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify(bodyData)
            });
            const data = await res.json().catch(() => ({}));

            if (!res.ok || data.error || data.success === false) {
                target.checked = !target.checked;
                showNotification(`❌ ${data.error || 'Server error'}`);
            } else {
                let labelText = '';
                if (target.classList.contains('watchlist-checkbox')) labelText = "watchlist";
                if (target.classList.contains('watched-checkbox')) labelText = "watched movies";
                if (target.classList.contains('favorite-checkbox')) labelText = "favorites";
                showNotification(`✔ "${movieTitle}" added to ${labelText}`);
            }
        } catch {
            target.checked = !target.checked;
            showNotification('⚠️ Connection error – Try again.');
        } finally {
            target.disabled = false;
            delete target.dataset.sending; // reset flagi
        }
    });


    // --- Modal filmowy ---
    const modal = document.getElementById('movieModal');
    const modalBody = document.getElementById('modalBody');
    const closeModalBtn = document.querySelector('.close-modal');

    if (modal && modalBody && closeModalBtn) {
        closeModalBtn.onclick = () => modal.style.display = "none";
        window.onclick = (event) => { if (event.target == modal) modal.style.display = "none"; };

        document.addEventListener('click', async (e) => {
            const movieEl = e.target.closest('.movie-item-content');
            if (!movieEl) return;

            if (e.target.closest('input[type="checkbox"], label.checkbox-container, .custom-checkbox')) return;

            const movieId = movieEl.dataset.movieId;
            if (!movieId) return;

            try {
                const res = await fetch('/movie_details', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ movie_id: movieId })
                });
                const data = await res.json();

                modalBody.innerHTML = `
                    <img class="modal-poster" src="${data.poster_path || ''}" alt="${data.title}">
                    <div class="modal-info">
                        <h2>${data.title}</h2>
                        <p>${data.overview || 'No description'}</p>
                        ${Array.isArray(data.genres) ? `<p><strong>Gatunki:</strong> ${data.genres.join(', ')}</p>` : ''}
                        ${Array.isArray(data.production_companies) ? `<p><strong>Studia:</strong> ${data.production_companies.join(', ')}</p>` : ''}
                        ${Array.isArray(data.production_countries) ? `<p><strong>Kraje produkcji:</strong> ${data.production_countries.join(', ')}</p>` : ''}
                        ${data.vote_average ? `<p><strong>Ocena:</strong> ${data.vote_average}</p>` : ''}
                    </div>
                `;
                modal.style.display = 'block';
            } catch {
                showNotification("⚠️ Not able to download movie details");
            }
        });
    }
});
